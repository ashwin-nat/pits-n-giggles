# 🚀 Running pits-n-giggles (Manually)

This project uses Python 3.12 or 3.13 and is structured as a suite of apps under the `apps/` directory. Each sub-app can be run independently using Python's `-m` module mode.

## 🧰 Requirements

- Python 3.12 or 3.13 installed and available in your `PATH`
- [Poetry](https://python-poetry.org/) installed (preferred for dependency management)

## 📦 Install Dependencies

Install only the production dependencies if you plan on running only the app and none of the tests
```bash
poetry install --without dev
```

If you plan on running app, dev utils and unit tests, install all dependencies
```bash
poetry install
```

This sets up a virtual environment and installs everything defined in `pyproject.toml`.

---

## ▶️ Running Apps

The app can be launched by using the command

```bash
poetry run python -m apps.launcher
```

All commands below must be run **from the project root directory** (i.e., the folder containing `pyproject.toml`).

### 🧠 Backend App

```bash
poetry run python -m apps.backend --replay-server
```

Note:
The --replay-server flag enables the replay mode for the backend,
allowing the server to process pre-recorded events for debugging and testing.
Without this flag, the server will run in normal mode. For example, to run
in default mode, use:

```bash
poetry run python -m apps.backend
```

### 🛠 Dev Tools (e.g., telemetry replayer)

```bash
poetry run python -m apps.dev_tools.telemetry_replayer --file-name example.f1pcap
```

---

## ❗ Notes

- Do **not** include `.py` in module paths.
- Use dot (`.`) separators for nested module paths.
- You **must** be in the project root (`pits-n-giggles/`) when running these commands.
- All directories under `apps/` should **avoid hyphens** (`-`). Use underscores or camelCase instead to remain Python-compatible.

---

## 🐳 Running with Docker

### Build the Image

```bash
docker build -t pits-n-giggles .
```

### Run the Container

```bash
docker run -d \
  --name png-backend \
  -p 4768:4768 \
  -p 4767:4767 \
  -p 20777:20777/udp \
  -v /path/to/your/png_config.json:/app/png_config.json:ro \
  pits-n-giggles
```

| Flag | Purpose |
|------|---------|
| `-p 4768:4768` | Web UI (HTTP) |
| `-p 4767:4767` | Save Data Viewer (HTTP) |
| `-p 20777:20777/udp` | F1 telemetry data (UDP) — must be reachable from the F1 game host |
| `-v ...png_config.json:/app/png_config.json:ro` | Mount your own config (read-only) |

> **Note:** The UDP port for telemetry must be reachable on the Docker host.
> If the F1 game runs on a different machine, ensure firewall rules allow
> UDP traffic on port 20777. On Linux, `--network host` can be used as an
> alternative to explicit port mapping for lower latency.

### Multi-Driver Setup (Multiple Ports)

For training sessions with multiple drivers on a single instance, each driver
uses a dedicated port starting at 4768. Configure additional ports in
`png_config.json` and expose them in `docker run`:

```bash
docker run -d \
  --name png-backend \
  -p 4767:4767 \
  -p 4768:4768 \
  -p 4769:4769 \
  -p 4770:4770 \
  -p 20777:20777/udp \
  -v /path/to/your/png_config.json:/app/png_config.json:ro \
  pits-n-giggles
```

| Port | Purpose |
|------|---------|
| 4767 | Save Data Viewer |
| 4768 | Driver 1 (primary) |
| 4769 | Driver 2 |
| 4770 | Driver 3 |

> **Tip:** For many ports, `--network host` avoids listing each `-p` flag
> individually (Linux only).

### Verify

Open `http://localhost:4768` in your browser to access the Web UI.

---

## 🔒 Network Bind Address

By default, the server binds to `0.0.0.0`, which makes it accessible to **all devices on your local network**. This is intentional — the tool is designed for LAN use so that tablets, phones, and other PCs can access the dashboard.

If you want to restrict access to only the local machine, set `bind_address` to `"127.0.0.1"` in your `png_config.json`:

```json
{
  "Network": {
    "bind_address": "127.0.0.1"
  }
}
```

> **⚠️ Security Warning:** When `bind_address` is `0.0.0.0`, the HTTP server and UDP listener are reachable by anyone on your network. Do not use this setting on untrusted networks unless you understand the implications.

---

## 🧼 Cleaning Up

To remove the virtual environment created by Poetry:

```bash
poetry env remove python
```

To reinstall everything clean:

```bash
poetry install --no-root
```
