# F1 26 UDP Protocol Migration Plan

Source: *F1 25 – F1 26 DLC UDP Packages* spec diff.

## NOTE: ALWAYS PROPOSE THE CHANGES TO THE USER, ONCE THEY APPROVE, MAKE THE CHANGES.
NEVER MAKE CHANGES WITHOUT NOTIFYING THE USER!!!!!!!!!!!

Also refer to F1 25 - ``F1 26 DLC UDP Packages.pdf`` for whats changing. If you have any questions, stop and ask

---

## Overview

The 2026 Season Pack DLC introduces a new `m_packetFormat = 2026` (game year 26). The changes fall into five categories, ordered below by implementation risk. The codebase uses format-version branching in several packets, so 2026 support must be threaded through each.

---

## Progress Tracker

- `grep -r "F126-IMPL" lib/ tests/` — all 2026-specific implementation blocks
- `grep -r "F126-CAPTURE" tests/` — capture stubs still awaiting real packet bytes

| Pkt | Name | Phases | Parser | Tests | Impl tag | Capture tag |
|-----|------|--------|--------|-------|----------|-------------|
| 0 | Car Motion Data | 1, 2a, 5b | ✅ | ✅ random · stub actual | `F126-IMPL: PKT0` | `F126-CAPTURE: PKT0` |
| 1 | Session Data | 3b, 5b | ✅ | ✅ stub actual | `F126-IMPL: PKT1` | `F126-CAPTURE: PKT1` |
| 2 | Lap Data | 1 | ✅ | ✅ random · stub actual | `F126-IMPL: PKT2` | `F126-CAPTURE: PKT2` |
| 3 | Event Data (COLL) | 3a, 5b | ✅ | ✅ random · stub actual | `F126-IMPL: PKT3` | `F126-CAPTURE: PKT3` |
| 4 | Participants Data | 1, 2b, 5b | ✅ | ✅ random · stub actual | `F126-IMPL: PKT4` | `F126-CAPTURE: PKT4` |
| 5 | Car Setups | 1 | ✅ | ✅ random · stub actual | `F126-IMPL: PKT5` | `F126-CAPTURE: PKT5` |
| 6 | Car Telemetry | 1 | ✅ | ✅ random · stub actual | `F126-IMPL: PKT6` | `F126-CAPTURE: PKT6` |
| 7 | Car Status | 1, 2c, 5b | ✅ | ✅ random · stub actual | `F126-IMPL: PKT7` | `F126-CAPTURE: PKT7` |
| 8 | Final Classification | 1 | ✅ | ✅ random · stub actual | `F126-IMPL: PKT8` | `F126-CAPTURE: PKT8` |
| 9 | Lobby Info | 1, 2d, 5b | ✅ | ✅ random · stub actual | `F126-IMPL: PKT9` | `F126-CAPTURE: PKT9` |
| 10 | Car Damage | 1 | ✅ | ✅ random · stub actual | `F126-IMPL: PKT10` | `F126-CAPTURE: PKT10` |
| 11 | Session History | N/A | — | — | — | — |
| 12 | Tyre Sets | N/A | — | — | — | — |
| 13 | Motion Ex | N/A | — | — | — | — |
| 14 | Time Trial | 2e, 5b | ✅ | ✅ random · stub actual | `F126-IMPL: PKT14` | `F126-CAPTURE: PKT14` |
| 15 | Lap Positions | 1 (dual struct) | ✅ | ✅ random · stub actual | `F126-IMPL: PKT15` | `F126-CAPTURE: PKT15` |
| 16 | Car Telemetry 2 | 4 (new file) | ✅ | ✅ random · stub actual | `F126-IMPL: PKT16` | `F126-CAPTURE: PKT16` |

---

## Backward Compatibility Requirement

**Existing 2023/2024/2025 test cases must continue to pass without modification.** All 2026 changes must be additive and version-gated. The established pattern in this codebase (see `packet_1_session_data.py`) is:

```python
# Section 5 - F1 24 specific stuff
if header.m_packetFormat == 2024:
    # parse new fields, unpack into self.*
    ...
else:
    # assign zero/None defaults so the attribute always exists
    self.m_newField = 0
```

For F1 26, follow the same pattern: add an `elif header.m_packetFormat >= 2026:` block and an `else:` that zeros out all new attributes. Every attribute introduced for 2026 must be assigned in the `else` branch so that older-format packets produce a complete object.

### Critical: Fixed-Array Count Must Be Version-Gated

For packets where the array count is fixed (not read from a field in the packet) — Packets 0, 2, 4, 5, 6, 7, 10, 15 — simply bumping `MAX_CARS` from 22 to 24 **will break existing test fixtures**: the parser would try to consume 24 × item_len bytes from a 22-car binary blob.

