import { useEffect, useMemo, useRef, useState, type HTMLAttributes, type PointerEvent as ReactPointerEvent } from "react";
import uPlot from "uplot";
import type { SensorDefinition } from "../../types/api";
import type { Viewport, ActiveSection } from "../../types/store";
import type { InterpolatedPoint } from "../../lib/interpolation";
import { computeRateOfChange } from "../../lib/rateOfChange";
import { resolveEnumLabel } from "../../lib/enumLabels";
import {
  getChartHeightPx,
  LANE_HEIGHT_PX,
  LAP_SLOT_COLORS,
  LAP_SLOT_LETTERS,
  MAX_LANE_HEIGHT_PX,
  MIN_LANE_HEIGHT_PX,
} from "../../lib/chartConstants";
import { attachWheelZoomAndPan } from "../../lib/uplotZoomPan";
import { InfoTooltip } from "./InfoTooltip";

// One lap's trace in a lane. `slot` is the lap's position (0 = A) and picks its colour.
export interface LaneSeries {
  slot: number;
  points: InterpolatedPoint[];
}

export interface ChartLaneProps {
  sensor: SensorDefinition;
  series: LaneSeries[];
  // Slots listed in the header, in order. A slot without a series reads as missing.
  slots: number[];
  // Colour header values by sign (loss/gain) instead of by slot -- the delta lane.
  signColored?: boolean;
  viewport: Viewport | null;
  onViewportChange: (viewport: Viewport) => void;
  crosshairPosition: number | null;
  onCrosshairMove: (distanceM: number | null) => void;
  focusZone: ActiveSection | null;
  hoverZone: ActiveSection | null;
  heightPx?: number;
  // Present on lanes that can be resized by dragging their bottom edge.
  onHeightChange?: (px: number) => void;
  // Spread on the drag grip; present on lanes that can be reordered.
  gripProps?: HTMLAttributes<HTMLDivElement>;
}

type ViewMode = "value" | "rate";

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

// Rate mode's last grid point is always null by design (computeRateOfChange
// has no next sample to diff against), so the literal last index isn't a
// safe "last known value" -- walk back to the last non-null one instead.
function lastValueIndex(points: InterpolatedPoint[]): number {
  for (let i = points.length - 1; i >= 0; i--) {
    if (points[i].value !== null) {
      return i;
    }
  }
  return points.length - 1;
}

// The y-axis range for a lane: either the sensor's fixed manifest range
// (always clamped to it, verbatim) or one derived once from the full trace
// data (every lap's series, whichever points are actually being charted --
// e.g. rate-mode values, not raw ones, when in Rate view). This is
// deliberately computed from the *whole* dataset, not the currently zoomed
// x-window -- wheel-zoom/pan only ever calls setScale("x", ...), so as long
// as nothing re-derives this from view state, the y-axis stays put while
// zooming/panning on x, which is what makes a chart readable while zoomed.
function computeYAxisRange(sensor: SensorDefinition, series: LaneSeries[]): [number, number] {
  if (sensor.range !== undefined) {
    return sensor.range;
  }
  let min = Infinity;
  let max = -Infinity;
  for (const { points } of series) {
    for (const p of points) {
      if (p.value === null) continue;
      if (p.value < min) min = p.value;
      if (p.value > max) max = p.value;
    }
  }
  if (!Number.isFinite(min) || !Number.isFinite(max)) {
    return [0, 1];
  }
  // Discrete sensors get fixed +/-1 unit padding (percentage padding fights
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
  // Discrete values are never fractional -- float32 is just the wire format.
  const precision = sensor.type === "discrete" ? 0 : 1;
  return `${value.toFixed(precision)}${unit ? ` ${unit}` : ""}`;
}

