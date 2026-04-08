# 🚀 Running pits-n-giggles (Manually)

This project uses Python 3.12 and is structured as a suite of apps under the `apps/` directory. Each sub-app can be run independently using Python's `-m` module mode.

## 🧰 Requirements

- Python 3.12 installed and available in your `PATH`
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

## 🧼 Cleaning Up

To remove the virtual environment created by Poetry:

```bash
poetry env remove python
```

To reinstall everything clean:

```bash
poetry install --no-root
```

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
  -p 4769:4769 \
  -p 20777:20777/udp \
  -v /path/to/your/png_config.json:/app/png_config.json:ro \
  pits-n-giggles
```

| Flag | Purpose |
|------|---------|n| `-p 4768:4768` | Web UI (HTTP) |
| `-p 4769:4769` | Save Data Viewer (HTTP) |
| `-p 20777:20777/udp` | F1 telemetry data (UDP) — must be reachable from the F1 game host |
| `-v ...png_config.json:/app/png_config.json:ro` | Mount your own config (read-only) |

> **Note:** The UDP port for telemetry must be reachable on the Docker host.
> If the F1 game runs on a different machine, ensure firewall rules allow
> UDP traffic on port 20777. On Linux, `--network host` can be used as an
> alternative to explicit port mapping for lower latency.

### Verify

Open `http://localhost:4768` in your browser to access the Web UI.
