from datetime import datetime, timezone
from typing import Optional
import uuid
from uuid import UUID
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.models import LeadModel, JobModel
from app.db.session import get_db
from app.schemas.lead import Lead, LeadListResponse, LeadStatus, LeadUpdateRequest

router = APIRouter(prefix="/leads", tags=["leads"])


def _effective_score(lead: LeadModel) -> int:
    if lead.overridden_score is not None:
        return lead.overridden_score
    if lead.llm_output and "overall_lead_score" in lead.llm_output:
        return lead.llm_output["overall_lead_score"]
    return 0


@router.get("", response_model=LeadListResponse)
def list_leads(
    status: Optional[LeadStatus] = None,
    min_score: Optional[int] = Query(None, ge=0, le=100),
    has_website: Optional[bool] = None,
    search: Optional[str] = None,
    sort_by: str = Query("overall_score", pattern="^(overall_score|business_name|created_at)$"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(LeadModel)

    if status is not None:
        query = query.filter(LeadModel.status == status.value)
    if has_website is not None:
        query = query.filter(LeadModel.website_url.isnot(None) == has_website)
    if search:
        query = query.filter(LeadModel.business_name.ilike(f"%{search}%"))

    all_leads = query.all()

    if min_score is not None:
        all_leads = [l for l in all_leads if _effective_score(l) >= min_score]

    reverse = sort_dir == "desc"
    if sort_by == "overall_score":
        all_leads.sort(key=_effective_score, reverse=reverse)
    elif sort_by == "business_name":
        all_leads.sort(key=lambda l: l.business_name.lower(), reverse=reverse)
    else:
        all_leads.sort(key=lambda l: l.created_at, reverse=reverse)

    total = len(all_leads)
    start = (page - 1) * page_size
    page_items = all_leads[start : start + page_size]

    return LeadListResponse(
        items=[Lead.model_validate(l) for l in page_items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{lead_id}", response_model=Lead)
def get_lead(lead_id: str, db: Session = Depends(get_db)):
    lead = db.query(LeadModel).filter(LeadModel.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.patch("/{lead_id}", response_model=Lead)
def update_lead(lead_id: str, patch: LeadUpdateRequest, db: Session = Depends(get_db)):
    lead = db.query(LeadModel).filter(LeadModel.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    update_data = patch.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(lead, field, value.value if hasattr(value, "value") else value)
    lead.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(lead)
    return lead


@router.get("/export/csv")
def export_leads_csv():
    raise HTTPException(status_code=501, detail="Not implemented yet")

@router.post("/ingest")
def ingest_leads(leads_data: list[dict], job_id: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Endpoint for Person A's pipeline to write leads to the database.
    Maps scraper output (business data) into leads.
    Optionally associates leads with a job_id for batch tracking.
    """
    ingested_count = 0
    
    for lead_dict in leads_data:
        # Add job_id if provided
        if job_id:
            lead_dict["job_id"] = job_id
        
        # Generate ID if not provided
        if "id" not in lead_dict:
            lead_dict["id"] = str(uuid.uuid4())
        
        # Add timestamps
        now =  datetime.now(timezone.utc)
        if "created_at" not in lead_dict:
            lead_dict["created_at"] = now
        if "updated_at" not in lead_dict:
            lead_dict["updated_at"] = now
        
        # Validate
        try:
            validated = Lead(**lead_dict)
        except Exception as e:
            print(f"Skipped invalid lead: {e}")
            continue
        
        # Check if already exists
        existing = db.query(LeadModel).filter(LeadModel.id == validated.id).first()
        if not existing:
            db_lead = LeadModel(**validated.model_dump())
            db.add(db_lead)
            ingested_count += 1
    
    db.commit()
    if job_id:
        job = db.query(JobModel).filter(JobModel.id == job_id).first()
        if job:
            job.leads_found = (job.leads_found or 0) + ingested_count
            db.commit()
    
    return {"ingested": ingested_count, "total": len(leads_data)}


class PipelineUpdate(BaseModel):
    scrape_data: Optional[dict] = None
    contact_email: Optional[str] = None
    sub_scores: Optional[dict] = None
    llm_output: Optional[dict] = None

@router.patch("/{lead_id}/pipeline")
def update_lead_pipeline(lead_id: str, update: PipelineUpdate, db: Session = Depends(get_db)):
    """
    Staged pipeline endpoint: Person A calls this multiple times as data becomes available.
    - First call: add scrape_data + contact_email after website analysis
    - Second call: add sub_scores + llm_output after LLM scoring
    Automatically increments job's leads_processed counter if lead has a job_id.
    """
    lead = db.query(LeadModel).filter(LeadModel.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Track if this is a meaningful update
    scraped_now = update.scrape_data is not None and lead.scrape_data is None
    scored_now = update.llm_output is not None and lead.llm_output is None
    
    # Update lead fields
    if update.scrape_data is not None:
        lead.scrape_data = update.scrape_data
    if update.contact_email is not None:
        lead.contact_email = update.contact_email
    if update.sub_scores is not None:
        lead.sub_scores = update.sub_scores
    if update.llm_output is not None:
        lead.llm_output = update.llm_output
    
    # Increment job progress if this lead belongs to a job
    if lead.job_id:
        job = db.query(JobModel).filter(JobModel.id == lead.job_id).first()
        if job:
            if scraped_now or scored_now:
                job.leads_processed = (job.leads_processed or 0) + 1
    
    lead.updated_at = datetime.utcnow()
    db.commit()
    
    return {"status": "updated", "lead_id": lead_id}