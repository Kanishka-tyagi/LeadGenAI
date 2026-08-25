"""
Phase 2 processing script — pulls leads that have a website but haven't
been scraped yet, runs the website analyzer + deterministic scoring on
each, and saves results via the pipeline endpoint.

NOTE: maps_data isn't returned by GET /leads yet (pending B's schema fix) —
falls back to {} until that's added, meaning reviews_count/rating will be
None in sub_scores for now. Safe to run and test everything else in the
meantime.

Usage:
    python scripts/run_scraper.py
"""
import sys
from pathlib import Path

import httpx

sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.services.scraper.website_analyzer import analyze_website
from app.services.scoring.deterministic_scoring import compute_sub_scores

BASE_URL = "http://localhost:8000"
PIPELINE_URL_TEMPLATE = BASE_URL + "/leads/{lead_id}/pipeline"  # confirmed doubled path from /docs


def get_leads_to_scrape() -> list[dict]:
    resp = httpx.get(f"{BASE_URL}/leads", params={"has_website": True, "status": "new"}, timeout=10.0)
    resp.raise_for_status()
    return resp.json()["items"]


def process_lead(lead: dict):
    lead_id = lead["id"]
    url = lead["website_url"]
    print(f"\nScraping {lead['business_name']} ({url})...")

    try:
        scrape_data = analyze_website(url)
    except Exception as e:
        print(f"  Failed to scrape: {e}")
        return

    emails = scrape_data.get("contact_info", {}).get("emails_found", [])
    contact_email = emails[0] if emails else None

    # TODO: swap for lead.get("maps_data", {}) once B adds that field to Lead schema
    maps_data = lead.get("maps_data", {}) or {}

    sub_scores = compute_sub_scores(maps_data=maps_data, scrape_data=scrape_data, has_website=True)

    payload = {
        "scrape_data": scrape_data,
        "contact_email": contact_email,
        "sub_scores": sub_scores,
    }

    try:
        resp = httpx.patch(PIPELINE_URL_TEMPLATE.format(lead_id=lead_id), json=payload, timeout=15.0)
        resp.raise_for_status()
        print(f"  Saved. Email found: {contact_email or 'none'} | broken_links: {sub_scores['broken_links_count']}")
    except httpx.HTTPStatusError as e:
        print(f"  Failed to save: {e} — response body: {resp.text}")


def run():
    leads = get_leads_to_scrape()
    print(f"Found {len(leads)} leads to scrape.")
    for lead in leads:
        process_lead(lead)
    print("\nDone.")


if __name__ == "__main__":
    run()