#!/usr/bin/env python3
"""Capture README screenshots from a local Keycloak running the material3 theme.

Prerequisites:
    pip install playwright && playwright install chromium
    docker compose -f dev/docker-compose.dev.yml up -d   (or the docker run from README)

Usage:
    python3 dev/screenshots.py [output_dir]
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://localhost:8080/realms/demo/account/"
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "docs")
OUT.mkdir(parents=True, exist_ok=True)


def wait_login(page):
    page.wait_for_selector("#kc-page-title", timeout=15000)
    page.wait_for_timeout(400)


def login(page):
    page.evaluate("document.querySelector('details.m3-pass-details').open = true")
    page.fill("#username", "demo")
    page.fill("#password", "demo1234")
    page.click("#kc-login")
    page.wait_for_selector(".pf-v5-c-nav", timeout=20000)
    page.wait_for_timeout(1200)


def shot(page, name):
    page.screenshot(path=str(OUT / name))
    print("saved", OUT / name)


with sync_playwright() as p:
    browser = p.chromium.launch()

    for scheme in ("light", "dark"):
        ctx = browser.new_context(
            viewport={"width": 1440, "height": 900},
            color_scheme=scheme,
            locale="en-US",
        )
        page = ctx.new_page()

        page.goto(BASE)
        wait_login(page)
        shot(page, f"login-{scheme}.png")

        if scheme == "light":
            page.click("#kc-registration a")
            wait_login(page)
            shot(page, "register-light.png")
            page.goto(BASE)
            wait_login(page)

        login(page)
        shot(page, f"account-{scheme}.png")
        ctx.close()

    # mobile viewport
    ctx = browser.new_context(
        viewport={"width": 390, "height": 844},
        color_scheme="light",
        locale="en-US",
        device_scale_factor=2,
        is_mobile=True,
    )
    page = ctx.new_page()
    page.goto(BASE)
    wait_login(page)
    shot(page, "login-mobile.png")
    ctx.close()

    browser.close()
