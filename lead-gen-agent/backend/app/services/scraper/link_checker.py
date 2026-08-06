import httpx


def check_link_health(links: list[str]) -> dict:
    """Checks HTTP status of each link. Returns broken link ratio + details."""
    results = {}
    with httpx.Client(timeout=10.0, follow_redirects=True) as client:
        for link in links:
            try:
                resp = client.head(link)
                results[link] = resp.status_code
            except httpx.RequestError:
                results[link] = None  # timed out / unreachable

    broken = sum(1 for status in results.values() if status is None or status >= 400)
    ratio = broken / len(results) if results else 0
    return {"link_statuses": results, "broken_link_ratio": ratio}