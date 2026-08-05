import io
from typing import Any

import pandas as pd

from app.engines.base import BaseEngine, EngineContext


class ExportEngine(BaseEngine):
    """Responsible for Excel, JSON, CSV exports."""

    def execute(self, context: EngineContext) -> EngineContext:
        formats = context.metadata.get("export_formats") or ["json"]
        records = context.records
        results = context.results or []

        merged = []
        for i, record in enumerate(records):
            row = {**record}
            if i < len(results):
                row["result"] = results[i]
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

        context.metadata["exports"] = exports
        return context
