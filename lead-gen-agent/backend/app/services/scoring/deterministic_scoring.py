"""
Turns raw maps_data + scrape_data into the SubScores shape expected by
app/schemas/lead.py — this is the last step of Phase 2, before Phase 3's
LLM scoring (llm_scoring.py) reads sub_scores and produces llm_output.
"""


def compute_sub_scores(maps_data: dict, scrape_data: dict, has_website: bool) -> dict:
    """
    Reads raw signals from maps_data (Places API) and scrape_data
    (website_analyzer output) and returns a dict matching SubScores:
      has_website, mobile_responsive, broken_links_count,
      outdated_tech_flags, load_time_ms, reviews_count, rating
    """
    tech = (scrape_data or {}).get("tech_signals", {})
    links = (scrape_data or {}).get("links", {})

    outdated_flags = []
    if tech.get("outdated_signal"):
        outdated_flags.append("outdated content")
    if not tech.get("has_viewport_meta"):
        outdated_flags.append("not mobile-responsive")
    if not tech.get("uses_https"):
        outdated_flags.append("no SSL")
    if tech.get("cms_detected") in ("Wix", "GoDaddy Website Builder"):
        outdated_flags.append("template builder site")
    if tech.get("frameworks_detected") and "jQuery only (legacy)" in tech["frameworks_detected"]:
        outdated_flags.append("jQuery-only")
    if not tech.get("analytics_detected"):
        outdated_flags.append("no analytics installed")

    link_statuses = links.get("link_statuses", {})
    broken_links_count = sum(
        1 for status in link_statuses.values() if status is None or status >= 400
    )

    return {
        "has_website": has_website,
        "mobile_responsive": tech.get("has_viewport_meta"),
        "broken_links_count": broken_links_count,
        "outdated_tech_flags": outdated_flags,
        "load_time_ms": tech.get("response_time_ms"),
        "reviews_count": (maps_data or {}).get("reviews_count"),
        "rating": (maps_data or {}).get("rating"),
    }


if __name__ == "__main__":
    # Quick manual test with fake sample data, styled to match app/db/seed.py
    fake_maps_data = {"rating": 4.1, "reviews_count": 18}
    fake_scrape_data = {
        "tech_signals": {
            "has_viewport_meta": False,
            "outdated_signal": True,
            "uses_https": False,
            "cms_detected": None,
            "frameworks_detected": ["jQuery only (legacy)"],
            "analytics_detected": [],
            "response_time_ms": 4200,
        },
        "links": {
            "link_statuses": {"https://x.com/a": 200, "https://x.com/b": 404, "https://x.com/c": None},
        },
    }

    result = compute_sub_scores(fake_maps_data, fake_scrape_data, has_website=True)
    print(result)