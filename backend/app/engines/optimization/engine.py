import asyncio
import hashlib
import json

from cachetools import LRUCache
from deep_translator import GoogleTranslator
from loguru import logger
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.engines.base import BaseEngine, EngineContext


class OptimizationEngine(BaseEngine):
    """Responsible for translation, prompt normalization, deduplication.
    Respects optimize_tokens flag: if False, skips translation entirely.

    Uses asyncio.to_thread() for GoogleTranslator (sync lib) with semaphore
    to achieve real concurrency (default 20 parallel translations).
    Includes timeout (10s) and retry with exponential backoff (max 3 attempts).
    Uses LRU cache (max 10000 entries) to avoid unbounded memory growth.
    """

    MAX_CONCURRENT_TRANSLATIONS = 20
    TRANSLATION_TIMEOUT = 10.0  # seconds
    MAX_RETRIES = 3
    CACHE_MAX_SIZE = 10000

    def __init__(self, cache: LRUCache | None = None) -> None:
        self._cache: LRUCache = cache or LRUCache(maxsize=self.CACHE_MAX_SIZE)

    async def execute(self, context: EngineContext) -> EngineContext:
        target_language = context.metadata.get("target_language") or "en"
        optimize = context.metadata.get("optimize_tokens", True)
        review_column = context.metadata.get("review_column") or "reseña"

        if not optimize:
            for record in context.records:
                text = record.get(review_column, record.get("text", ""))
                record["optimized_text"] = text
                record["translation_hit"] = False
            context.metrics["translations_performed"] = 0
            context.metrics["translations_skipped"] = len(context.records)
            context.metrics["translation_hits"] = 0
            return context

        # Separate cached vs non-cached records
        to_translate: list[tuple[int, str]] = []  # (index, text)
        for i, record in enumerate(context.records):
            text = record.get(review_column, record.get("text", ""))
            key_data = {"text": text, "lang": target_language}
            cache_key = hashlib.md5(json.dumps(key_data).encode()).hexdigest()

            if cache_key in self._cache:
                record["optimized_text"] = self._cache[cache_key]
                record["translation_hit"] = True
            else:
                record["translation_hit"] = False
                to_translate.append((i, text))

        # Translate non-cached records concurrently
        translated_count = await self._translate_batch(
            to_translate, target_language, context
        )

        skipped_count = len(context.records) - translated_count
        context.metadata["optimization_cache_size"] = len(self._cache)
        context.metrics["translations_performed"] = translated_count
        context.metrics["translations_skipped"] = skipped_count
        context.metrics["translation_hits"] = sum(
            1 for r in context.records if r.get("translation_hit")
        )

        return context

    async def _translate_batch(
        self,
        to_translate: list[tuple[int, str]],
        target_language: str,
        context: EngineContext,
    ) -> int:
        """Translate a batch of texts with controlled concurrency, timeout and retry."""
        if not to_translate:
            return 0

        semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_TRANSLATIONS)
        translated_count = 0
        failed_count = 0

        @retry(
            wait=wait_exponential(multiplier=1, min=1, max=10),
            stop=stop_after_attempt(self.MAX_RETRIES),
            retry=retry_if_exception_type(Exception),
            reraise=True,
        )
        async def _translate_with_retry(text: str, target_lang: str) -> str:
            translator = GoogleTranslator(source="auto", target=target_lang)
            return await asyncio.to_thread(translator.translate, text)

        async def translate_one(index: int, text: str) -> None:
            nonlocal translated_count, failed_count
            async with semaphore:
                normalized = self._normalize(text)
                if not normalized:
                    context.records[index]["optimized_text"] = normalized
                    return

                try:
                    # GoogleTranslator is sync -> run in thread pool with timeout + retry
                    optimized = await asyncio.wait_for(
                        _translate_with_retry(normalized, target_language),
                        timeout=self.TRANSLATION_TIMEOUT,
                    )
                    context.records[index]["optimized_text"] = optimized
                    key_data = {"text": text, "lang": target_language}
                    cache_key = hashlib.md5(json.dumps(key_data).encode()).hexdigest()
                    self._cache[cache_key] = optimized
                    translated_count += 1
                except TimeoutError:
                    logger.warning(
                        "Translation timeout "
                        f"({self.TRANSLATION_TIMEOUT}s) for record {index}: "
                        f"{text[:50]}..."
                    )
                    context.records[index]["optimized_text"] = normalized
                    context.records[index]["translation_error"] = "timeout"
                    failed_count += 1
                except Exception as e:
                    logger.warning(
                        "Translation failed after "
                        f"{self.MAX_RETRIES} retries for record {index}: "
                        f"{text[:50]}... Error: {e}"
                    )
                    context.records[index]["optimized_text"] = normalized
                    context.records[index]["translation_error"] = str(e)[:200]
                    failed_count += 1

        tasks = [translate_one(idx, text) for idx, text in to_translate]
        await asyncio.gather(*tasks)

        context.metrics["translation_failures"] = failed_count
        return translated_count

    def _normalize(self, text: str) -> str:
        return text.strip().replace("\n", " ").replace("\t", " ")
