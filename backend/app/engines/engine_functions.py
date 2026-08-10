"""Pure function implementations of engines.

Each function receives EngineContext and returns modified EngineContext.
No classes, no internal state - just pure transformations.
"""

import asyncio
import hashlib
import io
import json
import time
from datetime import UTC, datetime
from typing import Any, cast

import httpx
import pandas as pd
import tiktoken
from cachetools import LRUCache
from deep_translator import GoogleTranslator
from loguru import logger
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.engines.context_models import EngineContext, RecordDict

# Module-level encoding (initialized once)
_tokenizer_encoding = None
_analyze_encoding = None

# Module-level state for engines with persistent state
_optimization_cache: LRUCache | None = None
_optimization_semaphore: asyncio.Semaphore | None = None
_analyze_semaphore: asyncio.Semaphore | None = None


def _get_encoding() -> tiktoken.Encoding:
    global _tokenizer_encoding
    if _tokenizer_encoding is None:
        _tokenizer_encoding = tiktoken.get_encoding(settings.TOKENIZER_ENCODING)
    return _tokenizer_encoding


def _get_analyze_encoding() -> tiktoken.Encoding:
    global _analyze_encoding
    if _analyze_encoding is None:
        _analyze_encoding = tiktoken.get_encoding(settings.TOKENIZER_ENCODING)
    return _analyze_encoding


def _get_optimization_cache() -> LRUCache:
    global _optimization_cache
    if _optimization_cache is None:
        _optimization_cache = LRUCache(maxsize=10000)
    return _optimization_cache


def _get_optimization_semaphore() -> asyncio.Semaphore:
    global _optimization_semaphore
    if _optimization_semaphore is None:
        _optimization_semaphore = asyncio.Semaphore(20)
    return _optimization_semaphore


def _get_analyze_semaphore() -> asyncio.Semaphore:
    global _analyze_semaphore
    if _analyze_semaphore is None:
        _analyze_semaphore = asyncio.Semaphore(20)
    return _analyze_semaphore


# ... (rest of existing functions remain the same)


def tokenizer_engine(context: EngineContext) -> EngineContext:
    """Count tokens for each record using tiktoken encoding."""
    encoding = _get_encoding()
    total_tokens = 0

    for record in context.records:
        text = record.get("optimized_text", record.get("text", ""))
        tokens = encoding.encode(text)
        token_count = len(tokens)
        record["token_count"] = token_count
        total_tokens += token_count

    context.metrics.total_tokens = total_tokens
    context.metrics.avg_tokens_per_record = total_tokens / max(len(context.records), 1)
    return context


COST_PER_MILLION_TOKENS = 2.50


def cost_engine(context: EngineContext) -> EngineContext:
    """Calculate costs at $2.50 USD per million tokens.
    Supports daily (10k reviews) and monthly (300k reviews) projections."""
    total_tokens = context.metrics.total_tokens
    total_input_tokens = context.metrics.total_input_tokens
    tokens = total_tokens or total_input_tokens

    estimated_cost = (tokens / 1_000_000) * COST_PER_MILLION_TOKENS

    total_records = context.metadata.total_records
    avg_tokens_per_record = tokens / max(total_records, 1)

    daily_10k = avg_tokens_per_record * 10_000
    monthly_300k = avg_tokens_per_record * 300_000

    context.metrics.cost_per_million_tokens = COST_PER_MILLION_TOKENS
    context.metrics.estimated_cost = round(estimated_cost, 6)
    context.metrics.daily_estimate_10k_reviews = {
        "total_tokens": round(daily_10k),
        "cost_usd": round((daily_10k / 1_000_000) * COST_PER_MILLION_TOKENS, 2),
    }
    context.metrics.monthly_estimate_300k_reviews = {
        "total_tokens": round(monthly_300k),
        "cost_usd": round(
            (monthly_300k / 1_000_000) * COST_PER_MILLION_TOKENS, 2
        ),
    }

    return context


