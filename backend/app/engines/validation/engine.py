from app.engines.base import BaseEngine
from app.engines.context_models import EngineContext


class ValidationEngine(BaseEngine):
    """Responsible for file validation, schema validation, required columns, empty records."""

    def execute(self, context: EngineContext) -> EngineContext:
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
