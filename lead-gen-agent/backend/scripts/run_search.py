"""
Phase 1 entry point — searches Places API and sends new leads to
Person B's ingest endpoint. Dedup is handled locally via a cache file,
since we no longer have direct DB access on this side.

Usage:
    python scripts/run_search.py "dental clinics" "Agra, India" --max 20
"""
import argparse
import json
import sys
from pathlib import Path

import httpx

sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.services.maps_client import search_businesses

INGEST_URL = "http://localhost:8000/leads/ingest"
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
    # business_name + website_url as the dedup key — matches what B's
    # side likely uses too, since there's still no place_id column.
    return f"{item['business_name']}|{item['website_url']}"


def run(keyword: str, location: str, max_results: int):
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
        print(f"Done. 0 new leads, {skipped} already sent previously.")
        return

    payload = [
        {
            "business_name": item["business_name"],
            "address": item["address"],
            "phone": item["phone"],
            "website_url": item["website_url"],
            "category": item["category"],
        }
        for item in new_items
    ]

    resp = httpx.post(INGEST_URL, json=payload, timeout=15.0)
    resp.raise_for_status()

    _save_cache(cache)  # only save after a successful send

    print(f"Done. Sent {len(payload)} new leads, skipped {skipped} duplicates. Response: {resp.json()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("keyword")
    parser.add_argument("location")
    parser.add_argument("--max", type=int, default=20, dest="max_results")
    args = parser.parse_args()
    run(args.keyword, args.location, args.max_results)