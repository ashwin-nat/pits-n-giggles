# apps/external

External submodules bundled into Pits n' Giggles.

## f1-save-viewer

A React app for browsing and analysing saved session JSON files.
Submodule source: `apps/external/f1-save-viewer`
Built output (`dist/`) is served by `apps/web/web_server.py` under `/save-viewer/*`.

### First-time setup

```bash
git submodule update --init
cd apps/external/f1-save-viewer
pnpm install
```

### Building (standalone, without PyInstaller)

Run this from the repo root (the `build_viewer` bash alias does this automatically):

```bash
cd apps/external/f1-save-viewer
VITE_BASE_PATH="/save-viewer/" \
VITE_EXTERNAL_LINK_TEMPLATE="/legacy/{slug}" \
VITE_EXTERNAL_LINK_LABEL="Legacy View" \
VITE_DISABLE_ANALYTICS="true" \
VITE_APP_NAME="Pits n' Giggles" \
pnpm build --mode production
```

On Windows (PowerShell), set the env vars before the command:

```powershell
$env:VITE_BASE_PATH              = "/save-viewer/"
$env:VITE_EXTERNAL_LINK_TEMPLATE = "/legacy/{slug}"
$env:VITE_EXTERNAL_LINK_LABEL    = "Legacy View"
$env:VITE_DISABLE_ANALYTICS      = "true"
$env:VITE_APP_NAME               = "Pits n' Giggles"
pnpm build --mode production
```

> **Note:** The page title version (`Pits n' Giggles - Save v...`) is injected at serve time by
> `apps/web/web_server.py` via `window.__PNG_VERSION__`, exactly like the Jinja `{{ version }}`
> in the live/eng-view pages. No version baking needed at build time.
>
> **Important:** `VITE_BASE_PATH` must be `/save-viewer/` (with both slashes) — it's baked into
> every asset URL and `fetch()` call in the built output. Omitting it silently reverts the build
> to root-relative paths (`base: "/"`), which 404s once served under `/save-viewer/*`. Both the
> `build_viewer` bash alias and `scripts/build.py` set this automatically; only a concern if you
> invoke `pnpm build` by hand.

### Env vars

| Variable | Value (embedded) | Purpose |
|---|---|---|
| `VITE_BASE_PATH` | `/save-viewer/` | Vite `base` — prefixes all built asset URLs and `fetch()` calls so the app works when served under `/save-viewer/*` instead of the domain root |
| `VITE_EXTERNAL_LINK_TEMPLATE` | `/legacy/{slug}` | URL pattern for the "Legacy View" link in `SessionHeader`; `{slug}` is replaced with the session slug |
| `VITE_EXTERNAL_LINK_LABEL` | `Legacy View` | Label text for that link |
| `VITE_DISABLE_ANALYTICS` | `true` | Disables Vercel Analytics (enabled on the public Vercel deployment) |
| `VITE_APP_NAME` | `Pits n' Giggles` | Overrides the displayed product name in the sidebar and upload screen |
