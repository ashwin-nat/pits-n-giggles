# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
poetry install

# Run tests
poetry run python tests/unit_tests.py

# Run a single test (by class/method name pattern)
poetry run python -m pytest tests/unit_tests.py -k "TestName"

# Lint
poetry run pylint --rcfile scripts/.pylintrc apps lib

# Build executable
poetry run python scripts/build.py

# Run coverage
poetry run python scripts/coverage_ut.py
poetry run python scripts/coverage_integration_tests.py
```

## Running Apps

Each app is a Python module; the launcher starts all others as subprocesses:

```bash
poetry run python -m apps.launcher          # Main GUI launcher
poetry run python -m apps.backend           # Telemetry server
poetry run python -m apps.hud               # In-game overlay
poetry run python -m apps.broker            # ZeroMQ message broker
poetry run python -m apps.save_viewer       # Post-race session viewer
poetry run python -m apps.dev_tools.telemetry_replayer --file-name example.f1pcap
```

## Architecture

**Pits n' Giggles** is a multi-process F1 telemetry suite. The F1 game broadcasts UDP telemetry; this app captures, parses, analyzes, and displays it via browser dashboards and an in-game overlay.

### Process Model

```
apps/launcher/     — Qt (PySide6) GUI; spawns and monitors all other processes via IPC
apps/backend/      — Core server: receives UDP/TCP from F1 game, runs analysis, serves WebSocket+REST
apps/hud/          — Always-on-top Qt overlay windows for in-game display
apps/broker/       — ZeroMQ pub/sub broker for multi-client telemetry forwarding
apps/save_viewer/  — Quart web server for analyzing saved session JSON files
apps/frontend/     — Vanilla JS/HTML/CSS browser UI (served by backend)
apps/dev_tools/    — Telemetry replayer and packet capture utilities
```

### Backend Layers (`apps/backend/`)

The backend is structured in three layers:

1. **`telemetry_layer/`** — UDP/TCP socket reception, packet parsing (16 F1 packet types), frame gating
2. **`state_mgmt_layer/`** — `SessionState` aggregates all parsed data; runs overtake/collision detection, tyre wear extrapolation, race analysis
3. **`intf_layer/`** — Quart web server + Socket.IO; pushes state updates to browser clients and HUD via WebSocket; exposes REST API

### Shared Library (`lib/`)

Reusable modules consumed by multiple apps:

- **`f1_types/`** — Packet dataclass definitions for F1 2023–2025 seasons (16 packet types)
- **`telemetry_manager/`** — Async UDP/TCP receiver manager and packet parser factory
- **`socket_receiver/`** — Base, UDP, TCP receiver implementations
- **`config/`** — Config loading from `png_config.json`/`app_settings.ini`; Pydantic validation models
- **`ipc/`** — Custom IPC: parent↔child process messaging, pub/sub patterns (used by launcher↔subprocesses)
- **`race_analyzer/`** — Lap time analysis
- **`tyre_wear_extrapolator/`** — Linear regression tyre wear prediction
- **`overtake_analyzer/`** — Overtake event detection and classification
- **`collisions_analyzer/`** — Collision detection and recording
- **`delta/`** — Lap delta calculations
- **`openf1/`** — Integration with the external OpenF1 API
- **`wdt/`** — Watchdog timer for async task health monitoring

### Data Flow

```
F1 Game (UDP/TCP)
  → TelemetryManager (lib/telemetry_manager) parses packets
  → SessionState (state_mgmt_layer) aggregates and runs analysis
  → TelemetryWebServer (intf_layer) broadcasts via Socket.IO
  → Browser dashboard (apps/frontend) + HUD overlay (apps/hud)
```

### Key Files

- `meta/meta.py` — Single source of version truth (`APP_VERSION`, `APP_NAME_SNAKE`)
- `png_config.json` — Runtime config (ports, capture mode, privacy, HUD, HTTPS)
- `scripts/png.spec` — PyInstaller spec (entry point, hidden imports, version injection)
- `pyproject.toml` — Poetry deps; requires Python 3.12–3.14

## Procedures

These files define step-by-step procedures for common dev tasks. Read the relevant file before starting the task.

- `.claude/commands/perf-report.md` — Generate a performance metrics report from a launcher log file. Use when asked to analyse performance, check latency/loss stats, or generate a report from a log.
- `.claude/commands/add-packet-type.md` — Scaffold a new F1 packet type across `lib/f1_types/` and `lib/telemetry_manager/`. Use when adding support for a new packet ID or season.
- `.claude/commands/new-overlay.md` — Scaffold a new HUD overlay widget. Use when adding a new in-game display panel.
- `.claude/commands/release-notes.md` — Generate user-facing release notes from commits since the last tag. Use when preparing a release.
- `.claude/commands/add-mcp-tool.md` — Scaffold a new MCP tool in `apps/mcp_server/`. Use when adding a new tool to the MCP server.

### IPC Pattern

The launcher communicates with child processes through `lib/ipc/`. Child processes receive IPC parent handles and publish state/status back. The broker (`apps/broker/`) uses ZeroMQ for external multi-client forwarding independent of the launcher IPC.
