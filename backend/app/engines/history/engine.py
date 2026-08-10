from datetime import UTC, datetime

from app.engines.base import BaseEngine
from app.engines.context_models import EngineContext


class HistoryEngine(BaseEngine):
    """Responsible for execution metadata, metrics, performance history.
    Never stores raw sensitive content. In-memory tracking for pipeline context."""

    def execute(self, context: EngineContext) -> EngineContext:
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
