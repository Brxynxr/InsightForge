import asyncio
import json
import time
from typing import Any

import httpx
import tiktoken
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.engines.base import BaseEngine, EngineContext

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


class AnalyzeEngine(BaseEngine):
    """Optimized engine for batch analysis of app reviews using LLM.
    Designed for high-throughput processing (150k+ reviews)."""

    BATCH_SIZE = 50
    MAX_CONCURRENT = 20
    MAX_RETRIES = 3
    RETRY_BASE_DELAY = 1.0
    LLM_TIMEOUT = 60.0  # seconds

    def __init__(self) -> None:
        self._encoding = tiktoken.get_encoding(settings.TOKENIZER_ENCODING)

    def execute(self, context: EngineContext) -> EngineContext:
        records = context.records
        optimize_tokens = context.metadata.get("optimize_tokens", True)

        context.metrics["total_records_input"] = len(records)
        context.metrics["optimize_tokens_enabled"] = optimize_tokens
        context.metrics["start_time"] = time.time()

        total_input_tokens = 0
        empty_count = 0
        for record in records:
            text = record.get("reseña", record.get("text", ""))
            if not text or not text.strip():
                empty_count += 1
                record["_skip_analysis"] = True
                record["token_count_original"] = 0
                continue
            tokens = self._encoding.encode(text)
            record["token_count_original"] = len(tokens)
            total_input_tokens += len(tokens)

        context.metrics["total_input_tokens"] = total_input_tokens
        context.metrics["empty_reviews"] = empty_count
        context.metrics["reviews_to_analyze"] = len(records) - empty_count

        return context

    async def analyze_async(self, context: EngineContext) -> list[dict[str, Any]]:
        """Run the async batch LLM analysis. Called by the pipeline."""
        records = context.records
        results: list[dict[str, Any] | None] = [None] * len(records)
        semaphore = asyncio.Semaphore(self.MAX_CONCURRENT)
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
            tasks.append(self._analyze_single(i, record, semaphore, results))

        if tasks:
            await asyncio.gather(*tasks)

        context.results = results  # type: ignore[assignment]

        context.metrics["cost_per_million"] = 2.50
        context.metrics["estimated_cost_input"] = round(
            (context.metrics.get("total_input_tokens", 0) / 1_000_000) * 2.50, 4
        )

        elapsed = time.time() - context.metrics["start_time"]
        context.metrics["processing_time_seconds"] = round(elapsed, 2)
        context.metrics["reviews_per_second"] = round(
            len(records) / max(elapsed, 0.001), 1
        )

        return results  # type: ignore[return-value]

    async def _analyze_single(
        self,
        index: int,
        record: dict[str, Any],
        semaphore: asyncio.Semaphore,
        results: list[dict[str, Any] | None],
    ) -> None:
        async with semaphore:
            text = record.get("reseña", record.get("text", ""))
            optimized_text = record.get("optimized_text", text)

            prompt_text = optimized_text if optimized_text else text
            prompt_tokens = len(self._encoding.encode(prompt_text))

            try:
                result = await self._call_llm_with_retry(prompt_text)
                tokens_used = len(self._encoding.encode(result))
                parsed = self._parse_response(result)

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
                    "summary": f"Failed after {self.MAX_RETRIES} attempts: {str(e)[:80]}",
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
    async def _call_llm_with_retry(self, text: str) -> str:
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not configured")

        prompt_content = ANALYSIS_PROMPT.replace("{text}", text[:2000])

        async with httpx.AsyncClient(timeout=self.LLM_TIMEOUT) as client:
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

    def _parse_response(self, raw: str) -> dict[str, Any]:
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
