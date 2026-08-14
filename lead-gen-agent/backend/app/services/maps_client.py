"""
Client for Google Places API (New) — Text Search.
Docs: https://developers.google.com/maps/documentation/places/web-service/text-search

Deliberately uses the official API (not Maps scraping) — see the
architecture doc for why: ToS compliance + reliability.
"""
import os
import time

import httpx
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
BASE_URL = "https://places.googleapis.com/v1/places:searchText"

# Only request the fields you actually use — Places API bills per field group,
# so a narrow field mask keeps cost down.
FIELD_MASK = ",".join([
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.internationalPhoneNumber",
    "places.websiteUri",
    "places.primaryType",
    "places.rating",
    "places.userRatingCount",
])


def search_businesses(keyword: str, location: str, max_results: int = 20) -> list[dict]:
    """
    Searches Places API (New) Text Search for `keyword` near `location`.
    Handles pagination automatically up to max_results.
    Returns a list of normalized dicts ready to insert as Lead rows.
    """
    if not API_KEY:
        raise RuntimeError("GOOGLE_PLACES_API_KEY not set — check your .env file.")

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": FIELD_MASK,
    }

    results: list[dict] = []
    page_token = None

    with httpx.Client(timeout=15.0) as client:
        while len(results) < max_results:
            body = {"textQuery": f"{keyword} in {location}"}
            if page_token:
                body["pageToken"] = page_token

            resp = client.post(BASE_URL, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()

            for place in data.get("places", []):
                results.append(_normalize_place(place))

            page_token = data.get("nextPageToken")
            if not page_token:
                break

            # Google requires a short delay before a page token becomes valid
            time.sleep(2)

    return results[:max_results]


def _normalize_place(place: dict) -> dict:
    """
    Normalizes a raw Places API result into our schema's field names.

    NOTE: rating/reviews_count are NOT columns on LeadModel — they get
    bundled into maps_data (JSON) when sending to the ingest endpoint,
    not passed as top-level fields. See run_search.py.
    """
    return {
        "business_name": place.get("displayName", {}).get("text", "Unknown"),
        "address": place.get("formattedAddress"),
        "phone": place.get("internationalPhoneNumber"),
        "website_url": place.get("websiteUri"),
        "category": place.get("primaryType"),
        "rating": place.get("rating"),
        "reviews_count": place.get("userRatingCount"),
    }


if __name__ == "__main__":
    # Quick manual sanity check — run this file directly to test your API key
    # before wiring it into anything else.
    leads = search_businesses("dental clinics", "Agra, India", max_results=5)
    for l in leads:
        print(l["business_name"], "-", l["rating"], f"({l['reviews_count']} reviews)", "-", l["website_url"] or "NO WEBSITE")