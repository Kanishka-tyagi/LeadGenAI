"""
SQLAlchemy table definitions — the real Postgres schema, matching the
Pydantic shapes in app/schemas/lead.py. This is your source of truth
for what's actually stored.
"""
import uuid
from datetime import datetime
from sqlalchemy import ForeignKey
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID

from app.db.session import Base


class LeadModel(Base):
    __tablename__ = "leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=True)  # ADD THIS
    business_name = Column(String, nullable=False)
    category = Column(String, nullable=True)
    address = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    website_url = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    scrape_data = Column(JSON, nullable=True)
    status = Column(String, default="new")

    # sub_scores and llm_output are stored as flexible JSON blobs —
    # their internal shape is defined by Pydantic (SubScores/LLMOutput),
    # not by separate Postgres columns.
    sub_scores = Column(JSON, nullable=True)
    llm_output = Column(JSON, nullable=True)

    overridden_score = Column(Integer, nullable=True)
    edited_email_subject = Column(String, nullable=True)
    edited_email_body = Column(String, nullable=True)
    reviewer_notes = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class JobModel(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    keywords = Column(String, nullable=False)
    location = Column(String, nullable=False)
    status = Column(String, default="queued")
    leads_found = Column(Integer, default=0)
    leads_processed = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)