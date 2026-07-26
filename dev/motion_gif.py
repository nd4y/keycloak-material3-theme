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

# Visible cursor + Material-colored click ripple, injected into every page so
# the recording shows what is being interacted with.
CURSOR_JS = """
(() => {
  const boot = () => {
    if (document.getElementById('__m3cursor')) return;
    const c = document.createElement('div');
    c.id = '__m3cursor';
    c.style.cssText = 'position:fixed;z-index:2147483647;width:22px;height:22px;' +
      'border-radius:50%;background:rgba(100,66,214,.9);border:2.5px solid #fff;' +
      'box-shadow:0 2px 10px rgba(0,0,0,.4);pointer-events:none;' +
      'transform:translate(-50%,-50%);left:-60px;top:-60px;' +
      'transition:width .12s,height .12s';
    document.body.appendChild(c);
    const st = document.createElement('style');
    st.textContent = '@keyframes __m3rip{to{width:70px;height:70px;opacity:0}}';
    document.head.appendChild(st);
    addEventListener('mousemove', e => {
      c.style.left = e.clientX + 'px'; c.style.top = e.clientY + 'px';
    }, true);
    addEventListener('mousedown', e => {
      c.style.width = '15px'; c.style.height = '15px';
      const r = document.createElement('div');
      r.style.cssText = 'position:fixed;z-index:2147483646;left:' + e.clientX +
        'px;top:' + e.clientY + 'px;width:16px;height:16px;border-radius:50%;' +
        'border:3px solid rgba(100,66,214,.75);pointer-events:none;' +
        'transform:translate(-50%,-50%);animation:__m3rip .55s ease-out forwards';
      document.body.appendChild(r);
      setTimeout(() => r.remove(), 700);
    }, true);
    addEventListener('mouseup', () => {
      c.style.width = '22px'; c.style.height = '22px';
    }, true);
  };
  if (document.readyState === 'loading') addEventListener('DOMContentLoaded', boot);
  else boot();
})();
"""


def glide(page, selector, steps=28):
    """Move the visible cursor smoothly onto the element's center."""
    el = page.locator(selector).first
    el.scroll_into_view_if_needed()
    box = el.bounding_box()
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2,
                    steps=steps)


def click(page, selector):
    glide(page, selector)
    page.wait_for_timeout(280)
    page.mouse.down()
    page.wait_for_timeout(110)
    page.mouse.up()


def main():
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="m3gif"))
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport=SIZE, color_scheme="light", locale="en",
                            record_video_dir=str(tmp), record_video_size=SIZE)
        ctx.add_init_script(CURSOR_JS)
        page = ctx.new_page()

        # Login: card entrance.
        page.goto(f"{BASE}/realms/demo/account/")
        page.wait_for_selector("#kc-page-title", timeout=20000)
        page.wait_for_timeout(1400)

        # Hover states: passkey button, a provider chip.
        glide(page, "#authenticateWebAuthnButton")
        page.wait_for_timeout(700)
        glide(page, ".m3-social-btn >> nth=0", steps=18)
        page.wait_for_timeout(700)

        # Password section expands and collapses.
        click(page, ".m3-pass-details summary")
        page.wait_for_timeout(1100)
        click(page, ".m3-pass-details summary")
        page.wait_for_timeout(900)

        # Theme toggle: light -> dark -> light.
        click(page, "#m3-theme-toggle")
        page.wait_for_timeout(1000)
        click(page, "#m3-theme-toggle")
        page.wait_for_timeout(900)

        # Register: exit + entrance animations, then back.
        click(page, "#kc-registration a")
        page.wait_for_selector("#kc-register-form", timeout=20000)
        page.wait_for_timeout(1500)
        click(page, 'a:has-text("Back to login")')
        page.wait_for_selector(".m3-pass-details", timeout=20000)
        page.wait_for_timeout(1200)

        # Sign in: loader reveal, then rail navigation (fade-through).
        click(page, ".m3-pass-details summary")
        page.wait_for_timeout(700)
        page.fill("#username", "demo")
        page.fill("#password", "demo1234")
        click(page, "#kc-login")
        page.wait_for_selector(".m3-rail", timeout=25000)
        page.wait_for_timeout(1600)
        click(page, '.m3-rail-item[href*="signing-in"]')
        page.wait_for_timeout(1500)
        click(page, '.m3-rail-item[href*="linked-accounts"]')
        page.wait_for_timeout(1500)
        click(page, "#m3-theme-toggle")
        page.wait_for_timeout(1400)

        page.close()
        video = page.video.path()
        ctx.close()
        b.close()

    # 50 fps is the physical ceiling of the GIF format (frame delays are in
    # centiseconds and browsers clamp anything under 2 cs) — motion-interpolate
    # the ~25 fps screen recording up to it for maximum smoothness.
    flt = ("minterpolate=fps=50:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,"
           "scale=960:-1:flags=lanczos")
    palette = tmp / "palette.png"
    subprocess.run(["ffmpeg", "-y", "-i", video,
                    "-vf", f"{flt},palettegen=stats_mode=diff",
                    str(palette)], check=True, capture_output=True)
    subprocess.run(["ffmpeg", "-y", "-i", video, "-i", str(palette),
                    "-lavfi", f"{flt}[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle",
                    str(OUT)], check=True, capture_output=True)
    print(f"saved {OUT} ({OUT.stat().st_size // 1024} KiB)")


if __name__ == "__main__":
    main()
