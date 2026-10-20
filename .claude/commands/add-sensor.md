---
description: Add a recordable lap analyzer sensor (config toggle, snapshot field, manifest entry), optionally wired to a packet field
allowed-tools: Read, Glob, Grep, Edit, Write, Bash, AskUserQuestion
---

Add one or more lap analyzer sensors end-to-end. A sensor is the user-facing toggle in the launcher's Lap Analyzer page plus the manifest entry and per-sample array written to `.pngt` files.

> The launcher settings page and the lap-analyzer frontend are both built from metadata (`sensor_field` annotations and the `.pngt` manifest). Neither needs editing for a new sensor.

---

## Step 1 — Gather info

Read `lib/config/schema/lap_analyzer.py` and `apps/backend/state_mgmt_layer/data_per_driver/telemetry_recorder/telemetry_recorder.py` first, so you can offer the existing groups/presets as choices and spot key collisions.

Ask the user (use `AskUserQuestion` for the enumerable ones, plain questions for the free-text ones) for anything not already given. Batch all sensors into one round of questions.

**Required**

| Info | Where it goes | Notes |
|---|---|---|
| Field name | schema field, `TelemetrySnapshot` field, `F1_SENSORS` dict key | snake_case, must match in all three places |
| Label | `sensor_field(label=...)` | shown in the launcher; also becomes the manifest label |
| Group | `SensorGroup` | existing member, or a new one (then optionally a `SENSOR_GROUP_INFO` tooltip) |
| Restricted | `sensor_field(restricted=...)` | `True` if other cars send zeros when their telemetry is set to Restricted (ERS, tyre wear, damage, fuel, etc.) |
| Presets | `sensor_field(presets=...)` | any of the `SensorPreset` members. `ALL` must always be included. In `DEFAULT` means on by default |
| Manifest key | `SensorConfig(key=...)` | dotted keys form groups in the frontend tree (`tyre_wear.fl` -> Tyre Wear > FL). **On-disk format: never rename once shipped** |
| Unit | `SensorConfig(unit=...)` | `""` for unitless |
| Type | `SensorType` | `CONTINUOUS` (interpolated) or `DISCRETE` (stepped: gear, modes, flags) |

**Optional**

| Info | Notes |
|---|---|
| Range | `(min, max)` with min < max; a viewer axis hint, not enforced |
| Tooltip | `sensor_field(info=...)` |
| Source | packet + field to read it from, plus any transform (e.g. `m_throttle * 100`). Ask whether to hook it up now. If not, the snapshot field stays `None` and the sensor records NaN until wired |

If the user wants it wired, resolve the source in this order and put the chosen expression in the plan:

1. **Tracked by `DataPerDriver` or one of its sub-containers.** Use that tracking. Search `apps/backend/state_mgmt_layer/data_per_driver/` for the datapoint first: `m_lap_info`, `m_tyre_info`, `m_car_info`, `m_pit_info`, `m_driver_info`, etc. Example: tyre wear reads `self.m_tyre_info.tyre_wear.latest`, not the raw damage packet.
2. **Otherwise, in `self.m_packet_copies`.** Read it off the stored packet (`m_packet_car_telemetry`, `m_packet_car_status`, ...), after verifying the field exists in `lib/f1_types/`. Example: throttle reads `car_telemetry_pkt.m_throttle`.
3. **Neither.** Stop and ask the user explicitly how to handle it: add new tracking, derive it from other values, leave it unwired, or something else. Do not invent tracking or reach into other drivers' or session state on your own.

---

## Step 2 — Present plan for approval

Show one table covering every sensor with all the info above, plus the source expression (or "not wired"). Wait for explicit approval.

---

## Step 3 — Implement

Read each file before editing. Keep the field order consistent across the three files, grouped under the same section comments.

### 3a. Config toggle — `lib/config/schema/lap_analyzer.py`

- New group: add the `SensorGroup` member, and a `SENSOR_GROUP_INFO` entry if a tooltip was given.
- Add the field to `LapAnalyzerSensorSettings` under its group comment:

```python
    oil_temp: bool = sensor_field(
        label="Oil Temperature", group=SensorGroup.CAR_STATE, restricted=False,
        presets={SensorPreset.ADVANCED, SensorPreset.ALL},
        info="Engine oil temperature in °C")
```

The default is derived from the presets (on iff `DEFAULT` is included); do not pass one.

### 3b. Snapshot field — `TelemetrySnapshot` in `telemetry_recorder.py`

```python
    oil_temp: Optional[float] = None
```

Use `Optional[int]` for discrete/ordered values (store `.value` of an enum, never the enum itself).

### 3c. Manifest entry — `F1_SENSORS` in `telemetry_recorder.py`

```python
    "oil_temp": RecordedSensor(
        config=SensorConfig(
            key="engine.oil_temp",
            label=_label("oil_temp"),
            unit="°C",
            type=SensorType.CONTINUOUS),
        get=attrgetter("oil_temp")),
```

Always use `_label(field)`; never hardcode the label.

### 3d. (Optional) Wire the source — `CarData.addTelemetrySnapshot` in `apps/backend/state_mgmt_layer/data_per_driver/data_per_driver.py`

Add the kwarg to the `TelemetrySnapshot(...)` call, using the source resolved in Step 1. Either way, a source that isn't available yet must yield `None`, never raise:

```python
            # 1. tracked: read the container, guard for "nothing tracked yet"
            tyre_wear_fl=tyre_wear.fl_tyre_wear if tyre_wear else None,
            # 2. packet copy: guard for the packet not having arrived
            oil_temp=(car_telemetry_pkt.m_engineTemperature if car_telemetry_pkt else None),
```

If the container value or packet copy isn't already pulled into a local at the top of the method, add it there. Derived values that reuse a local (like `ers_store_energy_perc` from `ers_store_energy_j`) compute from the local, not a second lookup. Skip this step if the user chose not to wire it.

---

## Step 4 — Verify

```bash
poetry run pytest tests/tests_config/tests_lap_analyzer_settings.py tests/tests_pngt_session_export.py -n 0 -q
poetry run pylint --rcfile scripts/.pylintrc lib/config/schema/lap_analyzer.py apps/backend/state_mgmt_layer/data_per_driver/telemetry_recorder/telemetry_recorder.py
```

The existing tests already enforce schema <-> `F1_SENSORS` key parity, unique manifest keys, label parity and complete annotations. Do **not** add tests for preset membership (presets are a UI construct). If the sensor joined `DEFAULT`, update `DEFAULT_KEYS` in `tests/tests_pngt_session_export.py` (it holds manifest keys, not field names).

Do not edit `png_config.json`; missing keys are filled with the Pydantic default on startup.

---

## Step 5 — Report

| Field | Label | Group | Restricted | Presets | Key | Unit | Type | Range | Source |
|---|---|---|---|---|---|---|---|---|---|

List anything left unwired so it is visible as follow-up. Do not commit; present the diff for review.
