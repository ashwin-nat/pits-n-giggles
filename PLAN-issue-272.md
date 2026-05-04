# Plan: Issue #272 — Replace track_radar Canvas with Qt Quick scene graph items

> **Do not commit this file.**

## Context

`track_radar.qml` currently uses a single `Canvas` with `renderStrategy: Canvas.Threaded`.
Every frame it CPU-rasterizes 4 dashed circles, a crosshair, 1–2 radial-gradient pie sectors,
and up to 20 rounded rectangles. At 60 fps the render thread is structurally behind:
88.6% miss rate, max streak 35.

The fix is to replace the Canvas with Qt Quick scene graph (SG) items. The SG is GPU-accelerated:
static items are tessellated once into GPU buffers; only changed properties trigger incremental
GPU uploads. Zero per-frame CPU rasterization for anything that doesn't change.

**Scope constraint:** rendering only — no changes to data pipeline, IPC, base infra, or
`render_frame()` logic. The Python side already computes and sets `carData`, `carOnLeft`,
`carOnRight` via `set_qml_property()`. The only Python addition is generating the two glow
images and wiring an image provider in `post_setup()`.

---

## Layers of change

| Layer | Files changed |
|---|---|
| QML rewrite | `apps/hud/ui/overlays/track_radar/track_radar.qml` |
| Python — image provider + pre_setup | `apps/hud/ui/overlays/track_radar/track_radar.py` |
| Base class additions | `apps/hud/ui/overlays/base/base.py`, `apps/hud/ui/overlays/base/base_qml.py` |

---

## Steps

### ~~Step 1 — Replace static geometry: grid circles and crosshair~~ ✅ DONE (commit 0ba4540b)

**Goal:** Remove the Canvas entirely for the static layer. Add `Shape { ShapePath { PathAngleArc } }`
items for the 4 dashed grid circles and two `Rectangle` items for the crosshair. These are
created once, never repainted.

**Details:**
- Import `QtQuick.Shapes`
- 4 `Shape` items, each containing a `ShapePath` with `PathAngleArc` (full 360°), dashed stroke
  (`strokeStyle: ShapePath.DashLine`, `dashPattern: [5, 5]`), no fill, `strokeColor: "rgba(255,255,255,0.22)"`.
  Radii: `halfR * 0.5`, `halfR * 1.0`, `halfR * 1.5`, `halfR * 2.0` where `halfR = baseWidth * radarAreaRatio / 2`.
- 2 thin `Rectangle` items crossing center for the crosshair (`color: "rgba(255,255,255,0.28)"`).
- Remove the `onPaint` grid-circle and crosshair drawing blocks from Canvas.
- Keep Canvas temporarily for the remaining dynamic parts (glows + cars) — this step is
  intentionally partial so it can be committed and tested in isolation.

**Before committing:** Ask user to run the HUD with a replay and visually confirm the grid circles
and crosshair render correctly (correct radii, dashed style, opacity). Commit only after confirmation.

**Commit message:** `perf(track_radar): replace canvas grid circles and crosshair with SG items`

---

### ~~Step 2 — Replace sector glows with pre-baked Image items + Python image provider~~ ✅ DONE

**Goal:** Eliminate `createRadialGradient()` which re-allocates and CPU-rasterizes a gradient
object every frame it is active.

**Python changes (`track_radar.py`):**
- Add a `RadarGlowImageProvider(QQuickImageProvider)` class that serves two images:
  `"glow-left"` and `"glow-right"`. Each is a `QImage(300, 300, QImage.Format_ARGB32)`
  painted once with `QPainter` + `QRadialGradient` at base 300×300 resolution — the same
  geometry (pie sector from center to `halfR`, radial fade 0.8→0.4→0.0) currently drawn
  by the Canvas code.
- In `post_setup()`, instantiate the provider and register it:
  `self._engine.addImageProvider("radar", provider)`.
  `self._engine` is accessible via `BaseOverlayQML`.

**QML changes:**
- Add two `Image` items:
  ```qml
  Image { source: "image://radar/glow-left";  opacity: carOnLeft  ? 1.0 : 0.0; ... }
  Image { source: "image://radar/glow-right"; opacity: carOnRight ? 1.0 : 0.0; ... }
  ```
  with `Behavior on opacity { NumberAnimation { duration: 150 } }` for the fade effect.
