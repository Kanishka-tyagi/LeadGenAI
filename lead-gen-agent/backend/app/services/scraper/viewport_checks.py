"""
Captures screenshots of a website at desktop, tablet, and mobile
viewport sizes — used to visually/programmatically assess responsiveness.
"""
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

VIEWPORTS = {
    "desktop": {"width": 1280, "height": 800},
    "tablet": {"width": 768, "height": 1024},
    "mobile": {"width": 375, "height": 812},
}


def capture_viewports(url: str, save_dir: str = "screenshots") -> dict:
    """
    Screenshots the page at desktop/tablet/mobile sizes.

    Waits for network idle + a short settle time so JS-driven fade-in
    animations and lazy-loaded content finish before capturing —
    otherwise screenshots can look broken/blank on animated sites.

    Returns a dict mapping viewport name -> saved file path.
    """
    paths = {}

    with sync_playwright() as p:
        browser = p.chromium.launch()

        for name, size in VIEWPORTS.items():
            page = browser.new_page(viewport=size)
            page.goto(url, timeout=20000, wait_until="networkidle")

            # let CSS/JS fade-in animations finish before capturing
            page.wait_for_timeout(2000)

            path = f"{save_dir}/{urlparse(url).netloc}_{name}.png"
            page.screenshot(path=path, full_page=True)  # full layout, not just first fold
            paths[name] = path

            page.close()

        browser.close()

    return paths


if __name__ == "__main__":
    # Quick manual test — swap in a real business URL from your leads table
    result = capture_viewports("https://drsunainadentalcare.com/")
    print(result)