"""
Run this once to populate the leads table with fake data for testing
the dashboard, independent of Person A's actual pipeline.
Usage (from backend/): python -m app.db.seed
"""
import uuid
from datetime import datetime

from app.db.models import LeadModel
from app.db.session import SessionLocal

FAKE_LEADS = [
    {
        "business_name": "Riverside Plumbing Co.",
        "category": "Plumber",
        "address": "142 Elm St, Springfield",
        "phone": "555-0142",
        "website_url": "https://riversideplumbing.example",
        "status": "scored",
        "sub_scores": {
            "has_website": True,
            "mobile_responsive": False,
            "broken_links_count": 3,
            "outdated_tech_flags": ["jQuery-only", "no SSL"],
            "load_time_ms": 4200,
            "reviews_count": 18,
            "rating": 4.1,
        },
        "llm_output": {
            "website_score": 32,
            "digital_presence": 40,
            "overall_lead_score": 78,
            "reasoning": "Outdated, non-responsive site with broken links.",
            "recommended_pitch": "Mobile-first redesign + SSL fix",
            "drafted_email_subject": "Quick note on riversideplumbing.example",
            "drafted_email_body": "Hi there — noticed a few things on your site...",
        },
    },
    {
        "business_name": "Bright Smile Dental",
        "category": "Dentist",
        "address": "88 Oak Ave, Springfield",
        "phone": "555-0188",
        "website_url": None,
        "status": "new",
        "sub_scores": {
            "has_website": False,
            "outdated_tech_flags": [],
            "reviews_count": 42,
            "rating": 4.7,
        },
        "llm_output": None,
    },
]


def seed():
    db = SessionLocal()
    try:
        for data in FAKE_LEADS:
            lead = LeadModel(
                id=uuid.uuid4(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                **data,
            )
            db.add(lead)
        db.commit()
        print(f"Seeded {len(FAKE_LEADS)} leads.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()