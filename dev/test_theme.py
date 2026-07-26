#!/usr/bin/env python3
"""End-to-end tests for the material3 Keycloak theme.

Runs against a Keycloak started with dev/docker-compose.dev.yml (or the CI
equivalent). Environment:
    BASE_URL        default http://localhost:8080
    EXPECT_PASSKEY  "1" if the server supports the passkeys conditional UI
                    (Keycloak >= 26.2 with KC_FEATURES=passkeys), else "0"

Usage: python3 dev/test_theme.py
"""
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = os.environ.get("BASE_URL", "http://localhost:8080")
EXPECT_PASSKEY = os.environ.get("EXPECT_PASSKEY", "1") == "1"
THEME = Path(__file__).resolve().parent.parent / "theme" / "material3"

AUTH_URL = (
    f"{BASE}/realms/demo/protocol/openid-connect/auth"
    "?client_id=account-console"
    f"&redirect_uri={BASE}/realms/demo/account/".replace(":", "%3A").replace("/", "%2F")
)

FAILURES = []


def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {name}" + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        FAILURES.append(name)


def login_url(locale):
    return (
        f"{BASE}/realms/demo/protocol/openid-connect/auth?client_id=account-console"
        f"&redirect_uri={BASE.replace(':', '%3A').replace('/', '%2F')}%2Frealms%2Fdemo%2Faccount%2F"
        "&response_type=code&scope=openid"
        "&code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM&code_challenge_method=S256"
        f"&ui_locales={locale}"
    )


def test_messages_files():
    ru = (THEME / "login" / "messages" / "messages_ru.properties").read_text(encoding="utf-8")
    props = dict(
        line.split("=", 1)
        for line in ru.splitlines()
        if "=" in line and not line.strip().startswith("#")
    )
    check(
        "ru: webauthn-passwordless-display-name is not 'Пароль'",
        props.get("webauthn-passwordless-display-name") == "Ключ доступа",
        repr(props.get("webauthn-passwordless-display-name")),
    )
    check(
        "ru: webauthn-login-title mentions passkey",
        "passkey" in props.get("webauthn-login-title", "").lower(),
        repr(props.get("webauthn-login-title")),
    )
    for key in ("webauthn-error-api-get", "webauthn-error-user-not-found", "passkey-autofill-select"):
        val = props.get(key, "")
        check(f"ru: {key} does not say 'пароль'", val != "" and "парол" not in val.lower(), repr(val))


def test_login_pages(browser):
    for locale, btn_text, toggle_expected in (("en", "Sign in with a passkey", True), ("ru", "Войти с passkey", True)):
        ctx = browser.new_context(viewport={"width": 1280, "height": 900}, locale=locale)
        page = ctx.new_page()
        page.goto(login_url(locale))
        page.wait_for_selector("#kc-page-title", timeout=20000)
        check(f"login[{locale}]: themed card", page.locator(".m3-card").count() == 1)
        check(f"login[{locale}]: social buttons", page.locator(".m3-social-btn").count() == 4)
        check(f"login[{locale}]: collapsed password form", page.locator("details.m3-pass-details").count() == 1)
        check(f"login[{locale}]: theme toggle present", page.locator("#m3-theme-toggle").count() == 1)

        if EXPECT_PASSKEY:
            check(
                f"login[{locale}]: passkey button text",
                page.locator("#authenticateWebAuthnButton").count() == 1
                and btn_text in page.locator("#authenticateWebAuthnButton").inner_text(),
                page.locator("#authenticateWebAuthnButton").inner_text()
                if page.locator("#authenticateWebAuthnButton").count()
                else "button missing",
            )
        else:
            check(f"login[{locale}]: passkey button absent", page.locator("#authenticateWebAuthnButton").count() == 0)

        # Help dialog opens, shows onboarding text, closes.
        check(f"login[{locale}]: help button present", page.locator("#m3-help-btn").count() == 1)
        page.click("#m3-help-btn")
        page.wait_for_timeout(200)
        check(
            f"login[{locale}]: help dialog opens",
            page.evaluate("document.getElementById('m3-help')?.open === true"),
        )
        help_text = page.locator("#m3-help").inner_text()
        needle = "passkey" if locale == "en" else "passkey"
        check(f"login[{locale}]: help mentions passkey", needle in help_text.lower(), help_text[:120])
        page.click("#m3-help-close")
        page.wait_for_timeout(200)
        check(
            f"login[{locale}]: help dialog closes",
            page.evaluate("document.getElementById('m3-help')?.open === false"),
        )
        # "Try another way" is hidden on the main login page.
        check(
            f"login[{locale}]: try-another-way hidden",
            page.evaluate(
                "(el => !el || getComputedStyle(el).display === 'none')(document.querySelector('.m3-try-another'))"
            ),
        )

        # Theme toggle flips tokens and persists.
        bg_before = page.evaluate("getComputedStyle(document.body).backgroundColor")
        page.click("#m3-theme-toggle")
        page.wait_for_timeout(200)
        bg_after = page.evaluate("getComputedStyle(document.body).backgroundColor")
        check(f"login[{locale}]: toggle changes theme", bg_before != bg_after, f"{bg_before} -> {bg_after}")
        page.reload()
        page.wait_for_selector("#kc-page-title", timeout=20000)
        bg_reloaded = page.evaluate("getComputedStyle(document.body).backgroundColor")
        check(f"login[{locale}]: toggle persists", bg_reloaded == bg_after, f"{bg_reloaded} != {bg_after}")
        page.evaluate("localStorage.removeItem('m3-theme')")
        ctx.close()


