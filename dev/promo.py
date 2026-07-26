"""Render docs/hero.png — the README hero: three device mockups (laptop,
tablet, phone) with live screenshots of the theme, composed on an M3
gradient backdrop. Run against the dev stack:

    BASE_URL=http://localhost:8080 python3 dev/promo.py
"""

import os
import pathlib
import tempfile

from playwright.sync_api import sync_playwright

BASE = os.environ.get("BASE_URL", "http://localhost:8080")
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "hero.png"


def login_url(page):
    page.goto(f"{BASE}/realms/demo/account/")
    page.wait_for_selector("#kc-page-title", timeout=20000)


def sign_in(page):
    login_url(page)
    page.evaluate("document.querySelector('details.m3-pass-details').open = true")
    page.fill("#username", "demo")
    page.fill("#password", "demo1234")
    page.click("#kc-login")
    page.wait_for_selector(".m3-rail", timeout=25000, state="attached")
    page.wait_for_timeout(1200)


HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&family=Google+Sans+Text:wght@400;500&display=swap" rel="stylesheet">
<style>
  * { margin: 0; box-sizing: border-box; }
  body { width: 2560px; height: 1280px; overflow: hidden; position: relative;
         background: linear-gradient(135deg, #FEFBFF 0%, #F1E4F5 45%, #DCDAF5 100%);
         font-family: "Google Sans", sans-serif; }
  .blob { position: absolute; border-radius: 50%; filter: blur(2px); }
  .b1 { width: 900px; height: 900px; right: -260px; top: -380px; background: #6442D6; opacity: .16; }
  .b2 { width: 620px; height: 620px; left: -200px; bottom: -260px; background: #F1D3F9; opacity: .8; }
  .b3 { width: 300px; height: 300px; left: 46%; bottom: -120px; background: #DCDAF5; opacity: .9;
        border-radius: 36% 64% 58% 42% / 46% 38% 62% 54%; }

  .copy { position: absolute; left: 120px; top: 130px; width: 760px; z-index: 5; }
  .copy .badge { display: inline-flex; align-items: center; gap: 14px; margin-bottom: 42px; }
  .copy .badge img { width: 72px; height: 72px; }
  .copy .badge span { font-size: 30px; font-weight: 500; color: #4D4256; letter-spacing: .5px; }
  .copy h1 { font-size: 88px; font-weight: 500; line-height: 1.08; color: #1C1B1D; letter-spacing: 0; }
  .copy h1 em { font-style: normal; color: #6442D6; }
  .copy p { margin-top: 34px; font-family: "Google Sans Text", sans-serif;
            font-size: 30px; line-height: 1.45; color: #4D4256; max-width: 21em; }
  .chips { display: flex; gap: 14px; margin-top: 44px; flex-wrap: wrap; }
  .chip { padding: 14px 26px; border-radius: 100px; background: #DCDAF5; color: #21182B;
          font-size: 24px; font-weight: 500; }
  .chip.filled { background: #6442D6; color: #fff; }

  .stage { position: absolute; right: 0; top: 0; width: 1660px; height: 1280px;
           perspective: 3200px; z-index: 2; }

  .laptop { position: absolute; right: 420px; top: 170px; width: 1060px;
            transform: rotateY(-10deg) rotateX(3deg); transform-style: preserve-3d; }
  .laptop .screen { border-radius: 26px; padding: 16px; background: #1c1b1d;
                    box-shadow: 0 60px 120px rgba(30, 20, 60, .35); }
  .laptop .screen img { display: block; width: 100%; border-radius: 14px; }
  .laptop .base { margin: 0 -60px; height: 26px; border-radius: 0 0 22px 22px;
                  background: linear-gradient(#e8e2ea, #c9c2cc);
                  box-shadow: 0 30px 60px rgba(30, 20, 60, .25); }
  .laptop .base::before { content: ""; display: block; margin: 0 auto; width: 180px; height: 10px;
                          border-radius: 0 0 12px 12px; background: #b3adb8; }

  .tablet { position: absolute; right: 64px; top: 84px; width: 470px;
            transform: rotateY(-14deg) rotateX(2deg);
            border-radius: 34px; padding: 18px; background: #1c1b1d;
            box-shadow: 0 50px 100px rgba(30, 20, 60, .38); }
  .tablet img { display: block; width: 100%; border-radius: 18px; }

  .phone { position: absolute; right: 348px; bottom: 96px; width: 300px;
           transform: rotateY(8deg) rotateZ(-3deg);
           border-radius: 46px; padding: 14px; background: #1c1b1d;
           box-shadow: 0 50px 110px rgba(30, 20, 60, .45); z-index: 6; }
  .phone img { display: block; width: 100%; border-radius: 34px; }
  .phone::after { content: ""; position: absolute; top: 26px; left: 50%; margin-left: -7px;
                  width: 14px; height: 14px; border-radius: 50%; background: #000; }
</style></head>
<body>
  <div class="blob b1"></div><div class="blob b2"></div><div class="blob b3"></div>
  <div class="copy">
    <div class="badge"><img src="__FAVICON__" alt=""><span>keycloak-theme-material3</span></div>
    <h1>Material&nbsp;3 Expressive<br>for <em>Keycloak</em></h1>
    <p>Passkey-first login and a fully re-imagined Account Console — styled to
       match m3.material.io, down to the pixel.</p>
    <div class="chips">
      <span class="chip filled">Passkey-first</span>
      <span class="chip">Light &amp; dark</span>
      <span class="chip">Adaptive</span>
      <span class="chip">No rebuild</span>
    </div>
  </div>
  <div class="stage">
    <div class="tablet"><img src="__TABLET__" alt=""></div>
    <div class="laptop">
      <div class="screen"><img src="__LAPTOP__" alt=""></div>
      <div class="base"></div>
    </div>
    <div class="phone"><img src="__PHONE__" alt=""></div>
  </div>
</body></html>
"""


def main():
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="m3promo"))
    with sync_playwright() as p:
        b = p.chromium.launch()

        # Laptop: login page with the brand panel (light).
        ctx = b.new_context(viewport={"width": 1440, "height": 900}, color_scheme="light",
                            device_scale_factor=2)
        pg = ctx.new_page()
        login_url(pg)
        pg.wait_for_timeout(600)
        pg.screenshot(path=str(tmp / "laptop.png"))
        ctx.close()

        # Tablet: Account Console "Signing in" page, dark.
        ctx = b.new_context(viewport={"width": 834, "height": 1112}, color_scheme="dark",
                            device_scale_factor=2)
        pg = ctx.new_page()
        sign_in(pg)
        pg.goto(f"{BASE}/realms/demo/account/account-security/signing-in")
        pg.wait_for_selector(".m3-rail", timeout=25000, state="attached")
        pg.wait_for_timeout(1500)
        pg.screenshot(path=str(tmp / "tablet.png"))
        ctx.close()

        # Phone: login page, light.
        ctx = b.new_context(viewport={"width": 390, "height": 844}, color_scheme="light",
                            device_scale_factor=2, is_mobile=True)
        pg = ctx.new_page()
        login_url(pg)
        pg.wait_for_timeout(600)
        pg.screenshot(path=str(tmp / "phone.png"))
        ctx.close()

        favicon = (ROOT / "theme/material3/login/resources/img/favicon.svg").as_uri()
        html = (HTML
                .replace("__LAPTOP__", (tmp / "laptop.png").as_uri())
                .replace("__TABLET__", (tmp / "tablet.png").as_uri())
                .replace("__PHONE__", (tmp / "phone.png").as_uri())
                .replace("__FAVICON__", favicon))
        page_file = tmp / "promo.html"
        page_file.write_text(html, encoding="utf-8")

        ctx = b.new_context(viewport={"width": 2560, "height": 1280})
        pg = ctx.new_page()
        pg.goto(page_file.as_uri())
        pg.wait_for_timeout(2500)  # fonts + images
        pg.screenshot(path=str(OUT))
        ctx.close()
        b.close()
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
