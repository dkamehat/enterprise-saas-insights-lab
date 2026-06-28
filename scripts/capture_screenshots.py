"""Capture portfolio screenshots from the running Streamlit app.

Run the app first (``streamlit run app.py --server.headless true``), then:

    python scripts/capture_screenshots.py

Images are written to ``docs/assets/``. Uses the pre-installed Chromium.
"""

from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://localhost:8501"
OUT = Path(__file__).resolve().parents[1] / "docs" / "assets"

# (slug, output filename). "" is the home page.
PAGES = [
    ("", "home.png"),
    ("GTM_Economics", "gtm_economics.png"),
    ("Executive_Portfolio", "executive_portfolio.png"),
    ("Revenue_Assurance", "revenue_assurance.png"),
    ("Model_Governance", "model_governance.png"),
    ("Data_Quality", "data_quality.png"),
]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    # The pre-installed Chromium may not match the pip playwright version, so point
    # at the on-disk binary directly instead of downloading a new one.
    candidates = list(Path("/opt/pw-browsers").glob("chromium-*/chrome-linux/chrome"))
    launch_kwargs = {"executable_path": str(candidates[0])} if candidates else {}
    with sync_playwright() as p:
        browser = p.chromium.launch(**launch_kwargs)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        for slug, filename in PAGES:
            url = f"{BASE}/{slug}" if slug else BASE
            page.goto(url, wait_until="networkidle", timeout=60_000)
            # Let Streamlit finish its run and Plotly render.
            page.wait_for_timeout(4500)
            page.screenshot(path=str(OUT / filename), full_page=True)
            print(f"captured {filename}")
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
