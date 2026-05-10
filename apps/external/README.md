# apps/external

External submodules bundled into Pits n' Giggles.

## f1-save-viewer

A React app for browsing and analysing saved session JSON files.
Submodule source: `apps/external/f1-save-viewer`
Built output (`dist/`) is served by `apps/save_viewer/save_web_server.py` at `/`.

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
VITE_EXTERNAL_LINK_TEMPLATE="/legacy/{slug}" \
VITE_EXTERNAL_LINK_LABEL="Legacy View" \
VITE_DISABLE_ANALYTICS="true" \
pnpm build --mode production
```

On Windows (PowerShell), set the env vars before the command:

```powershell
$env:VITE_EXTERNAL_LINK_TEMPLATE = "/legacy/{slug}"
$env:VITE_EXTERNAL_LINK_LABEL    = "Legacy View"
$env:VITE_DISABLE_ANALYTICS      = "true"
pnpm build --mode production
```

> **Note:** The page title version (`Pits n' Giggles - Save v...`) is injected at serve time by
> `save_web_server.py` via `window.__PNG_VERSION__`, exactly like the Jinja `{{ version }}`
> in the legacy/live views. No version baking needed at build time.

The full `scripts/build.py` run does this automatically as part of the PyInstaller build.

### Env vars

| Variable | Value (embedded) | Purpose |
|---|---|---|
| `VITE_EXTERNAL_LINK_TEMPLATE` | `/legacy/{slug}` | URL pattern for the "Legacy View" link in `SessionHeader`; `{slug}` is replaced with the session slug |
| `VITE_EXTERNAL_LINK_LABEL` | `Legacy View` | Label text for that link |
| `VITE_DISABLE_ANALYTICS` | `true` | Disables Vercel Analytics (enabled on the public Vercel deployment) |
