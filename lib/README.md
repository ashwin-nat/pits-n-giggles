
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
| `ipc/` | Inter-process communication between subsystems |
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
| `button_debouncer.py` | Debounce logic for UDP-triggered actions |
| `event_counter.py` | Event counting utilities |
| `pending_events.py` | Deferred event queue |
| `custom_marker_tracker.py` | User-defined marker tracking |
| `inter_task_communicator.py` | Cross-task message passing |
| `child_proc_mgmt.py` | Child process lifecycle management |
| `save_to_disk.py` | Session data serialization and autosave |
| `error_status.py` | Error state tracking |
| `file_path.py` | File path utilities |
| `version.py` | Runtime version resolution |

## Purpose

The `lib/` folder is not a standalone app. Instead, it provides reusable modules that the apps (`backend`, `hud`, `save_viewer`, `launcher`, `frontend`) can import.

## Usage Example

```python
from lib.f1_types.lap_data import LapData

lap = LapData.from_dict(raw_lap_data)
```

## Notes

- Keep this folder free of any UI code or app-specific logic.
- All shared logic that may be used across two or more apps should live here.
- No introducing internal dependencies like logger into this. If logging is required, pass the logger object