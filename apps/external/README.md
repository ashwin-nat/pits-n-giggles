# apps/external

External submodules bundled into Pits n' Giggles.

## f1-save-viewer

A React app for browsing and analysing saved session JSON files.
Submodule source: `apps/external/f1-save-viewer`
Built output (`dist/`) is served by `apps/save_viewer/save_web_server.py` under `/viewer/`.

### First-time setup

```bash
git submodule update --init
cd apps/external/f1-save-viewer
pnpm install
```

### Building (standalone, without PyInstaller)

Run this from the repo root (the `build_viewer` bash alias does this automatically):

```bash
_ver=$(python -c 'from lib.version import get_version; print(get_version())')
cd apps/external/f1-save-viewer
VITE_EXTERNAL_LINK_TEMPLATE="/legacy/{slug}" \
VITE_EXTERNAL_LINK_LABEL="Legacy View" \
VITE_DISABLE_ANALYTICS="true" \
VITE_APP_VERSION="$_ver" \
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL="*" \
pnpm build --base /viewer/ --mode production
```

On Windows (PowerShell), set the env vars before the command:

```powershell
$ver = python -c 'from lib.version import get_version; print(get_version())'
$env:VITE_EXTERNAL_LINK_TEMPLATE = "/legacy/{slug}"
$env:VITE_EXTERNAL_LINK_LABEL    = "Legacy View"
$env:VITE_DISABLE_ANALYTICS      = "true"
$env:VITE_APP_VERSION            = $ver
$env:MSYS_NO_PATHCONV            = "1"
$env:MSYS2_ARG_CONV_EXCL         = "*"
pnpm build --base /viewer/ --mode production
```

The full `scripts/build.py` run does this automatically as part of the PyInstaller build.

### Env vars

| Variable | Value (embedded) | Purpose |
|---|---|---|
| `VITE_EXTERNAL_LINK_TEMPLATE` | `/legacy/{slug}` | URL pattern for the "Legacy View" link in `SessionHeader`; `{slug}` is replaced with the session slug |
| `VITE_EXTERNAL_LINK_LABEL` | `Legacy View` | Label text for that link |
| `VITE_APP_VERSION` | e.g. `4.1.0` | Sets the page title to `Pits n' Giggles - Save v{VERSION}`; omit for standalone/Vercel |
| `VITE_DISABLE_ANALYTICS` | `true` | Disables Vercel Analytics (enabled on the public Vercel deployment) |
| `MSYS_NO_PATHCONV` / `MSYS2_ARG_CONV_EXCL` | `1` / `*` | Prevents Git Bash / MSYS2 from mangling the `/viewer/` base path into a Windows absolute path |
