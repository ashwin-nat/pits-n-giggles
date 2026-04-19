---
description: Scaffold a new HUD overlay widget in apps/hud/ui/overlays/ with full wiring
allowed-tools: Read, Glob, Grep, Edit, Write
---

Scaffold a new HUD overlay and wire it end-to-end: config knobs, UDP action codes, backend dispatch, HUD socketio handlers, and the overlay class itself.

## Input

The user must provide:
- **Overlay name** in snake_case (e.g. `fuel_monitor`) — used for directory and file names
- **Class name** in PascalCase (e.g. `FuelMonitorOverlay`)
- **Data style**: "high-frequency" (polled via `render_frame`) or "event-driven" (push via `@on_event`)
- **Event/topic name** if event-driven (e.g. `"fuel-update"`)
- **Extra UDP interactions** beyond the mandatory toggle (e.g. "cycle page", "reset") — optional

If overlay name or class name are missing, ask before proceeding.

---

## Steps

Work through these in order. Read each target file before editing it.

### 1. Config knobs — `lib/config/schema/hud/hud.py`

Read the file first to understand field ordering and helper functions (`udp_action_field`, `overlay_enable_field`, `ui_scale_field` from `lib/config/schema/utils.py`).

Add, grouped together under a comment `# ============== <OVERLAY NAME> OVERLAY ==============`:

**a) Enable/disable knob** (catastrophic — requires HUD restart):
```python
show_<overlay_name>: bool = overlay_enable_field(description="Enable <Overlay Name> overlay", group="<Overlay Name>")
```

**b) Toggle UDP action code** (non-catastrophic — runtime update):
```python
<overlay_name>_toggle_udp_action_code: Optional[int] = udp_action_field(
    description="Toggle <Overlay Name> overlay UDP action code", group="<Overlay Name>"
)
```

**c) Any additional interaction UDP action codes** the user requested — one `udp_action_field` per interaction, same group.

Also add the overlay ID constant at the top of the file (or in `lib/config/schema/hud/__init__.py` if that's where the other `*_OVERLAY_ID` constants live):
```python
<OVERLAY_NAME>_OVERLAY_ID = "<overlay_name>"
```

### 2. Register overlay ID — `lib/config/schema/hud/layout.py`

Read the file. Add `"<overlay_name>"` to the allowed overlay ID set/list so the config system recognises it.

### 3. Wire enable knob as catastrophic — `apps/launcher/subsystems/hud_mgr/hud_mgr.py`

Read `on_settings_change`. In the `settings_requiring_restart` diff block under `"HUD"`, add:
```python
"show_<overlay_name>",
```

### 4. Wire UDP action codes as non-catastrophic — `apps/launcher/subsystems/backend_mgr.py`

Read `on_settings_change`. In the `udp_action_codes_diff` block under `"HUD"`, add:
```python
"<overlay_name>_toggle_udp_action_code",
```
Plus any additional interaction action codes defined in step 1c.

### 5. Register UDP action codes in the backend — `apps/backend/telemetry_layer/telemetry_handler.py`

Read the file. Three edits:

**a)** In `UdpActionCodes` dataclass, add fields:
```python
toggle_<overlay_name>: Optional[int] = None
# one per extra interaction
```

**b)** In `UdpActionCodes._MAP`, add entries mapping the config field name → dataclass field name:
```python
"<overlay_name>_toggle_udp_action_code": "toggle_<overlay_name>",
```

**c)** In `F1TelemetryHandler.__init__`, pass the new action codes when constructing `UdpActionCodes(...)`:
```python
toggle_<overlay_name>=settings.HUD.<overlay_name>_toggle_udp_action_code,
```

**d)** In `handleButtonStatus` (inside `registerCallbacks`), add `_handle_udp_action` calls:
```python
await self._handle_udp_action(
    buttons,
    self.m_udp_action_codes.toggle_<overlay_name>,
    'Toggle <overlay_name> overlay',
    lambda: self._processToggleHud('<overlay_name>')
)
```
For extra interactions, add a new `_process<Action>` private method following the pattern of `_processCycleMFD`, and a matching `HudXxxNotification` dataclass + `MessageType` enum value (steps 6 and 7 below).

### 6. New ITC notification types (only if extra interactions beyond toggle)

Edit `lib/inter_task_communicator.py`:

**a)** Add a new `@dataclass` notification class following the pattern of `HudCycleMfdNotification`:
```python
@dataclass
class Hud<Action>Notification:
    ...
```

**b)** Add a new `MessageType` enum value:
```python
HUD_<ACTION>_NOTIFICATION = "hud-<action>-notification"
```

### 7. Backend emits new socketio events — `apps/backend/intf_layer/telemetry_web_server.py`

Read the file. In the `client_event_mappings` for `ClientType.HUD`, add the new socketio event name(s) from step 6b so the backend forwards them to HUD clients:
```python
'hud-<action>-notification',
```
(Skip this step if there are no extra interactions — the toggle reuses the existing `hud-toggle-notification` event via `_processToggleHud`.)

### 8. HUD socketio handlers — `apps/hud/listener/client.py`

Read the file. For each extra interaction (not toggle — that's already handled generically by `toggle_overlays_visibility`), register a new `@self.on(...)` handler following the pattern of `handle_hud_cycle_mfd_notification`:
```python
@self.on('hud-<action>-notification')
def handle_hud_<action>_notification(data):
    self.m_overlays_mgr.<action>(<overlay_name>)
```

### 9. Overlay class — `apps/hud/ui/overlays/<overlay_name>/`

Create two files:

**`<overlay_name>.py`**:
- MIT licence header (copy from template)
- Class extends `BaseOverlayQML`
- `QML_FILE = Path(__file__).parent / "<overlay_name>.qml"`
- `OVERLAY_ID = "<overlay_name>"`
- For high-frequency: `self.subscribe_hf(<HFType>)` in `__init__`, implement `render_frame()`
- For event-driven: `self._register_event_handlers()` in `__init__`, implement `@self.on_event("<topic>")` handler

**`<overlay_name>.qml`**:
- Minimal Rectangle root (`id: root`), transparent background, placeholder Text

### 10. Register overlay in OverlaysMgr — `apps/hud/hud.py`

Read the file. Import the new class and add it to the overlay instantiation block following the pattern of existing overlays. Gate on `config.HUD.show_<overlay_name>`.

### 11. PyInstaller spec — `scripts/png.spec`

Do not edit this file. Tell the user to add the following entry to the `datas` list manually:
```
('apps/hud/ui/overlays/<overlay_name>/<overlay_name>.qml', 'apps/hud/ui/overlays/<overlay_name>')
```

---

## Summary

After completing all steps, report:
- Files created
- Files modified, with a one-line description of what changed in each
- Remind user to: add the overlay position to `png_config.json` under the HUD layout section, and update `scripts/png.spec`