def test_webauthn_error_message(browser):
    """Regression for upstream RU mistranslation: a failed passkey attempt must
    not claim a *password* failure."""
    if not EXPECT_PASSKEY:
        print("[skip] webauthn error message (no passkeys support)")
        return
    ctx = browser.new_context(viewport={"width": 1280, "height": 900}, locale="ru")
    page = ctx.new_page()
    page.goto(login_url("ru"))
    page.wait_for_selector("#webauth", timeout=20000, state="attached")
    page.evaluate(
        """() => {
          document.getElementById('error').value = 'test-cancelled';
          document.getElementById('webauth').submit();
        }"""
    )
    page.wait_for_selector("#kc-page-title", timeout=20000)
    body = page.evaluate("document.body.innerText")
    check("passkey error: no 'с помощью пароля'", "с помощью пароля" not in body, body[:300])
    check("passkey error: mentions ключ/passkey", ("ключ" in body.lower()) or ("passkey" in body.lower()), body[:300])
    ctx.close()


def test_register_page(browser):
    ctx = browser.new_context(viewport={"width": 1280, "height": 900}, locale="en")
    page = ctx.new_page()
    page.goto(login_url("en"))
    page.wait_for_selector("#kc-page-title", timeout=20000)
    page.click("#kc-registration a")
    page.wait_for_selector("#kc-register-form", timeout=20000)
    check("register: themed inputs", page.locator(".m3-input").count() >= 4)
    check(
        "register: filled submit",
        "m3-btn-filled" in (page.get_attribute("#kc-register-form input[type=submit]", "class") or ""),
    )
    ctx.close()


