# 🚀 Running pits-n-giggles (Manually)

This project uses Python 3.12 and is structured as a suite of apps under the `apps/` directory. Each sub-app can be run independently using Python's `-m` module mode.

## 🧰 Requirements

- Python 3.12 installed and available in your `PATH`
- [Poetry](https://python-poetry.org/) installed (preferred for dependency management)

## 📦 Install Dependencies

Install only the production dependencies if you plan on running only the backend
```bash
poetry install --without dev
```

If you plan on running backend, dev utils and unit tests, install all dependencies
```bash
poetry install
```

This sets up a virtual environment and installs everything defined in `pyproject.toml`.

---

## ▶️ Running Apps

All commands below must be run **from the project root directory** (i.e., the folder containing `pyproject.toml`).

### 🧠 Backend App

```bash
poetry run python -m apps.backend.app --replay-server
```

### 🛠 Dev Tools (e.g., telemetry replayer)

```bash
poetry run python -m apps.dev.telemetry_replayer --file-name example.f1pcap
```

### 🧪 Test Utilities (example)

```bash
poetry run python -m apps.test.some_test_runner
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