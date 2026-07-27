<#macro registrationLayout bodyClass="" displayInfo=false displayMessage=true displayRequiredFields=false>
<!DOCTYPE html>
<html class="${properties.kcHtmlClass!}" lang="${(lang)!(locale.currentLanguageTag)!'en'}"<#if realm.internationalizationEnabled> dir="${((locale.rtl)!false)?then('rtl','ltr')}"</#if>>

<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="color-scheme" content="light dark">
    <meta name="robots" content="noindex, nofollow">

    <#if properties.meta?has_content>
        <#list properties.meta?split(' ') as meta>
            <meta name="${meta?split('==')[0]}" content="${meta?split('==')[1]}"/>
        </#list>
    </#if>
    <script>
        (function () {
            try {
                var t = localStorage.getItem("m3-theme");
                if (t === "light" || t === "dark") document.documentElement.setAttribute("data-m3-theme", t);
            } catch (e) { /* storage unavailable */ }
            try {
                // Set right before leaving for an external identity provider (see
                // the click handler below); survives the round trip since
                // sessionStorage is scoped to the tab, not the page. Stale after
                // 60s so a flag can never haunt an unrelated later visit.
                var a = sessionStorage.getItem("m3-authing");
                if (a && (Date.now() - parseInt(a, 10)) < 60000) {
                    document.documentElement.classList.add("m3-authing");
                } else if (a) {
                    sessionStorage.removeItem("m3-authing");
                }
            } catch (e) { /* storage unavailable */ }
        })();
    </script>
    <title>${msg("loginTitle",(realm.displayName!''))}</title>
    <#-- ?v= is the icon revision — bump when favicon.svg changes -->
    <link rel="icon" href="${url.resourcesPath}/img/favicon.svg?v=3" type="image/svg+xml"/>
    <#if properties.stylesCommon?has_content>
        <#list properties.stylesCommon?split(' ') as style>
            <link href="${url.resourcesCommonPath}/${style}" rel="stylesheet" />
        </#list>
    </#if>
    <#if properties.styles?has_content>
        <#list properties.styles?split(' ') as style>
            <link href="${url.resourcesPath}/${style}" rel="stylesheet" />
        </#list>
    </#if>
    <#if properties.scripts?has_content>
        <#list properties.scripts?split(' ') as script>
            <script src="${url.resourcesPath}/${script}" type="text/javascript"></script>
        </#list>
    </#if>
    <script type="importmap">
        {
            "imports": {
                "rfc4648": "${url.resourcesCommonPath}/vendor/rfc4648/rfc4648.js"
            }
        }
    </script>
    <script src="${url.resourcesPath}/js/menu-button-links.js" type="module"></script>
    <script type="module">
        // Theme-mode menu: system (follow the OS) / forced light / forced dark.
        // "system" is the absence of the stored key, so the login page and the
        // Account Console (same localStorage key) stay in sync.
        document.addEventListener("DOMContentLoaded", () => {
            const btn = document.getElementById("m3-theme-toggle");
            const menu = document.getElementById("m3-theme-menu");
            if (!btn || !menu) return;
            const stored = () => {
                try {
                    const t = localStorage.getItem("m3-theme");
                    return t === "light" || t === "dark" ? t : "system";
                } catch (e) { return "system"; }
            };
            const apply = (mode) => {
                try {
                    if (mode === "system") localStorage.removeItem("m3-theme");
                    else localStorage.setItem("m3-theme", mode);
                } catch (e) { /* ignore */ }
                const root = document.documentElement;
                if (mode === "system") root.removeAttribute("data-m3-theme");
                else root.setAttribute("data-m3-theme", mode);
                menu.querySelectorAll("[data-mode]").forEach((b) =>
                    b.setAttribute("aria-checked", String(b.dataset.mode === mode)));
            };
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
                apply(b.dataset.mode);
                close();
            });
            document.addEventListener("click", (e) => {
                if (!menu.hidden && !menu.contains(e.target) && !btn.contains(e.target)) close();
            });
            addEventListener("keydown", (e) => {
                if (e.key === "Escape" && !menu.hidden) close();
            });
            apply(stored());
        });
        // Exit animation before same-origin navigations (Forgot password,
        // Register, Back to login…). pageshow restores the card when the
        // page comes back from the bfcache.
        document.addEventListener("click", (e) => {
            const a = e.target.closest("a[href]");
            if (!a || e.defaultPrevented || e.metaKey || e.ctrlKey || a.target === "_blank") return;
            let url;
            try { url = new URL(a.href, location.href); } catch (err) { return; }
            if (url.origin !== location.origin || !/^https?:$/.test(url.protocol)) return;
            if (a.classList.contains("m3-social-btn")) {
                // Handing off to Google/GitHub/etc. and back — Keycloak's own
                // broker/login redirect step and the eventual return trip
                // (server-side token exchange, then a redirect here or straight
                // to the account console) can both take a visible moment, with
                // nothing of ours on screen to fill it. Show the bridge overlay
                // right now, before the card even has a chance to fade, so it
                // covers the whole hand-off instead of just the return half;
                // most browsers keep the last painted frame — this overlay —
                // through same-origin redirect hops until the next page has
                // something to paint. The flag makes it pick back up if we do
                // land on a themed page again.
                try { sessionStorage.setItem("m3-authing", String(Date.now())); } catch (err) { /* ignore */ }
                document.documentElement.classList.add("m3-authing");
                e.preventDefault();
                requestAnimationFrame(() => requestAnimationFrame(() => { location.href = url.href; }));
                return;
            }
            e.preventDefault();
            document.body.classList.add("m3-exit");
            setTimeout(() => { location.href = url.href; }, 170);
        });
        addEventListener("pageshow", () => document.body.classList.remove("m3-exit"));
        document.addEventListener("DOMContentLoaded", () => {
            const dlg = document.getElementById("m3-help");
            const open = document.getElementById("m3-help-btn");
            const close = document.getElementById("m3-help-close");
            if (!dlg || !open) return;
            open.addEventListener("click", () => dlg.showModal());
            close.addEventListener("click", () => dlg.close());
            dlg.addEventListener("click", (e) => { if (e.target === dlg) dlg.close(); });
        });
    </script>
    <#if scripts??>
        <#list scripts as script>
            <script src="${script}" type="text/javascript"></script>
        </#list>
    </#if>
    <script type="module">
        import { startSessionPolling } from "${url.resourcesPath}/js/authChecker.js";

        startSessionPolling(
            "${url.ssoLoginInOtherTabsUrl?no_esc}"
        );
    </script>
    <script type="module">
        document.addEventListener("click", (event) => {
            const link = event.target.closest("a[data-once-link]");

            if (!link) {
                return;
            }

            if (link.getAttribute("aria-disabled") === "true") {
                event.preventDefault();
                return;
            }

            const { disabledClass } = link.dataset;

            if (disabledClass) {
                link.classList.add(...disabledClass.trim().split(/\s+/));
            }

            link.setAttribute("role", "link");
            link.setAttribute("aria-disabled", "true");
        });
    </script>
    <#if authenticationSession?? && (authenticationSession.authSessionIdHash)??>
        <script type="module">
            import { checkAuthSession } from "${url.resourcesPath}/js/authChecker.js";

            checkAuthSession(
                "${authenticationSession.authSessionIdHash}"
            );
        </script>
    </#if>
    <script>
        (function () {
            if (!document.documentElement.classList.contains("m3-authing")) return;
            var hidden = false;
            var hide = function () {
                if (hidden) return;
                hidden = true;
                try { sessionStorage.removeItem("m3-authing"); } catch (e) { /* ignore */ }
                document.documentElement.classList.remove("m3-authing");
                var ov = document.getElementById("m3-oidc-overlay");
                if (ov) {
                    ov.classList.add("m3-oidc-hide");
                    setTimeout(function () { ov.remove(); }, 300);
                }
            };
            // A brief minimum display avoids a one-frame flash on fast
            // responses; a failsafe guarantees the user is never stuck behind it.
            var reveal = function () { setTimeout(hide, 220); };
            if (document.readyState === "complete") reveal();
            else addEventListener("load", reveal);
            setTimeout(hide, 6000);
        })();
    </script>
