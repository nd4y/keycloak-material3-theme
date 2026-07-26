# Keycloak Material 3 Theme

A [Material 3 Expressive](https://m3.material.io/) theme for Keycloak — login pages **and**
Account Console. Passkey-first, responsive, with automatic light/dark mode.

No server rebuild, no JAR packaging, no Keycloakify toolchain: it is a plain theme directory
that you mount into the official Keycloak image.

![Login page](docs/login-light.png)

<p align="center">
  <img src="docs/login-dark.png" alt="Login page, dark" width="68%">
  <img src="docs/login-mobile.png" alt="Login page, mobile" width="24%">
</p>

## Features

- **Passkey-first sign-in** — the passkey button is the single filled (most prominent) button
  on the page; identity providers come second as tonal icon buttons; the username/password
  form is collapsed behind a text button and expands only on demand (or automatically when
  it is the only option, or after a failed attempt).
- **Automatic light / dark theme** via `prefers-color-scheme` — pure CSS, no toggle, no JS.
- **Responsive** — a single centered card on mobile, card plus a decorative brand panel on
  desktop. The brand panel picks up your realm display name.
- **Identity-provider icons** — Google, GitHub, GitLab and Telegram icons ship out of the box,
  matched by provider alias. Adding a provider is one SVG file, no template changes
  ([details below](#identity-provider-icons)).
- **Account Console included** — the same design tokens applied to the `keycloak.v3` Account
  Console (PatternFly variable overrides). The Admin Console is intentionally left untouched.
- **English + Russian** UI strings for the custom elements; all standard strings come from
  Keycloak's own translations, so other locales degrade gracefully.
- **All login flows styled** — registration, password reset, OTP, WebAuthn, `select-authenticator`,
  logout confirmation and error pages inherit the same look through the base theme's
  class hooks.

| Account Console | |
|---|---|
| ![Account light](docs/account-light.png) | ![Account dark](docs/account-dark.png) |

## Compatibility

Developed and tested against **Keycloak 26.3** (quay.io image). The login theme extends the
built-in `base` theme and the account theme extends `keycloak.v3`, so any 26.x should work.
The passkey button relies on the `passkeys` preview feature (see below); without it the theme
still works — the button simply does not render.

## Installation

The theme is a plain directory that ends up mounted at `/opt/keycloak/themes/material3`
inside the official Keycloak image — no `kc.sh build`, no custom Keycloak image. Pick
whichever delivery method fits your setup.

### Option A — theme image (recommended)

The theme ships as a tiny carrier image
(`ghcr.io/nd4y/keycloak-theme-material3`, busybox + theme files, multi-arch). On start it
copies the theme into a shared volume and exits; Keycloak mounts that volume. Nothing to
place on the host — everything comes from registries, and upgrading the theme is
`docker compose pull` + re-deploy:

```yaml
# docker-compose.yml
volumes:
  material3-theme:

services:
  theme:
    image: ghcr.io/nd4y/keycloak-theme-material3:latest
    restart: "no"
    network_mode: "none"   # it only copies files — no network needed
    volumes:
      - material3-theme:/target

  keycloak:
    image: quay.io/keycloak/keycloak:26.3
    command: start
    depends_on:
      theme:
        condition: service_completed_successfully
    volumes:
      - material3-theme:/opt/keycloak/themes/material3:ro
    # ... the rest of your configuration
```

Kubernetes — same idea with an init container:

```yaml
initContainers:
  - name: material3-theme
    image: ghcr.io/nd4y/keycloak-theme-material3:latest
    command: ["sh", "-c", "cp -a /theme/material3/. /target/"]
    volumeMounts:
      - { name: material3-theme, mountPath: /target }
containers:
  - name: keycloak
    volumeMounts:
      - { name: material3-theme, mountPath: /opt/keycloak/themes/material3, readOnly: true }
volumes:
  - { name: material3-theme, emptyDir: {} }
```

Tags: `latest` (main branch), `X.Y.Z` / `X.Y` (releases), `sha-<commit>` for pinning.

### Option B — bind-mount the directory

Clone the repo and mount the theme directly:

```yaml
services:
  keycloak:
    image: quay.io/keycloak/keycloak:26.3
    command: start
    volumes:
      - ./keycloak-theme-material3/theme/material3:/opt/keycloak/themes/material3:ro
```

Bare metal: copy `theme/material3` to `/opt/keycloak/themes/material3`.

## Configuring Keycloak

Everything below is realm/server configuration — the theme itself needs no build step.

### 1. Switch the realm to the theme

**Realm settings → Themes**:

- *Login theme* → `material3`
- *Account theme* → `material3`
- leave *Admin theme* as is (the Admin Console is intentionally not themed).

Themes are cached in production mode; restart Keycloak after updating theme files
(not needed when only switching the realm setting).

### 2. Localization

**Realm settings → Localization**:

- *Internationalization* → Enabled
- *Supported locales* → English, Русский (plus any others — the theme's own strings exist
  in en/ru; other locales fall back to Keycloak's stock translations)

This also enables the language switcher on the login card.

### 3. Passkeys (the hero button)

The passkey button uses Keycloak's built-in passkeys support (preview in 26.x, needs ≥ 26.2):

1. Start Keycloak with the feature enabled:

   ```yaml
   environment:
     KC_FEATURES: passkeys
   ```

2. **Authentication → Policies → WebAuthn Passwordless Policy**:
   - *Enable passkeys* → On
   - recommended: *Requires discoverable credential* → Yes,
     *User verification requirement* → required

3. Let users register a passkey: **Authentication → Required actions** → enable
   *Webauthn Register Passwordless*, or users add one themselves in the Account Console
   under *Account security → Signing in*.

With the feature active, the login page renders the filled *Sign in with a passkey* button and
also offers passkeys through the browser's username autofill (conditional UI). On older
servers (or with the feature off) the theme degrades gracefully — the button simply is not
rendered. Both the default browser flow and custom flows that keep the standard
*Username Password Form* work.

### 4. Identity providers

Add providers under **Identity providers** as usual. The login page shows one round button
per provider, with icons matched by the provider **alias** (`google`, `github`, `gitlab`,
`telegram` ship out of the box; anything else falls back to a neutral key icon — see
[Identity-provider icons](#identity-provider-icons)).

### 5. Registration model

The theme supports both onboarding styles:

- **Open self-registration**: enable **Realm settings → Login → User registration** — the
  login card shows a "New user? Register" link and a Material-styled registration form.
- **IdP-first onboarding** (no registration form): leave registration off and let accounts
  be created on the first identity-provider sign-in. The login card's **help dialog**
  (the "?" button) explains exactly this to end users: sign in with any listed provider
  first, then optionally set up a passkey or a password (with optional OTP) in the account
  settings.

To reword the help dialog (or any other string) for your realm without forking the theme,
use **Realm settings → Localization → Realm overrides** and override the message keys
`m3HelpTitle`, `m3HelpBody1`, `m3HelpBody2`.

## Identity-provider icons

Icons live in
[`theme/material3/login/resources/img/providers/`](theme/material3/login/resources/img/providers/)
and are matched by the **provider alias** in your realm:

```
providers/
  google.svg      ← alias "google"
  github.svg      ← alias "github"
  gitlab.svg      ← alias "gitlab"
  telegram.svg    ← alias "telegram"
  oidc.svg        ← fallback for any alias without its own file
```

To add an icon for a new provider, drop a square SVG named `<alias>.svg` into that directory —
nothing else to change. A provider without an icon automatically falls back to the neutral
key icon (`oidc.svg`).

## Changing the color palette

All colors are CSS custom properties generated from the Material seed color `#6750A4`:

- login: [`theme/material3/login/resources/css/material3.css`](theme/material3/login/resources/css/material3.css) (`--m3-*` tokens, light + dark blocks at the top)
- account: [`theme/material3/account/resources/css/material3-account.css`](theme/material3/account/resources/css/material3-account.css)

To rebrand, generate a palette from your own seed color with the
[Material Theme Builder](https://material-foundation.github.io/material-theme-builder/) and
replace the token values — the layout never references raw colors.

Custom UI strings (button labels, hints) live in
`theme/material3/login/messages/messages_{en,ru}.properties`; add more locales by dropping in
additional `messages_<lang>.properties` files and listing the locale in `theme.properties`.

## Development

A ready-made dev stack with a demo realm (test IdPs, passkeys enabled, `demo`/`demo1234` user):

```bash
docker compose -f dev/docker-compose.dev.yml up
# → http://localhost:8080/realms/demo/account/  (login UI)
# → http://localhost:8080/admin/                (admin/admin)
```

It runs `start-dev` with theme caching disabled, so template and CSS edits apply on refresh.
README screenshots are generated with [`dev/screenshots.py`](dev/screenshots.py) (Playwright).
The e2e suite ([`dev/test_theme.py`](dev/test_theme.py)) runs in CI against Keycloak 26.0 and
26.3 before the image is built.

When releasing a change to CSS or JS, bump the `?v=` query in both `theme.properties` files —
Keycloak's `/resources/<hash>/` URLs change with the server version, not with theme content,
so without the bump browsers keep serving month-old cached assets.

## License

[MIT](LICENSE) © [nd4y](https://github.com/nd4y)
