import inspect
import time
import uuid
from collections.abc import Awaitable
from datetime import UTC, datetime
from typing import Any

from app.core.database import async_session
from app.engines.analyze.engine import AnalyzeEngine
from app.engines.base import BaseEngine, EngineContext
from app.engines.cost.engine import CostEngine
from app.engines.export.engine import ExportEngine
from app.engines.history.engine import HistoryEngine
from app.engines.input.engine import InputEngine
from app.engines.optimization.engine import OptimizationEngine
from app.engines.token_compare.engine import TokenCompareEngine
from app.engines.tokenizer.engine import TokenizerEngine
from app.engines.validation.engine import ValidationEngine
from app.models import Job, JobRecord, JobStatus
from app.schemas.job import AnalyzeRequest, AnalyzeResponse, JobRequest, JobResponse

BATCH_INSERT_SIZE = 1000


def _is_async_engine(engine: BaseEngine) -> bool:
    """Check if engine.execute is a coroutine function."""
    return inspect.iscoroutinefunction(engine.execute)


async def _run_engine(engine: BaseEngine, context: EngineContext) -> EngineContext:
    """Execute engine, handling both sync and async execute methods."""
    result = engine.execute(context)
    if isinstance(result, Awaitable):
        return await result
    return result


async def _persist_job_records(
    job_id: int,
    records: list[dict[str, Any]],
    results: list[dict[str, Any]],
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
                result = batch_results[j] if j < len(batch_results) else {}

                if original_data_filter:
                    original_data = {k: v for k, v in record.items() if not k.startswith("_")}
                else:
                    original_data = record

                records_to_insert.append(JobRecord(
                    job_id=job_id,
                    record_index=i + j,
                    original_data=original_data,
                    optimized_text=record.get("optimized_text"),
                    token_count=record.get(token_count_key, 0),
                    parsed_result=result if isinstance(result, dict) else {},
                    error=result.get("error") if isinstance(result, dict) else None,
                ))

            db.add_all(records_to_insert)
            await db.commit()


class Pipeline:
    """Standard processing pipeline for general use."""

    def __init__(self) -> None:
        self.engines: list[tuple[str, BaseEngine]] = [
            ("input", InputEngine()),
            ("validation", ValidationEngine()),
            ("optimization", OptimizationEngine()),
            ("tokenizer", TokenizerEngine()),
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
            exports=context.metadata.get("exports"),
        )

    async def _persist_job(self, job_id: int, context: EngineContext) -> None:
        async with async_session() as db:
            job = await db.get(Job, job_id)
            if job:
                has_errors = bool(context.errors)
                job.status = (
                    JobStatus.COMPLETED_WITH_ERRORS if has_errors else JobStatus.COMPLETED
                )
                job.total_records = context.metadata.get("total_records", 0)
                job.validated_records = context.metrics.get("validated_count", 0)
                job.rejected_records = context.metrics.get("rejected_count", 0)
                job.total_tokens = context.metrics.get("total_tokens", 0)
                job.estimated_cost = context.metrics.get("estimated_cost", 0.0)
                job.completed_at = datetime.now(UTC)
                job.job_metadata = context.metadata
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
        context.metrics["total_pipeline_time_seconds"] = round(elapsed, 2)

        return AnalyzeResponse(
            batch_id=context.batch_id,
            status="completed" if not context.errors else "completed_with_errors",
            metrics=context.metrics,
            results=context.results,
            token_comparison=context.metrics.get("token_comparison"),
        )

    async def _persist_job(self, job_id: int, context: EngineContext) -> None:
        async with async_session() as db:
            job = await db.get(Job, job_id)
            if job:
                has_errors = bool(context.errors)
                job.status = (
                    JobStatus.COMPLETED_WITH_ERRORS if has_errors else JobStatus.COMPLETED
                )
                job.total_records = context.metadata.get("total_records", 0)
                job.validated_records = context.metrics.get("validated_count", 0)
                job.rejected_records = context.metrics.get("rejected_count", 0)
                job.total_tokens = context.metrics.get("total_input_tokens", 0)
                job.estimated_cost = context.metrics.get("estimated_cost_input", 0.0)
                job.completed_at = datetime.now(UTC)
                job.job_metadata = context.metadata
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
