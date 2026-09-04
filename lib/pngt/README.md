
# lib/pngt/

Read/write library for the `.pngt` session file format — a ZIP-based container that
holds one recorded F1 sim session's driver metadata and per-lap telemetry, for the
Telemetry Visualizer feature.

This module is deliberately **format-agnostic**: it has zero embedded knowledge of
what sensors exist. `write_session()` takes whatever `SensorConfig` list it's given
and serializes it; it never hardcodes a real F1 sensor key (`speed`, `tyre_temp.fl`,
etc). The actual F1 sensor catalog and packet-to-telemetry mapping belong to the
(separate, not-yet-built) ingest layer — this library only knows how to lay data out
on disk, read it back, and apply a handful of in-place mutations.

## On-disk layout

A `.pngt` file is a ZIP archive:

```
header.json                      # {"format": "pngt", "version": 1} -- pure format identity
manifest.json                    # sensor registry: {"sensors": {key: {label, unit, type}, ...}}
session.json                     # session facts: track, timestamp, laps count/best, etc.
drivers.json                     # all drivers, including Restricted ones
drivers/{driver_index:02d}/
    laps.json                    # this driver's lap metadata (completed + in-progress)
    lap_{lap_number:03d}.npz     # this lap's telemetry arrays
```

`header.json` and `manifest.json` are deliberately separate: `header.json` is the
two-field identity blob read unconditionally on every open (before anything else is
trusted); `manifest.json` is the actual itemized "what's in this archive" sensor
list — a better fit for the word "manifest" than a format/version pair.

A driver with `is_telemetry_public == False` appears in `drivers.json` but has
**no** `drivers/{idx}/` folder at all — `read_driver_laps()` returns `[]` for one,
not an error. JSON entries are `ZIP_DEFLATED`; `.npz` entries are `ZIP_STORED`
(numpy's own compression, if any, lives inside the `.npz`, so double-compressing
would just waste CPU).

## Structure

| File | Purpose |
|---|---|
| `dto.py` | Public dataclass contract: `SessionMetadata`, `TrackInfo`, `SessionBest`, `SensorConfig`, `DriverRecord`, `LapMetadata`, `CompletedLap`, `DriverExportData`, `DeleteLapsResult`, `MarkLapGoodResult`, plus the `SensorType` enum (the one field this library validates against a closed set — see Notes) |
| `dtypes.py` | `SensorDtype` enum and its mapping to NumPy dtypes / missing-value sentinels (`nan` for float32, `-1` for int dtypes) |
| `exceptions.py` | `PngtError` base and its subclasses — one per failure mode |
| `manifest.py` | `header.json` validation (`validate_pngt_zip`), shared by every read/mutate entry point |
| `writer.py` | `write_session()` — validates, applies default-good-lap marking, then writes the ZIP |
| `reader.py` | `read_header()` / `read_manifest()` / `read_session()` / `read_driver_laps()` / `read_lap_telemetry()` |
| `mutate.py` | `delete_laps()` / `mark_lap_good()` / `rename_session()` — in-place archive rebuilds |
| `filename.py` | `suggest_filename()` — cosmetic default filename, never used implicitly by `write_session()` |

## Usage

```python
from lib.pngt import (
    SessionMetadata, TrackInfo, SessionBest, SensorConfig, SensorDtype, SensorType,
    DriverRecord, DriverExportData, CompletedLap, LapMetadata,
    write_session, read_session, read_driver_laps, read_lap_telemetry,
    delete_laps, mark_lap_good, rename_session,
)

session = SessionMetadata(
    session_uid=1234567890123456789, session_name="Spa GP", session_type="race",
    app_version="4.4.0", game_year=2025, formula="F1", game_version="1.24",
    timestamp="2026-08-27T14:32:00Z",
    track=TrackInfo(id=10, name="Circuit de Spa-Francorchamps"),  # id = the sim's own TrackID
    laps_count=1, session_best=SessionBest(driver_index=0, lap_number=1, lap_time_ms=105812),
)
sensors = [SensorConfig(key="speed", label="Speed", unit="km/h", type=SensorType.CONTINUOUS)]
dtypes = {"speed": SensorDtype.FLOAT32}
drivers = [DriverRecord(driver_index=0, name="Driver 1", team="Red Bull Racing", is_ai=False,
                         car_number=1, nationality="NL", platform="Steam", is_telemetry_public=True)]
lap = CompletedLap(
    metadata=LapMetadata(lap_number=1, lap_time_ms=105812, valid=True, tyre_compound="Soft",
                          tyre_laps=1, pit_in_lap=False, pit_out_lap=False, num_points=3, is_good=False),
    telemetry={"lap_distance": [0.0, 100.0, 200.0], "speed": [100.0, 150.0, 200.0]},
)
dest = write_session("session.pngt", session, sensors, dtypes, drivers,
                      {0: DriverExportData(driver_index=0, completed_laps=[lap])})

parsed = read_session(dest)                 # -> ParsedSession(session, drivers, sensors)
laps = read_driver_laps(dest, 0)            # -> list[LapMetadata]
telemetry = read_lap_telemetry(dest, 0, 1)  # -> dict[str, np.ndarray], exactly what's in the .npz

rename_session(dest, "Spa GP (renamed)")    # in-place, session_uid untouched
mark_lap_good(dest, 0, 1)                   # in-place, idempotent
delete_laps(dest, 0, [1])                   # in-place, full archive rebuild
```

