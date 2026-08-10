import inspect
import time
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

from app.core.database import async_session
from app.engines.analyze.engine import AnalyzeEngine
from app.engines.base import BaseEngine
from app.engines.context_models import EngineContext, RecordDict, ResultDict
from app.engines.cost.engine import CostEngine
from app.engines.engine_functions import tokenizer_engine
from app.engines.export.engine import ExportEngine
from app.engines.history.engine import HistoryEngine
from app.engines.input.engine import InputEngine
from app.engines.optimization.engine import OptimizationEngine
from app.engines.token_compare.engine import TokenCompareEngine
from app.engines.validation.engine import ValidationEngine
from app.models import Job, JobRecord, JobStatus
from app.schemas.job import AnalyzeRequest, AnalyzeResponse, JobRequest, JobResponse

BATCH_INSERT_SIZE = 1000


EngineCallable = Callable[[EngineContext], EngineContext | Awaitable[EngineContext]]


def _is_async_engine(engine: BaseEngine | EngineCallable) -> bool:
    """Check if engine is a coroutine function or has async execute method."""
    if isinstance(engine, BaseEngine):
        return inspect.iscoroutinefunction(engine.execute)
    return inspect.iscoroutinefunction(engine)


async def _run_engine(engine: BaseEngine | EngineCallable, context: EngineContext) -> EngineContext:
    """Execute engine, handling both sync and async engines (class or function)."""
    result = engine.execute(context) if isinstance(engine, BaseEngine) else engine(context)
    if isinstance(result, Awaitable):
        return await result
    return result


async def _persist_job_records(
    job_id: int,
    records: list[RecordDict],
    results: list[ResultDict],
    original_data_filter: bool = False,
    token_count_key: str = "token_count",
) -> None:
    """Persist job records in batches to avoid memory issues with large datasets."""
    from app.core.database import async_session

    async with async_session() as db:
        for i in range(0, len(records), BATCH_INSERT_SIZE):
            batch_records = records[i:i + BATCH_INSERT_SIZE]
            batch_results = results[i:i + BATCH_INSERT_SIZE]

            records_to_insert = []
            for j, record in enumerate(batch_records):
                result: ResultDict | dict[str, Any] = (
                    batch_results[j] if j < len(batch_results) else {}
                )

                if original_data_filter:
                    original_data = record.model_dump(
                        exclude={"_skip_analysis", "_source_file"}
                    )
                else:
                    original_data = record.model_dump()

                parsed_result = (
                    result.model_dump() if hasattr(result, "model_dump") else result
                )
                error = (
                    result.get("error")
                    if isinstance(result, dict)
                    else getattr(result, "error", None)
                )

                records_to_insert.append(JobRecord(
                    job_id=job_id,
                    record_index=i + j,
                    original_data=original_data,
                    optimized_text=record.get("optimized_text"),
                    token_count=record.get(token_count_key, 0),
                    parsed_result=parsed_result,
                    error=error,
                ))

            db.add_all(records_to_insert)
            await db.commit()


class Pipeline:
    """Standard processing pipeline for general use."""

    def __init__(self) -> None:
        self.engines: list[tuple[str, BaseEngine | EngineCallable]] = [
            ("input", InputEngine()),
            ("validation", ValidationEngine()),
            ("optimization", OptimizationEngine()),
            ("tokenizer", tokenizer_engine),
            ("cost", CostEngine()),
            ("export", ExportEngine()),
            ("history", HistoryEngine()),
        ]

    async def run(self, request: JobRequest) -> JobResponse:
        batch_id = str(uuid.uuid4())

        async with async_session() as db:
            job = Job(
                batch_id=batch_id,
                status=JobStatus.PROCESSING,
                file_name=request.file_path.split("/")[-1] if request.file_path else "unknown",
                target_language=request.target_language,
                export_formats=request.export_formats or ["json"],
            )
            db.add(job)
            await db.commit()
            await db.refresh(job)
            job_id = job.id

        context = EngineContext(
            batch_id=batch_id,
            metadata={
                "file_path": request.file_path,
                "job_id": job_id,
                "required_columns": request.required_columns,
                "target_language": request.target_language,
                "export_formats": request.export_formats,
                "optimize_tokens": request.optimize_tokens,
            },
        )

        for _name, engine in self.engines:
            context = await _run_engine(engine, context)

        await self._persist_job(job_id, context)

        return JobResponse(
            batch_id=context.batch_id,
            status="completed" if not context.errors else "completed_with_errors",
            metrics=context.metrics,
            results=context.results,
            exports=context.metadata.exports,
        )

    async def _persist_job(self, job_id: int, context: EngineContext) -> None:
        async with async_session() as db:
            job = await db.get(Job, job_id)
            if job:
                has_errors = bool(context.errors)
                job.status = (
                    JobStatus.COMPLETED_WITH_ERRORS if has_errors else JobStatus.COMPLETED
                )
                job.total_records = context.metadata.total_records
                job.validated_records = context.metrics.validated_count
                job.rejected_records = context.metrics.rejected_count
                job.total_tokens = context.metrics.total_tokens
                job.estimated_cost = context.metrics.estimated_cost
                job.completed_at = datetime.now(UTC)
                job.job_metadata = context.metadata.model_dump()
                await db.commit()

        # Persist records in batches (separate session to avoid long transaction)
        await _persist_job_records(
            job_id=job_id,
            records=context.records,
            results=context.results,
            original_data_filter=False,
            token_count_key="token_count",
        )


