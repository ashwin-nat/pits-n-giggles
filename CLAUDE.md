# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
poetry install

# First-time only: fetch the f1-save-viewer React submodule (built output served by save_viewer)
git submodule update --init

# Run tests
poetry run pytest tests/

# By name pattern (class, method, or keyword)
poetry run pytest tests/ -k "TestWatchDogTimerAsync"
poetry run pytest tests/ -k "test_initial_state_idle"

# Only the serial (IPC/socket/process) suites
poetry run pytest tests/ -m serial

# Only the parallel-safe suites
poetry run pytest tests/ -m "not serial"

# Live API tests (OpenF1 schema checks) — requires network, excluded from default run
poetry run pytest tests/tests_openf1/tests_openf1_integration.py -m openf1 -v -n 0

# Run a single file
poetry run pytest tests/tests_version.py

# Lint
poetry run pylint --rcfile scripts/.pylintrc apps lib

# Lint QML (HUD overlays)
poetry run python scripts/qmllint.py

# Build executable
poetry run python scripts/build.py

# Run coverage
poetry run python scripts/coverage_ut.py
poetry run python scripts/coverage_integration_tests.py
```

## Tests

See `tests/README.md` for full details. Key conventions:

- Test files must be named `tests_*.py` to be collected; the default run is parallel (`-n auto --dist=loadgroup`) with `openf1`-marked tests excluded.
- Tests that bind real sockets/ports or spawn processes must be marked serial via module-level `pytestmark = pytest.mark.serial` so xdist funnels them to one worker.
- Write **new** tests in native pytest style: plain `assert`, `@pytest.mark.parametrize`, and bare `async def test_*` (asyncio_mode is `auto` — no decorator or base class needed).
- Existing tests are `unittest.TestCase`-style and run under pytest as-is; do not rewrite them.
- `tests/integration_test/` is the full-app integration runner and is not collected by pytest.

## Running Apps

The launcher is the entry point — it spawns every other subsystem (backend, hud, broker, save_viewer, mcp_server) as subprocesses and sends them periodic heartbeats over IPC. A subsystem started on its own fails the heartbeat check and self-terminates, so **do not run subsystems standalone**; always go through the launcher:

```bash
poetry run python -m apps.launcher          # Main GUI launcher (starts everything else)
poetry run python -m apps.dev_tools.telemetry_replayer --file-name example.f1pcap   # Dev tool, runs standalone
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
apps/mcp_server/   — Exposes live telemetry as MCP tools (FastMCP; stdio standalone, HTTP/SSE when launcher-managed)
apps/frontend/     — Vanilla JS/HTML/CSS browser UI (served by backend)
apps/external/     — Bundled external submodules (f1-save-viewer React app; dist/ served by save_viewer)
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
- **`ipc/`** — ZeroMQ-based IPC with three patterns: pub/sub (`IpcPubSubBroker`, `IpcPublisherAsync`, `IpcSubscriber*`), req/rep (`IpcServer*`, `IpcClientSync`), and router/dealer (`IpcRouter`, `IpcDealerClient`, `IpcDealerAsync`); also provides `PngAppId` for app identity
- **`race_ctrl/`** — Race control event tracking: pit stops, car damage, tyre/wing changes; per-driver and per-session managers
- **`tyre_wear_extrapolator/`** — Linear regression tyre wear prediction
- **`delta/`** — Lap delta calculations
- **`openf1/`** — Integration with the external OpenF1 API
- **`wdt/`** — Watchdog timer for async task health monitoring (sync and async variants)
- **`web_server/`** — Shared async web server base (`BaseWebServer`) and uvicorn socket helper used by backend and save_viewer
- **`assets_loader/`** — Loads fonts and icons (team logos, tyre compounds) for Qt HUD
- **`event_counter/`** — Rate/count statistics tracking for telemetry performance metrics
- **`track_segment_info/`** — Track segment metadata and per-circuit sector boundary database

`lib/` also holds ~19 single-file utility modules at the top level (e.g. `packet_cap.py`, `fuel_rate_recommender.py`, `race_analyzer.py`, `overtake_analyzer.py`, `collisions_analyzer.py`, `logger.py`, `version.py`) — see `lib/README.md` for the full table. Rules for `lib/`: no UI code or app-specific logic; no internal dependency on `lib/logger.py` — pass a logger object in instead.

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
- `.claude/commands/add-config-field.md` — Add a new config field with validation, subsystem wiring, and tests. Use when adding any new field to `png_config.json`.

### IPC Pattern

`lib/ipc/` provides three ZeroMQ-backed communication patterns:

- **Pub/Sub** — `IpcPublisherAsync` broadcasts; `IpcSubscriberAsync`/`IpcSubscriberSync` consume. The launcher uses `IpcPubSubBroker` to fan out state updates to all child processes.
- **Req/Rep** — `IpcClientSync` sends requests; `IpcServerSync`/`IpcServerAsync` handle them. Used for synchronous control commands (e.g. launcher → child process).
- **Router/Dealer** — `IpcRouter` (server-side) paired with `IpcDealerClient`/`IpcDealerAsync` (client-side) for async many-to-one messaging.

`PngAppId` enumerates all app identities; IPC sockets bind to OS-assigned ephemeral ports. The broker (`apps/broker/`) uses ZeroMQ independently for external multi-client forwarding.
