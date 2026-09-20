
# lib/pngt/ingest/

Per-driver telemetry accumulation for a live F1 sim session. Sits between the
existing telemetry-parsing codebase and `lib/pngt`'s file writer.

Full behavioural spec: `plans/telemetry_recording/telemetry-ingest-spec.md`.

## Design principles

- Each driver has its own isolated `DriverTelemetryRecorder`; internal state is opaque.
- No I/O, no file system access, no knowledge of the `.pngt` ZIP layout — that's the
  parent package's `writer.py`. `export()` returns plain Python data
  (`DriverExportData`); turning that into bytes on disk is the caller's job.
- No NumPy dependency — buffers are plain Python lists. `SensorDtype` (shared with
  the format layer, see `../dtypes.py`) is only a width *hint* carried on
  `IngestSensorConfig` for the writer to act on later.
- Sensor extraction is injected via `SensorMapper`, so the recorder never hardcodes
  an F1-specific field name — `F1SensorMapper` is the production implementation,
  `StubSensorMapper` the test one.
- Ordered-int sensors (e.g. ERS deploy mode) are typed plain `int` on
  `TelemetrySnapshot`, not as an `IntEnum` — the enum itself is owned by whoever
  builds the snapshot from real sim packets, not by this layer.
- Configuration (`TelemetryRecorderConfig`) is a frozen dataclass, immutable
  after construction. Deliberately not a pydantic model: it's built internally
  from already-validated `lib/config` settings (Phase 9's
  `build_recorder_config()`), never from untrusted input, and `lib/config` is
  where this repo's app-config schemas live — this class isn't one of those.

## Structure

No `__init__.py` here — this is a plain namespace package, same as `lib/ipc/pubsub/`
or `lib/ipc/reqrep/` elsewhere in this repo. The one export surface for the whole
package is `lib/pngt/__init__.py`, which imports straight from these files; import
from `lib.pngt`, not `lib.pngt.ingest.dto`, unless you're inside this package.

| File | Purpose |
|---|---|
| `dto.py` | `TelemetrySnapshot`, `TelemetryRecorderConfig` (no collision with the parent package, plain names), plus `IngestLapMetadata`, `IngestSensorConfig`, `IngestCompletedLap`, `IngestDriverExportData` (named with the `Ingest` prefix because the parent package's `dto.py` already has a `LapMetadata`/`SensorConfig`/`CompletedLap`/`DriverExportData` meaning something different) |
| `mapper.py` | `SensorMapper` ABC, `F1SensorMapper`, `StubSensorMapper` |
| `recorder.py` | `DriverTelemetryRecorder` — accumulation, lap rollover, flashback detection/rollback, export |

## Not in scope here

Owning multiple drivers, scope filtering (spectator mode, other players' cars,
`Restricted` telemetry), session-best tracking, and assembling/writing the final
`.pngt` file are `SessionExportManager`'s job (not yet built — see the top-level
implementation plan's Phase 8). This package only accumulates one driver's telemetry
and hands back plain data at `export()`.
