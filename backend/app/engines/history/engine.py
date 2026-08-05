from datetime import UTC, datetime

from app.engines.base import BaseEngine, EngineContext


class HistoryEngine(BaseEngine):
    """Responsible for execution metadata, metrics, performance history.
    Never stores raw sensitive content. In-memory tracking for pipeline context."""

    def execute(self, context: EngineContext) -> EngineContext:
        summary = {
            "batch_id": context.batch_id,
            "batch_index": context.batch_index,
            "total_batches": context.total_batches,
            "timestamp": datetime.now(UTC).isoformat(),
            "record_count": len(context.records),
            "metrics": context.metrics,
            "error_count": len(context.errors),
        }
        context.metadata.setdefault("history", []).append(summary)
        return context
