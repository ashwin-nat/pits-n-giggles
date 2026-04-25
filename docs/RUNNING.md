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
