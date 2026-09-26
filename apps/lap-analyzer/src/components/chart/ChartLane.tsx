import { useEffect, useMemo, useRef, useState } from "react";
import uPlot from "uplot";
import type { SensorDefinition } from "../../types/api";
import type { Viewport, ActiveSection } from "../../types/store";
import type { InterpolatedPoint } from "../../lib/interpolation";
import { computeRateOfChange } from "../../lib/rateOfChange";
import { resolveEnumLabel } from "../../lib/enumLabels";
import { getChartHeightPx } from "../../lib/chartConstants";
import { attachWheelZoomAndPan } from "../../lib/uplotZoomPan";
import { InfoTooltip } from "./InfoTooltip";

export interface ChartLaneProps {
  sensor: SensorDefinition;
  primaryColor: string;
  primaryPoints: InterpolatedPoint[];
  primaryVisible?: boolean;
  referenceColor?: string;
  referencePoints?: InterpolatedPoint[];
  referenceVisible?: boolean;
  viewport: Viewport | null;
  onViewportChange: (viewport: Viewport) => void;
  crosshairPosition: number | null;
  onCrosshairMove: (distanceM: number | null) => void;
  focusZone: ActiveSection | null;
  isBottomLane: boolean;
  heightOverridePx?: number;
  onIncreaseHeight: () => void;
  onDecreaseHeight: () => void;
  onMoveUp: () => void;
  onMoveDown: () => void;
  canMoveUp: boolean;
  canMoveDown: boolean;
  // False while the mouse is outside the whole chart area (ChartLaneList),
  // even though crosshairPosition itself stays put -- see ChartLaneList.
  showTooltip: boolean;
}

type ViewMode = "value" | "rate";

// Roughly ChartArea's sticky header height (progress bar + legend + distance
// axis) plus the point-tooltip's own height and a small margin -- below this
// screen Y, opening the tooltip upward would push it behind that header.
const TOOLTIP_FLIP_THRESHOLD_PX = 170;

// Points sit on a distance-sorted grid -- binary search instead of a linear
// scan, since this runs on every crosshair move (up to 2x per visible lane).
function findNearestIndex(points: InterpolatedPoint[], distance: number): number {
  let lo = 0;
  let hi = points.length - 1;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (points[mid].lapDistance < distance) {
      lo = mid + 1;
    } else {
      hi = mid;
    }
  }
  if (lo > 0 && Math.abs(points[lo - 1].lapDistance - distance) <= Math.abs(points[lo].lapDistance - distance)) {
    return lo - 1;
  }
  return lo;
}

// The y-axis range for a lane: either the sensor's fixed manifest range
// (always clamped to it, verbatim) or one derived once from the full trace
// data (primary + reference, whichever points are actually being charted --
// e.g. rate-mode values, not raw ones, when in Rate view). This is
// deliberately computed from the *whole* dataset, not the currently zoomed
// x-window -- wheel-zoom/pan only ever calls setScale("x", ...), so as long
// as nothing re-derives this from view state, the y-axis stays put while
// zooming/panning on x, which is what makes a chart readable while zoomed.
function computeYAxisRange(
  sensor: SensorDefinition,
  primary: InterpolatedPoint[],
  reference: InterpolatedPoint[] | undefined
): [number, number] {
  if (sensor.range !== undefined) {
    return sensor.range;
  }
  let min = Infinity;
  let max = -Infinity;
  for (const p of primary) {
    if (p.value === null) continue;
    if (p.value < min) min = p.value;
    if (p.value > max) max = p.value;
  }
  if (reference !== undefined) {
    for (const p of reference) {
      if (p.value === null) continue;
      if (p.value < min) min = p.value;
      if (p.value > max) max = p.value;
    }
  }
  if (!Number.isFinite(min) || !Number.isFinite(max)) {
    return [0, 1];
  }
  // Same padding rationale as the old scales.y.range function this replaces:
  // discrete sensors get fixed +/-1 unit padding (percentage padding fights
  // uPlot's "nice number" snapping on small integer ranges like DRS's 0/1),
  // continuous ones get uPlot's own 10% padding helper.
  if (sensor.type === "discrete") {
    return [Math.floor(min) - 1, Math.ceil(max) + 1];
  }
  const [rangeMin, rangeMax] = uPlot.rangeNum(min, max, 0.1, true);
  return [rangeMin ?? min, rangeMax ?? max];
}

