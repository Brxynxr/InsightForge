import asyncio
import hashlib
import json
from typing import Any

from deep_translator import GoogleTranslator
from loguru import logger

from app.engines.base import BaseEngine, EngineContext


class OptimizationEngine(BaseEngine):
    """Responsible for translation, prompt normalization, deduplication.
    Respects optimize_tokens flag: if False, skips translation entirely.

    Uses asyncio.to_thread() for GoogleTranslator (sync lib) with semaphore
    to achieve real concurrency (default 20 parallel translations).
    """

    MAX_CONCURRENT_TRANSLATIONS = 20

    def __init__(self, cache: dict[str, Any] | None = None) -> None:
        self._cache: dict[str, Any] = cache or {}

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
        """Translate a batch of texts with controlled concurrency."""
        if not to_translate:
            return 0

        semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_TRANSLATIONS)
        translated_count = 0

        async def translate_one(index: int, text: str) -> None:
            nonlocal translated_count
            async with semaphore:
                normalized = self._normalize(text)
                if not normalized:
                    context.records[index]["optimized_text"] = normalized
                    return

                try:
                    # GoogleTranslator is sync -> run in thread pool
                    translator = GoogleTranslator(source="auto", target=target_language)
                    optimized = await asyncio.to_thread(translator.translate, normalized)
                    context.records[index]["optimized_text"] = optimized
                    key_data = {"text": text, "lang": target_language}
                    cache_key = hashlib.md5(json.dumps(key_data).encode()).hexdigest()
                    self._cache[cache_key] = optimized
                    translated_count += 1
                except Exception as e:
                    logger.warning(
                        f"Translation failed for record {index}: {text[:50]}... Error: {e}"
                    )
                    context.records[index]["optimized_text"] = normalized

        tasks = [translate_one(idx, text) for idx, text in to_translate]
        await asyncio.gather(*tasks)
        return translated_count

    def _normalize(self, text: str) -> str:
        return text.strip().replace("\n", " ").replace("\t", " ")
