from fastapi import APIRouter, HTTPException

from app.core.jobs import job_store
from app.schemas.job import JobResponse

router = APIRouter()


@router.get("/jobs/{job_id}")
async def get_job(job_id: str) -> dict:
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job_not_found")
    response = JobResponse(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        completed_sources=job.completed_sources,
        pending_sources=job.pending_sources,
        result=job.result,
        error=job.error,
        created_at=job.created_at.isoformat() + "Z",
        updated_at=job.updated_at.isoformat() + "Z",
    )
    return {"data": response.model_dump(by_alias=True)}