- The images are at base 300×300 and scale for free with the parent `Scale` transform —
  no regeneration needed when `scaleFactor` changes.
- Remove the glow drawing blocks from Canvas `onPaint`.

**Deviations from original plan:**
- `pre_setup()` public hook added to `base.py` (mirrors `post_setup`; called before `_setup_window`) —
  provider must be registered before QML loads, not after.
- `qml_engine` property added to `base_qml.py` — avoids derived classes accessing `_engine` directly.
- `_make_glow_image` takes `is_left: bool` instead of a string side param.
- 150ms opacity `NumberAnimation` added to `Image` items for fade in/out.

**Commit message:** `perf(track_radar): replace canvas sector glows with pre-baked image provider`

---

### ~~Step 3 — Replace car rectangles with a fixed 22-slot Rectangle pool~~ ✅ DONE

**Goal:** Eliminate the per-frame Canvas translate/rotate/fill/stroke calls for up to 20 cars.

**QML changes:**
- Add a fixed pool of 22 `Rectangle` items in an `Item` (no Repeater/ListModel — avoids
  item churn). Each rectangle:
  - `width: carWidthPx`, `height: carLengthPx`
  - `x` and `y` set directly (top-left = position − half dimensions)
  - `rotation` set directly
  - `visible` toggled
  - `color: "#ffffff"`, `border.color: "#888888"`, `border.width: 1`, `radius: 2`
- Reference car: one additional `Rectangle` centered, `color: "#00ff00"`,
  `border.color: "#ffffff"`, `border.width: 2`, always visible.
- Python already writes `carData` as a flat `[x, y, heading, inRange, ...]` array (stride 4)
  where `x`/`y` are radar-center-relative coordinates. The QML pool reads these via
  `onCarDataChanged` and assigns `x`, `y`, `rotation`, `visible` per slot.
- Remove the car-drawing block from Canvas `onPaint`.

**After this step the Canvas is empty — remove it entirely.**

**Before committing:** Ask user to visually confirm all cars render with correct positions, headings,
and colors (white for others, green for reference car). Also ask user to gather a perf log so we can
compare miss rate vs the Canvas baseline. Commit only after confirmation.

**Commit message:** `perf(track_radar): replace canvas car rectangles with fixed SG Rectangle pool`

---

### ~~Step 4 — Cleanup and verification~~ ✅ DONE

**Goal:** Remove dead code, verify no regressions.

- Canvas and all `onPaint`/`requestPaint` wiring removed as part of step 3.
- `poetry run pylint` → 10.00/10, no issues.
- No unit tests cover QML rendering (confirmed by user).

**Commit message:** `refactor(track_radar): remove dead canvas code after SG migration`

---

## Critical files

| File | Role |
|---|---|
| [apps/hud/ui/overlays/track_radar/track_radar.qml](apps/hud/ui/overlays/track_radar/track_radar.qml) | Full QML rewrite across steps 1–3 |
| [apps/hud/ui/overlays/track_radar/track_radar.py](apps/hud/ui/overlays/track_radar/track_radar.py) | Add `_RadarGlowImageProvider`, wire in `pre_setup()` (step 2) |
| [apps/hud/ui/overlays/base/base.py](apps/hud/ui/overlays/base/base.py) | Added `pre_setup()` hook |
| [apps/hud/ui/overlays/base/base_qml.py](apps/hud/ui/overlays/base/base_qml.py) | Added `qml_engine` property |

## Existing utilities to reuse

- `qml_engine` (`BaseOverlayQML`) — QQmlApplicationEngine; call `addImageProvider()` on it in `pre_setup()`
- `set_qml_property()` (`BaseOverlayQML`) — already used in `render_frame()`; no changes needed
- `_RADAR_BASE_WIDTH`, `_RADAR_AREA_RATIO` constants in `track_radar.py` — reuse for image generation geometry

## Verification

1. Start backend with a replay: `poetry run python -m apps.dev_tools.telemetry_replayer --file-name example.f1pcap`
2. Launch HUD: `poetry run python -m apps.hud`
3. Confirm track radar renders correctly: grid circles, crosshair, glow sectors on overtake approach, car rectangles with correct headings.
4. Run `/perf-report` against a captured session log to compare miss rate vs baseline (88.6% → target <30%).
5. `poetry run python tests/unit_tests.py` — no failures.
