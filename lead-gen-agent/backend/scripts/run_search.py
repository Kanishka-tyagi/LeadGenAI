"""
Phase 1 entry point — creates a job, searches Places API, and ingests
new leads tagged with that job_id. Local dedup still applies on top.
"""
import argparse
import json
import sys
from pathlib import Path

import httpx

sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.services.maps_client import search_businesses

BASE_URL = "http://localhost:8000"  # verify against /docs — no /api prefix confirmed earlier
CACHE_FILE = Path(__file__).resolve().parent.parent / "sent_leads_cache.json"


def _load_cache() -> set:
    if CACHE_FILE.exists():
        with open(CACHE_FILE, "r") as f:
            return set(json.load(f))
    return set()


def _save_cache(cache: set):
    with open(CACHE_FILE, "w") as f:
        json.dump(list(cache), f)


def _dedup_key(item: dict) -> str:
    return f"{item['business_name']}|{item['website_url']}"


def create_job(keyword: str, location: str) -> str:
    resp = httpx.post(f"{BASE_URL}/jobs", json={"keywords": keyword, "location": location}, timeout=10.0)
    resp.raise_for_status()
    return resp.json()["id"]


def run(keyword: str, location: str, max_results: int):
    job_id = create_job(keyword, location)
    print(f"Created job {job_id}")

    found = search_businesses(keyword, location, max_results=max_results)
    cache = _load_cache()

    new_items = []
    skipped = 0
    for item in found:
        key = _dedup_key(item)
        if key in cache:
            skipped += 1
            continue
        new_items.append(item)
        cache.add(key)

    if not new_items:
        print(f"Done. 0 new leads, {skipped} already sent previously. Job {job_id} created with no leads.")
        return

    payload = [
        {
            "business_name": item["business_name"],
            "address": item["address"],
            "phone": item["phone"],
            "website_url": item["website_url"],
            "category": item["category"],
            "maps_data": {"rating": item["rating"], "reviews_count": item["reviews_count"]},
        }
        for item in new_items
    ]

    resp = httpx.post(f"{BASE_URL}/leads/ingest?job_id={job_id}", json=payload, timeout=15.0)
    resp.raise_for_status()

    _save_cache(cache)

    print(f"Done. Sent {len(payload)} new leads under job {job_id}, skipped {skipped} duplicates. Response: {resp.json()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("keyword")
    parser.add_argument("location")
    parser.add_argument("--max", type=int, default=20, dest="max_results")
    args = parser.parse_args()
    run(args.keyword, args.location, args.max_results)