# Plan: Standalone MFD Pages (Issue #285)

> **Issue:** [#285 — Decouple MFD pages: support standalone and MFD-hosted modes](https://github.com/ashwin-nat/pits-n-giggles/issues/285)
> **Branch to work on:** create a new branch off `main` for each step, or accumulate on one feature branch — your call.
> **Rule:** each numbered step = one commit. Update this doc's progress tracker before committing.

---

## 0. How to execute each step (process)

Each step is done in a **fresh Claude session** to avoid context overload. The session workflow is:

1. Tell Claude which step you are on and point it at this plan doc.
2. Claude reads the plan, implements the step, then posts a **summary of every change made** (files, what changed, why).
3. If any part of the step requires **manual verification** (e.g. run the app and confirm something), Claude asks you to do it before proceeding.
4. If Claude hits anything **ambiguous or missing** from the plan, it stops and asks rather than guessing.
5. You review the diff and summary. Give feedback if needed; Claude addresses it.
6. Once you are happy: Claude marks the step done in the progress tracker (Section 5), updates any stale notes in this doc, then commits. One commit per step.
7. Move to the next step in a new session.

---

## 1. Goal

MFD pages are currently only usable inside the MFD carousel. After this work, each page can also exist as its own always-on-top overlay window (standalone mode), independently of the MFD. Both instances can run simultaneously and receive the same broadcast events.

`CollapsedPage` is internal to MFD only and is excluded from standalone support.

---

## 2. Architecture Background

### Relevant files

| Path | Role |
|------|------|
| `apps/hud/ui/overlays/mfd/pages/base_page.py` | `MfdPageBase` — base for all MFD page logic |
| `apps/hud/ui/overlays/mfd/mfd.py` | `MfdOverlay` — hosts pages in a QML carousel |
| `apps/hud/ui/overlays/base/base_qml.py` | `BaseOverlayQML` — base for all QML window-based overlays |
| `apps/hud/ui/overlays/base/base.py` | `BaseOverlay` — abstract overlay interface |
| `apps/hud/ui/infra/overlays_mgr.py` | Creates and registers all overlay instances from config |
| `lib/config/schema/hud/hud.py` | `HudSettings` — all HUD configuration fields |
| `lib/config/schema/hud/layout.py` | `OverlayId` enum + `DEFAULT_OVERLAY_LAYOUT` dict |
| `lib/config/schema/utils.py` | `overlay_enable_field()` helper |

### Key classes

**`MfdPageBase`** (`base_page.py`):
- Stores `self.overlay`, `self._page_item`, `self._handlers`, `self._stats`, `self._page_props`
- `on_event(event_type)` — decorator that registers a handler into `self._handlers`
- `handle_event(event_type, data)` — dispatches to registered handler
- `set_page_property(name, value)` — pushes a QML property to the active page item
- `QML_FILE: Path` — points to the page content QML (loaded by MFD's `pageLoader`)

**`BaseOverlayQML`** (`base_qml.py`):
- `QML_FILE: Path` — points to the **Window** QML (must be a `Window {}` root)
- `on_event(cmd_name)` — decorator for overlay-level command handlers (e.g. next_page)
- `_setup_window()` — loads `QML_FILE`, asserts root is a `QQuickWindow`
- `post_setup()` — called after window is ready; override in subclasses

**`MfdOverlay`** (`mfd.py`):
- Inherits `BaseOverlayQML`
- `post_setup()` — instantiates all enabled pages via `cls(self, self.logger, **kwargs)`
- `_apply_current_page()` — sets `currentPageQml = page.QML_FILE` in QML to load page into Loader

**`HudSettings`** (`hud.py`):
- `show_<overlay>: bool` fields use `overlay_enable_field(description, group, preview_image)` helper
- `validate_hud_settings` validator auto-detects all `overlay_enable: True` fields

### MFD page instantiation flow

```
MfdOverlay.post_setup()
  for each enabled page:
    cls(overlay=self, logger=self.logger, **kwargs)
      → page.__init__ stores overlay ref, calls _init_event_handlers()
      → handlers registered into self._handlers

MfdOverlay._register_page_event_handlers()
  for each unique event_type in any page's _handlers:
    @self.on_event(event_type)
    def _handler(data): self._mfd_pages[current_index].handle_event(event_type, data)
```

### The naming conflict (resolved in Step 3)

Both `MfdPageBase` and `BaseOverlayQML` use `QML_FILE` for different things:
- `MfdPageBase.QML_FILE` = page content `Item {}` (e.g. `fuel_page.qml`), loaded by MFD's `pageLoader`
- `BaseOverlayQML.QML_FILE` = standalone `Window {}` (e.g. `fuel_standalone.qml`), loaded by overlay engine

**Decision:** rename `MfdPageBase.QML_FILE` → `PAGE_QML_FILE` across base + all 9 page subclasses + `MfdOverlay._apply_current_page()`. After this, `QML_FILE` on dual-mode pages unambiguously means the standalone Window QML.

### The `on_event` name collision (resolved in Step 1)

`MfdPageBase.on_event` and `BaseOverlayQML.on_event` are both decorators with the same name. Multiple inheritance breaks this. **Decision:** rename `MfdPageBase.on_event` → `on_page_event`.

---

## 3. Eligible pages for standalone

All 8 non-collapsed pages become dual-mode. `CollapsedPage` stays MFD-internal.

| Class | File | Config kwargs | Handler method name (current) |
|-------|------|---------------|-------------------------------|
| `FuelInfoPage` | `mfd/pages/fuel/fuel_page.py` | `fuel_est_mode` | `_init_handlers` |
| `TyreInfoPage` | `mfd/pages/tyre_wear/tyre_wear_page.py` | `tyre_wear_threshold`, `tyre_wear_rate_type` | `_init_event_handlers` |
| `LapTimesPage` | `mfd/pages/lap_times/lap_times.py` | none | `_init_event_handlers` |
| `WeatherForecastPage` | `mfd/pages/weather/weather.py` | `graph_based_ui` | `_init_event_handlers` |
| `PitRejoinPredictionPage` | `mfd/pages/pit_rejoin/pit_rejoin_page.py` | none | `_init_event_handlers` |
| `TyreSetsPage` | `mfd/pages/tyre_sets/tyre_sets_page.py` | none | `_init_event_handlers` |
| `PaceCompPage` | `mfd/pages/pace_comp/pace_comp.py` | none | `_init_event_handlers` |
| `TrafficMonitorPage` | `mfd/pages/traffic_monitor/traffic_monitor_page.py` | none | `_init_event_handlers` |

---

## 4. Steps

### Step 1 — Rename `MfdPageBase.on_event` → `on_page_event`

**Why:** `MfdPageBase.on_event` and `BaseOverlayQML.on_event` have the same name. Multiple inheritance (`StandalonePageOverlay`) would cause the wrong one to be used.

**Files changed:**
- `apps/hud/ui/overlays/mfd/pages/base_page.py` — rename the method
- All 8 eligible page files — rename `@self.on_event(...)` → `@self.on_page_event(...)` in their `_init_event_handlers` / `_init_handlers` bodies
  - `mfd/pages/fuel/fuel_page.py`
  - `mfd/pages/tyre_wear/tyre_wear_page.py`
  - `mfd/pages/lap_times/lap_times.py`
  - `mfd/pages/weather/weather.py`
  - `mfd/pages/pit_rejoin/pit_rejoin_page.py`
  - `mfd/pages/tyre_sets/tyre_sets_page.py`
  - `mfd/pages/pace_comp/pace_comp.py`
  - `mfd/pages/traffic_monitor/traffic_monitor_page.py`

**Do NOT rename** `@self.on_event(...)` calls in `mfd.py` — those are `BaseOverlayQML.on_event`, which keeps its name.

**Verification:** `poetry run pylint --rcfile scripts/.pylintrc apps lib` must pass clean. MFD pages must still update normally in the running app.

**After-step summary:** `MfdPageBase` now exposes `on_page_event` as its handler decorator. No behaviour change.

---

### Step 2 — Make `overlay` optional in `MfdPageBase.__init__`

**Why:** `create_for_mfd` (Step 5) will call `MfdPageBase.__init__` with `overlay=self` (a real `MfdOverlay`). Standalone instances call `MfdPageBase.__init__` with `overlay=None`. The current required param blocks this.

**Files changed:**
- `apps/hud/ui/overlays/mfd/pages/base_page.py`
  - Change `def __init__(self, overlay: "MfdOverlay", logger)` → `def __init__(self, overlay: Optional["MfdOverlay"] = None, *, logger: logging.Logger)`
  - Remove the `assert self.QML_FILE` / `assert isinstance` / `assert self.QML_FILE.is_file()` assertions (these belong to `BaseOverlayQML` now, not `MfdPageBase`)
  - `self.overlay = overlay` still assigned (may be `None`)

**No changes to page subclasses** — they still pass `overlay` positionally, which continues to work.

**Verification:** pylint clean. MFD pages still work.

**After-step summary:** `MfdPageBase.__init__` accepts `overlay=None`. QML file assertions removed from `MfdPageBase`.

---

### Step 3 — Rename `MfdPageBase.QML_FILE` → `PAGE_QML_FILE`

**Why:** Free the name `QML_FILE` so that `BaseOverlayQML` owns it unambiguously for the standalone Window QML.

**Files changed:**
- `apps/hud/ui/overlays/mfd/pages/base_page.py` — rename class attr `QML_FILE` → `PAGE_QML_FILE`
- All 9 page subclasses (including `CollapsedPage`) — rename their `QML_FILE = Path(...)` attr
- `apps/hud/ui/overlays/mfd/mfd.py` `_apply_current_page()` — change `page.QML_FILE` → `page.PAGE_QML_FILE`

**Verification:** pylint clean. MFD pages load correctly (title bar shows page name, content renders).

**After-step summary:** All page content QMLs referenced via `PAGE_QML_FILE`. `QML_FILE` is now free on these classes for the standalone window.

---

### Step 4 — Standardize `_init_event_handlers` + add `PAGE_QML_FILE` assertion

**Why:** `FuelInfoPage` still uses the old name `_init_handlers`. All pages need a consistent no-arg `_init_event_handlers()` that only registers handlers. Config fields are runtime-immutable and belong in `__init__`. Also add back the `PAGE_QML_FILE` assertion that was lost when `QML_FILE` assertions were removed.

**Changes per page:**

**`FuelInfoPage`** (`fuel_page.py`):
- Rename `_init_handlers` → `_init_event_handlers` (no args beyond `self`)
- `self._fuel_est_mode = fuel_est_mode` stays in `__init__` (set before `super().__init__()`)

**`TyreInfoPage`** (`tyre_wear_page.py`):
- `_init_event_handlers` takes no args
- `self.tyre_wear_threshold` and `self.tyre_wear_rate_type` set in `__init__` before `super().__init__()`

**`WeatherForecastPage`** (`weather.py`):
- `_init_event_handlers` takes no args
- `self.graph_based_ui` set in `__init__` before `super().__init__()`
- Internal state fields (`_last_processed_samples`, `session_index`, `num_sessions`, `session_uid`) stay in `__init__` before `super()`

**`LapTimesPage`**, **`PitRejoinPredictionPage`**, **`TyreSetsPage`**, **`PaceCompPage`**, **`TrafficMonitorPage`** — no changes needed.

**`base_page.py`**:
- Add `assert self.PAGE_QML_FILE, "PAGE_QML_FILE must be set in subclass"` in `__init__` alongside the existing `KEY` assert.

**Verification:** pylint clean. Run MFD and verify fuel/tyre/weather pages still display correct data.

**After-step summary:** All 8 pages use `_init_event_handlers()` (no args) — registers handlers only. Config fields set in `__init__` where they're visible as instance state. `PAGE_QML_FILE` asserted in base.

---

### Step 5 — Create `StandalonePageOverlay` base class

**New file:** `apps/hud/ui/overlays/mfd/pages/standalone_base.py`

**Class definition:**
```python
class StandalonePageOverlay(BaseOverlayQML, MfdPageBase):
    """Base for pages that can run both inside MFD and as a standalone overlay window."""
```

**MRO:** `StandalonePageOverlay → BaseOverlayQML → BaseOverlay → QObject → MfdPageBase`
- `self.on_event` resolves to `BaseOverlayQML.on_event` (overlay command handlers)
- `self.on_page_event` resolves to `MfdPageBase.on_page_event` (page data handlers)

**`__init__`:**
```python
def __init__(self, config, logger, locked, opacity, scale_factor, windowed_overlay, **page_kwargs):
    for k, v in page_kwargs.items():
        setattr(self, k, v)   # set config fields before handlers are registered
    MfdPageBase.__init__(self, overlay=None, logger=logger)
    self._init_event_handlers()
    BaseOverlayQML.__init__(self, config=config, logger=logger, locked=locked,
                            opacity=opacity, scale_factor=scale_factor,
                            windowed_overlay=windowed_overlay, refresh_interval_ms=None)
```

> **Note:** `setattr` requires kwarg names to exactly match instance field names. `FuelInfoPage` currently stores `self._fuel_est_mode` but the kwarg is `fuel_est_mode`. Rename `_fuel_est_mode` → `fuel_est_mode` in `fuel_page.py` as part of this step.

**`post_setup`:**
```python
def post_setup(self):
    # Page is always active when standalone — activate immediately with root item
    self._on_page_activated(self.root)
    self._wire_standalone_handlers()
```

**`_wire_standalone_handlers`:**
```python
def _wire_standalone_handlers(self):
    for event_type, handler in self._handlers.items():
        @self.on_event(event_type)
        def _fwd(data, _h=handler): _h(data)
```
This bridges page handlers (registered via `on_page_event`) into the overlay event system (via `on_event`), so broadcast telemetry events reach the standalone page.

**`create_for_mfd` classmethod:**
```python
@classmethod
def create_for_mfd(cls, overlay, logger, **kwargs) -> "MfdPageBase":
    obj = MfdPageBase.__new__(cls)
    for k, v in kwargs.items():
        setattr(obj, k, v)   # set config fields before handlers are registered
    MfdPageBase.__init__(obj, overlay=overlay, logger=logger)
    obj._init_event_handlers()
    return obj
```
This creates a page object for MFD use without triggering `BaseOverlayQML.__init__` (no Qt window created).

**Export:** add `StandalonePageOverlay` to `apps/hud/ui/overlays/mfd/pages/__init__.py`.

**Verification:** pylint clean. No behaviour change yet (no page uses this class yet).

**After-step summary:** `StandalonePageOverlay` and `create_for_mfd` exist. MFD is unchanged.

---

### Step 6 — Update `MfdOverlay.post_setup` to use `create_for_mfd`

**Why:** When instantiating pages, if the page class is a `StandalonePageOverlay` subclass, the MFD must use `create_for_mfd` instead of the normal constructor (which would open a Qt window).

**Files changed:**
- `apps/hud/ui/overlays/mfd/mfd.py` — `post_setup()`:

```python
for page_info in self.enabled_pages:
    cls = page_info["cls"]
    kwargs = page_info.get("kwargs", {})
    if issubclass(cls, StandalonePageOverlay):
        self._mfd_pages.append(cls.create_for_mfd(self, self.logger, **kwargs))
    else:
        self._mfd_pages.append(cls(self, self.logger, **kwargs))
```

Also import `StandalonePageOverlay` in `mfd.py`.

**Verification:** pylint clean. No behaviour change yet (no page is a `StandalonePageOverlay` subclass yet).

**After-step summary:** MFD branching logic is ready. Activates automatically once pages are converted in Step 7.

---

### Step 7 — Convert pages + add standalone QML wrappers

Convert all 8 eligible pages from `MfdPageBase` → `StandalonePageOverlay`. Add a standalone Window QML wrapper for each.

**For each page:**
1. Change `class XxxPage(MfdPageBase):` → `class XxxPage(StandalonePageOverlay):`
2. Add `QML_FILE: Path = Path(__file__).parent / "xxx_standalone.qml"` (BaseOverlayQML's window)
3. Keep `PAGE_QML_FILE: Path = Path(__file__).parent / "xxx_page.qml"` (MFD content, from Step 3)
4. Create `xxx_standalone.qml` in the same directory

**Standalone QML wrapper template** (same pattern for all pages, adjust dimensions per page):
```qml
import QtQuick
import QtQuick.Window

Window {
    id: root
    visible: true
    color: "black"
    property real scaleFactor: 1.0

    readonly property int baseWidth:  400
    readonly property int baseHeight: 220

    width:  baseWidth  * scaleFactor
    height: baseHeight * scaleFactor

    Item {
        id: scaledRoot
        anchors.fill: parent
        scale: root.scaleFactor
        transformOrigin: Item.TopLeft

        Loader {
            width:  baseWidth
            height: baseHeight
            source: "xxx_page.qml"
        }
    }
}
```

**Pages and their wrapper filenames:**
| Page | Wrapper QML | Base dimensions |
|------|-------------|-----------------|
| `FuelInfoPage` | `fuel_standalone.qml` | 400 × 220 |
| `TyreInfoPage` | `tyre_wear_standalone.qml` | 400 × 220 |
| `LapTimesPage` | `lap_times_standalone.qml` | 400 × 220 |
| `WeatherForecastPage` | `weather_standalone.qml` | 400 × 220 |
| `PitRejoinPredictionPage` | `pit_rejoin_standalone.qml` | 400 × 220 |
| `TyreSetsPage` | `tyre_sets_standalone.qml` | 400 × 220 |
| `PaceCompPage` | `pace_comp_standalone.qml` | 400 × 220 |
| `TrafficMonitorPage` | `traffic_monitor_standalone.qml` | 400 × 220 |

> **Note on dimensions:** The MFD's `baseHeightExpanded = 220` and `baseWidth = 400`. Verify the actual content size per page by running the MFD — some pages may need taller windows. Adjust `baseHeight` in each wrapper accordingly.

**`CollapsedPage`** is not converted. It stays `MfdPageBase`. No `QML_FILE` is needed on it after Step 3 (it only has `PAGE_QML_FILE`).

**Verification (manual):**
1. Run the HUD: `poetry run python -m apps.hud`
2. MFD must still work normally — pages cycle, data updates, collapse/expand animates
3. Temporarily wire one standalone page in `overlays_mgr.py` just to confirm the window opens and receives data (revert after confirming; proper wiring is Step 10)

**After-step summary:** All 8 pages are dual-mode. MFD uses `create_for_mfd` for them. Standalone QML wrappers exist. No standalone overlays are exposed in config yet.

---

### Step 8 — Add `OverlayId` entries + `DEFAULT_OVERLAY_LAYOUT` entries

**Files changed:**
- `lib/config/schema/hud/layout.py`

Add to `OverlayId` enum:
```python
FUEL_INFO      = "fuel_info"
TYRE_INFO      = "tyre_info"
LAP_TIMES      = "lap_times_standalone"
WEATHER        = "weather_standalone"
PIT_REJOIN     = "pit_rejoin_standalone"
TYRE_SETS      = "tyre_sets_standalone"
PACE_COMP      = "pace_comp_standalone"
TRAFFIC_MONITOR = "traffic_monitor_standalone"
```

Add to `DEFAULT_OVERLAY_LAYOUT`:
```python
OverlayId.FUEL_INFO:        OverlayPosition(x=420, y=355),
OverlayId.TYRE_INFO:        OverlayPosition(x=420, y=355),
OverlayId.LAP_TIMES:        OverlayPosition(x=420, y=355),
OverlayId.WEATHER:          OverlayPosition(x=420, y=355),
OverlayId.PIT_REJOIN:       OverlayPosition(x=420, y=355),
OverlayId.TYRE_SETS:        OverlayPosition(x=420, y=355),
OverlayId.PACE_COMP:        OverlayPosition(x=420, y=355),
OverlayId.TRAFFIC_MONITOR:  OverlayPosition(x=420, y=355),
```

> Positions above are placeholders. Adjust to sensible defaults (similar to existing MFD position at x=10, y=355; standalone pages can go alongside). Verify visually in Step 10.

Also add `OVERLAY_ID` class attributes on each converted page class, matching the new `OverlayId` values (required by `BaseOverlayQML`):
```python
class FuelInfoPage(StandalonePageOverlay):
    OVERLAY_ID = OverlayId.FUEL_INFO
    ...
```

**Verification:** pylint clean. `poetry run pytest tests/` passes (config schema tests).

**After-step summary:** Config enum and layout defaults exist. No UI changes yet.

---

### Step 9 — Add `HudSettings.show_*` fields + preview images

**Files changed:**
- `lib/config/schema/hud/hud.py`
- `assets/overlay-previews/` — add 8 new PNG files

**Preview images:** take a screenshot of each standalone page (after Step 7, you can temporarily enable one via Step 10 patch to take a screenshot). Until then, use `assets/overlay-previews/mfd.png` as a placeholder copy. Name them:
```
assets/overlay-previews/fuel-info.png
assets/overlay-previews/tyre-info.png
assets/overlay-previews/lap-times-standalone.png
assets/overlay-previews/weather-standalone.png
assets/overlay-previews/pit-rejoin-standalone.png
assets/overlay-previews/tyre-sets-standalone.png
assets/overlay-previews/pace-comp-standalone.png
assets/overlay-previews/traffic-monitor-standalone.png
```

**Add to `HudSettings`** (under a new group `"MFD Pages (Standalone)"`):

All 7 pages without interactive controls follow this pattern:
```python
show_fuel_info: bool = overlay_enable_field(
    description="Enable fuel info standalone overlay",
    group="MFD Pages (Standalone)",
    default=False,
    preview_image="assets/overlay-previews/fuel-info.png",
)
show_tyre_info: bool = overlay_enable_field(
    description="Enable tyre info standalone overlay",
    group="MFD Pages (Standalone)",
    default=False,
    preview_image="assets/overlay-previews/tyre-info.png",
)
# same pattern for: lap_times, pit_rejoin, tyre_sets, pace_comp, traffic_monitor
```

Weather is the exception — it needs an `ext_info` note explaining how session cycling works in standalone mode, consistent with the existing `mfd_interaction_udp_action_code` tooltip (see `hud.py:258-264`):
```python
show_weather_standalone: bool = overlay_enable_field(
    description="Enable weather forecast standalone overlay",
    group="MFD Pages (Standalone)",
    default=False,
    preview_image="assets/overlay-previews/weather-standalone.png",
    ext_info=[
        "Use the MFD interact action (mfd_interaction_udp_action_code) to cycle through "
        "forecast sessions. If both the MFD weather page and this standalone overlay are "
        "enabled simultaneously, the interact button cycles both."
    ],
)
```

> `default=False` keeps all standalone pages opt-in — existing configs are unaffected.

The `validate_hud_settings` validator already auto-detects `overlay_enable: True` fields — no changes needed there.

**Verification:** pylint clean. `poetry run pytest tests/` passes. Settings UI shows new group with 8 checkboxes (all off by default).

**After-step summary:** Config fields exist. Enabling them has no effect yet (manager not wired).

---

### Step 10 — Update overlay manager

**Files changed:**
- `apps/hud/ui/infra/overlays_mgr.py`

For each of the 8 standalone pages, add a registration block analogous to the existing non-MFD overlays. The kwargs come from the same `settings.HUD.*` fields already used by the MFD (`_get_page_kwargs`).

**Pattern (fuel as example):**
```python
self._register_overlay_if_enabled(
    enabled=settings.HUD.show_fuel_info,
    overlay_cls=FuelInfoPage,
    overlay_cfg=settings.HUD.layout[OverlayId.FUEL_INFO],
    opacity=settings.HUD.overlays_opacity,
    windowed_overlay=settings.HUD.use_windowed_overlays,
    scale_factor=settings.HUD.layout[OverlayId.FUEL_INFO].scale_factor,
    fuel_est_mode=settings.HUD.overlays_fuel_estimation_mode,
)
```

Pages without config kwargs (LapTimes, PitRejoin, TyreSets, PaceComp, TrafficMonitor) omit the extra kwargs.

Also import all 8 page classes at the top of `overlays_mgr.py`.

**`mfd_interact` broadcast change:**

`WeatherForecastPage` handles an `"mfd_interact"` event to cycle through forecast sessions. Currently `overlays_mgr.mfd_interact()` unicasts only to `MfdOverlay.OVERLAY_ID`, so a standalone weather instance never receives it.

**Decision:** change `mfd_interact()` to broadcast to all overlays:

```python
# Before
def mfd_interact(self):
    self.window_manager.unicast_data(MfdOverlay.OVERLAY_ID, 'mfd_interact', {})

# After
def mfd_interact(self):
    self.window_manager.broadcast_data('mfd_interact', {})
```

**Known trade-off:** if both MFD weather and standalone weather are enabled simultaneously, pressing the interact button cycles both instances at the same time. This is acceptable.

Also import all 8 page classes at the top of `overlays_mgr.py`.

**Verification (manual):**
1. Enable `show_fuel_info: true` in `png_config.json`
2. Run `poetry run python -m apps.hud`
3. Fuel standalone window must appear, receive telemetry updates, and be positionable
4. MFD fuel page must still work simultaneously
5. Enable `show_weather_standalone: true`, press MFD interact in-game — standalone weather must cycle sessions
6. If MFD weather is also enabled, confirm both cycle simultaneously (expected behaviour)

**After-step summary:** All 8 standalone overlays are wired end-to-end. Weather session cycling works via the existing MFD interact button (broadcast to all overlays).

---

## 5. Progress tracker

- [x] Step 1 — Rename `on_event` → `on_page_event`
- [x] Step 2 — Make `overlay` optional in `MfdPageBase.__init__`
- [x] Step 3 — Rename `QML_FILE` → `PAGE_QML_FILE`
- [x] Step 4 — Standardize `_init_event_handlers` + `PAGE_QML_FILE` assertion
- [ ] Step 5 — Create `StandalonePageOverlay` + `create_for_mfd`
- [ ] Step 6 — Update `MfdOverlay.post_setup` to use `create_for_mfd`
- [ ] Step 7 — Convert pages + add standalone QML wrappers
- [ ] Step 8 — Add `OverlayId` + `DEFAULT_OVERLAY_LAYOUT` entries
- [ ] Step 9 — Add `HudSettings.show_*` fields + preview images
- [ ] Step 10 — Update overlay manager
