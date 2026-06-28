"""Build an animated walkthrough GIF from the running Streamlit app.

Captures viewport frames while scrolling key pages, then assembles them with
Pillow (no ffmpeg/gif filters required). Run the app first, then:

    python scripts/capture_demo_gif.py

Output: docs/assets/demo.gif  (synthetic data only).
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8501"
OUT = Path(__file__).resolve().parents[1] / "docs" / "assets"
VIEW = {"width": 1280, "height": 800}
GIF_WIDTH = 900

# (slug, [scroll_y positions]). The first frame of each page is held longer.
PLAN = [
    ("GTM_Economics", [0, 0, 360, 720, 1080, 1500, 1950, 2380]),
    ("Executive_Portfolio", [0, 0, 460, 980, 1500]),
]


def _grab(page, y: int) -> Image.Image:
    page.evaluate(f"window.scrollTo(0, {y})")
    page.wait_for_timeout(450)
    png = page.screenshot()
    img = Image.open(io.BytesIO(png)).convert("RGB")
    h = round(img.height * GIF_WIDTH / img.width)
    return img.resize((GIF_WIDTH, h), Image.LANCZOS)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    candidates = list(Path("/opt/pw-browsers").glob("chromium-*/chrome-linux/chrome"))
    launch_kwargs = {"executable_path": str(candidates[0])} if candidates else {}
    frames: list[Image.Image] = []
    durations: list[int] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(**launch_kwargs)
        page = browser.new_page(viewport=VIEW)
        for slug, positions in PLAN:
            page.goto(f"{BASE}/{slug}", wait_until="networkidle", timeout=60_000)
            page.wait_for_timeout(3500)
            for i, y in enumerate(positions):
                frames.append(_grab(page, y))
                durations.append(1500 if i == 0 else 700)
        browser.close()

    # Crop every frame to the shortest height so the GIF has a single canvas size.
    min_h = min(f.height for f in frames)
    frames = [f.crop((0, 0, GIF_WIDTH, min_h)) for f in frames]
    palette_frames = [
        f.convert("P", palette=Image.ADAPTIVE, colors=128, dither=Image.FLOYDSTEINBERG)
        for f in frames
    ]
    out = OUT / "demo.gif"
    palette_frames[0].save(
        out,
        save_all=True,
        append_images=palette_frames[1:],
        duration=durations,
        loop=0,
        optimize=True,
        disposal=2,
    )
    size_mb = out.stat().st_size / 1_000_000
    print(f"wrote {out} ({len(frames)} frames, {size_mb:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
