"""
Orchestrates all website checks: link crawling/health, viewport
screenshots, contact info extraction, and tech signal detection.

Each check is wrapped individually — one slow/broken site shouldn't
cause the whole lead to lose all its signals. A failed check just
falls back to an empty/neutral result instead of crashing the batch.
"""
import re
from urllib.parse import urlparse, urlunparse

from playwright.sync_api import sync_playwright
import httpx

from app.services.scraper.link_checker import check_link_health
from app.services.scraper.tech_detector import detect_tech_signals
from app.services.scraper.viewport_checks import capture_viewports

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")


def _normalize_url(url: str) -> str:
    """Strips fragment + query params + trailing slash so the same page
    reached via different link variants counts as one URL, not several."""
    parsed = urlparse(url)
    normalized = urlunparse((parsed.scheme, parsed.netloc, parsed.path.rstrip("/"), "", "", ""))
    return normalized


def crawl_internal_links(url: str, max_links: int = 15) -> list[str]:
    domain = urlparse(url).netloc
    links = set()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url, timeout=30000, wait_until="domcontentloaded")

        hrefs = page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
        for href in hrefs:
            if urlparse(href).netloc == domain:
                links.add(_normalize_url(href))
            if len(links) >= max_links:
                break

        browser.close()

    return list(links)


def extract_contact_info(url: str) -> dict:
    with httpx.Client(timeout=10.0, follow_redirects=True) as client:
        resp = client.get(url)
        html = resp.text

    emails = set(EMAIL_REGEX.findall(html))
    mailto_matches = re.findall(r'mailto:([^"\'>?]+)', html)
    emails.update(mailto_matches)

    return {"emails_found": list(emails)}


def analyze_website(url: str) -> dict:
    """
    Runs all checks and returns one combined signals dict for a lead.
    Each check is isolated — a failure in one (timeout, network error,
    site blocking automation) doesn't prevent the others from running,
    and doesn't crash the whole batch in run_scraper.py.
    """
    # --- Links: crawl + health check ---
    try:
        links = crawl_internal_links(url)
        link_health = check_link_health(links)
    except Exception as e:
        print(f"  [warn] link crawl/check failed for {url}: {e}")
        link_health = {"link_statuses": {}, "broken_link_ratio": None}

    # --- Viewport screenshots ---
    try:
        screenshots = capture_viewports(url)
    except Exception as e:
        print(f"  [warn] screenshot capture failed for {url}: {e}")
        screenshots = {}

    # --- Contact info (emails) ---
    try:
        contact_info = extract_contact_info(url)
    except Exception as e:
        print(f"  [warn] contact info extraction failed for {url}: {e}")
        contact_info = {"emails_found": []}

    # --- Tech signals ---
    try:
        tech_signals = detect_tech_signals(url)
    except Exception as e:
        print(f"  [warn] tech signal detection failed for {url}: {e}")
        tech_signals = {}

    return {
        "links": link_health,
        "screenshots": screenshots,
        "contact_info": contact_info,
        "tech_signals": tech_signals,
    }


if __name__ == "__main__":
    result = analyze_website("https://drsunainadentalcare.com/")
    print(result)