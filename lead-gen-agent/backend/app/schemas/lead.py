"""
Shared Lead schema — the contract between the pipeline (Person A) and the
API/dashboard (Person B). Changes here should be agreed on together.
"""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class LeadStatus(str, Enum):
    new = "new"
    scored = "scored"
    reviewed = "reviewed"
    contacted = "contacted"
    converted = "converted"
    rejected = "rejected"


class SubScores(BaseModel):
    """Deterministic sub-scores computed by the backend before the LLM step."""
    has_website: bool
    mobile_responsive: Optional[bool] = None
    broken_links_count: Optional[int] = None
    outdated_tech_flags: list[str] = Field(default_factory=list)
    load_time_ms: Optional[int] = None
    reviews_count: Optional[int] = None
    rating: Optional[float] = None


class LLMOutput(BaseModel):
    """Exact shape returned by the local LLM scoring/drafting step."""
    website_score: int = Field(ge=0, le=100)
    digital_presence: int = Field(ge=0, le=100)
    overall_lead_score: int = Field(ge=0, le=100)
    reasoning: str
    recommended_pitch: str
    drafted_email_subject: str
    drafted_email_body: str


class Lead(BaseModel):
    model_config = {"from_attributes": True}
    id: str
    job_id: Optional[str] = None  

    business_name: str
    category: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    website_url: Optional[str] = None
    contact_email: Optional[str] = None
    scrape_data: Optional[dict] = None
    status: LeadStatus = LeadStatus.new

    sub_scores: Optional[SubScores] = None
    llm_output: Optional[LLMOutput] = None

    # human overrides — edited from the dashboard
    overridden_score: Optional[int] = None
    edited_email_subject: Optional[str] = None
    edited_email_body: Optional[str] = None
    reviewer_notes: Optional[str] = None

    created_at: datetime
    updated_at: datetime
    @field_validator("id", mode="before")
    @classmethod
    def _stringify_id(cls, v):
        return str(v)


class LeadListResponse(BaseModel):
    items: list[Lead]
    total: int
    page: int
    page_size: int


class LeadUpdateRequest(BaseModel):
    status: Optional[LeadStatus] = None
    overridden_score: Optional[int] = None
    edited_email_subject: Optional[str] = None
    edited_email_body: Optional[str] = None
    reviewer_notes: Optional[str] = None


class JobCreateRequest(BaseModel):
    keywords: str
    location: str
    max_results: int = 50


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class Job(BaseModel):
    model_config = {"from_attributes": True}
    id: str
    keywords: str
    location: str
    status: JobStatus
    leads_found: int = 0
    leads_processed: int = 0
    created_at: datetime
    updated_at: datetime
    @field_validator("id", mode="before")
    @classmethod
    def _stringify_id(cls, v):
        return str(v)