"""
Local LLM scoring + email drafting — reads a lead's business info and
sub_scores (already computed by deterministic_scoring.py), asks the
local Ollama model to produce the final LLMOutput shape.
"""
import json

import httpx

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.1:8b"

REQUIRED_KEYS = [
    "website_score",
    "digital_presence",
    "overall_lead_score",
    "reasoning",
    "recommended_pitch",
    "drafted_email_subject",
    "drafted_email_body",
]

PROMPT_TEMPLATE = """You are scoring a business lead for a B2B web/app services company that SELLS website modernization, redesign, and digital presence improvement services to local businesses.

IMPORTANT — what "lead score" means here: overall_lead_score measures SALES OPPORTUNITY, not website quality. A business with a broken, outdated, non-responsive website is a HIGH-value lead. A business with an excellent, modern site is a LOW-value lead. A business with NO WEBSITE AT ALL is typically the HIGHEST-value lead of all — maximum opportunity, nothing to lose by pitching them.

Use these fixed reference points to calibrate overall_lead_score consistently:
- No website at all: 90-100 (maximum opportunity)
- Website with many serious problems (slow, broken links, not mobile-friendly, no SSL): 75-90
- Website with a few minor issues (e.g. missing analytics only, slightly slow): 40-60
- Website that is fast, responsive, secure, with analytics and no real flaws: 0-25 (almost nothing to sell them)

Business: {business_name}
Category: {category}

Deterministic signals already computed about this business:
{sub_scores_json}

Score based on OPPORTUNITY TO SELL THEM SOMETHING, anchored to the reference points above. Return ONLY valid JSON (no markdown formatting, no preamble, no explanation outside the JSON) with exactly this shape:
{{
  "website_score": <integer 0-100, current website QUALITY — 100 = excellent site, 0 = terrible/no site>,
  "digital_presence": <integer 0-100, current digital maturity — 100 = strong presence, 0 = nonexistent>,
  "overall_lead_score": <integer 0-100, SALES OPPORTUNITY calibrated to the reference points above>,
  "reasoning": "<one paragraph explaining the scores, referencing specific signals>",
  "recommended_pitch": "<the specific service or fix worth offering this business — if their site is already excellent, say so and note this is a low-priority lead>",
  "drafted_email_subject": "<short, non-spammy email subject line>",
  "drafted_email_body": "<a friendly, specific outreach email referencing real issues found on their site — not generic. If they have no real issues, keep this brief and note internally this lead may not be worth pursuing>"
}}
"""


def score_lead_with_llm(business_name: str, category: str, sub_scores: dict, retries: int = 1) -> dict | None:
    """
    Calls the local Ollama model with a lead's sub_scores, returns a dict
    matching LLMOutput, or None if the model fails to return valid JSON
    after retries.
    """
    prompt = PROMPT_TEMPLATE.format(
        business_name=business_name,
        category=category or "Unknown",
        sub_scores_json=json.dumps(sub_scores, indent=2),
    )

    for attempt in range(retries + 1):
        resp = httpx.post(
            OLLAMA_URL,
            json={"model": MODEL, "prompt": prompt, "format": "json", "stream": False},
            timeout=180.0,  # generous buffer for CPU inference (dev machine hits an Ollama/RTX 50-series
                             # Blackwell GPU-detection bug — falls back to CPU; production hardware won't have this issue)
        )
        resp.raise_for_status()
        raw_text = resp.json()["response"]

        try:
            parsed = json.loads(raw_text)
            if all(key in parsed for key in REQUIRED_KEYS):
                return parsed
            missing = [k for k in REQUIRED_KEYS if k not in parsed]
            print(f"  [warn] LLM response missing keys {missing}, retrying...")
        except json.JSONDecodeError:
            print(f"  [warn] LLM returned invalid JSON (attempt {attempt + 1}), retrying...")

    print(f"  [error] LLM scoring failed after {retries + 1} attempts for {business_name}")
    return None


if __name__ == "__main__":
    # Quick manual test with fake sub_scores, no DB/API needed
    fake_sub_scores = {
        "has_website": True,
        "mobile_responsive": False,
        "broken_links_count": 3,
        "outdated_tech_flags": ["outdated content", "not mobile-responsive", "no SSL"],
        "load_time_ms": 4200,
        "reviews_count": 18,
        "rating": 4.1,
    }

    result = score_lead_with_llm("Riverside Plumbing Co.", "Plumber", fake_sub_scores)
    print(json.dumps(result, indent=2))