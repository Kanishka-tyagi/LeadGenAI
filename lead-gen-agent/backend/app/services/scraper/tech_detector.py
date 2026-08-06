import re
from datetime import datetime

import httpx


def detect_tech_signals(url: str) -> dict:
    """
    Comprehensive tech/digital-presence signal detection for a business website.
    """
    with httpx.Client(timeout=10.0, follow_redirects=True) as client:
        resp = client.get(url)
        html = resp.text
        headers = resp.headers

    signals = {}

    # --- Responsiveness / freshness (already had these) ---
    signals["has_viewport_meta"] = 'name="viewport"' in html
    year_matches = re.findall(r"(?:©|copyright)\s*(\d{4})", html, re.IGNORECASE)
    copyright_year = max([int(y) for y in year_matches], default=None)
    signals["copyright_year"] = copyright_year
    signals["outdated_signal"] = (
        copyright_year is not None and copyright_year < datetime.now().year - 3
    )

    # --- CMS / platform detection (expanded) ---
    cms_fingerprints = {
        "WordPress": "wp-content",
        "Wix": "wixstatic",
        "Squarespace": "squarespace",
        "Shopify": "cdn.shopify.com",
        "Webflow": "webflow.io",
        "Joomla": "/media/jui/",
        "Drupal": "sites/default/files",
        "GoDaddy Website Builder": "godaddysites.com",
    }
    signals["cms_detected"] = next(
        (name for name, marker in cms_fingerprints.items() if marker in html), None
    )

    # --- Frontend framework detection (custom-built vs template) ---
    framework_fingerprints = {
        "React": ("__next" in html or "react" in html.lower()),
        "Angular": "ng-version" in html,
        "Vue": "data-v-" in html,
        "jQuery only (legacy)": ("jquery" in html.lower() and signals["cms_detected"] is None),
    }
    signals["frameworks_detected"] = [name for name, found in framework_fingerprints.items() if found]

    # --- SSL / security ---
    signals["uses_https"] = url.startswith("https://")

    # --- Analytics / marketing maturity (relevant to "digital presence" score) ---
    analytics_fingerprints = {
        "Google Analytics": ("gtag(" in html or "google-analytics.com" in html),
        "Google Tag Manager": "googletagmanager.com" in html,
        "Facebook Pixel": "connect.facebook.net" in html,
        "Meta Business": "fbevents.js" in html,
    }
    signals["analytics_detected"] = [name for name, found in analytics_fingerprints.items() if found]

    # --- Live chat / support widgets (upsell signal) ---
    chat_fingerprints = {
        "Intercom": "widget.intercom.io" in html,
        "Drift": "js.driftt.com" in html,
        "Tawk.to": "embed.tawk.to" in html,
        "WhatsApp widget": "wa.me" in html or "api.whatsapp.com" in html,
    }
    signals["chat_widget_detected"] = [name for name, found in chat_fingerprints.items() if found]

    # --- App / ERP / portal signals (from your original workflow) ---
    app_store_signals = {
        "iOS app": "apps.apple.com" in html,
        "Android app": "play.google.com/store/apps" in html,
    }
    signals["app_links_detected"] = [name for name, found in app_store_signals.items() if found]

    portal_keywords = ["student portal", "patient portal", "client portal", "erp login", "login portal"]
    signals["portal_keywords_found"] = [kw for kw in portal_keywords if kw in html.lower()]

    # --- Server / hosting fingerprint (from response headers) ---
    signals["server_header"] = headers.get("server")
    signals["powered_by_header"] = headers.get("x-powered-by")

    # --- SEO maturity signals ---
    signals["response_time_ms"] = int(resp.elapsed.total_seconds() * 1000)

    return signals


def check_seo_files(base_url: str) -> dict:
    """Checks for robots.txt and sitemap.xml — basic SEO maturity indicators."""
    base = base_url.rstrip("/")
    results = {}
    with httpx.Client(timeout=8.0, follow_redirects=True) as client:
        for path in ["/robots.txt", "/sitemap.xml"]:
            try:
                resp = client.get(base + path)
                results[path.strip("/")] = resp.status_code == 200
            except httpx.RequestError:
                results[path.strip("/")] = False
    return results


if __name__ == "__main__":
    result = detect_tech_signals("https://drsunainadentalcare.com/")
    print(result)
    print(check_seo_files("https://drsunainadentalcare.com/"))