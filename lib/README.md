
# lib/

This directory contains shared code used across multiple apps in the Pits N Giggles suite. It acts as a common library for data types, utilities, and core logic.

## Structure

- `f1_types/`: Defines core data structures (e.g. lap data, car status, session info) used by telemetry processing and visualization.

## Purpose

The `lib/` folder is not a standalone app. Instead, it provides reusable modules that other apps (like `frontend`, `replay_viewer`, and `telemetry_dashboard`) can import.

## Usage Example

```python
from lib.f1_types.lap_data import LapData

lap = LapData.from_dict(raw_lap_data)
```

## Notes

- Keep this folder free of any UI code or app-specific logic.
- All shared logic that may be used across two or more apps should live here.
- No introducing internal dependencies like logger into this. If logging is required, pass the logger object