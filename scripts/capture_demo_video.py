"""Record a short walkthrough of the running Streamlit app to a webm video.

Run the app first, then:  python scripts/capture_demo_video.py
Outputs docs/assets/_demo.webm (converted to demo.gif by the Makefile target).
"""

from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://localhost:8501"
OUT = Path(__file__).resolve().parents[1] / "docs" / "assets"
SIZE = {"width": 1280, "height": 800}


def _scroll_through(page, total: int, steps: int, pause: int) -> None:
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(pause)
    for i in range(1, steps + 1):
        page.evaluate(f"window.scrollTo(0, {int(total * i / steps)})")
        page.wait_for_timeout(pause)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    candidates = list(Path("/opt/pw-browsers").glob("chromium-*/chrome-linux/chrome"))
    launch_kwargs = {"executable_path": str(candidates[0])} if candidates else {}
    with sync_playwright() as p:
        browser = p.chromium.launch(**launch_kwargs)
        context = browser.new_context(
            viewport=SIZE, record_video_dir=str(OUT), record_video_size=SIZE
        )
        page = context.new_page()
        # GTM Economics — the flagship S&O view.
        page.goto(f"{BASE}/GTM_Economics", wait_until="networkidle", timeout=60_000)
        page.wait_for_timeout(4000)
        _scroll_through(page, total=2400, steps=10, pause=520)
        # Executive Portfolio — value x win-fit x data trust.
        page.goto(f"{BASE}/Executive_Portfolio", wait_until="networkidle", timeout=60_000)
        page.wait_for_timeout(3500)
        _scroll_through(page, total=1700, steps=7, pause=520)
        video_path = page.video.path()
        context.close()
        browser.close()
    final = OUT / "_demo.webm"
    Path(video_path).replace(final)
    print(f"wrote {final}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
