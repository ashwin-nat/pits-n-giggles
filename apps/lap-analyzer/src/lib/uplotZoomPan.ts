// uPlot has no built-in scroll-to-zoom / drag-to-pan -- both are the
// standard hand-rolled recipe every uPlot-based app adds itself (see
// uPlot's own demos). This is that recipe, factored out so ChartLane stays
// focused on rendering.
import type uPlot from "uplot";

const ZOOM_FACTOR = 0.85; // per wheel notch

export interface ViewportRange {
  distanceStart: number;
  distanceEnd: number;
}

export interface DataBounds {
  dataMin: number;
  dataMax: number;
}

// Attaches wheel-zoom and drag-to-pan to a uPlot instance's plotting area.
// Both clamp to [dataMin, dataMax] -- never zoom/pan out past the recorded
// data -- and call onViewportChange with the resulting range. Returns a
// cleanup function.
//
// `getBounds` is a callback, not plain numbers -- ChartLane attaches this
// once per uPlot instance (the mount effect doesn't rebuild on every lap
// change, just on sensor/view-mode changes), but dataMin/dataMax come from
// primaryPoints, which *does* change on every lap switch. Capturing them by
// value here left a stale closure: switching to a longer or shorter lap
// while zoomed kept clamping to the previous lap's range. Reading through a
// callback (backed by a ref in ChartLane) means every handler always sees
// the current bounds regardless of when this was attached.
export function attachWheelZoomAndPan(
  u: uPlot,
  getBounds: () => DataBounds,
  onViewportChange: (viewport: ViewportRange) => void
): () => void {
  const over = u.over;

  function clamp(min: number, max: number): ViewportRange {
    const { dataMin, dataMax } = getBounds();
    let start = Math.max(min, dataMin);
    let end = Math.min(max, dataMax);
    if (start >= end) {
      start = dataMin;
      end = dataMax;
    }
    return { distanceStart: start, distanceEnd: end };
  }

  function onWheel(e: WheelEvent) {
    e.preventDefault();
    const { dataMin, dataMax } = getBounds();
    const rect = over.getBoundingClientRect();
    const cursorVal = u.posToVal(e.clientX - rect.left, "x");
    const scale = u.scales.x;
    const curMin = scale.min ?? dataMin;
    const curMax = scale.max ?? dataMax;
    const factor = e.deltaY < 0 ? ZOOM_FACTOR : 1 / ZOOM_FACTOR;

    const newMin = cursorVal - (cursorVal - curMin) * factor;
    const newMax = cursorVal + (curMax - cursorVal) * factor;
    const range = clamp(newMin, newMax);
    u.setScale("x", { min: range.distanceStart, max: range.distanceEnd });
    onViewportChange(range);
  }

  let dragging = false;
  let dragStartX = 0;
  let dragStartMin = 0;
  let dragStartMax = 0;

  function stopDragging() {
    dragging = false;
  }

  function onPointerDown(e: PointerEvent) {
    // Primary button/contact only -- a right-click (button 2, opens a
    // context menu that can swallow the paired pointerup) or a secondary
    // touch point must not start a pan.
    if (e.button !== 0 || !e.isPrimary) {
      return;
    }
    const { dataMin, dataMax } = getBounds();
    dragging = true;
    dragStartX = e.clientX;
    dragStartMin = u.scales.x.min ?? dataMin;
    dragStartMax = u.scales.x.max ?? dataMax;
    over.setPointerCapture(e.pointerId);
  }

  function onPointerMove(e: PointerEvent) {
    if (!dragging) {
      return;
    }
    // Defense in depth against a missed pointerup (e.g. the button was
    // released while a different window had focus, which doesn't always
    // replay as a pointerup on the captured element) -- if the primary
    // button isn't reported held anymore, stop rather than keep panning on
    // plain hover.
    if ((e.buttons & 1) === 0) {
      stopDragging();
      return;
    }
    const deltaPx = e.clientX - dragStartX;
    const rect = over.getBoundingClientRect();
    const deltaVal = (deltaPx / rect.width) * (dragStartMax - dragStartMin);
    const range = clamp(dragStartMin - deltaVal, dragStartMax - deltaVal);
    u.setScale("x", { min: range.distanceStart, max: range.distanceEnd });
    onViewportChange(range);
  }

  function onPointerUp(e: PointerEvent) {
    stopDragging();
    over.releasePointerCapture(e.pointerId);
  }

  over.addEventListener("wheel", onWheel, { passive: false });
  over.addEventListener("pointerdown", onPointerDown);
  over.addEventListener("pointermove", onPointerMove);
  over.addEventListener("pointerup", onPointerUp);
  // Fired instead of pointerup when the browser cancels tracking outright
  // (touch/pen palm rejection, OS-level gesture interception) or when
  // capture is released without an explicit pointerup -- without these,
  // `dragging` can get stuck true and the chart pans on plain mouse hover.
  over.addEventListener("pointercancel", stopDragging);
  over.addEventListener("lostpointercapture", stopDragging);

  return () => {
    over.removeEventListener("wheel", onWheel);
    over.removeEventListener("pointerdown", onPointerDown);
    over.removeEventListener("pointermove", onPointerMove);
    over.removeEventListener("pointerup", onPointerUp);
    over.removeEventListener("pointercancel", stopDragging);
    over.removeEventListener("lostpointercapture", stopDragging);
  };
}
