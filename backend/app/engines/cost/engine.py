from app.engines.base import BaseEngine
from app.engines.context_models import EngineContext


class CostEngine(BaseEngine):
    """Calculates costs at $2.50 USD per million tokens.
    Supports daily (10k reviews) and monthly (300k reviews) projections."""

    COST_PER_MILLION_TOKENS: float = 2.50

    def execute(self, context: EngineContext) -> EngineContext:
        total_tokens = context.metrics.total_tokens
        total_input_tokens = context.metrics.total_input_tokens
        tokens = total_tokens or total_input_tokens

        estimated_cost = (tokens / 1_000_000) * self.COST_PER_MILLION_TOKENS

        total_records = context.metadata.total_records
        avg_tokens_per_record = tokens / max(total_records, 1)

        daily_10k = avg_tokens_per_record * 10_000
        monthly_300k = avg_tokens_per_record * 300_000

        context.metrics.cost_per_million_tokens = self.COST_PER_MILLION_TOKENS
        context.metrics.estimated_cost = round(estimated_cost, 6)
        context.metrics.daily_estimate_10k_reviews = {
            "total_tokens": round(daily_10k),
            "cost_usd": round((daily_10k / 1_000_000) * self.COST_PER_MILLION_TOKENS, 2),
        }
        context.metrics.monthly_estimate_300k_reviews = {
            "total_tokens": round(monthly_300k),
            "cost_usd": round(
                (monthly_300k / 1_000_000) * self.COST_PER_MILLION_TOKENS, 2
            ),
        }

        return context
