---
description: Scaffold a new HUD overlay widget in apps/hud/ui/overlays/ with full wiring
allowed-tools: Read, Glob, Grep, Edit, Write
---

Scaffold a new HUD overlay and wire it end-to-end. Read each target file before editing it, and mirror the nearest existing overlay rather than the snippets here, which only name the touch points.

## Overlay types

Ask the user which type they want unless it is obvious (e.g. "same as the pit rejoin overlay" means A).

- **A. MFD page** - `MfdPageBase` subclass in `apps/hud/ui/overlays/mfd/pages/<name>/`. Event-driven only (no `render_frame`). Appears in the MFD carousel and can also run as a standalone window via `StandalonePageHost`. Use for data pages and tables.
- **B. Generic standalone overlay** - `BaseOverlay` subclass in `apps/hud/ui/overlays/<name>/`. Use for everything else (track radar, input telemetry, high-frequency `render_frame` overlays).

Inputs: snake_case name, PascalCase class name, display title, and the events it listens to (B also: event-driven vs high-frequency, extra UDP interactions). Ask if name or class are missing.

## Config fields

**Use the `/add-config-field` skill** for every config field (plan as one group, one approval; it covers schema, `on_settings_change` wiring and tests). Do not restate its steps here. The fields this skill needs:

- **A:** `show_<name>` via `overlay_enable_field(..., mfd_friendly=True, preview_image="assets/overlay-previews/<name-kebab>.png")` and `<name>_show_title` (check_box, same `group`) - both restart-required (hud_mgr). Optional `<name>_interact_udp_action_code` via `udp_action_field` (live, backend settings_change).
- **B:** `show_<name>` via `overlay_enable_field` (restart-required) and `<name>_toggle_udp_action_code` via `udp_action_field` (live), plus one `udp_action_field` per extra interaction.

Put them under the matching `# ====` section of `lib/config/schema/hud/hud.py`. Pair every `show_*` / `*_show_title` with an entry in the `settings_requiring_restart` HUD list in `apps/launcher/subsystems/hud_mgr/hud_mgr.py`; UDP codes go in the `udp_action_codes_diff` block in `apps/launcher/subsystems/backend_mgr/settings_change.py`.

## Steps common to both types

1. **`OverlayId`** - `lib/config/schema/hud/layout.py`: add the enum member (value is the id string, e.g. `"<name>_standalone"` for pages), its `display_name` mapping entry, and a non-overlapping `DEFAULT_OVERLAY_LAYOUT` position. Standalone MFD pages are 400x220 at scale 1; existing pages fill the rows at y=10, y=840 and y=1070, so pick a free slot.
2. **`enabled_overlays_by_id()`** - `lib/config/schema/hud/hud.py`: add `OverlayId.X: self.show_x` (explicit field, no `getattr`).
3. **Preview image** - always create `assets/overlay-previews/<name-kebab>.png` by copying an existing preview and renaming it (e.g. `cp pit-rejoin.png rivals-status.png`). It is a placeholder so the settings UI resolves the path; **tell the user explicitly** that it is a copy they must overwrite with a real screenshot.
4. **`scripts/png.spec`** - add the `qml_file(...)` entry next to the sibling overlays (pages: `qml_file("apps/hud/ui/overlays/mfd/pages/<name>", "<name>_page.qml")`; generic: `qml_file("apps/hud/ui/overlays/<name>", "<name>.qml")`). Do this yourself; the smoke test fails if the QML is missing from the spec.
5. **qmllint** - `poetry run python scripts/qmllint.py <new .qml>` must report 0 warnings (CI uses `--max-warnings 0`). Typical fixes: `pragma ComponentBehavior: Bound`, delegates with their own `id` and `required property`, qualify accesses with the root `id`.
6. **Verify** - `poetry run pylint --rcfile scripts/.pylintrc apps lib` (whole tree, not a sub-path, or relative-import errors appear that CI does not see).

## Type A specifics

- `MfdPageId` member in `lib/config/schema/hud/mfd.py` plus a `DEFAULT_PAGES` entry (use `enabled=False`, next free `position`).
- Page class `apps/hud/ui/overlays/mfd/pages/<name>/<name>_page.py` (MIT header) extending `MfdPageBase` with `OVERLAY_ID`, `KEY`, `PAGE_QML_FILE`, and a `standalone_show_title(cls, settings)` classmethod returning `settings.HUD.<name>_show_title`. Register handlers in `@final setup_page()` via `@self.on_event(...)` and push data with `set_qml_property`. Optional `on_page_activated()`. If `__init__` takes settings-derived kwargs, set them before `super().__init__` and override `from_settings`.
- QML `<name>_page.qml`: root must declare `property string title: "<TITLE>"` (both title bars read it), sized `parent ? parent.width : 400` / `220`. For tables, copy `pit_rejoin_page.qml` (icon maps, row delegate) and `pit_rejoin_page.py` (`get_ref_row`, `get_relevant_race_table_rows`).
- Export from `pages/__init__.py` (import + `__all__`), add to `MfdOverlay.PAGES` in `mfd/mfd.py`, and add to `OverlaysMgr.STANDALONE_PAGE_CLASSES` in `apps/hud/ui/infra/overlays_mgr.py` (the manager builds the host from `from_settings` and `standalone_show_title`; there is no per-page register call).
- Interact UDP code (only if requested): follow the "Extra interactions" section below, wired to the existing `mfd_interaction`-style path.

## Type B specifics

- Overlay `apps/hud/ui/overlays/<name>/<name>.py` extending `BaseOverlay` with `QML_FILE`, `OVERLAY_ID = OverlayId.X`; high-frequency: `self.subscribe_hf(<Type>)` + `render_frame()`; event-driven: `@self.on_event("<topic>")` in `__init__`. QML `<name>.qml` copied from `overlays/template_overlay/template_overlay.qml`. Export it from `apps/hud/ui/overlays/__init__.py`.
- Add the class to `OverlaysMgr.OVERLAY_CLASSES` in `overlays_mgr.py`; the manager instantiates it when its `OverlayId` is enabled.
- Toggle UDP code: in `apps/backend/telemetry_layer/telemetry_handler.py` add a `UdpActionCodes` field, its `_MAP` entry (config name -> field), pass it where `UdpActionCodes(...)` is built, and add a `_handle_udp_action(..., lambda: self._processToggleHud(OverlayId.X))` call in `handleButtonStatus`. The HUD side (`hud-toggle-notification`) is already generic.

## Extra interactions (beyond toggle)

Add a `_process<Action>` method to `F1TelemetryHandler` calling `self._notifyHud("hud-<action>-notification", {...})` (the literal string is both the dealer topic and message type; no backend mapping table exists), and a matching `@dealer.route("hud-<action>-notification")` handler in `apps/hud/ipc/dealer.py` with the `(data, sender)` signature that calls into `overlays_mgr`.

## Report

List files created and modified (one line each), confirm the qmllint and pylint results, and **state explicitly that the preview PNG is a renamed copy to be overwritten with a real screenshot**. Remind the user that a custom position in `png_config.json` is optional (defaults come from `DEFAULT_OVERLAY_LAYOUT`).
