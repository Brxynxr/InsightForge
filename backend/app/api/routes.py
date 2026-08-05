import os
import tempfile

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse
from loguru import logger
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import Job
from app.schemas.job import JobRequest, JobResponse
from app.services.pipeline import run_pipeline

router = APIRouter(prefix="/api/v1")


@router.post("/process", response_model=JobResponse)
async def process_job(
    file: UploadFile = File(...),
    required_columns: str | None = Form(None),
    target_language: str | None = Form(None),
    export_formats: str | None = Form(None),
) -> JobResponse:
    """Process an uploaded Excel file through the pipeline."""
    try:
        columns = required_columns.split(",") if required_columns else None
        formats = export_formats.split(",") if export_formats else ["json"]

        suffix = os.path.splitext(file.filename or ".xlsx")[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(file.file.read())
            tmp_path = tmp.name

        request = JobRequest(
            file_path=tmp_path,
            required_columns=columns,
            target_language=target_language,
            export_formats=formats,
        )

        result = await run_pipeline(request)

        os.unlink(tmp_path)
        logger.info(f"Job {result.batch_id} completed: {result.status}")
        return result
    except Exception as e:
        logger.error(f"Process job failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/health")
async def health_check() -> JSONResponse:
    return JSONResponse({"status": "healthy"})


@router.get("/history")
async def get_history(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Return processing history metadata from database."""
    result = await db.execute(
        select(Job)
        .order_by(desc(Job.created_at))
        .limit(limit)
        .offset(offset)
    )
    jobs = result.scalars().all()

    history = [
        {
            "batch_id": job.batch_id,
            "status": job.status.value,
            "file_name": job.file_name,
            "total_records": job.total_records,
            "validated_records": job.validated_records,
            "rejected_records": job.rejected_records,
            "total_tokens": job.total_tokens,
            "estimated_cost": job.estimated_cost,
            "target_language": job.target_language,
            "export_formats": job.export_formats,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "metrics": {
                "total_tokens": job.total_tokens,
                "estimated_cost": job.estimated_cost,
                "validated_count": job.validated_records,
                "rejected_count": job.rejected_records,
            },
        }
        for job in jobs
    ]

    return JSONResponse({"history": history})


@router.get("/history/{batch_id}")
async def get_job_detail(
    batch_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Return detailed job information including records."""
    result = await db.execute(select(Job).where(Job.batch_id == batch_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    from app.models import JobRecord
    records_result = await db.execute(
        select(JobRecord).where(JobRecord.job_id == job.id).order_by(JobRecord.record_index)
    )
    records = records_result.scalars().all()

    return JSONResponse({
        "job": {
            "batch_id": job.batch_id,
            "status": job.status.value,
            "file_name": job.file_name,
            "total_records": job.total_records,
            "validated_records": job.validated_records,
            "rejected_records": job.rejected_records,
            "total_tokens": job.total_tokens,
            "estimated_cost": job.estimated_cost,
            "target_language": job.target_language,
            "export_formats": job.export_formats,
            "error_message": job.error_message,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "metadata": job.job_metadata,
        },
        "records": [
            {
                "record_index": r.record_index,
                "original_data": r.original_data,
                "optimized_text": r.optimized_text,
                "token_count": r.token_count,
                "prompt": r.prompt,
                "llm_response": r.llm_response,
                "parsed_result": r.parsed_result,
                "error": r.error,
            }
            for r in records
        ],
    })
