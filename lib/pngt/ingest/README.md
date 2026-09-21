
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
  the format layer, see `../dtypes.py`) is only a width *hint*, sourced from
  `SensorMapper.get_dtype()` for the writer to act on later.
- Sensor extraction *and* dtype are both injected via the `SensorMapper` ABC, so the
  recorder never hardcodes an F1-specific field name or its storage width.
  `TelemetryRecorderConfig.sensors` is just a `tuple[str, ...]` of dotted keys
  (coerced from whatever iterable is passed in, and rejected if it has duplicates),
  not `(key, dtype)` pairs — dtype has exactly one source of truth (the mapper), not a
  second field that could drift out of agreement with it. A tuple, not a `list`,
  because `frozen=True` on the dataclass alone doesn't stop a list it points at from
  being mutated in place after a recorder is already built from it. This package ships only
  the interface — a real sensor catalog (e.g. one covering every F1 telemetry
  field), and the concrete snapshot subclass it reads from, are both
  game-/domain-specific and belong with whatever code actually populates that
  snapshot from real packets (`apps/backend/state_mgmt_layer/data_per_driver`'s own
  `TelemetrySnapshot`), not in this generic library. The recorder only ever needs `lap_distance`
  directly (see `BaseTelemetrySnapshot` below); everything else goes through the
  mapper. A stub implementation for exercising `DriverTelemetryRecorder` in tests
  lives in `tests/tests_pngt_ingest.py`, not here.
- Ordered-int sensors (e.g. ERS deploy mode) are typed plain `int` on the real
  snapshot dataclass, not as an `IntEnum` — the enum itself is owned by whoever
  builds the snapshot from real sim packets, not by this layer.
- Configuration (`TelemetryRecorderConfig`) is a frozen dataclass, immutable
  after construction. Deliberately not a pydantic model: it's built internally
  from already-validated `lib/config` settings (Phase 9's
  `build_recorder_config()`), never from untrusted input, and `lib/config` is
  where this repo's app-config schemas live — this class isn't one of those.
- `DriverTelemetryRecorder.__init__` resolves every configured key's dtype via
  `SensorMapper.get_dtype()` once, up front — this both fails fast on an
  unresolvable key (the spec's construction-time validation requirement) and
  avoids a mapper call in the 60 Hz `update()` hot path.
- `_current_lap_number`'s only real source of truth is `on_lap_change()`
  (`lap_number + 1`). A snapshot carries no lap number at all, so the
  first `update()` call (if it happens before any `on_lap_change()`) seeds it
  to `1` purely as an `export()` label for whatever partial lap recording
  started mid-session on — not a claim about which lap it actually is.
- Flashback detection is frame_id-only, never the sim's own (unreliable)
  flashback event packet: lower layers already discard out-of-order packets,
  so any `frame_id` lower than the last one seen is unambiguously a rewind.
  Rollback truncates in place (Case A, `bisect.bisect_right` against
  `_frame_id_buffer`) when the target is still within the current lap, or
  pops and truncates the last completed lap back into the current buffer
  (Case B) when it isn't — discarding that lap's `IngestLapMetadata` for
  good; it's re-finalised as a new object when `on_lap_change()` fires again.
  The sim's 20-30s flashback buffer means the rewind target is never more
  than one completed lap back, so Case B never needs to reach further than
  the single most recently completed lap.

## Structure

No `__init__.py` here — this is a plain namespace package, same as `lib/ipc/pubsub/`
or `lib/ipc/reqrep/` elsewhere in this repo. The one export surface for the whole
package is `lib/pngt/__init__.py`, which imports straight from these files; import
from `lib.pngt`, not `lib.pngt.ingest.dto`, unless you're inside this package.

| File | Purpose |
|---|---|
| `dto.py` | `BaseTelemetrySnapshot` (mandatory `lap_distance`/`lap_time_ms`; a real snapshot subclasses this and adds its own fields), `TelemetryRecorderConfig` (no collision with the parent package, plain names), plus `IngestLapMetadata`, `IngestCompletedLap`, `IngestDriverExportData` (named with the `Ingest` prefix because the parent package's `dto.py` already has a `LapMetadata`/`CompletedLap`/`DriverExportData` meaning something different) |
| `mapper.py` | `SensorMapper` ABC only (`get_value()` + `get_dtype()`) — no concrete implementation ships here, see Design principles above |
| `recorder.py` | `DriverTelemetryRecorder` — accumulation, lap rollover, flashback detection/rollback, export |

## Not in scope here

Owning multiple drivers, scope filtering (spectator mode, other players' cars,
`Restricted` telemetry), session-best tracking, and assembling/writing the final
`.pngt` file are `SessionExportManager`'s job (not yet built — see the top-level
implementation plan's Phase 8). This package only accumulates one driver's telemetry
and hands back plain data at `export()`.

The concrete `TelemetrySnapshot` (every real F1 sensor field, subclassing
`BaseTelemetrySnapshot`) and its `SensorMapper` implementation both live in
`apps/backend/state_mgmt_layer/data_per_driver`, not here — this package only owns
the mandatory `lap_distance`/`lap_time_ms` fields every snapshot must carry. See
that package's own docstrings.
