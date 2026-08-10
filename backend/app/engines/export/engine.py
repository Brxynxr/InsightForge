import io
from typing import Any

import pandas as pd

from app.engines.base import BaseEngine
from app.engines.context_models import EngineContext


class ExportEngine(BaseEngine):
    """Responsible for Excel, JSON, CSV exports."""

    def execute(self, context: EngineContext) -> EngineContext:
        formats = context.metadata.export_formats or ["json"]
        records = context.records
        results = context.results

        merged = []
        for i, record in enumerate(records):
            row = record.model_dump()
            if i < len(results):
                result_item = results[i]
                row["result"] = (
                    result_item.model_dump()
                    if hasattr(result_item, "model_dump")
                    else result_item
                )
            merged.append(row)

        exports: dict[str, Any] = {}
        for fmt in formats:
            df = pd.DataFrame(merged)
            buffer = io.BytesIO()
            if fmt == "excel":
                df.to_excel(buffer, index=False)
                buffer.seek(0)
                exports[fmt] = buffer.getvalue()
            elif fmt == "csv":
                df.to_csv(buffer, index=False)
                buffer.seek(0)
                exports[fmt] = buffer.getvalue()
            else:
                result_bytes = df.to_json(orient="records").encode("utf-8")
                exports[fmt] = result_bytes

        context.metadata.exports = exports
        return context