The correct approach:

```python
# Compute the car count for this packet format
num_cars = 24 if header.m_packetFormat >= 2026 else 22

self.m_carData = parse_array(
    data=packet,
    offset=0,
    item_len=SomeCarData.PACKET_LEN,
    count=num_cars,          # version-gated actual count
    max_count=self.MAX_CARS  # MAX_CARS = 24 (global ceiling for validation)
)
```

`MAX_CARS` (set to 24) serves as the validation ceiling in `parse_array`. The actual count passed is derived from the packet format. Variable-count packets (8 and 9, where count comes from `m_numCars` / `m_numPlayers`) are unaffected by this concern.

---

## Phase 1 — Global Car Count: Conditional 22 / 24

**Do not simply change `MAX_CARS = 22` to `MAX_CARS = 24`.** The constant must remain the global ceiling for validation, and the actual count passed to the parser must be derived from `m_packetFormat` at runtime. Blindly hardcoding 24 will cause every pre-2026 packet to be parsed incorrectly (attempting to consume 2 extra cars' worth of bytes from a 22-car binary).

### Introduce a shared helper

Add the following to `lib/f1_types/common.py` (or a new `lib/f1_types/car_count.py`):

```python
MAX_CARS_PRE_2026: int = 22
MAX_CARS_2026: int = 24

def get_num_cars(packet_format: int) -> int:
    """Return the number of cars in fixed-array packets for the given packet format."""
    return MAX_CARS_2026 if packet_format >= 2026 else MAX_CARS_PRE_2026
```

### Update every fixed-array packet's `__init__`

Replace the hardcoded `count=self.MAX_CARS` calls with a version-gated value:

```python
num_cars = get_num_cars(header.m_packetFormat)
self.m_carData = parse_array(
    data=packet,
    offset=0,
    item_len=SomeData.PACKET_LEN,
    count=num_cars,           # actual count for this format
    max_count=MAX_CARS_2026,  # global ceiling
)
```

### Files to update

| File | Constant | Change |
|------|----------|--------|
| `apps/backend/state_mgmt_layer/session_state.py:301` | `MAX_DRIVERS = 22` | Change to 24 — this sizes the list, not binary parsing; pre-2026 will just leave slots 22–23 as `None` |
| `lib/f1_types/packet_0_car_motion_data.py:309` | `MAX_CARS = 22` | Set to 24; gate `count=` on `get_num_cars(header.m_packetFormat)` |
| `lib/f1_types/packet_2_lap_data.py:558` | `MAX_CARS = 22` | Same |
| `lib/f1_types/packet_4_participants_data.py:563` | `MAX_PARTICIPANTS = 22` | Same |
| `lib/f1_types/packet_5_car_setups_data.py:525` | `MAX_CARS = 22` | Same |
| `lib/f1_types/packet_6_car_telemetry_data.py:380` | `MAX_CARS = 22` | Same |
| `lib/f1_types/packet_7_car_status_data.py:542` | `MAX_CARS = 22` | Same |
| `lib/f1_types/packet_8_final_classification_data.py:588` | `MAX_CARS = 22` | Set to 24; uses `max_count=` only — no parse-count risk |
| `lib/f1_types/packet_9_lobby_info_data.py:360` | `MAX_PLAYERS = 22` | Set to 24; uses `max_count=` only — no parse-count risk |
| `lib/f1_types/packet_10_car_damage_data.py:527` | `MAX_CARS = 22` | Set to 24; gate `count=` on `get_num_cars(header.m_packetFormat)` |

### Tests

Each test file follows the two-test pattern used throughout the codebase: a **random roundtrip test** (generates data with `from_values()`, serialises, re-parses, and asserts equality) and an **actual game data test** (parses a hardcoded binary blob against a known-good JSON). For 2026:

- **`test_f1_26_random`** — Write now; must pass once the parser and `from_values()` / `to_bytes()` are implemented for 2026. In `setUp`, add `m_header_26 = F1TypesTest.getRandomHeader(F1PacketType.XXX, 26, self.m_num_players)` with `m_num_players = random.randint(1, 24)`. The test generates 24 cars, calls `from_values()`, `to_bytes()`, re-parses, and calls `assertEqual` + `jsonComparisionUtil`.
- **`test_f1_26_actual`** — Stub only; comment out the fixture bytes and expected JSON. Use `self.skipTest("awaiting 2026 capture")` as the placeholder body. Fill in once real game packets are captured.

| Test file | Array field to assert length == 24 |
|-----------|-------------------------------------|
| `tests/f1_types/tests_packet_0_car_motion_data.py` | `m_carMotionData` |
| `tests/f1_types/tests_packet_2_lap_data.py` | `m_lapData` |
| `tests/f1_types/tests_packet_4_participants_data.py` | `m_participants` |
| `tests/f1_types/tests_packet_5_car_setups_data.py` | `m_carSetups` |
| `tests/f1_types/tests_packet_6_car_telemetry_data.py` | `m_carTelemetryData` |
| `tests/f1_types/tests_packet_7_status_data.py` | `m_carStatusData` |
| `tests/f1_types/tests_packet_10_car_damage_data.py` | `m_carDamageData` |

Regression guard: do not modify the existing `23_24_25` random or actual tests; they must continue to pass and will still exercise 22-car arrays.

### Packet 15 special case (`packet_15_lap_positions_data.py:44`)

`COMPILED_PACKET_STRUCT_ARRAY = struct.Struct(f"<{MAX_CARS * MAX_LAPS}B")` is evaluated **at class load time**, not per-packet. This means the struct is permanently baked in as 22 × 50 = 1100 bytes on import. Setting `MAX_CARS = 24` would bake in 1200 bytes and immediately break all pre-2026 parsing.

Options:
1. Keep `MAX_CARS = 22` as a legacy class constant and add `MAX_CARS_2026 = 24` alongside it; build a second struct `COMPILED_PACKET_STRUCT_ARRAY_2026` for the 2026 case and select between them in `__init__` based on `header.m_packetFormat`.
2. Remove the class-level struct entirely and build it dynamically in `__init__` using `get_num_cars()`.

Option 1 is more consistent with the rest of the codebase.

### Tests (Packet 15)

Same two-test pattern:

- **`test_f1_26_random`** — Generate 24 lap-position entries via `from_values()`, serialise with `COMPILED_PACKET_STRUCT_ARRAY_2026`, re-parse, and `assertEqual`. Must pass once implementation is done.
- **`test_f1_26_actual`** — Stub; comment out fixture bytes + expected JSON; body: `self.skipTest("awaiting 2026 capture")`.

**Packet size changes from this phase alone:**

| Packet | Old size | New size | Delta |
|--------|----------|----------|-------|
| Lap Data (2) | 1285 B | 1399 B | +114 |
| Car Setups (5) | 1133 B | 1233 B | +100 |
| Car Telemetry (6) | 1352 B | 1448 B | +96 |
| Final Classification (8) | 1042 B | 1134 B | +92 |
| Lobby Info (9) | 954 B | 1062 B | +108 |
| Car Damage (10) | 1041 B | 1133 B | +92 |
| Lap Positions (15) | 1131 B | 1231 B | +100 |

---

## Phase 2 — Struct Field Type Changes (Binary Breaking)

These change the per-car struct layout, so they affect binary parsing correctness directly.

### 2a. Motion Data — G-Force Quantization (`packet_0_car_motion_data.py`)

**Spec:** `m_gForceLateral`, `m_gForceLongitudinal`, `m_gForceVertical` change from `float` → `int16`. Divide raw value by `1000.0` to get actual G-force.

**Current struct** (`CarMotionData`, ~lines 59–78):
```
"f"  m_gForceLateral       # 4 bytes
"f"  m_gForceLongitudinal  # 4 bytes
"f"  m_gForceVertical      # 4 bytes
```

**Change to** (for `m_packetFormat == 2026`):
```
"h"  m_gForceLateral       # 2 bytes  ÷ 1000.0
"h"  m_gForceLongitudinal  # 2 bytes  ÷ 1000.0
"h"  m_gForceVertical      # 2 bytes  ÷ 1000.0
```

- Saves 6 bytes per car × 24 cars = 144 bytes (packet shrinks from 1349 → 1325 B, -24 B per spec — note spec figure is for 22 cars; actual will differ at 24).
- The unpack path and any downstream consumers of these three fields (HUD, frontend dashboards) must divide by 1000.0.
- Search for callers: `m_gForceLateral`, `m_gForceLongitudinal`, `m_gForceVertical` across `apps/`.

**Approach:** Add a format-gated `COMPILED_PACKET_STRUCT_2026` alongside the existing struct, similar to how `packet_4_participants_data.py` already handles multi-format structs.

**Tests (`tests/f1_types/tests_packet_0_car_motion_data.py`):**

Same two-test pattern (extends Phase 1 — the 2026 random test covers both 24-car count and int16 g-force):

- **`test_f1_26_random`** — Generate 24 `CarMotionData` objects via `_generateRandomCarMotionData()` (g-force values are random floats in the ±32.767 range to stay within int16 after ÷1000 scaling), serialize with 2026 struct, re-parse, `assertEqual`. Verify `m_gForceLateral/Longitudinal/Vertical` round-trip correctly through int16 quantization.
- **`test_f1_26_actual`** — Stub; comment out fixture + expected JSON; body: `self.skipTest("awaiting 2026 capture")`.

### 2b. Participants Data — ID Fields 8-bit → 16-bit (`packet_4_participants_data.py`)

**Spec:** `m_driverId`, `m_networkId`, `m_teamId` expand from `uint8` → `uint16`.

**Current struct** (F1 25, ~lines 160–176):
```
"B"  m_driverId    # uint8  → needs "H" (uint16)
"B"  m_networkId   # uint8  → needs "H" (uint16)
"B"  m_teamId      # uint8  → needs "H" (uint16)
```

- +3 bytes per participant × 24 = +72 bytes (packet grows 1284 → 1470 B, +186 B per spec).
- `m_teamId` is cast to a `TeamID` enum at parse time — check if existing `TeamID25` covers the extended range or if a new `TeamID26` is needed in `lib/f1_types/common.py`.
- `m_driverId` and `m_networkId` are exposed in the JSON API — no frontend type changes expected (already treated as ints), but worth verifying.
- This file already has `COMPILED_PACKET_STRUCT_23_BASE`, `COMPILED_PACKET_STRUCT_24_BASE`, `COMPILED_PACKET_STRUCT_25_BASE` — add `COMPILED_PACKET_STRUCT_26_BASE` following the same pattern.

**Array size also changes**: `ParticipantData[22]` → `[24]` (covered by Phase 1).
**Packet size change:** 1284 → 1470 B (+186 B).

**Tests (`tests/f1_types/tests_packet_4_participants_data.py`):**

Same two-test pattern (covers both 24-car count and uint16 ID fields):

- **`test_f1_26_random`** — Generate 24 `ParticipantData` objects via `from_values()` using uint16-range random values for `m_driverId`, `m_networkId`, `m_teamId` (0–65535). Serialize, re-parse, `assertEqual` + `jsonComparisionUtil`.
- **`test_f1_26_actual`** — Stub; `self.skipTest("awaiting 2026 capture")`.

### 2c. Car Status — New Field (`packet_7_car_status_data.py`)

**Spec:** New field `m_ersHarvestLimitPerLap` (`float`) added to `CarStatusData`.

**Current struct** (~lines 74–111), current last fields:
```
"f"  m_ersDeployedThisLap
"B"  m_networkPaused        # currently last field
```

**Change:** Insert `"f" m_ersHarvestLimitPerLap` before `m_networkPaused` (position TBD — verify against actual 2026 packet captures). +4 bytes per car × 24 = +96 bytes.

- Update `__slots__`, the unpack assignment, `toJSON()`, and `__str__()`.
- Packet size change: 1239 → 1445 B (+206 B). The extra +110 B beyond the +96 from the new field is explained by the car count increase (22 → 24, ×81 bytes existing struct = +162 B; combined with new field ×24 = +96 B minus the size-22 baseline, the net lands at +206 B as per spec). Verify arithmetic once exact field position is confirmed.

**Tests (`tests/f1_types/tests_packet_7_status_data.py`):**

Same two-test pattern (covers 24-car count + new ERS field):

- **`test_f1_26_random`** — Generate 24 `CarStatusData` objects via `from_values()` including a random float for `m_ersHarvestLimitPerLap`. Serialize, re-parse, `assertEqual` + `jsonComparisionUtil`.
- **`test_f1_26_actual`** — Stub; `self.skipTest("awaiting 2026 capture")`.
- Existing `23_24_25` random test: no change needed; `m_ersHarvestLimitPerLap` will default to `0.0` in the else-branch so equality still holds.

### 2d. Lobby Info — `m_teamId` 8-bit → 16-bit (`packet_9_lobby_info_data.py`)

**Spec:** `m_teamId` in `LobbyInfoData` expands `uint8` → `uint16`.

- Existing code has format-branched structs for 2023/2024/2025. Add a 2026 branch.
- `m_lobbyPlayers[]` array also grows from 22 → 24 (Phase 1).
- Packet size change: 954 → 1062 B (+108 B).

**Tests (`tests/f1_types/tests_packet_9_lobby_info_data.py`):**

Same two-test pattern (covers 24-car count + uint16 teamId):

- **`test_f1_26_random`** — Generate 24 `LobbyInfoData` objects via `from_values()` using a uint16-range random value for `m_teamId`. Serialize, re-parse, `assertEqual` + `jsonComparisionUtil`.
- **`test_f1_26_actual`** — Stub; `self.skipTest("awaiting 2026 capture")`.

### 2e. Time Trial — `m_teamId` 8-bit → 16-bit (`packet_14_time_trial_data.py`)

**Spec:** `m_teamId` inside `TimeTrialDataSet` expands `uint8` → `uint16`.

**Current struct** (~lines 50–62):
```
"B"  m_teamId    # uint8 → "H" uint16
```

**Current format gate** (~lines 122–125):
```python
if packet_format < 2025:
    self.m_teamId = TeamID24.safeCast(self.m_teamId)
else:
    self.m_teamId = TeamID25.safeCast(self.m_teamId)
```

Add a `packet_format == 2026` branch. The struct is not duplicated per-format here — add a new `COMPILED_PACKET_STRUCT_2026` or gate field extraction inline.
Packet size change: 101 → 104 B (+3 B).

**Tests (`tests/f1_types/tests_packet_14_time_trial_data.py`):**

Same two-test pattern:

- **`test_f1_26_random`** — Generate `TimeTrialDataSet` objects via `from_values()` with uint16-range random values for `m_teamId` in all three data sets (`m_playerSession`, `m_rivalSession`, `m_personalBest`). Serialize, re-parse, `assertEqual` + `jsonComparisionUtil`.
- **`test_f1_26_actual`** — Stub; `self.skipTest("awaiting 2026 capture")`.

---

## Phase 3 — Existing Packet Structural Additions

### 3a. Event Data — Collision Severity (`packet_3_event_data.py`)

**Spec:** New `severity` field (`uint8`) added to the Collision event struct.
Values: `0 = Low`, `1 = Medium`, `2 = High`.

**Current `Collision` struct** (~lines 1407–1420):
```python
COMPILED_PACKET_STRUCT = struct.Struct("<BB")   # vehicle1Idx, vehicle2Idx
```

**Change to** (for `packet_format == 2026`):
```python
COMPILED_PACKET_STRUCT_2026 = struct.Struct("<BBB")  # + severity
```

- The event union is discriminated by a 4-char event string code. Collision events are `"COLL"`. The struct swap must be gated on `packet_format`.
- No packet-level size change (union sizing has enough padding — per spec: 45 → 45 B, no net change).
- Add `m_severity` to `__slots__`, unpack, `toJSON()`, `__str__()`.

**Tests (`tests/f1_types/tests_packet_3_event_data.py`):**

Same two-test pattern for the COLL event:

- **`test_f1_26_random` (COLL)** — Construct a `Collision` object via `from_values()` with random `vehicle1Idx`, `vehicle2Idx`, and `severity` (0–2). Serialize the full event packet, re-parse, `assertEqual`. Must pass once implementation is done.
- **`test_f1_26_actual` (COLL)** — Stub; `self.skipTest("awaiting 2026 capture")`. Note: capturing a COLL event requires triggering an on-track collision during a 2026-format session (see Packet Capture Checklist).
- Existing COLL tests: no change. `m_severity` will default to `0` in the else-branch so existing equality checks hold.

### 3b. Session Data — Active Aero, DRS Zones, Accessibility (`packet_1_session_data.py`)

**This is the most heavily modified packet** (753 → 926 B, +173 B).

**New structs needed:**
```
ActiveAeroZone { float m_zoneStart; float m_zoneEnd; }   # 8 bytes each
DRSZone        { float m_zoneStart; float m_zoneEnd; }   # 8 bytes each
```

**New fields appended to `PacketSessionData`:**

| Field | Type | Notes |
|-------|------|-------|
| `m_activeAeroTrackStatus` | uint8 | 0=Full Aero, 1=Partial Aero |
| `m_numActiveAeroZonesFull` | uint8 | Count for full mode |
| `m_activeAeroZonesFull[]` | ActiveAeroZone[8] | 64 bytes fixed array |
| `m_numActiveAeroZonesPartial` | uint8 | Count for partial mode |
| `m_activeAeroZonesPartial[]` | ActiveAeroZone[8] | 64 bytes fixed array |
| `m_numDRSZones` | uint8 | Max 4 |
| `m_drsZones[]` | DRSZone[4] | 32 bytes fixed array |
| `m_startReactionTime` | float | 0.0 if driving-assist |
| `m_antiLockBrakesAssist` | uint8 | |
| `m_tractionControlAssist` | uint8 | 0=Off, 1=Medium, 2=Full |
| `m_dynamicRacingLineHiVis` | uint8 | |
| `m_dynamicRacingLineColourBlind` | uint8 | |
| `m_recurringRewindPrompt` | uint8 | |

The existing session packet is already parsed in sections (SECTION_0 through SECTION_5) with constants for offsets. Add a `SECTION_6` (or extend SECTION_5) gated on `packet_format == 2026`.

The `cs_maxActiveAeroZonesPerLap = 8` and `cs_maxDRSZonesPerLap = 4` constants should be added alongside existing max constants (~line 526).

**Also:** Formula enum gains value `13 = F1 26`. Add to the `Formula` enum in `lib/f1_types/common.py` (or wherever it is defined in this file).

**Tests (`tests/f1_types/tests_packet_1_session_data.py`):**

Same two-test pattern:

- **`test_f1_26_random`** — Construct a `PacketSessionData` object via `from_values()` supplying random values for all new 2026 fields (`m_activeAeroTrackStatus`, `m_numActiveAeroZonesFull`, `m_activeAeroZonesFull[8]`, `m_numActiveAeroZonesPartial`, `m_activeAeroZonesPartial[8]`, `m_numDRSZones`, `m_drsZones[4]`, `m_startReactionTime`, and the accessibility flags). Serialize, re-parse, `assertEqual` + `jsonComparisionUtil`. Must pass once implementation is done.
- **`test_f1_26_actual`** — Stub; `self.skipTest("awaiting 2026 capture")`. This is the most complex actual test; the full 173-byte extension means the binary fixture is large — capture it from the game's first session packet.
- Existing `23_24_25` tests: no change. All new 2026 fields will default to `0`/`None` in the else-branch.

---

## Phase 4 — New Packet: Car Telemetry 2 (Packet ID 16)

**Spec:** New `ePacketIdCarTelemetry2`, packet ID 16. Total size: 269 bytes.

**Struct: `CarTelemetry2Data`** (per car):

| Field | Type | Description |
|-------|------|-------------|
| `m_activeAeroMode` | uint8 | 0=Corner Mode, 1=Straight Mode |
| `m_activeAeroAvailable` | uint8 | 0=Not Available, 1=Available |
| `m_activeAeroActivationDistance` | uint16 | Distance (m) until Active Aero |
| `m_overtakeAvailable` | uint8 | 0=Not Available, 1=Available |
| `m_overtakeActive` | uint8 | 0=Not Active, 1=Active |
| `m_overtakeActivationDistance` | uint16 | Distance (m) until Overtake Mode |
| `m_2026Regulations` | uint8 | 0=Pre-2026, 1=2026 Regulations |
| `m_drivingWrongWay` | uint8 | 0=Correct Way, 1=Wrong Way |

Array: `m_carTelemetry2Data[24]`.
Per-car struct size: 10 bytes. 24 × 10 + 29 (header) = 269 B ✓

**Files to create/modify:**

1. **Create** `lib/f1_types/packet_16_car_telemetry2_data.py`
   - Follow the pattern of `packet_6_car_telemetry_data.py` for structure.
   - Classes: `CarTelemetry2Data` (per-car), `PacketCarTelemetry2Data` (packet wrapper).

2. **`lib/f1_types/__init__.py`**
   - Add import: `from .packet_16_car_telemetry2_data import CarTelemetry2Data, PacketCarTelemetry2Data`
   - Add to `__all__`.

3. **`lib/f1_types/header.py`** (F1PacketType enum, ~line 49)
   - Add: `CAR_TELEMETRY_2 = 16`

4. **`lib/telemetry_manager/factory.py`**
   - Add import of `PacketCarTelemetry2Data`.
   - Add to `_PACKET_TYPE_MAP`: `F1PacketType.CAR_TELEMETRY_2: PacketCarTelemetry2Data`

5. **`apps/backend/state_mgmt_layer/session_state.py`**
   - Decide whether to store `PacketCarTelemetry2Data` in `SessionState` and expose it via the WebSocket/REST API.
   - If so, add to `__slots__`, initialise in `__init__`, clear in `_clearAllData`, handle in the appropriate `onXxx` callback.

6. **`apps/backend/intf_layer/`**
   - If the data is to be pushed to browser clients, add it to the Socket.IO broadcast payload.

### Tests (new file `tests/f1_types/tests_packet_16_car_telemetry2_data.py`)

Create the file following the structure of `tests_packet_6_car_telemetry_data.py`.

- **`setUp`** — Add `m_header_26 = F1TypesTest.getRandomHeader(F1PacketType.CAR_TELEMETRY_2, 26, self.m_num_players)` with `m_num_players = random.randint(1, 24)`. Comment out `m_packet_26` and `m_expected_json_26` stubs for later.
- **`test_f1_26_random`** — Generate 24 `CarTelemetry2Data` objects via `CarTelemetry2Data.from_values()` with random values for all 8 fields. Serialize, re-parse, `assertEqual` + `jsonComparisionUtil`. Must pass once implementation is done.
- **`test_f1_26_actual`** — Stub; `self.skipTest("awaiting 2026 capture")`. This packet is brand-new and only exists in 2026 sessions — confirm it arrives at all in the capture session.

---

## Phase 5 — Packet Format Version Gating

### 5a. Parser minimum format (`lib/telemetry_manager/factory.py:66`)

```python
_MIN_PACKET_FORMAT = 2023   # currently
```

No change needed — 2026 > 2023, so 2026 packets will already pass the gate. However, all format-specific branches in the packet files (see below) must explicitly handle 2026.

### 5b. Per-packet format branches

These files currently have `if packet_format == 2023/2024/2025` or `>= 2025` logic that must be extended:

| File | Location | What to add |
|------|----------|-------------|
| `packet_4_participants_data.py` | ~lines 211–274 | `2026` branch with new `uint16` ID fields |
| `packet_9_lobby_info_data.py` | ~lines 124–154 | `2026` branch with `uint16` teamId |
| `packet_14_time_trial_data.py` | ~lines 122–125 | `2026` branch for `uint16` teamId cast |
| `packet_3_event_data.py` | line 247 | Collision: gate `severity` parse on `>= 2026` |
| `packet_0_car_motion_data.py` | unpack path | Gate int16 g-force quantization on `>= 2026` |
| `packet_7_car_status_data.py` | unpack path | Gate new `m_ersHarvestLimitPerLap` on `>= 2026` |
| `packet_1_session_data.py` | section parsing | Gate new Active Aero/DRS fields on `>= 2026` |

---

## Phase 6 — Tests (Summary)

### Strategy

Each implementation phase above includes its own **Tests** subsection. Tests are written alongside the parser — not deferred to the end. The two-test pattern used throughout the codebase is:

1. **Random roundtrip test** (`test_f1_26_random`) — Generate data programmatically via `from_values()`, serialize with `to_bytes()`, re-parse, and assert equality with `assertEqual` + `jsonComparisionUtil`. Write now; must pass once the corresponding parser and `from_values()` / `to_bytes()` are implemented. No real game capture needed.

2. **Actual game data test** (`test_f1_26_actual`) — Parses a hardcoded binary blob captured from the live game against a known-good expected JSON. **Stub only for now**: comment out `m_packet_26` / `m_expected_json_26` in `setUp`; use `self.skipTest("awaiting 2026 capture")` as the method body. Fill in once captures are available (see Packet Capture Checklist).

Do **not** modify existing `23_24_25` fixtures or test methods. They must pass unchanged.

### Affected test files

| Test file | Why affected | Random test | Actual test |
|-----------|-------------|-------------|-------------|
| `tests/f1_types/tests_packet_0_car_motion_data.py` | g-force int16 + 24 cars | Write + must pass | Stub |
| `tests/f1_types/tests_packet_1_session_data.py` | New Active Aero/DRS fields | Write + must pass | Stub |
| `tests/f1_types/tests_packet_2_lap_data.py` | 24 cars | Write + must pass | Stub |
| `tests/f1_types/tests_packet_3_event_data.py` | Collision severity field | Write + must pass | Stub |
| `tests/f1_types/tests_packet_4_participants_data.py` | uint16 IDs + 24 cars | Write + must pass | Stub |
| `tests/f1_types/tests_packet_5_car_setups_data.py` | 24 cars | Write + must pass | Stub |
| `tests/f1_types/tests_packet_6_car_telemetry_data.py` | 24 cars | Write + must pass | Stub |
| `tests/f1_types/tests_packet_7_status_data.py` | New ERS field + 24 cars | Write + must pass | Stub |
| `tests/f1_types/tests_packet_9_lobby_info_data.py` | uint16 teamId + 24 cars | Write + must pass | Stub |
| `tests/f1_types/tests_packet_10_car_damage_data.py` | 24 cars | Write + must pass | Stub |
| `tests/f1_types/tests_packet_14_time_trial_data.py` | uint16 teamId | Write + must pass | Stub |
| `tests/f1_types/tests_packet_15_lap_positions_data.py` | 24 cars (dual struct) | Write + must pass | Stub |
| `tests/f1_types/` (new file) | New Packet 16 | Write + must pass | Stub |

---

## Packet Capture Checklist

Every 2026 test fixture requires a raw binary blob captured from the live game. The capture pattern used in this codebase is to print/log `data` as a Python `bytes` literal and paste it into the test file.

### Where to set the breakpoint

**Primary capture point — `lib/telemetry_manager/factory.py`, inside `parse()`, just before the parser class is instantiated (~line 115).**

At that point `header` (with `m_packetFormat` and `m_packetId`) and `data` (raw payload bytes, header already stripped) are both in scope. Add a temporary debug statement, gate on format + packet ID:

```python
# Temporary capture helper — remove before committing
if header.m_packetFormat == 2026:
    import sys
    print(f"PKT {header.m_packetId}: {data!r}", file=sys.stderr)
```

Run the game, trigger a session, then collect the printed lines. Each line is the fixture for one packet type.

### Packets requiring a capture session

| Packet ID | Class | Trigger condition | Notes |
|-----------|-------|-----------------|-------|
| 0 | `PacketMotionData` | Any session with movement | Needed because g-force struct changes |
| 1 | `PacketSessionData` | Enter a session | Needed for new Active Aero/DRS fields |
| 2 | `PacketLapData` | Any session in progress | 24-car array |
| 3 | `PacketEventData` (COLL) | Two-car collision | Needs `severity` field; gate capture on event code `== b"COLL"` — add a secondary condition in the capture helper or break inside `Collision.__init__` |
| 4 | `PacketParticipantsData` | Any multiplayer or 24-car grid | 24-car array + uint16 IDs |
| 5 | `PacketCarSetupData` | Pre-session setup screen | 24-car array |
| 6 | `PacketCarTelemetryData` | Any session with movement | 24-car array |
| 7 | `PacketCarStatusData` | Any session in progress | New ERS field + 24-car array |
| 8 | `PacketFinalClassificationData` | End of race | 24-car array |
| 9 | `PacketLobbyInfoData` | Multiplayer lobby | uint16 teamId + 24-car array |
| 10 | `PacketCarDamageData` | Any session | 24-car array |
| 14 | `PacketTimeTrialData` | Time trial mode | uint16 teamId |
| 15 | `PacketLapPositionsData` | Race in progress | 24-car array |
| 16 | `PacketCarTelemetry2Data` | Any session (2026 regs) | Brand-new packet; confirm it arrives at all |

### Special case: Event COLL capture

The event packet's payload is a union; the COLL struct occupies only the first 3 bytes of it. Add a secondary capture point inside `Collision.__init__` in `packet_3_event_data.py` when `m_packetFormat >= 2026`, or post-filter the factory output by checking the 4-byte event code at the start of `data`.

---

## Out of Scope (No Changes Needed)

| Packet | Reason |
|--------|--------|
| Session History (11) | Single-car indexed via `m_carIdx` |
| Tyre Sets (12) | Single-car indexed |
| Motion Ex (13) | Single player car only |

---

## Unchanged Packet Sizes Reference

Packets whose sizes remain the same in F1 26 despite car count changes (useful for validation):

| Packet | Size |
|--------|------|
| Session History (11) | 1460 B |
| Tyre Sets (12) | 231 B |
| Motion Ex (13) | 273 B |

---

## Frontend & HUD — Deferred Evaluation

The following subsystems consume parsed packet data and will likely need changes, but a full audit is deferred until the backend parser changes are complete.

### Frontend (`apps/frontend/`)

Areas to evaluate once backend changes are merged:

- **Timing tower / standings**: any table or list capped at 22 rows needs to support up to 24.
- **G-force display**: if any dashboard panel renders `m_gForceLateral/Longitudinal/Vertical`, the values will now arrive pre-scaled (already divided by 1000.0 in the parser), so this may be a no-op. Verify no second division is happening in JS.
- **Active Aero / Overtake Mode (new)**: decide whether to surface `PacketCarTelemetry2Data` fields (`m_activeAeroMode`, `m_activeAeroAvailable`, `m_overtakeActive`, etc.) in any panel.
- **Participant IDs**: `m_driverId`, `m_networkId`, `m_teamId` expand to uint16. Check any JS that casts these to uint8 or uses them as array indices into a 255-element lookup.
- **ERS panel**: `m_ersHarvestLimitPerLap` is a new float on `CarStatusData`. Evaluate whether to display it.
- **Session info panel**: new Active Aero zone map, DRS zones, and accessibility flags arrive in `PacketSessionData`.

### HUD (`apps/hud/`)

Areas to evaluate:

- **Driver list overlays**: any QML/widget that iterates over drivers and is hardcoded to 22 entries needs to handle up to 24.
- **G-force widget** (if present): same scaling concern as frontend — confirm no double-division.
- **Tyre/ERS status overlay**: `m_ersHarvestLimitPerLap` may be relevant.
- **Active Aero indicator**: `PacketCarTelemetry2Data.m_activeAeroMode` / `m_activeAeroAvailable` could drive a new in-game widget.

---

## Recommended Implementation Order

```
Phase 1  →  Phase 5b (format gates skeleton)
         →  Phase 2a, 2b, 2c, 2d, 2e (struct fixes, each independently testable)
         →  Phase 3a (event collision)
         →  Phase 3b (session — most complex, save for last among existing packets)
         →  Phase 4 (new packet 16 — fully additive, no risk to existing parsing)
         →  Phase 6 (tests — update fixtures throughout, run full suite)
```

Each phase can be a separate PR. Phases 2a–2e are independent of each other and can be parallelised.
