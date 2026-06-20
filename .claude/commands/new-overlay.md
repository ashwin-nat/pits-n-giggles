---
description: Scaffold a new HUD overlay widget in apps/hud/ui/overlays/ with full wiring
allowed-tools: Read, Glob, Grep, Edit, Write
---

Scaffold a new HUD overlay and wire it end-to-end: config knobs, UDP action codes, backend dispatch, HUD socketio handlers, and the overlay class itself.

## Overlay types

There are two overlay types. Ask the user which they want before proceeding.

**A. MFD page overlay** — an `MfdPageBase` subclass that lives inside `apps/hud/ui/overlays/mfd/pages/`. It appears in the MFD carousel *and* can optionally run as a standalone always-on-top window (via `StandalonePageHost`). Always event-driven (no `render_frame`). Use this for data pages (lap times, fuel, tyre wear, etc.).

**B. Generic standalone overlay** — a `BaseOverlay` subclass in `apps/hud/ui/overlays/<name>/`. Use for everything else (track radar, input telemetry, etc.).

---

## Type A — MFD page overlay

### Inputs required

- **Page name** in snake_case (e.g. `gap_to_leader`)
- **Class name** in PascalCase (e.g. `GapToLeaderPage`)
- **Display title** — string shown in the MFD title bar (e.g. `"GAP TO LEADER"`)
- **Event types** it listens to (e.g. `"race_table_update"`, `"stream_overlay_update"`) — MFD pages are always event-driven; do not use `render_frame`
- **Config kwargs** if the page has config-driven behaviour (e.g. a display mode enum) — optional
- **Extra MFD interactions** beyond the standard toggle (e.g. cycle through views) — optional

If page name or class name are missing, ask before proceeding.

---

### Steps (Type A)

Work through these in order. Read each target file before editing it.

#### A1. Add `MfdPageId` value — `lib/config/schema/hud/mfd.py`

Add an entry to the `MfdPageId` enum:
```python
GAP_TO_LEADER = "gap_to_leader"
```

#### A2. Add `OverlayId` value — `lib/config/schema/hud/layout.py`

Add an entry to the `OverlayId` enum:
```python
GAP_TO_LEADER = "gap_to_leader_standalone"
```

Then add a default position to `DEFAULT_OVERLAY_LAYOUT`. All standalone MFD pages are 400×220 at scale=1. Spread it so it does not overlap existing entries (existing pages occupy the top row y=10 and bottom row y=840 across x=10/420/830/1240 — pick a free slot or the next row).

```python
OverlayId.GAP_TO_LEADER: OverlayPosition(x=<x>, y=<y>),
```

#### A3. Add config fields — `lib/config/schema/hud/hud.py`

> **Use the `/add-config-field` skill for this step.**

Under the `# ============== MFD PAGES (STANDALONE) ==============` section, add a group of fields together:

**a) Enable knob** (catastrophic — requires HUD restart):
```python
show_gap_to_leader: bool = overlay_enable_field(
    description="Enable gap to leader standalone overlay",
    group="Gap To Leader",
    default=False,
    mfd_friendly=True,
    preview_image="assets/overlay-previews/gap-to-leader.png",
)
```

**b) Title bar toggle** (catastrophic):
```python
gap_to_leader_show_title: bool = Field(
    default=True,
    description="Show title bar in gap to leader overlay",
    json_schema_extra={"ui": {"type": "check_box", "visible": True, "group": "Gap To Leader"}},
)
```

**c) Any page-specific config fields** (e.g. display mode enum) — same group.

**d) MFD interact UDP action code** if the page needs an interact button (non-catastrophic):
```python
gap_to_leader_interact_udp_action_code: Optional[int] = udp_action_field(
    description="Interact with gap to leader overlay UDP action code", group="Gap To Leader"
)
```

#### A4. Mark enable knob as catastrophic — `apps/launcher/subsystems/hud_mgr/hud_mgr.py`

In `on_settings_change`, inside the `settings_requiring_restart` diff block under `"HUD"`, add:
```python
"show_gap_to_leader",
"gap_to_leader_show_title",
```

#### A5. Wire UDP interact code (if applicable) — `apps/launcher/subsystems/backend_mgr.py`

In `on_settings_change`, inside the `udp_action_codes_diff` block under `"HUD"`, add:
```python
"gap_to_leader_interact_udp_action_code",
```

#### A6. Register UDP interact in backend (if applicable)

Follow the same three-file pattern as the generic overlay steps 5–8 below for:
- `apps/backend/telemetry_layer/telemetry_handler.py` — `UdpActionCodes` dataclass + `_MAP` + `handleButtonStatus`
- `lib/inter_task_communicator.py` — new notification dataclass + `MessageType` value
- `apps/backend/intf_layer/telemetry_web_server.py` — add socketio event to HUD client mappings
- `apps/hud/listener/client.py` — add `@self.on(...)` handler