// One uPlot instance per sensor, one series per lap that has the sensor,
// coloured by slot, all on A's distance grid.
export function ChartLane({
  sensor,
  series,
  slots,
  signColored = false,
  viewport,
  onViewportChange,
  crosshairPosition,
  onCrosshairMove,
  focusZone,
  hoverZone,
  heightPx,
  onHeightChange,
  gripProps,
}: ChartLaneProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<uPlot | null>(null);
  const [collapsed, setCollapsed] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>("value");

  // Props change every render -- keep the latest values in a ref so uPlot
  // hooks (set up once) always see current props without a chart rebuild.
  const propsRef = useRef({ onViewportChange, onCrosshairMove, focusZone, hoverZone });
  propsRef.current = { onViewportChange, onCrosshairMove, focusZone, hoverZone };
  const viewportRef = useRef(viewport);
  viewportRef.current = viewport;
  const heightRef = useRef(heightPx);
  heightRef.current = heightPx;

  // The last distance *this* chart's own native cursor hook reported. Lets
  // the crosshair-sync effect below skip re-applying setCursor on the lane
  // the mouse is actually over.
  const ownLastReportRef = useRef<number | null>(null);

  const canRate = sensor.type === "continuous";
  const effectiveViewMode = canRate ? viewMode : "value";

  // Gated on effectiveViewMode: a real smoothing + finite-difference pass
  // over the full grid, not worth computing for lanes never put in Rate view.
  const displayed = useMemo<LaneSeries[]>(
    () =>
      effectiveViewMode === "rate"
        ? series.map((s) => ({ slot: s.slot, points: computeRateOfChange(s.points) }))
        : series,
    [series, effectiveViewMode]
  );
  // The series set decides the uPlot series list, which can't be mutated in place.
  const slotKey = displayed.map((s) => s.slot).join(",");

  const dataMin = displayed[0]?.points[0]?.lapDistance ?? 0;
  const dataMax = displayed[0]?.points[displayed[0].points.length - 1]?.lapDistance ?? 0;

  // Read by attachWheelZoomAndPan via a getter, not captured by value -- the
  // mount effect below doesn't rebuild on every lap switch.
  const boundsRef = useRef({ dataMin, dataMax });
  boundsRef.current = { dataMin, dataMax };

  // Derived once per dataset (or sensor range), not per zoomed view, so the
  // y-axis stays put while zooming/panning on x.
  const yRange = useMemo(() => computeYAxisRange(sensor, displayed), [sensor, displayed]);
  const yRangeRef = useRef(yRange);
  yRangeRef.current = yRange;

  function toData(): uPlot.AlignedData {
    return [
      displayed[0]?.points.map((p) => p.lapDistance) ?? [],
      ...displayed.map((s) => s.points.map((p) => p.value)),
    ];
  }
  const dataRef = useRef(toData);
  dataRef.current = toData;

  // Rebuild the uPlot instance when the sensor, view mode or set of laps
  // changes -- series count/paths/axis label can't be mutated in place.
  // Data, scale, zone and height updates below are imperative.
  useEffect(() => {
    const container = containerRef.current;
    if (container === null) {
      return;
    }

    const seriesOptions: uPlot.Series[] = [
      {},
      ...displayed.map((s): uPlot.Series => ({
        stroke: LAP_SLOT_COLORS[s.slot],
        width: s.slot === 0 ? 2 : 1.5,
        spanGaps: false,
        paths: sensor.type === "discrete" ? uPlot.paths.stepped!({ align: 1 }) : undefined,
      })),
    ];

    const unit = effectiveViewMode === "rate" ? `${sensor.unit}/m` : sensor.unit;

    // uPlot's defaults are tuned for a light background; set light axis colours.
    const axisColor = "#94a3b8"; // slate-400
    const gridColor = "rgba(148, 163, 184, 0.15)"; // slate-400 @ 15%

    const options: uPlot.Options = {
      width: container.clientWidth || 600,
      height: getChartHeightPx(heightRef.current),
      series: seriesOptions,
      scales: {
        x: { time: false },
        // auto: false with a static `range` -- the axis range comes from
        // computeYAxisRange and is kept in sync by the setScale effect below,
        // never recomputed from the zoomed x-window. `range`, not `min`/`max`,
        // which uPlot documents as resolved state and can leave the scale
        // empty on a rebuild.
        y: {
          auto: false,
          range: [yRangeRef.current[0], yRangeRef.current[1]],
        },
      },
      axes: [
        {
          show: true,
          stroke: axisColor,
          grid: { stroke: gridColor },
          ticks: { stroke: gridColor },
        },
        {
          label: unit,
          stroke: axisColor,
          grid: { stroke: gridColor },
          ticks: { stroke: gridColor },
          // Discrete sensors only take whole-number values.
          ...(sensor.type === "discrete"
            ? {
                incrs: [1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000],
                values: (_u: uPlot, splits: number[]) => splits.map((v) => String(Math.round(v))),
              }
            : {}),
        },
      ],
      legend: { show: false },
      cursor: {
        drag: { x: false, y: false },
        y: false,
      },
      hooks: {
        setCursor: [
          (u) => {
            const idx = u.cursor.idx;
            if (idx === null || idx === undefined) {
              // Mouse left the chart area -- keep the last reported position
              // so the crosshair, lane headers and strip marker stay put.
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
            // Hovered section lighter than the selected one.
            const { focusZone: focus, hoverZone: hover } = propsRef.current;
            for (const [zone, fill] of [
              [hover, "rgba(255, 255, 255, 0.07)"],
              [focus, "rgba(56, 189, 248, 0.12)"],
            ] as const) {
              if (zone === null) {
                continue;
              }
              const left = u.valToPos(zone.distanceStart, "x", true);
              const right = u.valToPos(zone.distanceEnd, "x", true);
              ctx.save();
              ctx.fillStyle = fill;
              ctx.fillRect(left, u.bbox.top, right - left, u.bbox.height);
              ctx.restore();
            }
          },
        ],
      },
    };

    const chart = new uPlot(options, dataRef.current(), container);
    chartRef.current = chart;

    const detachZoomPan = attachWheelZoomAndPan(chart, () => boundsRef.current, (range) =>
      propsRef.current.onViewportChange(range)
    );

    const resizeObserver = new ResizeObserver(() => {
      chart.setSize({ width: container.clientWidth || 600, height: getChartHeightPx(heightRef.current) });
    });
    resizeObserver.observe(container);

    // uPlot hides its own native cursor on mouseleave regardless of the
    // setCursor hook, and the crosshair-sync effect skips this chart, so
    // restore it right after uPlot's own handler runs.
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sensor.key, sensor.type, effectiveViewMode, slotKey]);

  // Data updates -- doesn't rebuild the chart.
  useEffect(() => {
    const chart = chartRef.current;
    if (chart === null) {
      return;
    }
    // Discrete lanes use stepped paths, which only rebuild once the x scale is
    // re-ranged -- resetScales=false left them blank until the first zoom.
    // Re-ranging resets x to the data bounds, so reapply the viewport after.
    chart.setData(dataRef.current(), true);
    const vp = viewportRef.current;
    chart.setScale("x", vp === null ? { min: dataMin, max: dataMax } : { min: vp.distanceStart, max: vp.distanceEnd });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [displayed]);

  // Height drag -> resize in place; rebuilding on every pointer move is too heavy.
  useEffect(() => {
    chartRef.current?.setSize({
      width: containerRef.current?.clientWidth || 600,
      height: getChartHeightPx(heightPx),
    });
  }, [heightPx]);

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

  // Only the y scale is ever set from yRange; wheel zoom/pan touch x alone.
  useEffect(() => {
    chartRef.current?.setScale("y", { min: yRange[0], max: yRange[1] });
  }, [yRange]);

  // Externally-driven crosshair (from a sibling lane) -> move this chart's
  // cursor without re-firing onCrosshairMove (fireHook = false avoids the
  // feedback loop). Skipped when this chart is the one the mouse is over.
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

  // Zones are read from propsRef inside the draw hook -- repaint when they
  // change. redraw(false) repaints from cached paths; the default would
  // re-range x and paint an empty chart.
  useEffect(() => {
    chartRef.current?.redraw(false);
  }, [focusZone, hoverZone, effectiveViewMode]);

  // Header rows: each listed slot's value at the crosshair; no crosshair falls
  // back to the lap's last point, never blank. A lap without the sensor reads missing.
  const rows = slots.map((slot) => {
    const points = displayed.find((s) => s.slot === slot)?.points;
    if (points === undefined || points.length === 0) {
      return { slot, value: null as number | null, present: false };
    }
    const idx = crosshairPosition === null ? lastValueIndex(points) : findNearestIndex(points, crosshairPosition);
    return { slot, value: points[idx]?.value ?? null, present: true };
  });

  function rowColor(row: { slot: number; value: number | null }): string {
    if (!signColored || row.value === null) {
      return LAP_SLOT_COLORS[row.slot];
    }
    return row.value > 0 ? "#f87171" : row.value < 0 ? "#4ade80" : LAP_SLOT_COLORS[row.slot];
  }

  function startResize(event: ReactPointerEvent<HTMLDivElement>) {
    if (onHeightChange === undefined) {
      return;
    }
    const startY = event.clientY;
    const startHeight = heightPx ?? LANE_HEIGHT_PX;
    const target = event.currentTarget;
    target.setPointerCapture(event.pointerId);
    const move = (e: PointerEvent) => {
      const next = startHeight + (e.clientY - startY);
      onHeightChange(Math.min(MAX_LANE_HEIGHT_PX, Math.max(MIN_LANE_HEIGHT_PX, next)));
    };
    const end = () => {
      target.removeEventListener("pointermove", move);
      target.removeEventListener("pointerup", end);
      target.removeEventListener("pointercancel", end);
    };
    target.addEventListener("pointermove", move);
    target.addEventListener("pointerup", end);
    target.addEventListener("pointercancel", end);
  }

  return (
    <div className="relative grid grid-cols-[180px_1fr] border-b border-slate-800">
      <div className="flex flex-col gap-1.5 bg-slate-900 px-3 py-2 text-xs">
        <div className="flex items-center gap-1.5">
          {gripProps !== undefined && (
            <div
              {...gripProps}
              draggable
              title="Drag to reorder"
              className="cursor-grab select-none text-slate-500 hover:text-slate-200 active:cursor-grabbing"
            >
              ⠿
            </div>
          )}
          <span className="font-medium text-slate-200">{sensor.label}</span>
        </div>
        <div className={`grid gap-x-3 gap-y-0.5 ${rows.length > 3 ? "grid-cols-2" : "grid-cols-1"}`}>
          {rows.map((row) => (
            <div
              key={row.slot}
              className={`flex items-baseline gap-1.5 ${rows.length === 1 ? "text-xl" : "text-sm"} font-semibold`}
              style={{ color: row.present ? rowColor(row) : "#64748b" }}
            >
              {rows.length > 1 && <span className="w-3 text-2xs font-medium opacity-80">{LAP_SLOT_LETTERS[row.slot]}</span>}
              <span>{row.present ? formatValue(sensor, row.value, effectiveViewMode) : "–"}</span>
            </div>
          ))}
        </div>
        {canRate && (
          <div className="flex items-center gap-1 text-slate-300">
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
            {/* Always hoverable, so the feature is explained before someone tries it. */}
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
        <div className="mt-auto flex items-center gap-2 border-t border-slate-800 pt-1.5 text-slate-300">
          <button type="button" onClick={() => setCollapsed((c) => !c)} className="text-slate-500 hover:text-slate-200">
            {collapsed ? "∨" : "∧"}
          </button>
        </div>
      </div>
      <div ref={containerRef} style={{ display: collapsed ? "none" : "block" }} />
      {onHeightChange !== undefined && !collapsed && (
        <div
          onPointerDown={startResize}
          title="Drag to resize"
          className="absolute inset-x-0 bottom-0 z-10 h-1.5 cursor-row-resize hover:bg-slate-600/60"
        />
      )}
    </div>
  );
}