def export_engine(context: EngineContext) -> EngineContext:
    """Export records to Excel, JSON, or CSV formats."""
    formats = context.metadata.export_formats or ["json"]
    records = context.records
    results = context.results

    merged = []
    for i, record in enumerate(records):
        row = record.model_dump()
        if i < len(results):
            result_item = results[i]
            row["result"] = (
                result_item.model_dump()
                if hasattr(result_item, "model_dump")
                else result_item
            )
        merged.append(row)

    exports: dict[str, Any] = {}
    for fmt in formats:
        df = pd.DataFrame(merged)
        buffer = io.BytesIO()
        if fmt == "excel":
            df.to_excel(buffer, index=False)
            buffer.seek(0)
            exports[fmt] = buffer.getvalue()
        elif fmt == "csv":
            df.to_csv(buffer, index=False)
            buffer.seek(0)
            exports[fmt] = buffer.getvalue()
        else:
            result_bytes = df.to_json(orient="records").encode("utf-8")
            exports[fmt] = result_bytes

    context.metadata.exports = exports
    return context


def validation_engine(context: EngineContext) -> EngineContext:
    """Validate required columns and filter out invalid records."""
    required_columns = context.metadata.required_columns or []
    validated = []
    rejected = 0

    for i, record in enumerate(context.records):
        missing = [col for col in required_columns if col not in record or not record[col]]
        if missing:
            context.add_error(
                "validation",
                f"Missing required columns: {missing}",
                record_index=i,
            )
            rejected += 1
            continue
        validated.append(record)

    context.records = validated
    context.metrics.validated_count = len(validated)
    context.metrics.rejected_count = rejected
    return context


def history_engine(context: EngineContext) -> EngineContext:
    """Track execution metadata, metrics, and performance history."""
    metrics_dict = (
        context.metrics.model_dump()
        if hasattr(context.metrics, "model_dump")
        else dict(context.metrics)
    )
    summary = {
        "batch_id": context.batch_id,
        "batch_index": context.batch_index,
        "total_batches": context.total_batches,
        "timestamp": datetime.now(UTC).isoformat(),
        "record_count": len(context.records),
        "metrics": metrics_dict,
        "error_count": len(context.errors),
    }
    history = context.metadata.history or []
    history.append(summary)
    context.metadata.history = history
    return context


def token_compare_engine(context: EngineContext) -> EngineContext:
    """Compare token counts between original (Spanish) and translated (English) text.
    Used for cost analysis and optimization reporting."""
    encoding = _get_encoding()
    records = context.records
    cost_per_million = getattr(settings, "LLM_PRICE_PER_1M_TOKENS", 2.50)

    total_original = 0
    total_translated = 0

    for record in records:
        original = record.get("reseña", record.get("text", ""))
        translated = record.get("optimized_text", original)

        orig_tokens = len(encoding.encode(original)) if original else 0
        trans_tokens = len(encoding.encode(translated)) if translated else 0

        record["tokens_original"] = orig_tokens
        record["tokens_translated"] = trans_tokens
        record["token_diff"] = orig_tokens - trans_tokens

        total_original += orig_tokens
        total_translated += trans_tokens

    total_diff = total_original - total_translated
    cost_original = (total_original / 1_000_000) * cost_per_million
    cost_translated = (total_translated / 1_000_000) * cost_per_million
    cost_savings = cost_original - cost_translated

    n = max(len(records), 1)
    factor_daily = 10000 / n
    factor_monthly = 300000 / n

    context.metrics.token_comparison = {
        "total_original_tokens": total_original,
        "total_translated_tokens": total_translated,
        "token_difference": total_diff,
        "percentage_reduction": round((total_diff / max(total_original, 1)) * 100, 2),
        "cost_original_usd": round(cost_original, 4),
        "cost_translated_usd": round(cost_translated, 4),
        "cost_savings_usd": round(cost_savings, 4),
        "cost_per_million_tokens": cost_per_million,
        "daily_projection_10k": {
            "tokens_original": round(total_original * factor_daily),
            "tokens_translated": round(total_translated * factor_daily),
            "cost_original_usd": round(cost_original * factor_daily, 2),
            "cost_translated_usd": round(cost_translated * factor_daily, 2),
            "savings_usd": round(cost_savings * factor_daily, 2),
        },
        "monthly_projection_300k": {
            "tokens_original": round(total_original * factor_monthly),
            "tokens_translated": round(total_translated * factor_monthly),
            "cost_original_usd": round(cost_original * factor_monthly, 2),
            "cost_translated_usd": round(cost_translated * factor_monthly, 2),
            "savings_usd": round(cost_savings * factor_monthly, 2),
        },
    }

    return context