#### A7. Create the page class — `apps/hud/ui/overlays/mfd/pages/gap_to_leader/`

Create two files:

**`gap_to_leader_page.py`**:
- MIT licence header
- Extends `MfdPageBase`
- Class attributes:
  ```python
  OVERLAY_ID = OverlayId.GAP_TO_LEADER
  KEY = MfdPageId.GAP_TO_LEADER
  PAGE_QML_FILE: Path = Path(__file__).parent / "gap_to_leader_page.qml"
  ```
- If config kwargs: set them as instance attributes **before** calling `super().__init__`,
  because `super().__init__` calls `setup_page()` which uses them.
- `@final def setup_page(self)` — initialise per-instance state (caches, counters) and
  register all event handlers via `@self.on_event("<event_type>")`. Handlers call
  `self.set_qml_property(name, value)` to push data to QML. Do **not** implement
  `render_frame` — MFD pages are event-driven only.
- `@final def on_page_activated(self)` — optional; called after `setup_page()` when the page
  item is live. Use to invalidate caches or push initial QML property values.

Pattern:
```python
class GapToLeaderPage(MfdPageBase):
    OVERLAY_ID = OverlayId.GAP_TO_LEADER
    KEY = MfdPageId.GAP_TO_LEADER
    PAGE_QML_FILE: Path = Path(__file__).parent / "gap_to_leader_page.qml"

    def __init__(self, logger, some_kwarg: SomeType):
        self._some_kwarg = some_kwarg   # set BEFORE super().__init__
        super().__init__(logger)

    @final
    def setup_page(self):
        self._last_data = None

        @self.on_event("race_table_update")
        def _handle(data: Dict[str, Any]) -> None:
            ...
            self.set_qml_property("someProperty", value)

    @final
    def on_page_activated(self):
        self._last_data = None  # invalidate cache so first real event re-renders
```

**`gap_to_leader_page.qml`**:
- Root item **must** declare `property string title: "GAP TO LEADER"`. The standalone wrapper reads this property to populate its title bar, and `mfd.qml` reads it for the MFD title bar. Without it both title bars are blank.
- `width: parent ? parent.width : 400` and `height: parent ? parent.height : 220`
- Declare all QML properties that Python will set via `set_qml_property`
- Copy structure from the nearest existing page QML

#### A8. Export from pages `__init__.py` — `apps/hud/ui/overlays/mfd/pages/__init__.py`

Add the import and `__all__` entry:
```python
from .gap_to_leader import GapToLeaderPage
```
```python
"GapToLeaderPage",
```

#### A9. Register in MFD overlay — `apps/hud/ui/overlays/mfd/mfd.py`

**a)** Import the class and add it to the `PAGES` list:
```python
PAGES = [
    ...
    GapToLeaderPage,
]
```
`PAGE_CLS_BY_KEY` is built automatically from `PAGES`.

**b)** If the page has config kwargs, add an entry to `_get_page_kwargs`:
```python
GapToLeaderPage.KEY: {
    "some_kwarg": settings.HUD.some_config_field,
},
```

#### A10. Register as standalone in `OverlaysMgr` — `apps/hud/ui/infra/overlays_mgr.py`

Import the class and add a `_register_page_host_if_enabled` call in the `# ---- MFD pages (standalone) ----` block:
```python
self._register_page_host_if_enabled(
    enabled=settings.HUD.show_gap_to_leader,
    page_cls=GapToLeaderPage,
    overlay_cfg=settings.HUD.layout[OverlayId.GAP_TO_LEADER],
    opacity=settings.HUD.overlays_opacity,
    windowed_overlay=settings.HUD.use_windowed_overlays,
    scale_factor=settings.HUD.layout[OverlayId.GAP_TO_LEADER].scale_factor,
    show_title_bar=settings.HUD.gap_to_leader_show_title,
    # any config kwargs:
    # some_kwarg=settings.HUD.some_config_field,
)
```

#### A11. PyInstaller spec — `scripts/png.spec`

Do not edit this file. Tell the user to add the following entry to the `datas` list manually:
```
('apps/hud/ui/overlays/mfd/pages/gap_to_leader/gap_to_leader_page.qml',
 'apps/hud/ui/overlays/mfd/pages/gap_to_leader')
```

---

## Type B — Generic standalone overlay

### Inputs required

- **Overlay name** in snake_case (e.g. `fuel_monitor`)
- **Class name** in PascalCase (e.g. `FuelMonitorOverlay`)
- **Data style**: "high-frequency" (polled via `render_frame`) or "event-driven" (push via `@on_event`)
- **Event/topic name** if event-driven (e.g. `"fuel-update"`)
- **Extra UDP interactions** beyond the mandatory toggle (e.g. "cycle page", "reset") — optional

