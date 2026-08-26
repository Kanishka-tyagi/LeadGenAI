"""
Celery tasks — the automated version of run_search.py / run_scraper.py /
run_llm_scoring.py. These write directly to the database (no HTTP calls
to our own API), chaining automatically: search -> scrape -> LLM score.
"""
from datetime import datetime

from app.workers.celery_app import celery_app
from app.db.session import SessionLocal
from app.db.models import LeadModel, JobModel
from app.services.maps_client import search_businesses
from app.services.scraper.website_analyzer import analyze_website
from app.services.scoring.deterministic_scoring import compute_sub_scores
from app.services.scoring.llm_scoring import score_lead_with_llm


@celery_app.task(name="run_search_job")
def run_search_job(job_id: str, keywords: str, location: str, max_results: int = 20):
    """
    Triggered when a job is created. Searches Places API, ingests new
    leads tagged with job_id, then enqueues the next step for each —
    scraping for leads with a website, straight to LLM scoring otherwise.
    """
    db = SessionLocal()
    try:
        job = db.query(JobModel).filter(JobModel.id == job_id).first()
        if not job:
            return
        job.status = "running"
        db.commit()

        found = search_businesses(keywords, location, max_results=max_results)
        inserted = []  # (lead_id, website_url) pairs

        for item in found:
            exists = db.query(LeadModel).filter_by(
                business_name=item["business_name"], website_url=item["website_url"]
            ).first()
            if exists:
                continue

            lead = LeadModel(
                job_id=job_id,
                business_name=item["business_name"],
                address=item["address"],
                phone=item["phone"],
                website_url=item["website_url"],
                category=item["category"],
                maps_data={"rating": item["rating"], "reviews_count": item["reviews_count"]},
                status="new",
            )
            db.add(lead)
            db.flush()  # populates lead.id before commit
            inserted.append((str(lead.id), lead.website_url))

        job.leads_found = len(inserted)
        db.commit()

        for lead_id, website_url in inserted:
            if website_url:
                scrape_and_score_lead.delay(lead_id)
            else:
                score_lead_with_llm_task.delay(lead_id)  # no website -> skip straight to LLM

    finally:
        db.close()


@celery_app.task(name="scrape_and_score_lead")
def scrape_and_score_lead(lead_id: str):
    """
    Scrapes a lead's website, computes deterministic sub_scores,
    saves both, then enqueues LLM scoring.
    """
    db = SessionLocal()
    try:
        lead = db.query(LeadModel).filter(LeadModel.id == lead_id).first()
        if not lead:
            return

        scrape_data = analyze_website(lead.website_url)
        emails = scrape_data.get("contact_info", {}).get("emails_found", [])
        contact_email = emails[0] if emails else None

        sub_scores = compute_sub_scores(
            maps_data=lead.maps_data or {},
            scrape_data=scrape_data,
            has_website=True,
        )

        lead.scrape_data = scrape_data
        lead.contact_email = contact_email
        lead.sub_scores = sub_scores
        lead.updated_at = datetime.utcnow()
        db.commit()
    finally:
        db.close()

    score_lead_with_llm_task.delay(lead_id)


@celery_app.task(name="score_lead_with_llm_task")
def score_lead_with_llm_task(lead_id: str):
    """
    Final step — runs LLM scoring, saves llm_output, marks the lead
    scored, and updates the parent job's progress/completion status.
    """
    db = SessionLocal()
    try:
        lead = db.query(LeadModel).filter(LeadModel.id == lead_id).first()
        if not lead:
            return

        llm_output = score_lead_with_llm(lead.business_name, lead.category, lead.sub_scores or {})
        if llm_output:
            lead.llm_output = llm_output
            lead.status = "scored"
        lead.updated_at = datetime.utcnow()
        db.commit()

        if lead.job_id:
            job = db.query(JobModel).filter(JobModel.id == lead.job_id).first()
            if job:
                job.leads_processed = (job.leads_processed or 0) + 1
                if job.leads_found and job.leads_processed >= job.leads_found:
                    job.status = "completed"
                db.commit()
    finally:
        db.close()