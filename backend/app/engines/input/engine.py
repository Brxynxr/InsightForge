from pathlib import Path
from typing import Any, cast

import pandas as pd

from app.engines.base import BaseEngine
from app.engines.context_models import EngineContext, RecordDict


class InputEngine(BaseEngine):
    """Responsible for reading Excel files, folder scanning, and batch generation."""

    def execute(self, context: EngineContext) -> EngineContext:
        file_path = context.metadata.file_path
        folder_path = context.metadata.folder_path

        if folder_path:
            return self._process_folder(folder_path, context)
        elif file_path:
            return self._process_file(file_path, context)
        else:
            context.add_error("input", "No file_path or folder_path provided")
            return context

    def _process_file(self, file_path: str, context: EngineContext) -> EngineContext:
        try:
            df = pd.read_excel(file_path)
            context.metadata.columns = list(df.columns)
            context.metadata.total_records = len(df)
            context.metadata.source_type = "single_file"
            context.metadata.files_processed = [file_path]
            raw_records: list[dict[str, Any]] = cast(
                list[dict[str, Any]], df.to_dict(orient="records")
            )
            context.records = [RecordDict(**r) for r in raw_records]
        except Exception as e:
            context.add_error("input", str(e))
        return context

    def _process_folder(self, folder_path: str, context: EngineContext) -> EngineContext:
        folder = Path(folder_path)
        if not folder.exists() or not folder.is_dir():
            context.add_error("input", f"Folder not found: {folder_path}")
            return context

        excel_files = sorted(folder.glob("*.xlsx")) + sorted(folder.glob("*.xls"))
        if not excel_files:
            context.add_error("input", f"No Excel files found in: {folder_path}")
            return context

        all_records: list[RecordDict] = []
        files_processed: list[str] = []
        columns_detected: list[str] = []

        for excel_file in excel_files:
            try:
                df = pd.read_excel(excel_file)
                if not columns_detected:
                    columns_detected = list(df.columns)
                raw_records: list[dict[str, Any]] = cast(
                    list[dict[str, Any]], df.to_dict(orient="records")
                )
                for record in raw_records:
                    record["_source_file"] = excel_file.name
                    all_records.append(RecordDict(**record))
                files_processed.append(str(excel_file))
            except Exception as e:
                context.add_error("input", str(e), file=str(excel_file))

        context.records = all_records
        context.metadata.columns = columns_detected
        context.metadata.total_records = len(all_records)
        context.metadata.source_type = "folder"
        context.metadata.files_processed = files_processed
        context.metadata.folder_path = folder_path

        return context
