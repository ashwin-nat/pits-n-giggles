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

Run this from the repo root:

```bash
cd apps/external/f1-save-viewer
VITE_EXTERNAL_LINK_TEMPLATE="/legacy/{slug}" \
VITE_EXTERNAL_LINK_LABEL="Legacy View" \
VITE_DISABLE_ANALYTICS="true" \
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL="*" \
pnpm build --base /viewer/ --mode production
```

On Windows (PowerShell), set the env vars before the command:

```powershell
$env:VITE_EXTERNAL_LINK_TEMPLATE = "/legacy/{slug}"
$env:VITE_EXTERNAL_LINK_LABEL    = "Legacy View"
$env:VITE_DISABLE_ANALYTICS      = "true"
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
| `VITE_DISABLE_ANALYTICS` | `true` | Disables Vercel Analytics (enabled on the public Vercel deployment) |
| `MSYS_NO_PATHCONV` / `MSYS2_ARG_CONV_EXCL` | `1` / `*` | Prevents Git Bash / MSYS2 from mangling the `/viewer/` base path into a Windows absolute path |
