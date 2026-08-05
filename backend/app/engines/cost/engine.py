from app.core.config import settings
from app.engines.base import BaseEngine, EngineContext


class CostEngine(BaseEngine):
    """Responsible for daily/monthly estimation, savings calculation, comparative reports."""

    def execute(self, context: EngineContext) -> EngineContext:
        total_tokens = context.metrics.get("total_tokens", 0)
        price_per_1k = getattr(settings, "LLM_PRICE_PER_1K_TOKENS", 0.00015)
        estimated_cost = (total_tokens / 1000) * price_per_1k
        context.metrics["estimated_cost"] = round(estimated_cost, 6)
        context.metrics["daily_estimate"] = round(estimated_cost * 30, 4)
        context.metrics["monthly_estimate"] = round(estimated_cost * 300, 4)
        return context
