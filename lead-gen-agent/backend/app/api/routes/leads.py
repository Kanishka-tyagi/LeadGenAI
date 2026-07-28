"""
Lead endpoints. Swap the in-memory FAKE_DB / query logic for real DB session
calls once Person A's schema/models.py lands — the response shapes here are
the contract, so the frontend can be built against this today.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.schemas.lead import Lead, LeadListResponse, LeadStatus, LeadUpdateRequest

router = APIRouter(prefix="/leads", tags=["leads"])

# --- temporary in-memory store, replace with DB session ---
FAKE_DB: dict[str, Lead] = {}


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
):
    """List leads with filters/sort/pagination — backs the dashboard table."""
    items = list(FAKE_DB.values())

    if status is not None:
        items = [l for l in items if l.status == status]
    if has_website is not None:
        items = [l for l in items if bool(l.website_url) == has_website]
    if min_score is not None:
        items = [
            l for l in items
            if (l.overridden_score or (l.llm_output.overall_lead_score if l.llm_output else 0)) >= min_score
        ]
    if search:
        s = search.lower()
        items = [l for l in items if s in l.business_name.lower()]

    def score_key(l: Lead) -> int:
        return l.overridden_score or (l.llm_output.overall_lead_score if l.llm_output else 0)

    key_fn = {
        "overall_score": score_key,
        "business_name": lambda l: l.business_name.lower(),
        "created_at": lambda l: l.created_at,
    }[sort_by]
    items.sort(key=key_fn, reverse=(sort_dir == "desc"))

    total = len(items)
    start = (page - 1) * page_size
    page_items = items[start : start + page_size]

    return LeadListResponse(items=page_items, total=total, page=page, page_size=page_size)


@router.get("/{lead_id}", response_model=Lead)
def get_lead(lead_id: str):
    lead = FAKE_DB.get(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.patch("/{lead_id}", response_model=Lead)
def update_lead(lead_id: str, patch: LeadUpdateRequest):
    """Human review actions: override score, edit email, change status, add notes."""
    lead = FAKE_DB.get(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    update_data = patch.model_dump(exclude_unset=True)
    updated = lead.model_copy(update={**update_data, "updated_at": datetime.utcnow()})
    FAKE_DB[lead_id] = updated
    return updated


@router.get("/export/csv")
def export_leads_csv():
    """Stub — wire up a StreamingResponse with csv.writer once needed."""
    raise HTTPException(status_code=501, detail="Not implemented yet")