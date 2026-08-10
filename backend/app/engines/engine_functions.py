"""Pure function implementations of engines.

Each function receives EngineContext and returns modified EngineContext.
No classes, no internal state - just pure transformations.
"""

import io
from datetime import UTC, datetime
from typing import Any, cast

import pandas as pd
import tiktoken

from app.core.config import settings
from app.engines.context_models import EngineContext

# Module-level encoding (initialized once)
_tokenizer_encoding = None


def _get_encoding() -> tiktoken.Encoding:
    global _tokenizer_encoding
    if _tokenizer_encoding is None:
        _tokenizer_encoding = tiktoken.get_encoding(settings.TOKENIZER_ENCODING)
    return _tokenizer_encoding


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

