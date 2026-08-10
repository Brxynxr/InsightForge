import tiktoken

from app.core.config import settings
from app.engines.base import BaseEngine
from app.engines.context_models import EngineContext


class TokenCompareEngine(BaseEngine):
    """Compares token counts between original (Spanish) and translated (English) text.
    Used for cost analysis and optimization reporting."""

    def __init__(self) -> None:
        self._encoding = tiktoken.get_encoding(settings.TOKENIZER_ENCODING)

    def execute(self, context: EngineContext) -> EngineContext:
        records = context.records
        cost_per_million = getattr(settings, "LLM_PRICE_PER_1M_TOKENS", 2.50)

        total_original = 0
        total_translated = 0

        for record in records:
            original = record.get("reseña", record.get("text", ""))
            translated = record.get("optimized_text", original)

            orig_tokens = len(self._encoding.encode(original)) if original else 0
            trans_tokens = len(self._encoding.encode(translated)) if translated else 0

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
