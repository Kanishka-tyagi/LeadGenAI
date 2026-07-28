"""
Job endpoints — triggers a new keyword/location search and lets the
dashboard poll for progress while Person A's Celery workers run.
"""
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.schemas.lead import Job, JobCreateRequest, JobStatus

router = APIRouter(prefix="/jobs", tags=["jobs"])

FAKE_JOBS: dict[str, Job] = {}


@router.post("", response_model=Job, status_code=201)
def create_job(payload: JobCreateRequest):
    """
    Creates a job record and (in the real implementation) enqueues the
    Celery task that kicks off Places API discovery for this
    keyword/location. Replace the body below with:
        task = celery_app.send_task("discover_leads", args=[job.id, payload...])
    """
    now = datetime.utcnow()
    job = Job(
        id=str(uuid.uuid4()),
        keywords=payload.keywords,
        location=payload.location,
        status=JobStatus.queued,
        created_at=now,
        updated_at=now,
    )
    FAKE_JOBS[job.id] = job
    return job


@router.get("/{job_id}", response_model=Job)
def get_job(job_id: str):
    """Polled by the dashboard to show progress (e.g. every 3-5s)."""
    job = FAKE_JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("", response_model=list[Job])
def list_jobs():
    return sorted(FAKE_JOBS.values(), key=lambda j: j.created_at, reverse=True)