</head>

<body class="${properties.kcBodyClass!} ${bodyClass}" data-page-id="login-${(pageId)!''}">
<div id="m3-oidc-overlay" aria-hidden="true">
    <div id="m3-oidc-spinner"></div>
    <span>${msg("m3AuthingText")}</span>
</div>
<div class="m3-shell">
    <#assign brandName = (realm.displayName!'')>
    <aside class="m3-brand" aria-hidden="true">
        <div class="m3-blob m3-blob-1"></div>
        <div class="m3-blob m3-blob-2"></div>
        <div class="m3-blob m3-blob-3"></div>
        <div class="m3-brand-text">
            <h2>${kcSanitize(msg("loginTitleHtml",(realm.displayNameHtml!'')))?no_esc}</h2>
            <p>${msg("m3BrandTagline")}</p>
        </div>
    </aside>
    <main class="m3-main">
        <div class="m3-card">
            <div class="m3-card-top">
                <div class="m3-logo" aria-hidden="true"><#if brandName?has_content>${brandName[0]?upper_case}<#else>K</#if></div>
                <div class="m3-card-top-actions">
                <button type="button" id="m3-help-btn" class="m3-icon-btn" aria-label="${msg("m3Help")}" title="${msg("m3Help")}" aria-haspopup="dialog"></button>
                <div class="m3-theme">
                    <button type="button" id="m3-theme-toggle" class="m3-theme-toggle" aria-label="${msg("m3ThemeToggle")}" title="${msg("m3ThemeToggle")}" aria-haspopup="menu" aria-expanded="false"></button>
                    <div id="m3-theme-menu" class="m3-theme-menu" role="menu" aria-label="${msg("m3ThemeToggle")}" hidden>
                        <button type="button" role="menuitemradio" data-mode="system" aria-checked="false"><span class="m3-mode-ico m3-mode-system" aria-hidden="true"></span>${msg("m3ThemeSystem")}</button>
                        <button type="button" role="menuitemradio" data-mode="light" aria-checked="false"><span class="m3-mode-ico m3-mode-light" aria-hidden="true"></span>${msg("m3ThemeLight")}</button>
                        <button type="button" role="menuitemradio" data-mode="dark" aria-checked="false"><span class="m3-mode-ico m3-mode-dark" aria-hidden="true"></span>${msg("m3ThemeDark")}</button>
                    </div>
                </div>
                <#if realm.internationalizationEnabled && locale.supported?size gt 1>
                    <div class="menu-button-links m3-locale" id="kc-locale">
                        <button tabindex="1" id="kc-current-locale-link" aria-label="${msg("languages")}" aria-haspopup="true" aria-expanded="false" aria-controls="language-switch1">
                            <span class="m3-icon-globe" aria-hidden="true"></span>${locale.current}
                        </button>
                        <ul role="menu" tabindex="-1" aria-labelledby="kc-current-locale-link" aria-activedescendant="" id="language-switch1" class="m3-locale-list">
                            <#assign i = 1>
                            <#list locale.supported as l>
                                <li role="none">
                                    <a role="menuitem" id="language-${i}" href="${l.url}"<#if l.languageTag == locale.currentLanguageTag> class="m3-locale-current"</#if>>${l.label}</a>
                                </li>
                                <#assign i++>
                            </#list>
                        </ul>
                    </div>
                </#if>
                </div>
            </div>

            <header class="m3-header">
                <#if !(auth?has_content && auth.showUsername() && !auth.showResetCredentials())>
                    <h1 id="kc-page-title" class="m3-title"><#nested "header"></h1>
                    <#if displayRequiredFields>
                        <p class="m3-subtitle m3-required-note"><span class="m3-required">*</span> ${msg("requiredFields")}</p>
                    </#if>
                <#else>
                    <h1 id="kc-page-title" class="m3-title"><#nested "header"></h1>
                    <#nested "show-username">
                    <div id="kc-username" class="m3-attempted">
                        <span class="m3-attempted-avatar" aria-hidden="true">${(auth.attemptedUsername[0])!'?'}</span>
                        <label id="kc-attempted-username">${auth.attemptedUsername}</label>
                        <a id="reset-login" class="m3-attempted-reset" href="${url.loginRestartFlowUrl}" aria-label="${msg("restartLoginTooltip")}" title="${msg("restartLoginTooltip")}">
                            <span class="m3-icon-restart" aria-hidden="true"></span>
                        </a>
                    </div>
                    <#if displayRequiredFields>
                        <p class="m3-subtitle m3-required-note"><span class="m3-required">*</span> ${msg("requiredFields")}</p>
                    </#if>
                </#if>
            </header>

            <div id="kc-content" class="m3-content">
                <div id="kc-content-wrapper">

                    <#-- App-initiated actions should not see warning messages about the need to complete the action during login. -->
                    <#if displayMessage && message?has_content && (message.type != 'warning' || !isAppInitiatedAction??)>
                        <div class="m3-alert m3-alert-${message.type}" role="alert">
                            <span class="m3-alert-icon" aria-hidden="true"></span>
                            <span class="${properties.kcAlertTitleClass!}">${kcSanitize(message.summary)?no_esc}</span>
                        </div>
                    </#if>

                    <#nested "form">

                    <#if auth?has_content && auth.showTryAnotherWayLink()>
                        <form id="kc-select-try-another-way-form" action="${url.loginAction}" method="post" class="m3-try-another">
                            <input type="hidden" name="tryAnotherWay" value="on"/>
                            <a href="#" id="try-another-way" class="m3-btn m3-btn-text m3-btn-block"
                               onclick="document.forms['kc-select-try-another-way-form'].requestSubmit();return false;">${msg("doTryAnotherWay")}</a>
                        </form>
                    </#if>

                    <#nested "socialProviders">

                    <#if displayInfo>
                        <div id="kc-info" class="m3-info">
                            <div id="kc-info-wrapper">
                                <#nested "info">
                            </div>
                        </div>
                    </#if>
                </div>
            </div>
        </div>

        <dialog id="m3-help" class="m3-help" aria-labelledby="m3-help-title">
            <h2 id="m3-help-title">${msg("m3HelpTitle")}</h2>
            <p>${msg("m3HelpBody1")}</p>
            <p>${msg("m3HelpBody2")}</p>
            <div class="m3-help-actions">
                <button type="button" id="m3-help-close" class="m3-btn m3-btn-tonal">${msg("m3HelpClose")}</button>
            </div>
        </dialog>
    </main>
</div>
</body>
</html>
</#macro>
