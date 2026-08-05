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
    optimize_tokens: bool = True


class AnalyzeRequest(BaseModel):
    file_path: str
    review_column: str = "reseña"
    optimize_tokens: bool = True
    folder_path: str | None = None
    target_language: str = "en"


class AnalyzeResponse(BaseModel):
    batch_id: str
    status: str
    metrics: dict[str, Any]
    results: list[dict[str, Any]]
    token_comparison: dict[str, Any] | None = None


class GenerateRequest(BaseModel):
    num_records: int = 50000
    output_filename: str = "resenas_generadas.xlsx"


class BenchmarkResult(BaseModel):
    file_path: str
    columns: list[str]
    total_records: int
    reviews_with_text: int
    empty_reviews: int
    review_column: str
    optimize_tokens: bool
    target_language: str
    timings: dict[str, Any]
    totals: dict[str, Any]
    projections: dict[str, Any]
