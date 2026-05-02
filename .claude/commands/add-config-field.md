---
description: Add a new config field to png_config.json with Pydantic validation, subsystem wiring, and tests
allowed-tools: Read, Glob, Grep, Edit, Write, TodoWrite
---

Add one or more config fields end-to-end: Pydantic schema, JSON defaults, subsystem `on_settings_change` wiring, and unit tests.

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

### 2b. Add default to `png_config.json`

Read the file. Insert the field under the correct section key with its default value.

### 2c. Wire into subsystem managers

For each subsystem in the approved plan, read the file and add the field to the appropriate diff block in `on_settings_change`:

- **Catastrophic** (needs restart): add field name to the `settings_requiring_restart` diff dict under its section key
- **Live** (runtime update): add field name to the live-update diff dict and add handling logic

Subsystem manager files:
- `apps/launcher/subsystems/backend_mgr.py`
- `apps/launcher/subsystems/hud_mgr/hud_mgr.py`
- `apps/launcher/subsystems/broker_mgr.py`
- `apps/launcher/subsystems/save_viewer_mgr.py`
- `apps/launcher/subsystems/mcp_mgr.py`

---

## Step 3 — Tests

Read `tests/README.md` for instructions on how to run
Read `tests/tests_config/` to find the right test file for the section. If one exists, add to it. Otherwise create `tests/tests_config/tests_<section>_settings.py` following the base class pattern from `tests/tests_config/tests_config_base.py`.

Write tests covering:
- Default value is correct
- Valid boundary values accepted
- Invalid values raise `ValidationError`
- Cross-section constraint raises `ValidationError` (if applicable)

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
| `test_...` | one line |
