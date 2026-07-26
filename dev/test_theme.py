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

    # Compact m3Nav* labels exist in both account locales
    nav_keys = {"m3NavPersonalInfo", "m3NavSigningIn", "m3NavDeviceActivity",
                "m3NavLinkedAccounts", "m3NavApplications"}
    for lang in ("en", "ru"):
        txt = (THEME / "account" / "messages" / f"messages_{lang}.properties").read_text(encoding="utf-8")
        keys = {line.split("=", 1)[0].strip() for line in txt.splitlines()
                if "=" in line and not line.strip().startswith("#")}
        check(f"account {lang}: compact m3Nav* labels present", nav_keys <= keys,
              str(sorted(nav_keys - keys)))


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
        check(
            f"login[{locale}]: ID favicon",
            "img/favicon.svg" in (page.get_attribute('link[rel="icon"]', "href") or ""),
        )

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

        # Theme-mode menu: system / light / dark.
        bg_system = page.evaluate("getComputedStyle(document.body).backgroundColor")
        page.click("#m3-theme-toggle")
        page.wait_for_timeout(250)
        check(
            f"login[{locale}]: theme menu opens with 3 modes",
            page.evaluate("!document.getElementById('m3-theme-menu').hidden")
            and page.locator("#m3-theme-menu [data-mode]").count() == 3,
        )
        page.click('#m3-theme-menu [data-mode="dark"]')
        page.wait_for_timeout(250)
        bg_dark = page.evaluate("getComputedStyle(document.body).backgroundColor")
        check(f"login[{locale}]: dark mode applies", bg_dark != bg_system, f"{bg_system} -> {bg_dark}")
        check(
            f"login[{locale}]: dark mode stored",
            page.evaluate("localStorage.getItem('m3-theme')") == "dark",
        )
        page.reload()
        page.wait_for_selector("#kc-page-title", timeout=20000)
        bg_reloaded = page.evaluate("getComputedStyle(document.body).backgroundColor")
        check(f"login[{locale}]: dark mode persists", bg_reloaded == bg_dark, f"{bg_reloaded} != {bg_dark}")
        # Back to "system": the stored key is cleared, the OS preference (light
        # in this context) applies again.
        page.click("#m3-theme-toggle")
        page.wait_for_timeout(250)
        page.click('#m3-theme-menu [data-mode="system"]')
        page.wait_for_timeout(250)
        check(
            f"login[{locale}]: system mode clears the override",
            page.evaluate("localStorage.getItem('m3-theme')") is None
            and page.evaluate("getComputedStyle(document.body).backgroundColor") == bg_system,
        )
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
    # Compact m3Nav* labels replace the console's long nav strings (which
    # double as page headings and must stay long there).
    first_label = page.locator('.m3-rail-item[href$="/account/"] .m3-rail-label, .m3-rail-item[href*="personal-info"] .m3-rail-label').first.inner_text().strip()
    check("account: rail uses compact nav labels", first_label == "Profile", repr(first_label))
    page.wait_for_selector(".m3-brand-mark", timeout=10000)
    check(
        "account: brand shows realm name + ID badge",
        page.locator(".m3-brand-name").inner_text() == "demo"
        and page.locator(".m3-brand-badge").inner_text() == "ID",
    )
    check(
        "account: brand links to the realm's account console",
        "/realms/demo/account" in (page.get_attribute(".pf-v5-c-masthead__brand", "href") or ""),
        page.get_attribute(".pf-v5-c-masthead__brand", "href"),
    )
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
    check(
        "account: page transition animation runs",
        page.evaluate("document.querySelector('.pf-v5-c-page__main').classList.contains('m3-page-in')"),
    )
    page.click('.m3-rail-item[href*="linked-accounts"]')
    page.wait_for_selector(".pf-v5-c-text-input-group", timeout=15000)
    check(
        "account: filter field wide enough",
        page.evaluate("document.querySelector('.pf-v5-c-text-input-group').getBoundingClientRect().width >= 260"),
    )
    placeholder = page.evaluate(
        "document.querySelector('.pf-v5-c-text-input-group__text-input')?.placeholder || ''"
    )
    check(
        "account: filter placeholder has no ellipsis",
        placeholder != "" and not placeholder.rstrip().endswith(("...", "…")),
        placeholder,
    )
    check(
        "account: search arrow centered in its round button",
        page.evaluate(
            """(() => {
              const b = document.querySelector('.pf-v5-c-button.pf-m-control');
              const i = b && b.querySelector('svg');
              if (!b || !i) return false;
              const br = b.getBoundingClientRect(), ir = i.getBoundingClientRect();
              return Math.abs((br.left + br.right) / 2 - (ir.left + ir.right) / 2) < 1.5
                  && Math.abs((br.top + br.bottom) / 2 - (ir.top + ir.bottom) / 2) < 1.5;
            })()"""
        ),
    )
    check(
        "account: ID favicon injected",
        page.evaluate(
            "(document.querySelector('link[rel=\\'icon\\']')?.href || '').includes('account/material3/img/favicon.svg')"
        ),
        page.evaluate("document.querySelector('link[rel=\\'icon\\']')?.href"),
    )
    # Theme-mode menu: system / light / dark.
    page.click("#m3-theme-toggle")
    page.wait_for_timeout(300)
    check(
        "account: theme menu opens with 3 modes",
        page.evaluate("!document.querySelector('.m3-theme-menu').hidden")
        and page.locator(".m3-theme-menu [data-mode]").count() == 3,
    )
    check(
        "account: theme menu labels localized",
        page.evaluate("document.querySelector('.m3-theme-menu [data-mode=\\'system\\'] span')?.textContent") == "System",
    )
    page.click('.m3-theme-menu [data-mode="dark"]')
    page.wait_for_timeout(300)
    check(
        "account: dark mode applies",
        page.evaluate("document.documentElement.classList.contains('pf-v5-theme-dark')"),
    )
    page.reload()
    page.wait_for_selector(".m3-rail", timeout=25000)
    check(
        "account: dark mode persists",
        page.evaluate("document.documentElement.classList.contains('pf-v5-theme-dark')"),
    )
    page.click("#m3-theme-toggle")
    page.wait_for_timeout(300)
    page.click('.m3-theme-menu [data-mode="system"]')
    page.wait_for_timeout(300)
    check(
        "account: system mode clears the override and follows the OS",
        page.evaluate("localStorage.getItem('m3-theme')") is None
        and not page.evaluate("document.documentElement.classList.contains('pf-v5-theme-dark')"),
    )

    # Fonts from m3.material.io (Google Sans) actually loaded.
    page.wait_for_timeout(500)
    check(
        "account: Google Sans loaded",
        page.evaluate("document.fonts.check('16px \"Google Sans\"') || document.fonts.check('16px \"Google Sans Text\"')"),
    )

    # Medium screens (768–1099): rail hides, hamburger + drawer appear.
    med = browser.new_context(viewport={"width": 1000, "height": 800}, locale="en")
    dpage = med.new_page()
    dpage.goto(f"{BASE}/realms/demo/account/")
    dpage.wait_for_selector("#kc-page-title", timeout=20000)
    dpage.evaluate("document.querySelector('details.m3-pass-details').open = true")
    dpage.fill("#username", "demo")
    dpage.fill("#password", "demo1234")
    dpage.click("#kc-login")
    dpage.wait_for_selector(".m3-rail", timeout=25000, state="attached")
    check(
        "account[medium]: rail hidden",
        dpage.evaluate("getComputedStyle(document.querySelector('.m3-rail')).display === 'none'"),
    )
    check(
        "account[medium]: hamburger visible",
        dpage.evaluate("getComputedStyle(document.querySelector('.m3-menu-btn')).display !== 'none'"),
    )
    dpage.click(".m3-menu-btn")
    dpage.wait_for_timeout(500)
    check(
        "account[medium]: drawer opens",
        dpage.evaluate("!document.querySelector('.m3-drawer').hidden && document.querySelector('.m3-drawer').classList.contains('m3-open')"),
    )
    check(
        "account[medium]: drawer has items",
        dpage.locator(".m3-drawer-item").count() >= 4,
    )
    dpage.click('.m3-drawer-item[href*="signing-in"]')
    dpage.wait_for_timeout(1200)
    check("account[medium]: drawer navigates", "signing-in" in dpage.url)
    check(
        "account[medium]: drawer closed after navigation",
        dpage.evaluate("document.querySelector('.m3-drawer').hidden === true"),
    )
    med.close()

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
    check(
        "account[mobile]: bottom bar labels fit without truncation",
        mpage.evaluate(
            """[...document.querySelectorAll('.m3-rail-label')]
                 .every(l => l.scrollWidth <= l.clientWidth)"""
        ),
        mpage.evaluate(
            """[...document.querySelectorAll('.m3-rail-label')]
                 .filter(l => l.scrollWidth > l.clientWidth).map(l => l.textContent).join(', ')"""
        ),
    )
    check(
        "account[mobile]: user-menu kebab pinned to the right edge",
        mpage.evaluate(
            """(() => {
              const b = document.querySelector('[data-testid="options-kebab-toggle"]');
              if (!b) return false;
              const r = b.getBoundingClientRect();
              return r.height > 0 && innerWidth - r.right < 72;
            })()"""
        ),
        mpage.evaluate(
            "JSON.stringify(document.querySelector('[data-testid=\\'options-kebab-toggle\\']')?.getBoundingClientRect())"
        ),
    )
    check(
        "account[mobile]: kebab drawn as a round icon button",
        mpage.evaluate(
            """(() => {
              const b = document.querySelector('[data-testid="options-kebab-toggle"]');
              if (!b) return false;
              const cs = getComputedStyle(b);
              const r = b.getBoundingClientRect();
              return cs.borderRadius.includes('50%') && Math.abs(r.width - r.height) < 2;
            })()"""
        ),
    )
    mob.close()

    # Russian nav labels are the longest strings — verify the compact set fits.
    mobru = browser.new_context(viewport={"width": 390, "height": 844}, locale="ru-RU", is_mobile=True)
    rpage = mobru.new_page()
    rpage.goto(f"{BASE}/realms/demo/account/")
    rpage.wait_for_selector("#kc-page-title", timeout=20000)
    rpage.evaluate("document.querySelector('details.m3-pass-details').open = true")
    rpage.fill("#username", "demo")
    rpage.fill("#password", "demo1234")
    rpage.click("#kc-login")
    rpage.wait_for_selector(".m3-rail", timeout=25000)
    ru_first = rpage.locator('.m3-rail-item[href$="/account/"] .m3-rail-label, .m3-rail-item[href*="personal-info"] .m3-rail-label').first.inner_text().strip()
    check("account[mobile,ru]: compact Russian labels", ru_first == "Профиль", repr(ru_first))
    check(
        "account[mobile,ru]: theme menu labels in Russian",
        rpage.evaluate("document.querySelector('.m3-theme-menu [data-mode=\\'system\\'] span')?.textContent") == "Системная",
    )
    check(
        "account[mobile,ru]: bottom bar labels fit without truncation",
        rpage.evaluate(
            """[...document.querySelectorAll('.m3-rail-label')]
                 .every(l => l.scrollWidth <= l.clientWidth)"""
        ),
        rpage.evaluate(
            """[...document.querySelectorAll('.m3-rail-label')]
                 .filter(l => l.scrollWidth > l.clientWidth).map(l => l.textContent).join(', ')"""
        ),
    )
    mobru.close()
    ctx.close()