def test_account_console(browser):
    ctx = browser.new_context(viewport={"width": 1440, "height": 900}, locale="en")
    page = ctx.new_page()
    page.goto(f"{BASE}/realms/demo/account/")
    page.wait_for_selector("#kc-page-title", timeout=20000)
    page.evaluate("document.querySelector('details.m3-pass-details').open = true")
    page.fill("#username", "demo")
    page.fill("#password", "demo1234")
    page.click("#kc-login")
    page.wait_for_selector(".m3-rail", timeout=25000)

    check(
        "account: theme css loaded",
        page.evaluate("[...document.styleSheets].some(s => (s.href||'').includes('material3-account.css'))"),
    )
    rail_items = page.locator(".m3-rail-item").count()
    check("account: rail has flattened destinations", rail_items >= 4, f"items={rail_items}")
    check(
        "account: PF sidebar hidden",
        page.evaluate(
            "(el => !el || getComputedStyle(el).display === 'none')(document.querySelector('.pf-v5-c-page__sidebar'))"
        ),
    )
    # Rail navigation works.
    page.click('.m3-rail-item[href*="signing-in"]')
    page.wait_for_timeout(1500)
    check("account: rail navigates", "signing-in" in page.url)
    check(
        "account: rail active state follows",
        page.evaluate(
            "document.querySelector('.m3-rail-item[data-active]')?.getAttribute('href')?.includes('signing-in')"
        ),
    )
    # Theme toggle.
    dark_before = page.evaluate("document.documentElement.classList.contains('pf-v5-theme-dark')")
    page.click("#m3-theme-toggle")
    page.wait_for_timeout(300)
    dark_after = page.evaluate("document.documentElement.classList.contains('pf-v5-theme-dark')")
    check("account: toggle flips scheme", dark_before != dark_after)
    page.reload()
    page.wait_for_selector(".m3-rail", timeout=25000)
    dark_reloaded = page.evaluate("document.documentElement.classList.contains('pf-v5-theme-dark')")
    check("account: toggle persists", dark_reloaded == dark_after)
    page.evaluate("localStorage.removeItem('m3-theme')")

    # Mobile: the rail becomes a bottom navigation bar.
    mob = browser.new_context(viewport={"width": 390, "height": 844}, locale="en", is_mobile=True)
    mpage = mob.new_page()
    mpage.goto(f"{BASE}/realms/demo/account/")
    mpage.wait_for_selector("#kc-page-title", timeout=20000)
    mpage.evaluate("document.querySelector('details.m3-pass-details').open = true")
    mpage.fill("#username", "demo")
    mpage.fill("#password", "demo1234")
    mpage.click("#kc-login")
    mpage.wait_for_selector(".m3-rail", timeout=25000)
    check(
        "account[mobile]: bottom navigation bar",
        mpage.evaluate(
            """() => {
              const el = document.querySelector('.m3-rail');
              const cs = getComputedStyle(el);
              const rect = el.getBoundingClientRect();
              return cs.flexDirection === 'row' && Math.abs(rect.bottom - innerHeight) < 2 && rect.width >= innerWidth - 2;
            }"""
        ),
    )
    mob.close()
    ctx.close()


def test_forced_light_on_dark_system(browser):
    """System prefers dark but the user forced light: text must stay readable
    (regression: UA canvastext painted headings white on the light ground)."""
    ctx = browser.new_context(viewport={"width": 1440, "height": 900}, color_scheme="dark", locale="en-US")
    page = ctx.new_page()
    page.add_init_script("try { localStorage.setItem('m3-theme', 'light'); } catch (e) {}")
    page.goto(f"{BASE}/realms/demo/account/")
    page.wait_for_selector("#kc-page-title", timeout=20000)
    page.evaluate("document.querySelector('details.m3-pass-details').open = true")
    page.fill("#username", "demo")
    page.fill("#password", "demo1234")
    page.click("#kc-login")
    page.wait_for_selector(".m3-rail", timeout=25000)
    page.click('.m3-rail-item[href*="signing-in"]')
    page.wait_for_timeout(2000)
    res = page.evaluate(
        """() => {
          const t = [...document.querySelectorAll('.pf-v5-c-title')].find(e => /auth|Password|Passkey/i.test(e.textContent));
          const bg = getComputedStyle(document.body).backgroundColor;
          const c = t ? getComputedStyle(t).color : null;
          return { bg, c };
        }"""
    )
    check(
        "mixed: forced-light headings readable",
        res["c"] is not None and res["c"] != "rgb(255, 255, 255)",
        str(res),
    )
    page.evaluate("localStorage.removeItem('m3-theme')")
    ctx.close()


def main():
    test_messages_files()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        test_login_pages(browser)
        test_webauthn_error_message(browser)
        test_register_page(browser)
        test_account_console(browser)
        test_forced_light_on_dark_system(browser)
        browser.close()
    print(f"\n{len(FAILURES)} failure(s)" if FAILURES else "\nAll tests passed")
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()
