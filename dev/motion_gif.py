"""Record docs/motion.gif — a walkthrough of the theme's animations:
card entrance/exit, password-section expansion, theme switching, page
transitions in the Account Console. Requires ffmpeg. Run against the
dev stack:

    BASE_URL=http://localhost:8080 python3 dev/motion_gif.py
"""

import os
import pathlib
import subprocess
import tempfile

from playwright.sync_api import sync_playwright

BASE = os.environ.get("BASE_URL", "http://localhost:8080")
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "motion.gif"
SIZE = {"width": 1280, "height": 800}


def main():
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="m3gif"))
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport=SIZE, color_scheme="light", locale="en",
                            record_video_dir=str(tmp), record_video_size=SIZE)
        page = ctx.new_page()

        # Login: card entrance.
        page.goto(f"{BASE}/realms/demo/account/")
        page.wait_for_selector("#kc-page-title", timeout=20000)
        page.wait_for_timeout(1400)

        # Hover states: passkey button, a provider chip.
        page.hover("#authenticateWebAuthnButton")
        page.wait_for_timeout(700)
        page.hover(".m3-social-btn >> nth=0")
        page.wait_for_timeout(700)

        # Password section expands and collapses.
        page.click(".m3-pass-details summary")
        page.wait_for_timeout(1100)
        page.click(".m3-pass-details summary")
        page.wait_for_timeout(900)

        # Theme toggle: light -> dark -> light.
        page.click("#m3-theme-toggle")
        page.wait_for_timeout(1000)
        page.click("#m3-theme-toggle")
        page.wait_for_timeout(900)

        # Register: exit + entrance animations, then back.
        page.click("#kc-registration a")
        page.wait_for_selector("#kc-register-form", timeout=20000)
        page.wait_for_timeout(1500)
        page.click('a:has-text("Back to login")')
        page.wait_for_selector(".m3-pass-details", timeout=20000)
        page.wait_for_timeout(1200)

        # Sign in: loader reveal, then rail navigation (fade-through).
        page.evaluate("document.querySelector('details.m3-pass-details').open = true")
        page.wait_for_timeout(400)
        page.fill("#username", "demo")
        page.fill("#password", "demo1234")
        page.click("#kc-login")
        page.wait_for_selector(".m3-rail", timeout=25000)
        page.wait_for_timeout(1600)
        page.click('.m3-rail-item[href*="signing-in"]')
        page.wait_for_timeout(1500)
        page.click('.m3-rail-item[href*="linked-accounts"]')
        page.wait_for_timeout(1500)
        page.click("#m3-theme-toggle")
        page.wait_for_timeout(1400)

        page.close()
        video = page.video.path()
        ctx.close()
        b.close()

    palette = tmp / "palette.png"
    subprocess.run(["ffmpeg", "-y", "-i", video,
                    "-vf", "fps=18,scale=960:-1:flags=lanczos,palettegen=stats_mode=diff",
                    str(palette)], check=True, capture_output=True)
    subprocess.run(["ffmpeg", "-y", "-i", video, "-i", str(palette),
                    "-lavfi", "fps=18,scale=960:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle",
                    str(OUT)], check=True, capture_output=True)
    print(f"saved {OUT} ({OUT.stat().st_size // 1024} KiB)")


if __name__ == "__main__":
    main()
