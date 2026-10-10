# Web Server

Quart + Socket.IO server behind the browser UI: live dashboards, the save-viewer and the home page, all on one port.

## Modes

| Mode | Launched by | Serves |
|------|-------------|--------|
| Managed | the Launcher | live dashboards, save-viewer, home page. Consumes broker telemetry and queries the backend |
| Headless | you, with `--headless` | home page and save-viewer only. No launcher, broker or backend needed |

Never run the managed mode standalone: it fails the heartbeat check and self-terminates.

## Headless mode

Serves saved sessions from disk with nothing else running. Not registered: the live pages
(`/live`, `/eng-view`, ...) and their data endpoints. Not started: the management IPC server,
broker subscriber, backend dealer and the emit timers. The browser is not auto-opened, and the
home page and sidebar hide the live-view links.

### Prerequisites

- Poetry environment set up (`poetry install --without-dev`)
- `png_config.json` in the working directory. Headless exits if it is missing, so generate it up front:

```bash
poetry run python -m apps.generate_default_config
```

### Run

From the repo root:

```bash
poetry run python -m apps.web --headless
```

Then open `http://localhost:<Network.server_port>/` (default 4768).

| Flag | Default | Description |
|------|---------|-------------|
| `--headless` | off | Run without a launcher or live data |
| `--log-file` | `png_web_headless.log` | Log file (plain text). Stdout only gets the start and stop messages (version, config and log paths) |
| `--debug` | off | Debug logging |
| `--config-file` | `png_config.json` | Config to load |

### Configuration

All from `png_config.json`; there are no headless-specific settings.

| Setting | Effect |
|---------|--------|
| `Network.server_port` | Port to listen on |
| `Network.bind_address` | Interface to bind. Change it to expose the server beyond localhost |
| `Capture.session_dir` | Directory scanned for saved sessions (relative paths resolve from the app base dir) |
| `HTTPS.cert_path` / `HTTPS.key_path` | Serve over HTTPS |
