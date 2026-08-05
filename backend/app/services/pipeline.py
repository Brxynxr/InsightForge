import uuid
from datetime import datetime

from app.core.database import async_session
from app.engines.base import BaseEngine, EngineContext
from app.engines.cost.engine import CostEngine
from app.engines.export.engine import ExportEngine
from app.engines.history.engine import HistoryEngine
from app.engines.input.engine import InputEngine
from app.engines.llm.engine import LLMEngine
from app.engines.optimization.engine import OptimizationEngine
from app.engines.parser.engine import ParserEngine
from app.engines.prompt_builder.engine import PromptBuilderEngine
from app.engines.tokenizer.engine import TokenizerEngine
from app.engines.validation.engine import ValidationEngine
from app.models import Job, JobRecord, JobStatus
from app.schemas.job import JobRequest, JobResponse


class Pipeline:
    """Orchestrates the processing pipeline through all engines."""

    def __init__(self) -> None:
        self.engines: list[tuple[str, BaseEngine]] = [
            ("input", InputEngine()),
            ("validation", ValidationEngine()),
            ("optimization", OptimizationEngine()),
            ("tokenizer", TokenizerEngine()),
            ("cost", CostEngine()),
            ("prompt_builder", PromptBuilderEngine()),
            ("llm", LLMEngine()),
            ("parser", ParserEngine()),
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
            },
        )

        for _name, engine in self.engines:
            context = engine.execute(context)

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
                job.completed_at = datetime.utcnow()
                job.job_metadata = context.metadata
                await db.commit()

                records_to_insert = []
                for i, record in enumerate(context.records):
                    result = context.results[i] if i < len(context.results) else {}
                    llm_responses = context.metadata.get("llm_responses", [])
                    llm_response = llm_responses[i] if i < len(llm_responses) else None
                    prompts = context.metadata.get("prompts", [])
                    prompt = prompts[i].get("user") if i < len(prompts) else None

                    records_to_insert.append(JobRecord(
                        job_id=job_id,
                        record_index=i,
                        original_data=record,
                        optimized_text=record.get("optimized_text"),
                        token_count=record.get("token_count", 0),
                        prompt=prompt,
                        llm_response=llm_response if isinstance(llm_response, str) else None,
                        parsed_result=result if isinstance(result, dict) else {},
                        error=result.get("error") if isinstance(result, dict) else None,
                    ))

                db.add_all(records_to_insert)
                await db.commit()

        return JobResponse(
            batch_id=context.batch_id,
            status="completed" if not context.errors else "completed_with_errors",
            metrics=context.metrics,
            results=context.results,
            exports=context.metadata.get("exports"),
        )


async def run_pipeline(request: JobRequest) -> JobResponse:
    pipeline = Pipeline()
    return await pipeline.run(request)
