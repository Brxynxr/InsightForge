from typing import Any, cast

import pandas as pd

from app.engines.base import BaseEngine, EngineContext


class InputEngine(BaseEngine):
    """Responsible for reading Excel files, folder scanning, and batch generation."""

    def execute(self, context: EngineContext) -> EngineContext:
        file_path = context.metadata.get("file_path")
        if not file_path:
            context.errors.append({"engine": "input", "error": "No file_path provided"})
            return context

        try:
            df = pd.read_excel(file_path)
            context.metadata["columns"] = list(df.columns)
            context.metadata["total_records"] = len(df)
            records: list[dict[str, Any]] = cast(list[dict[str, Any]], df.to_dict(orient="records"))
            context.records = records
        except Exception as e:
            context.errors.append({"engine": "input", "error": str(e)})

        return context