class AnalyzePipeline:
    """Specialized pipeline for app review analysis with token comparison."""

    def __init__(self) -> None:
        self.engines: list[tuple[str, BaseEngine]] = [
            ("input", InputEngine()),
            ("validation", ValidationEngine()),
            ("optimization", OptimizationEngine()),
            ("token_compare", TokenCompareEngine()),
            ("analyze", AnalyzeEngine()),
            ("export", ExportEngine()),
            ("history", HistoryEngine()),
        ]

    async def run(self, request: AnalyzeRequest) -> AnalyzeResponse:
        batch_id = str(uuid.uuid4())
        start_time = time.time()

        async with async_session() as db:
            job = Job(
                batch_id=batch_id,
                status=JobStatus.PROCESSING,
                file_name=request.file_path.split("/")[-1] if request.file_path else "unknown",
                target_language=request.target_language,
                export_formats=["json"],
            )
            db.add(job)
            await db.commit()
            await db.refresh(job)
            job_id = job.id

        context = EngineContext(
            batch_id=batch_id,
            metadata={
                "file_path": request.file_path,
                "folder_path": request.folder_path,
                "job_id": job_id,
                "review_column": request.review_column,
                "target_language": request.target_language,
                "export_formats": ["json"],
                "optimize_tokens": request.optimize_tokens,
            },
        )

        analyze_engine = None
        for _name, engine in self.engines:
            if isinstance(engine, AnalyzeEngine):
                analyze_engine = engine

            context = await _run_engine(engine, context)

        if analyze_engine:
            await analyze_engine.analyze_async(context)

        await self._persist_job(job_id, context)

        elapsed = time.time() - start_time
        context.metrics.total_pipeline_time_seconds = round(elapsed, 2)

        return AnalyzeResponse(
            batch_id=context.batch_id,
            status="completed" if not context.errors else "completed_with_errors",
            metrics=context.metrics,
            results=context.results,
            token_comparison=context.metrics.token_comparison,
        )

    async def _persist_job(self, job_id: int, context: EngineContext) -> None:
        async with async_session() as db:
            job = await db.get(Job, job_id)
            if job:
                has_errors = bool(context.errors)
                job.status = (
                    JobStatus.COMPLETED_WITH_ERRORS if has_errors else JobStatus.COMPLETED
                )
                job.total_records = context.metadata.total_records
                job.validated_records = context.metrics.validated_count
                job.rejected_records = context.metrics.rejected_count
                job.total_tokens = context.metrics.total_input_tokens
                job.estimated_cost = context.metrics.estimated_cost_input
                job.completed_at = datetime.now(UTC)
                job.job_metadata = context.metadata.model_dump()
                await db.commit()

        # Persist records in batches (separate session to avoid long transaction)
        await _persist_job_records(
            job_id=job_id,
            records=context.records,
            results=context.results,
            original_data_filter=True,
            token_count_key="token_count_original",
        )


async def run_pipeline(request: JobRequest) -> JobResponse:
    pipeline = Pipeline()
    return await pipeline.run(request)


async def run_analyze_pipeline(request: AnalyzeRequest) -> AnalyzeResponse:
    pipeline = AnalyzePipeline()
    return await pipeline.run(request)
