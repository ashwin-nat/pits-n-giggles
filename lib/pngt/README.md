
# lib/pngt/

Read/write library for the `.pngt` session file format — a ZIP-based container that
holds one recorded F1 sim session's driver metadata and per-lap telemetry, for the
Telemetry Visualizer feature.

Format-agnostic: it has zero embedded knowledge of what sensors exist.
`write_session()` takes whatever `SensorConfig` list it's given and serializes it; it
never hardcodes a real F1 sensor key (`speed`, `tyre_temp.fl`, etc). The F1 sensor
catalog and the concrete snapshot type it reads from both live in
`apps/backend/state_mgmt_layer/data_per_driver` — see `RecordedSensor` below.

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

A driver with `is_telemetry_public == False` appears in `drivers.json` but has
**no** `drivers/{idx}/` folder at all — `read_driver_laps()` returns `[]` for one,
not an error. JSON entries are `ZIP_DEFLATED`; `.npz` entries are `ZIP_STORED`
(numpy's own compression, if any, lives inside the `.npz`, so double-compressing
would just waste CPU). Every array in a lap's `.npz` — every sensor,
`lap_distance`, and `lap_time_ms` alike — is `float32`; `NaN` is the only
missing value.

## Structure

| File | Purpose |
|---|---|
| `dto.py` | Input dataclasses (`SessionMetadata`, `DriverRecord`, `LapMetadata`, `CompletedLap`, `DriverExportData`, `SensorConfig` + `SensorType`, `DeleteLapsResult`, `MarkLapGoodResult`) carrying only caller-filled fields, plus the `Parsed*` read-side subclasses (`ParsedSessionMetadata`, `ParsedDriver`, `ParsedLap`) that add the fields `write_session()` derives |
| `archive.py` | `header.json` validation (`validate_pngt_zip`), shared JSON read/write helpers, archive rebuild, and `recompute_totals()` (laps count + session best), used by both `writer.py` and `mutate.py` |
| `writer.py` | `write_session()` — validates, derives `laps_count`/`session_best`/`is_telemetry_public`/`num_points`/`is_good`, then writes the ZIP |
| `reader.py` | `read_session()` / `read_driver_laps()` / `read_lap_telemetry()` |
| `mutate.py` | `delete_laps()` / `mark_lap_good()` / `rename_session()` — in-place archive rebuilds |
| `recorder.py` | `BaseTelemetrySnapshot` (mandatory `lap_distance`/`lap_time_ms`), `RecordedSensor` (a sensor's manifest entry + how to read its value off a snapshot), `DriverTelemetryRecorder` (accumulation, lap rollover, flashback detection/rollback, export) |
| `exceptions.py` | `PngtError` base and its subclasses — one per failure mode |

## Usage

```python
from lib.pngt import (
    SessionMetadata, TrackInfo, SensorConfig, SensorType,
    DriverRecord, DriverExportData, CompletedLap, LapMetadata,
    write_session, read_session, read_driver_laps, read_lap_telemetry,
    delete_laps, mark_lap_good, rename_session,
)

session = SessionMetadata(
    session_uid=1234567890123456789, session_name="Spa GP", session_type="race",
    app_version="4.4.0", game_year=2025, formula="F1", game_version="1.24",
    timestamp="2026-08-27T14:32:00Z",
    track=TrackInfo(id=10, name="Circuit de Spa-Francorchamps"),  # id = the sim's own TrackID
)
sensors = [SensorConfig(key="speed", label="Speed", unit="km/h", type=SensorType.CONTINUOUS)]
drivers = [DriverRecord(driver_index=0, name="Driver 1", team="Red Bull Racing",
                         car_number=1, nationality="NL", platform="Steam")]
lap = CompletedLap(
    metadata=LapMetadata(lap_number=1, lap_time_ms=105812, valid=True, tyre_compound="Soft",
                          tyre_laps=1, pit_in_lap=False, pit_out_lap=False),
    telemetry={"lap_distance": [0.0, 100.0, 200.0], "speed": [100.0, 150.0, 200.0]},
)
dest = write_session("session.pngt", session, sensors, drivers,
                      {0: DriverExportData(driver_index=0, completed_laps=[lap])})

parsed = read_session(dest)                 # -> ParsedSession(session, drivers, sensors)
laps = read_driver_laps(dest, 0)            # -> list[ParsedLap]
telemetry = read_lap_telemetry(dest, 0, 1)  # -> dict[str, np.ndarray], exactly what's in the .npz

rename_session(dest, "Spa GP (renamed)")    # in-place, session_uid untouched
mark_lap_good(dest, 0, 1)                   # in-place, idempotent
delete_laps(dest, 0, [1])                   # in-place, full archive rebuild
```

### Recording live telemetry

`DriverTelemetryRecorder` accumulates one driver's telemetry over a session and
produces a `DriverExportData` ready for `write_session()`. It never names a real
sensor — that comes entirely from the `RecordedSensor` list it's constructed with:

```python
from operator import attrgetter
from lib.pngt import BaseTelemetrySnapshot, RecordedSensor, DriverTelemetryRecorder

@dataclass(slots=True)
class TelemetrySnapshot(BaseTelemetrySnapshot):
    speed: float | None = None
    gear: int | None = None

SENSORS = (
    RecordedSensor(SensorConfig("speed", "Speed", "km/h", SensorType.CONTINUOUS), attrgetter("speed")),
    RecordedSensor(SensorConfig("gear", "Gear", "", SensorType.DISCRETE), attrgetter("gear")),
)

recorder = DriverTelemetryRecorder(driver_index=0, sensors=SENSORS)
recorder.update(TelemetrySnapshot(lap_distance=12.3, lap_time_ms=45000, speed=201.4, gear=6), frame_id=1)
recorder.on_lap_change(LapMetadata(lap_number=1, lap_time_ms=None, valid=False,
                                    tyre_compound="Soft", tyre_laps=1, pit_in_lap=False, pit_out_lap=False))
export = recorder.export()  # -> DriverExportData
```

`RecordedSensor.get` returning `None` means "unavailable this packet" — stored as
`NaN`, never raised. The real F1 catalog (`F1_SENSORS`) lives next to the real
`TelemetrySnapshot` in `apps/backend/state_mgmt_layer/data_per_driver`, not here.

## Notes

- **`sensors` is a top-level parameter, not nested in `SessionMetadata`.** It maps
  to its own `manifest.json` entry, distinct from `session.json`: `write_session(dest,
  session, sensors, drivers, driver_data)`, and `read_session()` returns them as
  `ParsedSession.sensors`.
- **Input types carry only what the caller fills; `write_session()` derives and
  persists the rest.** `SessionMetadata` has no `laps_count`/`session_best`,
  `DriverRecord` has no `is_telemetry_public`, `LapMetadata` has no `num_points`/
  `is_good` — those come back on the read side via `ParsedSessionMetadata`/
  `ParsedDriver`/`ParsedLap`, which subclass the input types and add exactly those
  fields. A driver's `is_telemetry_public` is `driver_index in driver_data`, not a
  separate flag to keep in sync.
- **Only sensor `type` (`SensorType`: `CONTINUOUS`/`DISCRETE`) is validated against
  a closed set.** `session_type` and `tyre_compound` are caller-owned labels, passed
  through as plain strings — the format spec gives `tyre_compound` as illustrative
  examples, not an exhaustive list, keeping sim-specific domain knowledge out of
  this format-agnostic library.
- **Validation is split by where the invariant lives.** A check that only depends
  on one object's own fields raises `ValueError` straight from that object's
  `__post_init__` (`SensorConfig`'s `type`, `CompletedLap`'s telemetry array-length
  agreement, `DriverExportData`'s in-progress-lap constraint). `write_session()`
  itself only checks what spans two independently-constructed arguments: a
  duplicate sensor key, an unregistered sensor key in a lap's telemetry, or a
  `driver_data` entry for a `driver_index` not in `drivers`.
- **Default-good-lap marking**: the fastest valid+timed lap (`valid=True`, minimum
  `lap_time_ms`) among a driver's `completed_laps` is always marked good at write
  time. Applies only to `completed_laps`, never to `in_progress_lap`. `delete_laps()`
  never auto-promotes a replacement good lap after a deletion — that's a fresh
  `write_session()` or `mark_lap_good()` call.
- Reading is forward-compatible by construction: unknown JSON fields are ignored
  (plain `dict` parsing, not a strict schema), and `read_lap_telemetry()` returns
  exactly the array names present in that lap's `.npz`.
- `write_session()` writes to a `.tmp` sibling and `os.replace()`s onto `dest_path`;
  every mutation in `mutate.py` follows the same atomic rebuild-then-replace pattern.

## Not in scope here

Config schema, the REST API, and the frontend live elsewhere in the app. The real
F1 sensor catalog and `TelemetrySnapshot` live in
`apps/backend/state_mgmt_layer/data_per_driver` — this package only reads, writes,
and mutates `.pngt` files given data the caller already has, and accumulates
telemetry into `DriverExportData` given a `RecordedSensor` list the caller supplies.