def input_engine(context: EngineContext) -> EngineContext:
    """Read Excel files (single file or folder) and convert to records."""
    file_path = context.metadata.file_path
    folder_path = context.metadata.folder_path

    if folder_path:
        return _process_folder(folder_path, context)
    elif file_path:
        return _process_file(file_path, context)
    else:
        context.add_error("input", "No file_path or folder_path provided")
        return context


def _process_file(file_path: str, context: EngineContext) -> EngineContext:
    import pandas as pd

    from app.engines.context_models import RecordDict

    try:
        df = pd.read_excel(file_path)
        context.metadata.columns = list(df.columns)
        context.metadata.total_records = len(df)
        context.metadata.source_type = "single_file"
        context.metadata.files_processed = [file_path]
        raw_records = df.to_dict(orient="records")
        context.records = [RecordDict(**cast(dict[str, Any], r)) for r in raw_records]
    except Exception as e:
        context.add_error("input", str(e))
    return context


def _process_folder(folder_path: str, context: EngineContext) -> EngineContext:
    from pathlib import Path

    import pandas as pd

    from app.engines.context_models import RecordDict

    folder = Path(folder_path)
    if not folder.exists() or not folder.is_dir():
        context.add_error("input", f"Folder not found: {folder_path}")
        return context

    excel_files = sorted(folder.glob("*.xlsx")) + sorted(folder.glob("*.xls"))
    if not excel_files:
        context.add_error("input", f"No Excel files found in: {folder_path}")
        return context

    all_records: list[RecordDict] = []
    files_processed: list[str] = []
    columns_detected: list[str] = []

    for excel_file in excel_files:
        try:
            df = pd.read_excel(excel_file)
            if not columns_detected:
                columns_detected = list(df.columns)
            raw_records = df.to_dict(orient="records")
            for record in raw_records:
                record["_source_file"] = excel_file.name
                all_records.append(RecordDict(**cast(dict[str, Any], record)))
            files_processed.append(str(excel_file))
        except Exception as e:
            context.add_error("input", str(e), file=str(excel_file))

    context.records = all_records
    context.metadata.columns = columns_detected
    context.metadata.total_records = len(all_records)
    context.metadata.source_type = "folder"
    context.metadata.files_processed = files_processed
    context.metadata.folder_path = folder_path

    return context


# =============================================================================
# OptimizationEngine - Translation with LRU cache, timeout, retry, concurrency
# =============================================================================

MAX_CONCURRENT_TRANSLATIONS = 20
TRANSLATION_TIMEOUT = 10.0  # seconds
MAX_RETRIES = 3
CACHE_MAX_SIZE = 10000


async def optimization_engine(context: EngineContext) -> EngineContext:
    """Translation, prompt normalization, deduplication with LRU cache and concurrency.
    Respects optimize_tokens flag: if False, skips translation entirely.
    Uses LRU cache (max 10000 entries) to avoid unbounded memory growth.
    """
    target_language = context.metadata.target_language or "en"
    optimize = context.metadata.optimize_tokens
    review_column = context.metadata.review_column or "reseña"

    if not optimize:
        for record in context.records:
            text = record.get(review_column, record.get("text", ""))
            record["optimized_text"] = text
            record["translation_hit"] = False
        context.metrics.translations_performed = 0
        context.metrics.translations_skipped = len(context.records)
        context.metrics.translation_hits = 0
        return context

    cache = _get_optimization_cache()
    semaphore = _get_optimization_semaphore()

    # Separate cached vs non-cached records
    to_translate: list[tuple[int, str]] = []  # (index, text)
    for i, record in enumerate(context.records):
        text = record.get(review_column, record.get("text", ""))
        key_data = {"text": text, "lang": target_language}
        cache_key = hashlib.md5(json.dumps(key_data).encode()).hexdigest()

        if cache_key in cache:
            record["optimized_text"] = cache[cache_key]
            record["translation_hit"] = True
        else:
            record["translation_hit"] = False
            to_translate.append((i, text))

    # Translate non-cached records concurrently
    translated_count = await _translate_batch(
        to_translate, target_language, context, cache, semaphore
    )

    skipped_count = len(context.records) - translated_count
    context.metadata.optimization_cache_size = len(cache)
    context.metrics.translations_performed = translated_count
    context.metrics.translations_skipped = skipped_count
    context.metrics.translation_hits = sum(
        1 for r in context.records if r.get("translation_hit")
    )

    return context


