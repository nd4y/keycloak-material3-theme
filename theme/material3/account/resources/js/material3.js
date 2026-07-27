/*
 * Material 3 runtime for the Keycloak Account Console (keycloak.v3).
 *
 * 1. Color-scheme toggle: overrides the console's automatic dark-mode class,
 *    persists the choice in localStorage under "m3-theme" (shared with the
 *    login theme) and keeps re-asserting it over the built-in matchMedia
 *    listener.
 * 2. Material navigation: replaces the PatternFly sidebar with an M3
 *    navigation rail (desktop) / navigation bar (phones). Items are collected
 *    from the real PF nav, so new console sections appear automatically.
 */

const THEME_KEY = "m3-theme";
const DARK_CLASS = "pf-v5-theme-dark";

/* The theme's own resource base. currentScript is null in module scripts
   (the console loads theme scripts as type="module"), so fall back to
   finding our own <script> tag. */
const SCRIPT_URL =
  (document.currentScript && document.currentScript.src) ||
  (document.querySelector('script[src*="material3.js"]') || {}).src ||
  "";

/* Swap the stock favicon for the theme's "ID" badge icon. The script URL
   carries the release ?v=, reuse it so the icon busts caches on updates. */
function initFavicon() {
  if (!SCRIPT_URL) return;
  let href;
  try {
    const u = new URL(SCRIPT_URL);
    href = new URL("../img/favicon.svg", u.origin + u.pathname).href + u.search;
  } catch (e) {
    return;
  }
  document.querySelectorAll('link[rel~="icon"]').forEach((l) => l.remove());
  const link = document.createElement("link");
  link.rel = "icon";
  link.type = "image/svg+xml";
  link.href = href;
  document.head.appendChild(link);
}
initFavicon();

/* ── icons (24px, stroke-based) ─────────────────────────────────────────── */

const ICONS = {
  person: '<circle cx="12" cy="8" r="4"/><path d="M4.5 20a7.5 7.5 0 0 1 15 0"/>',
  fingerprint: '<path d="M5 8.6a8 8 0 0 1 14 0"/><path d="M7.5 11.8a4.8 4.8 0 0 1 9 0c0 2.6-.4 5-1.3 7.2"/><path d="M12 11.8v2.7c0 2.3-.5 4.4-1.4 6.3"/><path d="M9.6 15.5c-.2 1.8-.7 3.4-1.5 5"/>',
  devices: '<rect x="3" y="5" width="18" height="12" rx="2"/><path d="M8 21h8"/>',
  link: '<path d="M10 13a4 4 0 0 0 6 .5l3-3a4 4 0 0 0-5.7-5.6l-1.6 1.6"/><path d="M14 11a4 4 0 0 0-6-.5l-3 3a4 4 0 0 0 5.7 5.6l1.6-1.6"/>',
  grid: '<rect x="4" y="4" width="7" height="7" rx="2"/><rect x="13" y="4" width="7" height="7" rx="2"/><rect x="4" y="13" width="7" height="7" rx="2"/><rect x="13" y="13" width="7" height="7" rx="2"/>',
  people: '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 19a6.5 6.5 0 0 1 13 0"/><path d="M16 5.5a3.5 3.5 0 0 1 0 6.6M17.5 13.4a6.5 6.5 0 0 1 4 5.6"/>',
  folder: '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
  dot: '<circle cx="12" cy="12" r="9.25"/><circle cx="12" cy="12" r="1" fill="currentColor"/>',
  menu: '<path d="M4 7h16M4 12h16M4 17h16"/>',
  contrast: '<circle cx="12" cy="12" r="9.25"/><path d="M12 2.75a9.25 9.25 0 0 1 0 18.5z" fill="currentColor" stroke="none"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.3 5.3l1.4 1.4M17.3 17.3l1.4 1.4M18.7 5.3l-1.4 1.4M6.7 17.3l-1.4 1.4"/>',
  moon: '<path d="M20 13A8 8 0 1 1 11 4a6.5 6.5 0 0 0 9 9z"/>',
};