## Notes

- **`sensors` is a top-level parameter/field, not nested in `SessionMetadata`.** It maps
  to its own `manifest.json` entry, distinct from `session.json`, so the Python API
  mirrors the on-disk split: `write_session(dest, session, sensors, dtypes, drivers,
  driver_data)`, and `read_session()` returns them as separate `ParsedSession.sensors`.
  `read_manifest()` reads the registry on its own, returning the same `list[SensorConfig]`
  shape — there's one `SensorConfig` class used on both the read and write path, no
  separate read-only type.
- **`dtype` is a separate `dtypes: dict[str, SensorDtype]` argument to `write_session()`,
  not a field on `SensorConfig`.** It has no on-disk representation — `manifest.json`
  entries only ever carry `label`/`unit`/`type` — so keeping it off `SensorConfig`
  means the same class works unmodified for both reading and writing, with no nullable
  field. The tradeoff: every sensor's `key` must have a matching entry in `dtypes`, or
  `write_session()` fails fast with `ValueError` at the validation step, before any I/O
  — not a `KeyError` surfacing later inside the NPZ writer.
- **Only sensor `type` (a `SensorType` enum: `CONTINUOUS`/`DISCRETE`) is
  validated against a closed set.** `session_type` and `tyre_compound` are documented
  in the format spec as caller-owned labels (the spec itself gives `tyre_compound` as
  illustrative examples, not an exhaustive list) — this library passes them straight
  through as plain strings rather than rejecting values it doesn't recognize, keeping
  sim-specific domain knowledge out of a format-agnostic library. `is_telemetry_public`
  is a plain `bool` (not a string), so there's no invalid-value question there at all —
  `False` is what drives the no-folder-on-disk behavior. Sensor `type` is different:
  this library's own behavior (which the viewer relies on for interpolation) depends on
  it directly, so it's a real `Enum` rather than a bare string.
- **Validation is split by where the invariant lives, not centralized in `write_session()`.**
  A check that only depends on one object's own fields raises `ValueError` straight from
  that object's `__post_init__`, before `write_session()` is ever called:
  `SensorConfig` validates its own `type`; `CompletedLap` validates that its telemetry
  arrays all agree in length; `DriverExportData` validates that its `in_progress_lap`
  (if any) has no final `lap_time_ms` and isn't `valid`. `write_session()` itself only
  checks what genuinely spans two independently-constructed arguments and so can't be
  caught any earlier: a sensor missing from `dtypes`, an unregistered sensor key in a
  lap's telemetry, or a `driver_data`/`drivers` mismatch. Either way every failure is a
  `ValueError`, raised as early as the data allows — nothing is silently dropped or
  defaulted. `write_session()` writes to a `.tmp` sibling and `os.replace()`s onto
  `dest_path` for partial-write safety — every mutation in `mutate.py` follows the same
  atomic rebuild-then-replace pattern.
- **Default-good-lap marking**: if no lap in a driver's `completed_laps` for a given
  `write_session()` call already has `is_good=True`, the fastest valid lap
  (`valid=True`, minimum `lap_time_ms`) is automatically marked good. Set `is_good`
  explicitly on a lap yourself to opt out of this. Applies only to `completed_laps`,
  never to `in_progress_lap`. `delete_laps()` never auto-promotes a replacement good
  lap after a deletion — that's a fresh `write_session()` or `mark_lap_good()` call.
- Reading is forward-compatible by construction, not by special-casing: unknown JSON
  fields are ignored (plain `dict` parsing, not a strict schema), and
  `read_lap_telemetry()` returns exactly the array names present in that lap's
  `.npz` — an older file with fewer sensors or a newer file with extra ones both work
  with zero extra code.

## Not in scope here

Recording live telemetry into these DTOs, the sensor catalog itself, config schema,
the REST API, and the frontend are a separate, not-yet-built ingest layer. This
module only reads, writes, and mutates `.pngt` files given data the caller already
has.