function formatValue(sensor: SensorDefinition, value: number | null, viewMode: ViewMode): string {
  if (value === null) {
    return "--";
  }
  if (viewMode === "value") {
    const label = resolveEnumLabel(sensor.key, value);
    if (label !== null) {
      return label;
    }
  }
  const unit = viewMode === "rate" ? `${sensor.unit}/m` : sensor.unit;
  return `${value.toFixed(1)}${unit ? ` ${unit}` : ""}`;
}

// One uPlot instance per sensor. Renders primary (solid) and, when present,
// reference (dashed, 60% opacity) traces against the shared distance grid.
export function ChartLane({
  sensor,
  primaryColor,
  primaryPoints,
  primaryVisible = true,
  referenceColor,
  referencePoints,
  referenceVisible = true,
  viewport,
  onViewportChange,
  crosshairPosition,
  onCrosshairMove,
  focusZone,
  isBottomLane,
  heightOverridePx,
  onIncreaseHeight,
  onDecreaseHeight,
  onMoveUp,
  onMoveDown,
  canMoveUp,
  canMoveDown,
  showTooltip,
}: ChartLaneProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<uPlot | null>(null);
  const [collapsed, setCollapsed] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>("value");

  // Props change every render (new arrays from ChartLaneList's useMemo when
  // relevant, but React re-renders more often than that) -- keep the latest
  // values in a ref so uPlot hooks (set up once) always see current props
  // without forcing a full chart rebuild.
  const propsRef = useRef({ onViewportChange, onCrosshairMove, focusZone });
  propsRef.current = { onViewportChange, onCrosshairMove, focusZone };

  // The last distance *this* chart's own native cursor hook reported. Lets
  // the crosshair-sync effect below skip re-applying setCursor on the lane
  // the mouse is actually over -- its own mousemove handling already moved
  // it, so re-driving it from the just-received prop is redundant work on
  // every single mousemove.
  const ownLastReportRef = useRef<number | null>(null);

  const canRate = sensor.type === "continuous";
  const effectiveViewMode = canRate ? viewMode : "value";

  // Gated on effectiveViewMode too, not just canRate -- this is a real
  // smoothing + finite-difference pass over the full interpolated grid
  // (thousands of samples), not a cheap derivation. Computing it on every
  // points change regardless of whether Rate mode is even active wasted
  // that cost on every continuous lane a user never toggles to Rate.
  const primaryRate = useMemo(
    () => (canRate && effectiveViewMode === "rate" ? computeRateOfChange(primaryPoints) : null),
    [canRate, effectiveViewMode, primaryPoints]
  );
  const referenceRate = useMemo(
    () => (canRate && effectiveViewMode === "rate" && referencePoints ? computeRateOfChange(referencePoints) : null),
    [canRate, effectiveViewMode, referencePoints]
  );

  const displayedPrimary = effectiveViewMode === "rate" && primaryRate !== null ? primaryRate : primaryPoints;
  const displayedReference =
    effectiveViewMode === "rate" && referenceRate !== null ? referenceRate : referencePoints;

  // A reference trace only really exists once *both* a color and its points
  // are available. referenceColor and referencePoints come from separate
  // async fetches upstream (different React Query calls) and can resolve on
  // different renders -- if the two conditions used to decide "is there a
  // reference series" ever disagree, uPlot ends up with a series declared
  // but no matching data array, which throws deep inside uPlot's internals
  // rather than failing gracefully. Every reference-related branch below
  // uses this single flag so that can't happen.
  const hasReference = referenceColor !== undefined && displayedReference !== undefined;

  const dataMin = primaryPoints[0]?.lapDistance ?? 0;
  const dataMax = primaryPoints[primaryPoints.length - 1]?.lapDistance ?? 0;

  // Read by attachWheelZoomAndPan via a getter, not captured by value --
  // the mount effect below only rebuilds on sensor/view-mode changes, not
  // on every lap switch, so a value captured at attach time would go stale
  // (zoom/pan staying clamped to the previous lap's range) the same way
  // propsRef exists to avoid for onViewportChange/onCrosshairMove/focusZone.
  const boundsRef = useRef({ dataMin, dataMax });
  boundsRef.current = { dataMin, dataMax };

  // Derived once per dataset (or sensor range), not per zoomed view -- see
  // computeYAxisRange. Read at chart-creation time via this ref for the same
  // stale-closure reason as boundsRef, and pushed to a live chart via the
  // dedicated effect below.
  const yRange = useMemo(
    () => computeYAxisRange(sensor, displayedPrimary, hasReference ? displayedReference : undefined),
    [sensor, displayedPrimary, displayedReference, hasReference]
  );
  const yRangeRef = useRef(yRange);
  yRangeRef.current = yRange;

  // Rebuild the uPlot instance when the sensor or view mode changes -- both
  // change series count/paths/axis label, which uPlot doesn't support
  // mutating in place. Data/scale/focus-zone updates below are imperative
  // and don't rebuild.
  useEffect(() => {
    const container = containerRef.current;
    if (container === null) {
      return;
    }

    const series: uPlot.Series[] = [
      {},
      {
        show: primaryVisible,
        stroke: primaryColor,
        width: 2,
        spanGaps: false,
        paths: sensor.type === "discrete" ? uPlot.paths.stepped!({ align: 1 }) : undefined,
      },
    ];
    if (hasReference) {
      series.push({
        show: referenceVisible,
        stroke: referenceColor,
        width: 2,
        alpha: 0.6,
        dash: [6, 4],
        spanGaps: false,
        paths: sensor.type === "discrete" ? uPlot.paths.stepped!({ align: 1 }) : undefined,
      });
    }

    const unit = effectiveViewMode === "rate" ? `${sensor.unit}/m` : sensor.unit;

    // Dark theme: uPlot's own defaults are tuned for a light background
    // (near-black axis text/lines), which is unreadable against our
    // slate-950 chart area -- every axis explicitly sets light colors here.
    const axisColor = "#94a3b8"; // slate-400
    const gridColor = "rgba(148, 163, 184, 0.15)"; // slate-400 @ 15%

    const options: uPlot.Options = {
      width: container.clientWidth || 600,
      height: getChartHeightPx(sensor, isBottomLane, heightOverridePx),
      series,
      scales: {
        x: { time: false },
        // auto: false with an explicit initial min/max -- the axis range
        // comes from computeYAxisRange (fixed sensor.range, or derived once
        // from the full dataset) and is kept in sync by the setScale effect
        // below, never recomputed from whatever's in the current zoomed
        // x-window. With auto: true, uPlot re-derives min/max from the
        // visible slice on every x zoom/pan, which made the y-axis rescale
        // itself mid-zoom.
        y: {
          auto: false,
          min: yRangeRef.current[0],
          max: yRangeRef.current[1],
        },
      },
      axes: [
        {
          show: isBottomLane,
          label: isBottomLane ? "Distance (m)" : undefined,
          stroke: axisColor,
          grid: { stroke: gridColor },
          ticks: { stroke: gridColor },
        },
        {
          label: unit,
          stroke: axisColor,
          grid: { stroke: gridColor },
          ticks: { stroke: gridColor },
        },
      ],
      legend: { show: false },
      cursor: {
        drag: { x: false, y: false },
        // Horizontal crosshair line off -- the vertical line is enough to
        // read a point off the x-axis, and the point-tooltip (which already
        // reads the real data value, not the raw mouse Y) covers what the
        // horizontal line used to approximate.
        y: false,
      },
      hooks: {
        setCursor: [
          (u) => {
            const idx = u.cursor.idx;
            if (idx === null || idx === undefined) {
              // Mouse left this chart (or the whole chart area) -- keep the
              // last reported position instead of clearing it, so the shared
              // crosshair, every lane's header values, and the progress
              // bar's marker all stay put rather than blanking out.
              return;
            }
            const x = u.data[0][idx] ?? null;
            ownLastReportRef.current = x;
            propsRef.current.onCrosshairMove(x);
          },
        ],
        draw: [
          (u) => {
            const ctx = u.ctx;
            const zone = propsRef.current.focusZone;
            // Independent of the focus zone -- previously this sat inside
            // the `zone === null` early return below, so the zero line only
            // ever appeared when a track segment was *also* selected.
            if (effectiveViewMode === "rate") {
              const zeroY = u.valToPos(0, "y", true);
              ctx.save();
              ctx.strokeStyle = "rgba(148, 163, 184, 0.6)";
              ctx.lineWidth = 1;
              ctx.beginPath();
              ctx.moveTo(u.bbox.left, zeroY);
              ctx.lineTo(u.bbox.left + u.bbox.width, zeroY);
              ctx.stroke();
              ctx.restore();
            }

            if (zone === null) {
              return;
            }
            const left = u.valToPos(zone.distanceStart, "x", true);
            const right = u.valToPos(zone.distanceEnd, "x", true);
            const top = u.bbox.top;
            const height = u.bbox.height;
            ctx.save();
            ctx.fillStyle = "rgba(56, 189, 248, 0.12)";
            ctx.fillRect(left, top, right - left, height);
            ctx.restore();
          },
        ],
      },
    };

    const initialData: uPlot.AlignedData = [displayedPrimary.map((p) => p.lapDistance), displayedPrimary.map((p) => p.value)];
    if (hasReference) {
      initialData.push(displayedReference!.map((p) => p.value));
    }
    const chart = new uPlot(options, initialData, container);
    chartRef.current = chart;

    const detachZoomPan = attachWheelZoomAndPan(chart, () => boundsRef.current, (range) =>
      propsRef.current.onViewportChange(range)
    );

    const resizeObserver = new ResizeObserver(() => {
      chart.setSize({ width: container.clientWidth || 600, height: getChartHeightPx(sensor, isBottomLane, heightOverridePx) });
    });
    resizeObserver.observe(container);

    // uPlot hides its own native cursor on mouseleave regardless of what the
    // setCursor hook above does (that hook's null-idx branch is a no-op, but
    // uPlot's internal pointer tracking still clears the visual cursor for
    // *this* chart). The externally-driven crosshair-sync effect below skips
    // re-driving this exact chart (it's "own last report" already matches),
    // so nothing else re-shows it -- this chart's cursor stays hidden even
    // though every sibling lane's stays put. Restore it ourselves right
    // after uPlot's own handler runs (attached after uPlot's own listener,
    // so it fires second on the same event).
    const handleMouseLeave = () => {
      const last = ownLastReportRef.current;
      if (last === null) {
        return;
      }
      chart.setCursor({ left: chart.valToPos(last, "x"), top: 0 }, false);
    };
    chart.over.addEventListener("mouseleave", handleMouseLeave);

    return () => {
      detachZoomPan();
      resizeObserver.disconnect();
      chart.over.removeEventListener("mouseleave", handleMouseLeave);
      chart.destroy();
      chartRef.current = null;
    };
    // Rebuilding also happens if the presence of a reference trace toggles
    // (series count changes), including the async-loads-after-mount case --
    // hasReference flipping false -> true tears down and rebuilds with 3
    // series instead of trying to add one to a live chart. Same for a height
    // override change (resize buttons) -- simpler and safe to just rebuild
    // rather than juggle a stale heightOverridePx closure inside the
    // ResizeObserver callback.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sensor.key, sensor.type, effectiveViewMode, hasReference, isBottomLane, heightOverridePx]);

  // Data updates -- doesn't rebuild the chart.
  useEffect(() => {
    const chart = chartRef.current;
    if (chart === null) {
      return;
    }
    const data: uPlot.AlignedData = [displayedPrimary.map((p) => p.lapDistance), displayedPrimary.map((p) => p.value)];
    if (hasReference) {
      data.push(displayedReference!.map((p) => p.value));
    }
    chart.setData(data, false);
  }, [displayedPrimary, displayedReference, hasReference]);

  // Legend visibility toggle -> series show/hide, without rebuilding the
  // chart. setSeries's 3rd arg (fireHook) defaults true but there's no
  // registered "setSeries" hook, so nothing loops back through this.
  useEffect(() => {
    const chart = chartRef.current;
    if (chart === null) {
      return;
    }
    chart.setSeries(1, { show: primaryVisible });
    if (hasReference) {
      chart.setSeries(2, { show: referenceVisible });
    }
  }, [primaryVisible, referenceVisible, hasReference]);

  // Viewport prop -> x scale. Zoom/pan interactions call onViewportChange,
  // which updates store.viewport, which flows back here -- setScale is a
  // no-op if already at that range, so this doesn't fight the user's drag.
  useEffect(() => {
    const chart = chartRef.current;
    if (chart === null) {
      return;
    }
    if (viewport === null) {
      chart.setScale("x", { min: dataMin, max: dataMax });
    } else {
      chart.setScale("x", { min: viewport.distanceStart, max: viewport.distanceEnd });
    }
  }, [viewport, dataMin, dataMax]);

  // yRange changes (new lap/reference data, or a view-mode switch that
  // doesn't trigger the chart-rebuild effect below) -> y scale. Deliberately
  // separate from the wheel-zoom/pan handlers, which only ever touch the x
  // scale -- this is the only thing that ever calls setScale("y", ...), so
  // zooming/panning on x never perturbs it.
  useEffect(() => {
    chartRef.current?.setScale("y", { min: yRange[0], max: yRange[1] });
  }, [yRange]);

  // Externally-driven crosshair (from a sibling lane) -> move this chart's
  // cursor without re-firing onCrosshairMove (fireHook = false avoids the
  // feedback loop back into the shared crosshair state). Skipped entirely
  // when this chart is the one the mouse is actually over -- its own
  // mousemove already positioned the cursor natively, so this would just be
  // redundant work on every mousemove.
  useEffect(() => {
    const chart = chartRef.current;
    if (chart === null || crosshairPosition === ownLastReportRef.current) {
      return;
    }
    if (crosshairPosition === null) {
      chart.setCursor({ left: -10, top: -10 }, false);
      return;
    }
    const left = chart.valToPos(crosshairPosition, "x");
    chart.setCursor({ left, top: 0 }, false);
  }, [crosshairPosition]);

  // Focus zone / rate-mode zero line are read from propsRef inside the draw
  // hook -- trigger a repaint when they change so the overlay stays in sync.
  // redraw(false) repaints from the cached series paths; the default
  // redraw() (rebuildPaths=true) re-triggers x-scale ranging and, with no
  // scale change to justify it, paints an empty chart -- always pass false
  // here.
  useEffect(() => {
    chartRef.current?.redraw(false);
  }, [focusZone, effectiveViewMode]);

  const primaryIdx = crosshairPosition === null ? null : findNearestIndex(displayedPrimary, crosshairPosition);
  const primaryValue = primaryIdx === null ? null : displayedPrimary[primaryIdx]?.value ?? null;
  const referenceIdx =
    crosshairPosition === null || !hasReference ? null : findNearestIndex(displayedReference!, crosshairPosition);
  const referenceValue = referenceIdx === null || !hasReference ? null : displayedReference![referenceIdx]?.value ?? null;

  // Follows the selected point instead of a static header readout -- pixel
  // position comes straight from the live chart instance (same valToPos
  // uPlot itself uses), so it tracks zoom/pan and per-lane height changes
  // with no extra bookkeeping. Anchored to the primary series' y; a
  // reference row is appended into the same box rather than getting its own
  // separately-positioned tooltip, since two floating boxes chasing two
  // different y positions would be more visual noise than signal.
  const chart = chartRef.current;
  const tooltipLeft =
    !collapsed && chart !== null && crosshairPosition !== null ? chart.valToPos(crosshairPosition, "x") : null;
  // Anchored to whichever trace is actually visible -- if primary is
  // legend-toggled off, anchoring to its (invisible) y-position left the
  // tooltip floating disconnected from the reference line the user is
  // actually looking at.
  const anchorValue = primaryVisible ? primaryValue : hasReference && referenceVisible ? referenceValue : null;
  const tooltipTop = tooltipLeft !== null && anchorValue !== null ? chart!.valToPos(anchorValue, "y") : null;

  // Opens above the point by default, but the topmost lane sits right under
  // ChartArea's sticky header (progress bar + legend + distance axis) --
  // for a point near the top of that lane's own plot, opening upward pushes
  // the tooltip behind that header (lower z-index, same bug class as
  // InfoTooltip's placement fix). Flip below when there isn't roughly a
  // tooltip's worth of room above the point on screen.
  const pointScreenTop =
    tooltipTop !== null ? (containerRef.current?.getBoundingClientRect().top ?? 0) + tooltipTop : null;
  const tooltipBelow = pointScreenTop !== null && pointScreenTop < TOOLTIP_FLIP_THRESHOLD_PX;

  return (
    <div className="border-b border-slate-800">
      <div className="flex items-center justify-between gap-3 bg-slate-900 px-3 py-1.5 text-xs">
        <span className="font-medium text-slate-200">{sensor.label}</span>
        <div className="flex items-center gap-3 text-slate-300">
          <div className="flex items-center gap-0.5 border-r border-slate-700 pr-2">
            <button
              type="button"
              onClick={onMoveUp}
              disabled={!canMoveUp}
              title="Move lane up"
              className="px-0.5 text-slate-400 hover:text-slate-100 disabled:cursor-not-allowed disabled:opacity-30 disabled:hover:text-slate-400"
            >
              ▲
            </button>
            <button
              type="button"
              onClick={onMoveDown}
              disabled={!canMoveDown}
              title="Move lane down"
              className="px-0.5 text-slate-400 hover:text-slate-100 disabled:cursor-not-allowed disabled:opacity-30 disabled:hover:text-slate-400"
            >
              ▼
            </button>
            <button
              type="button"
              onClick={onDecreaseHeight}
              title="Decrease lane height"
              className="px-0.5 text-slate-400 hover:text-slate-100"
            >
              −
            </button>
            <button
              type="button"
              onClick={onIncreaseHeight}
              title="Increase lane height"
              className="px-0.5 text-slate-400 hover:text-slate-100"
            >
              +
            </button>
          </div>
          {canRate && (
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={() => setViewMode("value")}
                className={`rounded px-1.5 py-0.5 ${viewMode === "value" ? "bg-slate-700 text-slate-100" : "text-slate-500"}`}
              >
                Value
              </button>
              <button
                type="button"
                onClick={() => setViewMode("rate")}
                className={`rounded px-1.5 py-0.5 ${viewMode === "rate" ? "bg-slate-700 text-slate-100" : "text-slate-500"}`}
              >
                Rate
              </button>
              {/* Always hoverable, not just once Rate is active -- the point
                  is to explain the feature *before* someone tries it. The
                  negative-values note only makes sense once Rate mode is
                  showing real data, so it's appended only then. */}
              <InfoTooltip
                text={
                  viewMode === "rate"
                    ? "Shows how fast this value is changing per metre of track -- useful for spotting where wear, temperature, or other values change fastest, like which corner is hardest on your tyres. Values can go negative -- that just means this sensor is decreasing at that point on track, even if its overall value never goes negative."
                    : "Shows how fast this value is changing per metre of track -- useful for spotting where wear, temperature, or other values change fastest, like which corner is hardest on your tyres."
                }
              >
                <span className="cursor-help text-slate-500">ⓘ</span>
              </InfoTooltip>
            </div>
          )}
          <button type="button" onClick={() => setCollapsed((c) => !c)} className="text-slate-500 hover:text-slate-200">
            {collapsed ? "∨" : "∧"}
          </button>
        </div>
      </div>
      <div className="relative">
        <div ref={containerRef} style={{ display: collapsed ? "none" : "block" }} />
        {showTooltip && tooltipTop !== null && (
          <div
            className="pointer-events-none absolute z-10 flex flex-col gap-0.5 whitespace-nowrap rounded-md border border-slate-700 bg-slate-800/95 px-2 py-1 text-xs text-slate-100 shadow-lg"
            style={{
              left: tooltipLeft!,
              top: tooltipTop,
              transform: tooltipBelow ? "translate(-50%, 10px)" : "translate(-50%, calc(-100% - 10px))",
            }}
          >
            <span className="text-[10px] text-slate-400">{Math.round(crosshairPosition!)} m</span>
            <span className="flex items-center gap-1.5">
              <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: primaryColor }} />
              {formatValue(sensor, primaryValue, effectiveViewMode)}
            </span>
            {hasReference && (
              <span className="flex items-center gap-1.5">
                <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: referenceColor }} />
                {formatValue(sensor, referenceValue, effectiveViewMode)}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