function iconSvg(name) {
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[name] || ICONS.dot}</svg>`;
}

function iconFor(href) {
  const h = href || "";
  if (h.includes("signing-in")) return "fingerprint";
  if (h.includes("device-activity")) return "devices";
  if (h.includes("linked-accounts")) return "link";
  if (h.includes("applications")) return "grid";
  if (h.includes("groups") || h.includes("organizations")) return "people";
  if (h.includes("resources")) return "folder";
  if (h.includes("personal-info") || /\/account\/?$/.test(h)) return "person";
  return "dot";
}

/* ── compact navigation labels ──────────────────────────────────────────
   M3 rails, bars and drawers use short labels, but the console's nav strings
   double as page headings ("personalInfo" is both), so they can't be
   shortened at the source. The theme ships its own m3Nav* message keys
   (overridable per realm like any other string); they're served by the
   account messages endpoint and matched to nav items by route slug. Items
   without a key (e.g. Groups) keep the console's original label. */

const NAV_LABEL_KEYS = {
  "": "m3NavPersonalInfo",
  "personal-info": "m3NavPersonalInfo",
  "signing-in": "m3NavSigningIn",
  "device-activity": "m3NavDeviceActivity",
  "linked-accounts": "m3NavLinkedAccounts",
  "applications": "m3NavApplications",
};

async function fetchM3Messages() {
  try {
    const env = JSON.parse(document.getElementById("environment").textContent);
    const root = new URL(SCRIPT_URL).pathname.split("/resources/")[0];
    const lang = env.locale || document.documentElement.lang || "en";
    const res = await fetch(`${root}/resources/${encodeURIComponent(env.realm)}/account/${lang}`);
    if (!res.ok) return {};
    const map = {};
    for (const { key, value } of await res.json()) {
      if (key.startsWith("m3")) map[key] = value;
    }
    return map;
  } catch (e) {
    return {};
  }
}

function shortLabel(href, fallback, labels) {
  let slug = (href || "").replace(/[?#].*$/, "").replace(/\/+$/, "").split("/").pop();
  if (slug === "account") slug = ""; // the root route is Personal info
  const key = NAV_LABEL_KEYS[slug];
  return (key && labels[key]) || fallback;
}

/* ── color-scheme preference ────────────────────────────────────────────── */

function storedTheme() {
  try {
    const t = localStorage.getItem(THEME_KEY);
    return t === "light" || t === "dark" ? t : null;
  } catch (e) {
    return null;
  }
}

function effectiveTheme() {
  return storedTheme() || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
}

function themeMode() {
  return storedTheme() || "system";
}

const MODE_ICON = { system: "contrast", light: "sun", dark: "moon" };

let applying = false;
function applyTheme() {
  applying = true;
  document.documentElement.classList.toggle(DARK_CLASS, effectiveTheme() === "dark");
  applying = false;
  const btn = document.getElementById("m3-theme-toggle");
  if (btn) btn.innerHTML = iconSvg(MODE_ICON[themeMode()]);
  document.querySelectorAll(".m3-theme-menu [data-mode]").forEach((b) =>
    b.setAttribute("aria-checked", String(b.dataset.mode === themeMode())));
}

/* Three modes, as everywhere in Material: follow the system, forced light,
   forced dark. "system" is the absence of the stored key — shared with the
   login page. */
function initTheme(msgsPromise) {
  applyTheme();
  // The console's own script toggles the class on matchMedia changes;
  // re-assert the user's explicit choice whenever the class flips.
  new MutationObserver(() => {
    if (applying || !storedTheme()) return;
    const wantDark = effectiveTheme() === "dark";
    if (document.documentElement.classList.contains(DARK_CLASS) !== wantDark) applyTheme();
  }).observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });
  // In system mode, follow OS switches live.
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
    if (!storedTheme()) applyTheme();
  });

  const btn = document.createElement("button");
  btn.id = "m3-theme-toggle";
  btn.type = "button";
  btn.className = "m3-theme-toggle";
  btn.setAttribute("aria-haspopup", "menu");
  btn.setAttribute("aria-expanded", "false");
  document.body.appendChild(btn);

  const menu = document.createElement("div");
  menu.className = "m3-theme-menu";
  menu.setAttribute("role", "menu");
  menu.hidden = true;
  document.body.appendChild(menu);

  const close = () => {
    menu.classList.remove("m3-open");
    btn.setAttribute("aria-expanded", "false");
    setTimeout(() => { menu.hidden = true; }, 160);
  };
  btn.addEventListener("click", () => {
    if (!menu.hidden) { close(); return; }
    menu.hidden = false;
    requestAnimationFrame(() => menu.classList.add("m3-open"));
    btn.setAttribute("aria-expanded", "true");
  });
  menu.addEventListener("click", (e) => {
    const b = e.target.closest("[data-mode]");
    if (!b) return;
    try {
      if (b.dataset.mode === "system") localStorage.removeItem(THEME_KEY);
      else localStorage.setItem(THEME_KEY, b.dataset.mode);
    } catch (err) { /* ignore */ }
    applyTheme();
    close();
  });
  document.addEventListener("click", (e) => {
    if (!menu.hidden && !menu.contains(e.target) && !btn.contains(e.target)) close();
  });
  addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !menu.hidden) close();
  });

  // Localized labels arrive with the shared m3* messages fetch; English
  // fallbacks keep the menu usable if that request ever fails.
  msgsPromise.then((msgs) => {
    const labels = {
      system: msgs.m3ThemeSystem || "System",
      light: msgs.m3ThemeLight || "Light",
      dark: msgs.m3ThemeDark || "Dark",
    };
    btn.setAttribute("aria-label", msgs.m3ThemeToggle || "Color theme");
    btn.title = msgs.m3ThemeToggle || "Color theme";
    menu.innerHTML = ["system", "light", "dark"]
      .map((m) =>
        `<button type="button" role="menuitemradio" data-mode="${m}" aria-checked="false">${iconSvg(MODE_ICON[m])}<span></span></button>`
      )
      .join("");
    menu.querySelectorAll("[data-mode]").forEach((b) => {
      b.querySelector("span").textContent = labels[b.dataset.mode];
    });
    applyTheme();
  });

  applyTheme();
}

/* ── loading overlay ─────────────────────────────────────────────────────
   Covers the app while React boots and the rail is being built, so the page
   appears fully assembled instead of popping in piece by piece.

   An external identity provider (Google etc.) can land the browser straight
   back here — skipping the login theme entirely when Keycloak's broker
   already knows the account — after a server-side round trip (token
   exchange, then a redirect) that takes a visible moment. The login theme
   arms a sessionStorage flag before departure (see template.ftl); if it's
   still here (and fresh) we add a "Signing you in…" label to this same
   overlay instead of a bare spinner, so the bridge from click to landing
   reads as one continuous, branded wait rather than two separate flashes. ── */

let hideLoader = () => {};

function oidcAuthingFlag() {
  try {
    const v = sessionStorage.getItem("m3-authing");
    if (v && Date.now() - parseInt(v, 10) < 60000) return true;
    if (v) sessionStorage.removeItem("m3-authing");
  } catch (e) { /* storage unavailable */ }
  return false;
}

function initLoader(msgsPromise) {
  const ov = document.createElement("div");
  ov.className = "m3-loader-overlay";
  ov.setAttribute("aria-hidden", "true");
  ov.innerHTML =
    '<svg class="m3-loader" viewBox="0 0 48 48"><circle cx="24" cy="24" r="18" fill="none" stroke-width="4"/></svg>';
  const authing = oidcAuthingFlag();
  if (authing) {
    const label = document.createElement("span");
    label.className = "m3-loader-label";
    label.textContent = document.documentElement.lang === "ru" ? "Выполняется вход…" : "Signing you in…";
    ov.appendChild(label);
    msgsPromise.then((m) => { if (m.m3AuthingText) label.textContent = m.m3AuthingText; });
  }
  document.body.appendChild(ov);
  let hidden = false;
  hideLoader = () => {
    if (hidden) return;
    hidden = true;
    if (authing) {
      try { sessionStorage.removeItem("m3-authing"); } catch (e) { /* ignore */ }
    }
    ov.classList.add("m3-loader-hide");
    setTimeout(() => ov.remove(), 400);
  };
  // Never trap the user behind the overlay.
  setTimeout(hideLoader, 8000);
}

/* ── navigation rail / bar ──────────────────────────────────────────────── */

function collectNavLinks(nav) {
  // Expand collapsed groups first so nested links exist in the DOM.
  nav.querySelectorAll('button[aria-expanded="false"]').forEach((b) => b.click());
  const links = [...nav.querySelectorAll("a.pf-v5-c-nav__link[href]")];
  const seen = new Set();
  return links
    .map((a) => ({ href: a.getAttribute("href"), label: a.textContent.trim() }))
    .filter((l) => l.href && l.label && !seen.has(l.href) && seen.add(l.href));
}

let lastPath = null;

function animatePageTransition() {
  const path = location.pathname;
  if (lastPath === path) return;
  const first = lastPath === null;
  lastPath = path;
  if (first) return; // no animation on initial load — the overlay handles that
  const main = document.querySelector(".pf-v5-c-page__main");
  if (!main) return;
  main.classList.remove("m3-page-in");
  void main.offsetWidth; // restart the animation
  main.classList.add("m3-page-in");
}

function markActive() {
  animatePageTransition();
  const path = location.pathname.replace(/\/$/, "");
  // The rail and the drawer mirror each other — mark both sets.
  for (const sel of ["a.m3-rail-item", "a.m3-drawer-item"]) {
    const links = [...document.querySelectorAll(sel)];
    if (!links.length) continue;
    let best = null;
    links.forEach((a) => {
      a.removeAttribute("data-active");
      const href = a.getAttribute("href").replace(/\/$/, "");
      if ((path === href || path.startsWith(href + "/") || path.startsWith(href + "#"))
          && (!best || href.length > best.getAttribute("href").replace(/\/$/, "").length)) {
        best = a;
      }
    });
    if (!best) best = links[0];
    best.setAttribute("data-active", "");
  }
}

function spaNavigate(href) {
  history.pushState({}, "", href);
  dispatchEvent(new PopStateEvent("popstate"));
  markActive();
}

/* Modal drawer + hamburger for medium screens (rail hidden 768–1099px) —
   mirrors how m3.material.io collapses its rail into a menu. */
function buildDrawer(items) {
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "m3-menu-btn";
  btn.setAttribute("aria-label", "Menu");
  btn.innerHTML = iconSvg("menu");
  const masthead = document.querySelector(".pf-v5-c-masthead");
  if (masthead) masthead.insertBefore(btn, masthead.firstChild);

  const drawer = document.createElement("div");
  drawer.className = "m3-drawer";
  drawer.hidden = true;
  drawer.innerHTML =
    '<aside class="m3-drawer-panel" role="dialog" aria-label="Navigation">' +
    items
      .map(
        (l) =>
          `<a class="m3-drawer-item" href="${l.href}">${iconSvg(iconFor(l.href))}<span>${l.label}</span></a>`
      )
      .join("") +
    "</aside>";
  document.body.appendChild(drawer);

  const close = () => {
    drawer.classList.remove("m3-open");
    setTimeout(() => { drawer.hidden = true; }, 300);
  };
  btn.addEventListener("click", () => {
    drawer.hidden = false;
    setTimeout(() => drawer.classList.add("m3-open"), 10);
  });
  drawer.addEventListener("click", (e) => {
    const a = e.target.closest("a.m3-drawer-item");
    if (a) {
      e.preventDefault();
      spaNavigate(a.getAttribute("href"));
      close();
      return;
    }
    if (e.target === drawer) close();
  });
  addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !drawer.hidden) close();
  });
}

function buildRail(nav, labels) {
  const items = collectNavLinks(nav).map((l) => ({
    href: l.href,
    label: shortLabel(l.href, l.label, labels),
  }));
  if (items.length < 2) return false;
  const rail = document.createElement("nav");
  rail.className = "m3-rail";
  rail.setAttribute("aria-label", "Account navigation");
  rail.innerHTML = items
    .map(
      (l) =>
        `<a class="m3-rail-item" href="${l.href}"><span class="m3-rail-ind">${iconSvg(iconFor(l.href))}</span><span class="m3-rail-label">${l.label}</span></a>`
    )
    .join("");
  // Navigate through the SPA router instead of full page loads.
  rail.addEventListener("click", (e) => {
    const a = e.target.closest("a.m3-rail-item");
    if (!a) return;
    e.preventDefault();
    spaNavigate(a.getAttribute("href"));
  });
  document.body.appendChild(rail);
  buildDrawer(items);
  markActive();
  // Track console-initiated navigation too.
  for (const fn of ["pushState", "replaceState"]) {
    const orig = history[fn].bind(history);
    history[fn] = (...args) => {
      const r = orig(...args);
      markActive();
      return r;
    };
  }
  addEventListener("popstate", () => markActive());
  document.documentElement.classList.add("m3-rail-on");
  // The console is assembled — reveal it. setTimeout rather than rAF: frame
  // callbacks stall in background tabs (and around view transitions).
  setTimeout(hideLoader, 80);
  return true;
}

async function initRail(msgsPromise) {
  // The loading overlay covers the console anyway, so waiting for the label
  // fetch costs nothing visible; on failure the console's labels are kept.
  const labels = await msgsPromise;
  const tryBuild = () => {
    const nav = document.querySelector(".pf-v5-c-nav");
    return nav ? buildRail(nav, labels) : false;
  };
  if (tryBuild()) return;
  const obs = new MutationObserver(() => {
    if (tryBuild()) obs.disconnect();
  });
  obs.observe(document.body, { childList: true, subtree: true });
  setTimeout(() => obs.disconnect(), 20000);
}

/* ── masthead brand: "<realm> ID" ────────────────────────────────────────
   Replaces the stock Keycloak logo with the realm name (taken from the
   console's environment JSON — nothing installation-specific lives in the
   theme) plus a neutral "ID" badge. ── */

function initBrand() {
  let realmName = "";
  let accountBase = "";
  try {
    const env = JSON.parse(document.getElementById("environment").textContent);
    realmName = env.realm || "";
    accountBase = env.baseUrl || "";
  } catch (e) { /* keep default logo */ }
  if (!realmName) return;

  const apply = () => {
    const brand = document.querySelector(".pf-v5-c-masthead__brand");
    if (!brand || brand.querySelector(".m3-brand-mark")) return !!brand;
    // The stock brand links to the server root (the master realm's welcome
    // page) — point it back at this realm's Account Console instead.
    if (accountBase && brand.tagName === "A") brand.setAttribute("href", accountBase);
    const mark = document.createElement("span");
    mark.className = "m3-brand-mark";
    mark.innerHTML =
      `<span class="m3-brand-name"></span><span class="m3-brand-badge">ID</span>`;
    mark.querySelector(".m3-brand-name").textContent = realmName;
    brand.appendChild(mark);
    document.documentElement.classList.add("m3-brand-on");
    return true;
  };
  if (apply()) return;
  const obs = new MutationObserver(() => {
    if (apply()) obs.disconnect();
  });
  obs.observe(document.body, { childList: true, subtree: true });
  setTimeout(() => obs.disconnect(), 20000);
}

/* ── user button ─────────────────────────────────────────────────────────
   PF renders the user menu as a "name + caret" pill next to a stock gray
   avatar. Collapse it to a Google-style round avatar with the user's
   initials (the pill text feeds them, so nothing installation-specific is
   hardcoded); the stock avatar is hidden in CSS. ── */

function initUserButton() {
  const apply = () => {
    const btn = document.querySelector('[data-testid="options-toggle"]');
    if (!btn) return false;
    if (btn.querySelector(".m3-user-avatar")) return true;
    const text = btn.querySelector(".pf-v5-c-menu-toggle__text");
    const name = (text ? text.textContent : "").trim();
    const initials = name
      .split(/\s+/)
      .slice(0, 2)
      .map((w) => w.charAt(0))
      .join("")
      .toUpperCase();
    const av = document.createElement("span");
    av.className = "m3-user-avatar";
    av.textContent = initials || "•";
    btn.insertBefore(av, btn.firstChild);
    if (name) btn.setAttribute("aria-label", name);
    return true;
  };
  apply();
  // Keep observing: PF re-renders the toggle on expand/collapse and may
  // drop the injected span — re-apply is idempotent and cheap.
  new MutationObserver(apply).observe(document.body, { childList: true, subtree: true });
}

function init() {
  initFavicon(); // again: stock <link rel="icon"> may appear after our script tag
  const msgsPromise = fetchM3Messages(); // shared: nav labels + theme-menu + authing labels
  initLoader(msgsPromise);
  initTheme(msgsPromise);
  initRail(msgsPromise);
  initBrand();
  initUserButton();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