def _dur(page, sel, prop="transition-duration", pseudo=None):
    """Longest duration (s) of a computed transition/animation on `sel`."""
    return page.evaluate(
        """([sel, prop, pseudo]) => {
          const el = document.querySelector(sel);
          if (!el) return -1;
          const v = getComputedStyle(el, pseudo || undefined).getPropertyValue(prop);
          return Math.max(...v.split(',').map(s => parseFloat(s) || 0));
        }""",
        [sel, prop, pseudo],
    )


def test_motion(browser):
    """Every user-facing interaction must be animated (M3 'expressive motion'):
    non-zero durations, M3 standard easing on big moves, and everything off
    under prefers-reduced-motion."""
    ctx = browser.new_context(viewport={"width": 1280, "height": 900}, locale="en")
    page = ctx.new_page()
    page.goto(login_url("en"))
    page.wait_for_selector("#kc-page-title", timeout=20000)

    check("motion[login]: card entrance animation",
          page.evaluate("getComputedStyle(document.querySelector('.m3-card')).animationName") == "m3-card-in"
          and _dur(page, ".m3-card", "animation-duration") > 0)
    page.evaluate("document.body.classList.add('m3-exit')")
    check("motion[login]: card exit animation",
          page.evaluate("getComputedStyle(document.querySelector('.m3-card')).animationName") == "m3-card-out")
    page.evaluate("document.body.classList.remove('m3-exit')")
    check("motion[login]: brand panel slides on breakpoint",
          _dur(page, ".m3-brand") > 0
          and "flex-basis" in page.evaluate(
              "getComputedStyle(document.querySelector('.m3-brand')).transitionProperty"))
    check("motion[login]: password details animates",
          _dur(page, ".m3-pass-details", pseudo="::details-content") > 0)
    check("motion[login]: details uses M3 standard easing",
          "0.2, 0, 0, 1" in page.evaluate(
              "getComputedStyle(document.querySelector('.m3-pass-details'), '::details-content').transitionTimingFunction"))
    for sel, name in ((".m3-social-btn", "social button"),
                      ("#m3-theme-toggle", "theme toggle"),
                      ("#m3-help-btn", "help button"),
                      (".m3-pass-details summary", "password summary"),
                      ("#kc-current-locale-link", "locale button")):
        if page.locator(sel).count():
            check(f"motion[login]: {name} hover is animated", _dur(page, sel) > 0)
    if EXPECT_PASSKEY:
        check("motion[login]: passkey button animated", _dur(page, "#authenticateWebAuthnButton") > 0)
    check("motion[login]: theme menu uses M3 easing",
          _dur(page, "#m3-theme-menu") > 0
          and "0.2, 0, 0, 1" in page.evaluate(
              "getComputedStyle(document.getElementById('m3-theme-menu')).transitionTimingFunction"))
    # Brand panel actually collapses (smoothly) when the window narrows.
    w_before = page.evaluate("document.querySelector('.m3-brand').getBoundingClientRect().width")
    page.set_viewport_size({"width": 800, "height": 900})
    page.wait_for_timeout(600)
    w_after = page.evaluate("document.querySelector('.m3-brand').getBoundingClientRect().width")
    check("motion[login]: brand panel collapses below 940px",
          w_before > 300 and w_after < 2, f"{w_before} -> {w_after}")
    ctx.close()

    # Reduced motion: all of it must switch off.
    rm = browser.new_context(viewport={"width": 1280, "height": 900}, locale="en",
                             reduced_motion="reduce")
    rpage = rm.new_page()
    rpage.goto(login_url("en"))
    rpage.wait_for_selector("#kc-page-title", timeout=20000)
    check("motion[login]: reduced-motion kills animations",
          rpage.evaluate("getComputedStyle(document.querySelector('.m3-card')).animationName") == "none"
          and _dur(rpage, ".m3-pass-details summary") == 0)
    rm.close()

    # Account console.
    ctx = browser.new_context(viewport={"width": 1440, "height": 900}, locale="en")
    page = ctx.new_page()
    page.goto(f"{BASE}/realms/demo/account/")
    page.wait_for_selector("#kc-page-title", timeout=20000)
    page.evaluate("document.querySelector('details.m3-pass-details').open = true")
    page.fill("#username", "demo")
    page.fill("#password", "demo1234")
    page.click("#kc-login")
    page.wait_for_selector(".m3-rail", timeout=25000)
    check("motion[account]: rail pill hover animated", _dur(page, ".m3-rail-ind") > 0)
    check("motion[account]: theme toggle animated", _dur(page, "#m3-theme-toggle") > 0)
    check("motion[account]: theme menu uses M3 easing",
          _dur(page, ".m3-theme-menu") > 0
          and "0.2, 0, 0, 1" in page.evaluate(
              "getComputedStyle(document.querySelector('.m3-theme-menu')).transitionTimingFunction"))
    check("motion[account]: buttons animated", _dur(page, ".pf-v5-c-button") > 0)
    check("motion[account]: drawer panel uses M3 easing",
          _dur(page, ".m3-drawer-panel") > 0
          and "0.2, 0, 0, 1" in page.evaluate(
              "getComputedStyle(document.querySelector('.m3-drawer-panel')).transitionTimingFunction"))
    check("motion[account]: page transition keyframes defined",
          page.evaluate(
              """[...document.styleSheets].some(s => {
                   try { return [...s.cssRules].some(r => r.name === 'm3-page-in-kf' || (r.cssText||'').includes('m3-page')); }
                   catch (e) { return false; }
                 })"""))
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
        test_motion(browser)
        test_forced_light_on_dark_system(browser)
        browser.close()
    print(f"\n{len(FAILURES)} failure(s)" if FAILURES else "\nAll tests passed")
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()