async def _translate_batch(
    to_translate: list[tuple[int, str]],
    target_language: str,
    context: EngineContext,
    cache: LRUCache,
    semaphore: asyncio.Semaphore,
) -> int:
    """Translate a batch of texts with controlled concurrency, timeout and retry."""
    if not to_translate:
        return 0

    translated_count = 0
    failed_count = 0

    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    async def _translate_with_retry(text: str, target_lang: str) -> str:
        translator = GoogleTranslator(source="auto", target=target_lang)
        return await asyncio.to_thread(translator.translate, text)

    async def translate_one(index: int, text: str) -> None:
        nonlocal translated_count, failed_count
        async with semaphore:
            normalized = _normalize(text)
            if not normalized:
                context.records[index]["optimized_text"] = normalized
                return

            try:
                optimized = await asyncio.wait_for(
                    _translate_with_retry(normalized, target_language),
                    timeout=10.0,
                )
                context.records[index]["optimized_text"] = optimized
                key_data = {"text": text, "lang": target_language}
                cache_key = hashlib.md5(json.dumps(key_data).encode()).hexdigest()
                cache[cache_key] = optimized
                translated_count += 1
            except TimeoutError:
                logger.warning(
                    "Translation timeout "
                    f"(10.0s) for record {index}: "
                    f"{text[:50]}..."
                )
                context.records[index]["optimized_text"] = normalized
                context.records[index]["translation_error"] = "timeout"
                failed_count += 1
            except Exception as e:
                logger.warning(
                    "Translation failed after "
                    f"3 retries for record {index}: "
                    f"{text[:50]}... Error: {e}"
                )
                context.records[index]["optimized_text"] = normalized
                context.records[index]["translation_error"] = str(e)[:200]
                failed_count += 1

    tasks = [translate_one(idx, text) for idx, text in to_translate]
    await asyncio.gather(*tasks)

    context.metrics.translation_failures = failed_count
    return translated_count


def _normalize(text: str) -> str:
    return text.strip().replace("\n", " ").replace("\t", " ")


# =============================================================================
# AnalyzeEngine - LLM-based review analysis with concurrency and retry
# =============================================================================

ANALYSIS_PROMPT = """You are an app review analyst.
Analyze the following review and extract:
1. "error_type": classify the issue (crash, bug, ui_issue,
   performance, feature_request, ux_problem, other)
2. "component": the specific app component affected
   (e.g., "login", "profile_picture_upload", "notifications",
   "inventory", "scanner", etc.)
3. "severity": how severe is the issue (critical, high, medium, low)
4. "summary": a one-line summary in English of the problem

Review text:
{text}

Respond ONLY with valid JSON in this exact format:
{{"error_type": "...", "component": "...", "severity": "...", "summary": "..."}}"""

SYSTEM_PROMPT = (
    "You are a precise technical analyst for mobile app reviews. "
    "Always respond with valid JSON only. No markdown, no extra text."
)

MAX_CONCURRENT = 20
MAX_RETRIES = 3
LLM_TIMEOUT = 60.0  # seconds


