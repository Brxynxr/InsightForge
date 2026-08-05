from typing import Any

from pydantic import BaseModel


class JobResponse(BaseModel):
    batch_id: str
    status: str
    metrics: dict[str, Any]
    results: list[dict[str, Any]]
    exports: dict[str, Any] | None = None


class JobRequest(BaseModel):
    file_path: str
    required_columns: list[str] | None = None
    target_language: str | None = None
    export_formats: list[str] | None = None
