import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import JobModel
from app.db.session import get_db
from app.schemas.lead import Job, JobCreateRequest, JobStatus

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=Job, status_code=201)
def create_job(payload: JobCreateRequest, db: Session = Depends(get_db)):
    job = JobModel(
        id=uuid.uuid4(),
        keywords=payload.keywords,
        location=payload.location,
        status=JobStatus.queued.value,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.get("/{job_id}", response_model=Job)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(JobModel).filter(JobModel.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("", response_model=list[Job])
def list_jobs(db: Session = Depends(get_db)):
    return db.query(JobModel).order_by(JobModel.created_at.desc()).all()