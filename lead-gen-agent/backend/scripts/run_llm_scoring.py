"""
Phase 3 processing script — pulls leads that have sub_scores but no
llm_output yet, runs each through the local LLM, and saves the result
via the pipeline endpoint.

Usage:
    python scripts/run_llm_scoring.py
"""
import sys
from pathlib import Path

import httpx

sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.services.scoring.llm_scoring import score_lead_with_llm

BASE_URL = "http://localhost:8000"
PIPELINE_URL_TEMPLATE = BASE_URL + "/leads/{lead_id}/pipeline"  # confirmed single "leads" path


def get_leads_to_score() -> list[dict]:
    """
    Pulls all leads, filters client-side for ones with sub_scores
    populated but llm_output still missing. (No direct server-side
    filter for "has sub_scores but no llm_output" — adjust if B adds one.)
    """
    resp = httpx.get(f"{BASE_URL}/leads", params={"page_size": 200}, timeout=10.0)
    resp.raise_for_status()
    items = resp.json()["items"]
    return [l for l in items if l.get("sub_scores") and not l.get("llm_output")]


def process_lead(lead: dict):
    lead_id = lead["id"]
    business_name = lead["business_name"]
    category = lead.get("category")
    sub_scores = lead["sub_scores"]

    print(f"\nScoring {business_name}...")

    llm_output = score_lead_with_llm(business_name, category, sub_scores)

    if llm_output is None:
        print(f"  Skipped — LLM failed to return valid output.")
        return

    try:
        resp = httpx.patch(
            PIPELINE_URL_TEMPLATE.format(lead_id=lead_id),
            json={"llm_output": llm_output},
            timeout=15.0,
        )
        resp.raise_for_status()
        print(f"  Saved. overall_lead_score: {llm_output['overall_lead_score']}")
    except httpx.HTTPStatusError as e:
        print(f"  Failed to save: {e} — response body: {resp.text}")


def run():
    leads = get_leads_to_score()
    print(f"Found {len(leads)} leads ready for LLM scoring.")
    for lead in leads:
        process_lead(lead)
    print("\nDone.")


if __name__ == "__main__":
    run()