If overlay name or class name are missing, ask before proceeding.

---

### Steps (Type B)

Work through these in order. Read each target file before editing it.

#### B1. Config knobs — `lib/config/schema/hud/hud.py`

> **Use the `/add-config-field` skill for this step.** Present the full set of config knobs below as a single group plan for user approval, then implement and test them all together. Do not do them one by one.

Read the file first to understand field ordering and helper functions (`udp_action_field`, `overlay_enable_field`, `ui_scale_field` from `lib/config/schema/utils.py`).

The group of fields to plan and add together, under a comment `# ============== <OVERLAY NAME> OVERLAY ==============`:

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

**c) Any additional interaction UDP action codes** the user requested — one `udp_action_field` per interaction, same group. Include these in the same group plan.

Also add the overlay ID constant at the top of the file (or in `lib/config/schema/hud/__init__.py` if that's where the other `*_OVERLAY_ID` constants live):
```python
<OVERLAY_NAME>_OVERLAY_ID = "<overlay_name>"
```

#### B2. Register overlay ID — `lib/config/schema/hud/layout.py`

Read the file. Add `"<overlay_name>"` to the allowed overlay ID set/list so the config system recognises it.

#### B3. Wire enable knob as catastrophic — `apps/launcher/subsystems/hud_mgr/hud_mgr.py`

Read `on_settings_change`. In the `settings_requiring_restart` diff block under `"HUD"`, add:
```python
"show_<overlay_name>",
```

#### B4. Wire UDP action codes as non-catastrophic — `apps/launcher/subsystems/backend_mgr.py`

Read `on_settings_change`. In the `udp_action_codes_diff` block under `"HUD"`, add:
```python
"<overlay_name>_toggle_udp_action_code",
```
Plus any additional interaction action codes defined in step B1c.

#### B5. Register UDP action codes in the backend — `apps/backend/telemetry_layer/telemetry_handler.py`

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
For extra interactions, add a new `_process<Action>` private method following the pattern of `_processCycleMFD`, and a matching `HudXxxNotification` dataclass + `MessageType` enum value (steps B6 and B7 below).

#### B6. New ITC notification types (only if extra interactions beyond toggle)

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

#### B7. Backend emits new socketio events — `apps/backend/intf_layer/telemetry_web_server.py`

Read the file. In the `client_event_mappings` for `ClientType.HUD`, add the new socketio event name(s) from step B6b so the backend forwards them to HUD clients:
```python
'hud-<action>-notification',
```
(Skip this step if there are no extra interactions — the toggle reuses the existing `hud-toggle-notification` event via `_processToggleHud`.)

#### B8. HUD socketio handlers — `apps/hud/listener/client.py`

Read the file. For each extra interaction (not toggle — that's already handled generically by `toggle_overlays_visibility`), register a new `@self.on(...)` handler following the pattern of `handle_hud_cycle_mfd_notification`:
```python
@self.on('hud-<action>-notification')
def handle_hud_<action>_notification(data):
    self.m_overlays_mgr.<action>(<overlay_name>)
```

#### B9. Overlay class — `apps/hud/ui/overlays/<overlay_name>/`

Create two files:

**`<overlay_name>.py`**:
- MIT licence header (copy from template)
- Class extends `BaseOverlay`
- `QML_FILE = Path(__file__).parent / "<overlay_name>.qml"`
- `OVERLAY_ID = "<overlay_name>"`
- For high-frequency: `self.subscribe_hf(<HFType>)` in `__init__`, implement `render_frame()`
- For event-driven: register handlers in `__init__` via `@self.on_event("<topic>")`,
  call `self.set_qml_property(name, value)` in handlers

**`<overlay_name>.qml`**:
- Minimal Rectangle root (`id: root`), transparent background, placeholder Text. Copy as much as possible from apps/hud/ui/overlays/template_overlay/template_overlay.qml
- If the overlay animates continuously (drives per-frame rendering via FrameAnimation), add a `FrameTelemetry` component and expose its stats as aliases on the root Window. This enables `get_window_stats()` to include QML-side frame metrics automatically:
  ```qml
  import "../base"

  property alias faFps:               frameTelemetry.fps
  property alias faFrameTimeMs:       frameTelemetry.frameTimeMs
  property alias faSmoothFrameTimeMs: frameTelemetry.smoothFrameTimeMs
  property alias faFrameCount:        frameTelemetry.frameCount

  FrameTelemetry { id: frameTelemetry }
  ```
  Event-driven overlays (no continuous animation) should omit this.

#### B10. Register overlay in OverlaysMgr — `apps/hud/ui/infra/overlays_mgr.py`

Read the file. Import the new class and add it to the overlay instantiation block following the pattern of existing overlays. Gate on `config.HUD.show_<overlay_name>`.

#### B11. PyInstaller spec — `scripts/png.spec`

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
