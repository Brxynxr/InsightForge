import hashlib
import json
from typing import Any

from deep_translator import GoogleTranslator
from loguru import logger

from app.engines.base import BaseEngine, EngineContext


class OptimizationEngine(BaseEngine):
    """Responsible for translation, prompt normalization, deduplication."""

    def __init__(self, cache: dict[str, Any] | None = None) -> None:
        self._cache: dict[str, Any] = cache or {}

    def execute(self, context: EngineContext) -> EngineContext:
        target_language = context.metadata.get("target_language") or "es"

        for record in context.records:
            text = record.get("text", "")
            key_data = {"text": text, "lang": target_language}
            cache_key = hashlib.md5(json.dumps(key_data).encode()).hexdigest()

            if cache_key in self._cache:
                record["optimized_text"] = self._cache[cache_key]
                record["translation_hit"] = True
            else:
                optimized = self._translate_and_normalize(text, target_language)
                record["optimized_text"] = optimized
                self._cache[cache_key] = optimized
                record["translation_hit"] = False

        context.metadata["optimization_cache_size"] = len(self._cache)
        context.metrics["translation_hits"] = sum(
            1 for r in context.records if r.get("translation_hit")
        )
        return context

    def _translate_and_normalize(self, text: str, target_language: str) -> str:
        normalized = self._normalize(text)
        if not normalized:
            return normalized

        if target_language.lower() == "en":
            return normalized

        try:
            translator = GoogleTranslator(source="auto", target=target_language)
            translated = translator.translate(normalized)
            return translated
        except Exception as e:
            logger.warning(f"Translation failed for text: {text[:50]}... Error: {e}")
            return normalized

    def _normalize(self, text: str) -> str:
        return text.strip().replace("\n", " ").replace("\t", " ")