def analyze_engine(context: EngineContext) -> EngineContext:
    """Sync phase: prepare records, count tokens, mark empty reviews."""
    records = context.records
    optimize_tokens = context.metadata.optimize_tokens

    context.metrics.total_records_input = len(records)
    context.metrics.optimize_tokens_enabled = optimize_tokens
    context.metrics.start_time = time.time()

    encoding = _get_analyze_encoding()
    total_input_tokens = 0
    empty_count = 0

    for record in records:
        text = record.get("reseña", record.get("text", ""))
        if not text or not text.strip():
            empty_count += 1
            record["_skip_analysis"] = True
            record["token_count_original"] = 0
            continue
        tokens = encoding.encode(text)
        record["token_count_original"] = len(tokens)
        total_input_tokens += len(tokens)

    context.metrics.total_input_tokens = total_input_tokens
    context.metrics.empty_reviews = empty_count
    context.metrics.reviews_to_analyze = len(records) - empty_count

    return context


async def analyze_async_engine(context: EngineContext) -> list[dict[str, Any]]:
    """Async phase: run batch LLM analysis with concurrency and retry."""
    records = context.records
    results: list[dict[str, Any] | None] = [None] * len(records)
    semaphore = _get_analyze_semaphore()
    tasks = []

    for i, record in enumerate(records):
        if record.get("_skip_analysis"):
            results[i] = {
                "record_index": i,
                "error_type": "empty",
                "component": "none",
                "severity": "none",
                "summary": "Empty review, no analysis possible.",
                "tokens_used": 0,
            }
            continue
        tasks.append(_analyze_single(i, record, semaphore, results))

    if tasks:
        await asyncio.gather(*tasks)

    context.results = results  # type: ignore[assignment]

    context.metrics.cost_per_million = 2.50
    context.metrics.estimated_cost_input = round(
        (context.metrics.total_input_tokens / 1_000_000) * 2.50, 4
    )

    elapsed = time.time() - context.metrics.start_time
    context.metrics.processing_time_seconds = round(elapsed, 2)
    context.metrics.reviews_per_second = round(
        len(records) / max(elapsed, 0.001), 1
    )

    return results  # type: ignore[return-value]


async def _analyze_single(
    index: int,
    record: RecordDict,
    semaphore: asyncio.Semaphore,
    results: list[dict[str, Any] | None],
) -> None:
    async with semaphore:
        text = record.get("reseña", record.get("text", ""))
        optimized_text = record.get("optimized_text", text)

        prompt_text = optimized_text if optimized_text else text
        prompt_tokens = len(_get_analyze_encoding().encode(prompt_text))

        try:
            result = await _call_llm_with_retry(prompt_text)
            tokens_used = len(_get_analyze_encoding().encode(result))
            parsed = _parse_response(result)

            results[index] = {
                "record_index": index,
                **parsed,
                "tokens_used": prompt_tokens + tokens_used,
                "raw_response": result,
            }
        except Exception as e:
            results[index] = {
                "record_index": index,
                "error_type": "analysis_failed",
                "component": "unknown",
                "severity": "unknown",
                "summary": f"Failed after 3 attempts: {str(e)[:80]}",
                "tokens_used": 0,
                "raw_response": None,
                "error": str(e)[:200],
            }


@retry(
    wait=wait_exponential(multiplier=1, min=1, max=20),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type((httpx.HTTPError, asyncio.TimeoutError)),
    reraise=True,
)
async def _call_llm_with_retry(text: str) -> str:
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not configured")

    prompt_content = ANALYSIS_PROMPT.replace("{text}", text[:2000])

    async with httpx.AsyncClient(timeout=LLM_TIMEOUT) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.LLM_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt_content},
                ],
                "max_tokens": 300,
                "temperature": 0.1,
            },
        )
        resp.raise_for_status()
        data = resp.json()

        if not data.get("choices") or not data["choices"]:
            raise ValueError("OpenAI response missing 'choices'")

        content = data["choices"][0]["message"]["content"]
        return content.strip() if content else ""


def _parse_response(raw: str) -> dict[str, Any]:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

    try:
        parsed = json.loads(cleaned)
        return {
            "error_type": parsed.get("error_type", "unknown"),
            "component": parsed.get("component", "unknown"),
            "severity": parsed.get("severity", "unknown"),
            "summary": parsed.get("summary", "No summary"),
        }
    except json.JSONDecodeError:
        return {
            "error_type": "parse_error",
            "component": "unknown",
            "severity": "unknown",
            "summary": f"Failed to parse LLM response: {cleaned[:200]}",
        }

