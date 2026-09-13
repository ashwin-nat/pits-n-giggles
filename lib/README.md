
# lib/

This directory contains shared code used across multiple apps in the Pits N Giggles suite. It acts as a common library for data types, utilities, and core logic.

## Structure

| Module / File | Purpose |
|---|---|
| `f1_types/` | Core data structures (lap data, car status, session info) used by telemetry processing and visualization |
| `config/` | Configuration schema (Pydantic models), loading, validation, and migration logic |
| `web_server/` | HTTP/Socket.IO server, static file serving, security headers, CORS |
| `telemetry_manager/` | Orchestrates telemetry ingest, state updates, and event distribution |
| `tyre_wear_extrapolator/` | Weather-aware tyre wear regression and prediction |
| `race_ctrl/` | Race control message parsing and factory |
| `delta/` | Lap delta and sector time computation |
| `pngt/` | `.pngt` session file format — read/write for the ZIP-based telemetry session container |
| `ipc/` | Inter-process communication between subsystems |
| `subsystem/` | Child-side lifecycle base for launcher-managed subsystems (boot, handshake, heartbeat, stats, teardown) |
| `socket_receiver/` | UDP socket wrapper for F1 telemetry packets |
| `wdt/` | Watchdog timer for health monitoring |
| `openf1/` | OpenF1 API integration |
| `assets_loader/` | Asset path resolution for bundled resources |
| `logger.py` | Centralized logging setup |
| `packet_cap.py` | Packet capture (recording telemetry to `.f1pcap` files) |
| `packet_forwarder.py` | Forwards raw UDP packets to external targets |
| `fuel_rate_recommender.py` | Live fuel consumption modelling and recommendations |
| `race_analyzer.py` | Post-race analysis utilities |
| `collisions_analyzer.py` | Collision detection and tracking |
| `overtake_analyzer.py` | Overtake detection |
| `rolling_history.py` | Rolling window data history |
| `rate_limiter.py` | Rate limiting for event emissions |
| `table_differ.py` | Row-granularity diffing of table data for UI patching |
| `button_debouncer.py` | Debounce logic for UDP-triggered actions |
| `event_counter.py` | Event counting utilities |
| `custom_marker_tracker.py` | User-defined marker tracking |
| `inter_task_communicator.py` | Cross-task message passing |
| `child_proc_mgmt.py` | Child process lifecycle management |
| `save_to_disk.py` | Session data serialization and autosave |
| `error_status.py` | Error state tracking |
| `file_path.py` | File path utilities |
| `version.py` | Runtime version resolution |

## Purpose

The `lib/` folder is not a standalone app. Instead, it provides reusable modules that the apps (`backend`, `web`, `hud`, `launcher`, `frontend`) can import.

## Usage Example

```python
from lib.f1_types.lap_data import LapData

lap = LapData.from_dict(raw_lap_data)
```

## Notes

- Keep this folder free of any UI code or app-specific logic.
- All shared logic that may be used across two or more apps should live here.
- No introducing internal dependencies like logger into this. If logging is required, pass the logger object
## Profiling

Any subsystem can be profiled with [yappi](https://github.com/sumerc/yappi). It is off, and
there is no flag or launcher toggle — set the class var and put it back when you are done.

### 1. Turn it on

Edit `PROFILE` on the subsystem you care about:

```python
class BackendSubsystem(AsyncSubsystem[BackendArgs]):
    NAME = "backend"
    PROFILE = True          # <-- revert before committing
```

Setting it on `PngSubsystem` instead profiles all five at once. That works — output files are
named after the subsystem, so they do not overwrite each other — but five wall-clock profiles of
processes that mostly wait on each other is rarely what you want.

The profile covers the whole process: the constructor (args, config, IPC binds, and everything
the subsystem builds), the run, and teardown. `yappi` is imported inside the `if`, so a normal
boot neither imports it nor pays for it.

### 2. Run through the launcher

```bash
poetry run python -m apps.launcher --replay-server
poetry run python -m apps.dev_tools.telemetry_replayer --file-name f1_24_sp_austria.f1pcap
```

Files are written when the subsystem exits cleanly, so let the replay finish and stop the
launcher normally — killing it skips teardown and you get nothing.

### 3. Read the output

Three files land in the working directory, named after the subsystem:

| File | What it is |
|---|---|
| `<name>_yappi.prof` | pstat format — open with `snakeviz <name>_yappi.prof` |
| `<name>_yappi.txt` | Cumulative-sorted text |
| `<name>_yappi.html` | The same text in a `<pre>` block |

Clock type is wall, not CPU, so I/O waits are included — which is usually the point for
subsystems that spend their time on sockets.

Full paths are kept rather than stripped, so you can filter down to this repo's own frames:

```bash
grep "$(pwd)" backend_yappi.txt
```

If your virtualenv lives inside the repo, narrow the pattern further to exclude `.venv/`.
