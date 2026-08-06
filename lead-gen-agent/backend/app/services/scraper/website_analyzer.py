import re
from urllib.parse import urlparse, urlunparse

from playwright.sync_api import sync_playwright
import httpx

from app.services.scraper.link_checker import check_link_health
from app.services.scraper.tech_detector import detect_tech_signals
from app.services.scraper.viewport_checks import capture_viewports

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")


from urllib.parse import urlparse, urlunparse
from playwright.sync_api import sync_playwright


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
        page.goto(url, timeout=15000, wait_until="domcontentloaded")

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
    """Runs all checks and returns one combined signals dict for a lead."""
    links = crawl_internal_links(url)
    return {
        "links": check_link_health(links),
        "screenshots": capture_viewports(url),
        "contact_info": extract_contact_info(url),
        "tech_signals": detect_tech_signals(url),
    }


if __name__ == "__main__":
    result = analyze_website("https://drsunainadentalcare.com/")
    print(result)