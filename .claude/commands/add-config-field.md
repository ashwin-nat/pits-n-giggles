---
description: Add a new config field with Pydantic validation, subsystem wiring, and tests
allowed-tools: Read, Glob, Grep, Edit, Write, TodoWrite
---

Add one or more config fields end-to-end: Pydantic schema, subsystem `on_settings_change` wiring, and unit tests.

> **Note:** Do NOT edit `png_config.json`. The app detects missing keys on startup and inserts the Pydantic default automatically.

**Present the full group of fields as a single plan for approval before writing any code. Do not implement field by field — batch all fields into one plan, get one approval, then implement all together.**

---

## Step 1 — Present plan for approval

Before any edits, show the user a single consolidated plan covering **all fields** being added. For each field, include:

1. **Field identity**: name, type, parent section (e.g. `Network`, `HUD`, `Capture`)
2. **Validation**: Pydantic constraints (`ge`, `le`, `pattern`, etc.) and any cross-section validators needed
3. **Subsystems interested**: which subsystem managers need to handle the change in `on_settings_change`, and whether the change is **catastrophic** (restart) or **live** (runtime update)
4. **Display strings**: The label shown in the settings UI and optionally a tooltip string

Present all fields in a table or grouped list. Wait for explicit approval before proceeding.

---

## Step 2 — Implement

Work through these in order. Read each file before editing.

### 2a. Add the field — `lib/config/schema/<section>.py`

Read the file. Add the field using the appropriate factory if one fits:
- `port_field(description, default, port_type)` — TCP/UDP ports
- `udp_action_field(description)` — bounded [1–12], optional
- `ui_scale_field(description)` — bounded [0.5–2.0], slider
- `overlay_enable_field(description, group)` — bool with overlay grouping

Otherwise use a plain `Field(default=..., description=..., json_schema_extra={"ui": {...}})`.

Add `@field_validator` or `@model_validator` if the field needs intra-section validation.

If the field requires a cross-section constraint (e.g. uniqueness with another section's field), add a `@model_validator(mode="after")` to `lib/config/schema/png.py`.

A rule between fields (a `@model_validator`, or `model_post_init`) must raise `ConflictError` from `lib/config/schema/utils.py`, naming **every** field it involves (paths relative to the model: `"udp_custom_action_code"`, `"pages.lap_times"`, `"Network.server_port"`). On load, the config loader resets exactly those fields to their defaults, so a hand-edited or upgraded config never fails to load. Use `PortConflictError` / `UdpActionCodeConflictError` for port and UDP code clashes. A plain `ValueError` from a rule can't be repaired: the loader falls back to the whole section. New `port_field` / `udp_action_field` fields join the existing uniqueness checks automatically.

### 2b. Wire into subsystem managers

For each subsystem in the approved plan, read the file and add the field to the appropriate diff block in `on_settings_change`:

- **Catastrophic** (needs restart): add field name to the `settings_requiring_restart` diff dict under its section key
- **Live** (runtime update): add field name to the live-update diff dict and add handling logic

Subsystem manager files:
- `apps/launcher/subsystems/backend_mgr.py`
- `apps/launcher/subsystems/hud_mgr/hud_mgr.py`
- `apps/launcher/subsystems/broker_mgr.py`
- `apps/launcher/subsystems/web_mgr.py`
- `apps/launcher/subsystems/mcp_mgr.py`

---

## Step 3 — Tests

Read `tests/README.md` for how to run tests, and its "Config Field Constraints" section.

**Field constraints:** add the field to `FIELDS` in `tests/tests_config/tests_config_properties.py`, one entry with the bounds from the approved plan (e.g. `IntRange(1, 120)`, `Choice(MyEnum, ("A", "B"))`). This covers valid values, invalid values, and the boundaries. Do not write per-field boundary tests. If no spec kind fits (custom string validator, `FilePathStr`, id-keyed dict), add the field to `EXAMPLE_ONLY` and write example tests for it instead. A required field with no default also needs a `REQUIRED` entry.

**Section test file:** find the section's file in `tests/tests_config/`. If one exists, add to it. Otherwise create `tests/tests_config/tests_<section>_settings.py` in native pytest style (see `tests/README.md`). Cover:
- Default value is correct (in `test_default_values`; the HUD's `_DEFAULTS` must name every HUD scalar field, so a new HUD field fails that test until it is added)
- Example tests for `EXAMPLE_ONLY` fields
- Cross-section constraint raises `ValidationError` (if applicable)

**New rule between fields:** add a case to `_BROKEN_RULES` in `tests/tests_config/tests_config_io.py`. It is a file breaking the rule, the values every involved field must reset to, and a value elsewhere that must survive the load.

---

## Step 4 — Verify

Run the unit tests per `tests/README.md` and confirm they pass.

---

## Step 5 — Report

Present a short summary covering all fields added:

**Fields table** (one row per field)

| Field | Section | Type | Default | Constraints | Subsystems |
|---|---|---|---|---|---|
| `field_name` | `SectionName` | `int / bool / str` | value | description | subsystem (restart/live) |

**Tests table**

| Test name | Description |
|---|---|
| `FIELDS[...]["field_name"]` | spec, e.g. `IntRange(1, 120)` |
| `test_...` | one line |
