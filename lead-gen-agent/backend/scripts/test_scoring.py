import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.services.scraper.website_analyzer import analyze_website
from app.services.scoring.deterministic_scoring import compute_sub_scores

scrape_result = analyze_website("https://drsunainadentalcare.com/")
sub_scores = compute_sub_scores(
    maps_data={"rating": 4.5, "reviews_count": 120},
    scrape_data=scrape_result,
    has_website=True,
)
print(sub_scores)