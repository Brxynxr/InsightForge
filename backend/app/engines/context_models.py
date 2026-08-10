from typing import Any

from pydantic import BaseModel, Field


class EngineError(BaseModel):
    engine: str
    record_index: int | None = None
    error: str
    file: str | None = None


class RecordDict(BaseModel):
    model_config = {"extra": "allow"}

    reseña: str | None = None
    text: str | None = None
    optimized_text: str | None = None
    token_count: int | None = None
    token_count_original: int | None = None
    tokens_original: int | None = None
    tokens_translated: int | None = None
    token_diff: int | None = None
    translation_hit: bool | None = None
    translation_error: str | None = None
    _skip_analysis: bool | None = None
    _source_file: str | None = None

    def get(self, key: str, default: Any = None) -> Any:
        """Dict-like get method for compatibility."""
        if hasattr(self, key):
            value = getattr(self, key)
            if value is not None:
                return value
        # Check extra fields
        extra = getattr(self, "__pydantic_extra__", None)
        if extra and key in extra:
            return extra[key]
        return default

    def __contains__(self, key: str) -> bool:
        """Support 'key in record' syntax."""
        if hasattr(self, key):
            return getattr(self, key) is not None
        extra = getattr(self, "__pydantic_extra__", None)
        return bool(extra and key in extra)

    def __getitem__(self, key: str) -> Any:
        """Support record[key] syntax."""
        value = self.get(key)
        extra = getattr(self, "__pydantic_extra__", None)
        has_extra = extra and key in extra
        if value is None and not (hasattr(self, key) or has_extra):
            raise KeyError(key)
        return value

    def __setitem__(self, key: str, value: Any) -> None:
        """Support record[key] = value syntax."""
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            # Store in extra fields
            if self.__pydantic_extra__ is None:
                self.__pydantic_extra__ = {}
            self.__pydantic_extra__[key] = value


class MetadataDict(BaseModel):
    model_config = {"extra": "allow"}

    file_path: str | None = None
    folder_path: str | None = None
    job_id: int | None = None
    required_columns: list[str] | None = None
    target_language: str | None = None
    export_formats: list[str] | None = None
    optimize_tokens: bool = True
    review_column: str = "reseña"
    columns: list[str] | None = None
    total_records: int = 0
    source_type: str | None = None
    files_processed: list[str] | None = None
    optimization_cache_size: int = 0
    history: list[dict[str, Any]] | None = None
    exports: dict[str, Any] | None = None


class MetricsDict(BaseModel):
    model_config = {"extra": "allow"}

    validated_count: int = 0
    rejected_count: int = 0
    total_tokens: int = 0
    avg_tokens_per_record: float = 0.0
    total_input_tokens: int = 0
    empty_reviews: int = 0
    reviews_to_analyze: int = 0
    cost_per_million: float = 2.50
    estimated_cost: float = 0.0
    estimated_cost_input: float = 0.0
    translations_performed: int = 0
    translations_skipped: int = 0
    translation_hits: int = 0
    translation_failures: int = 0
    start_time: float = 0.0
    processing_time_seconds: float = 0.0
    reviews_per_second: float = 0.0
    total_records_input: int = 0
    optimize_tokens_enabled: bool = True
    cost_per_million_tokens: float = 2.50
    daily_estimate_10k_reviews: dict[str, Any] | None = None
    monthly_estimate_300k_reviews: dict[str, Any] | None = None
    token_comparison: dict[str, Any] | None = None
    total_pipeline_time_seconds: float = 0.0


class ResultDict(BaseModel):
    model_config = {"extra": "allow"}

    record_index: int = 0
    error_type: str | None = None
    component: str | None = None
    severity: str | None = None
    summary: str | None = None
    tokens_used: int = 0
    raw_response: str | None = None
    error: str | None = None


class EngineContext(BaseModel):
    batch_id: str = ""
    batch_index: int = 0
    total_batches: int = 0
    records: list[RecordDict] = Field(default_factory=list)
    metadata: MetadataDict = Field(default_factory=MetadataDict)
    metrics: MetricsDict = Field(default_factory=MetricsDict)
    results: list[ResultDict] = Field(default_factory=list)
    errors: list[EngineError] = Field(default_factory=list)

    def add_error(
        self,
        engine: str,
        error: str,
        record_index: int | None = None,
        file: str | None = None,
    ) -> None:
        self.errors.append(
            EngineError(
                engine=engine,
                error=error,
                record_index=record_index,
                file=file,
            )
        )

    def get_record(self, index: int) -> RecordDict | None:
        if 0 <= index < len(self.records):
            return self.records[index]
        return None

    def set_record(self, index: int, record: RecordDict) -> None:
        if 0 <= index < len(self.records):
            self.records[index] = record
