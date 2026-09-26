import { useEffect, useMemo, useState, type ReactNode } from "react";
import { useSessions } from "../../hooks/useSessions";
import { useDrivers } from "../../hooks/useDrivers";
import { useTelemetry } from "../../hooks/useTelemetry";
import { useTelemetryStore } from "../../store/telemetryStore";
import { buildDistanceGrid, interpolateToGrid, type InterpolatedPoint } from "../../lib/interpolation";
import {
  COMPARISON_TRACE_COLOR,
  DELTA_TRACE_COLOR,
  MAX_LANE_HEIGHT_PX,
  MIN_LANE_HEIGHT_PX,
  LANE_HEIGHT_STEP_PX,
  PRIMARY_TRACE_COLOR,
  getLaneHeightPx,
} from "../../lib/chartConstants";
import { ChartLane } from "./ChartLane";
import type { ChartTraceVisibility } from "./ChartLegend";
import type { SensorDefinition } from "../../types/api";

// Synthetic sensor -- not part of any session's manifest. lap_time_ms is a
// mandatory pngt array (like lap_distance), always present in TelemetryPoint
// regardless of the user's sensor selection (see LocalFileProvider.ts and
// lap_analyzer_api.py's telemetry_points_to_api()), so it can always be
// interpolated to build the delta trace below once a reference lap exists.
const DELTA_SENSOR: SensorDefinition = {
  key: "lap_time_ms",
  label: "Delta",
  unit: "s",
  type: "continuous",
};

export interface ChartDomain {
  dataMin: number;
  dataMax: number;
}

interface ChartLaneListProps {
  visibility: ChartTraceVisibility;
  // Lifted to ChartArea so TrackProgressBar's cursor marker can share the
  // same crosshair position -- see ChartArea.
  crosshairPosition: number | null;
  onCrosshairMove: (position: number | null) => void;
  // Reports the loaded lap's distance range (the same ceil(first)/floor(last)
  // grid bound every ChartLane derives its own zoom-clamp from) so ChartArea
  // can drive the shared DistanceAxis above the lanes -- see ChartArea.
  onDomainChange: (domain: ChartDomain | null) => void;
}

function EmptyState({ children }: { children: ReactNode }) {
  return <div className="p-8 text-center text-sm text-slate-500">{children}</div>;
}

// Renders one ChartLane per sensor in primary.sensors manifest order.
// Owns: interpolation (real per-sensor work, memoized so it isn't redone on
// every crosshair-driven re-render), the shared crosshairPosition state that
// syncs all lanes, and the loading/empty/error states this area is
// responsible for (see frontend spec's Loading and Empty States table --
// sessions/drivers/laps loading live in their own sidebar components from
// Phase 4, this only covers the four rows the chart area itself owns).
export function ChartLaneList({
  visibility,
  crosshairPosition,
  onCrosshairMove,
  onDomainChange,
}: ChartLaneListProps) {
  const primary = useTelemetryStore((state) => state.primary);
  const reference = useTelemetryStore((state) => state.reference);
  const viewport = useTelemetryStore((state) => state.viewport);
  const setViewport = useTelemetryStore((state) => state.setViewport);
  const activeSection = useTelemetryStore((state) => state.activeSection);

  // Lane order and per-lane height overrides -- view-local UI state (not
  // store state, same reasoning as legend visibility), reset on remount
  // rather than persisted. Order starts as whatever primary.sensors gives on
  // first mount; the effect below keeps it in sync as sensors are
  // added/removed without reshuffling lanes that stay selected.
  const [order, setOrder] = useState<string[]>(() => [...primary.sensors]);
  const [heightOverrides, setHeightOverrides] = useState<Record<string, number>>({});

  // Point-tooltip visibility -- separate from crosshairPosition, which stays
  // put on purpose when the mouse leaves (see ChartLane's setCursor hook).
  // Tooltips shouldn't: they should disappear together as soon as the mouse
  // leaves this whole area, not linger at the last position. Tracked on the
  // wrapping div below rather than per-lane, since React's onMouseEnter/Leave
  // only fires for the wrapper's own boundary, not every child crossed while
  // moving between lanes.
  const [isHovering, setIsHovering] = useState(false);

  useEffect(() => {
    setOrder((prev) => {
      const kept = prev.filter((key) => primary.sensors.includes(key));
      const added = primary.sensors.filter((key) => !kept.includes(key));
      return [...kept, ...added];
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [primary.sensors.join(",")]);

  const { data: sessions } = useSessions();
  const { data: drivers } = useDrivers(primary.sessionId);
  const { data: referenceDrivers } = useDrivers(reference?.sessionId ?? null);
  const session = sessions?.find((s) => s.id === primary.sessionId);
  const driver = drivers?.find((d) => d.index === primary.driverIndex);
  const referenceDriver = referenceDrivers?.find((d) => d.index === reference?.driverIndex);

  const {
    data: telemetry,
    isFetching,
    error,
    refetch,
  } = useTelemetry(primary.sessionId, primary.driverIndex, primary.lapNumber, primary.sensors);
  // Reference shares primary's sensor selection (see SensorSelector) -- fetch
  // the same sensor keys against the reference session/driver/lap.
  const { data: referenceTelemetry } = useTelemetry(
    reference?.sessionId ?? null,
    reference?.driverIndex ?? null,
    reference?.lapNumber ?? null,
    primary.sensors
  );

  const interpolated = useMemo(() => {
    if (telemetry === undefined || session === undefined) {
      return null;
    }
    const grid = buildDistanceGrid(telemetry);
    const primaryMap = new Map<string, InterpolatedPoint[]>();
    const referenceMap = new Map<string, InterpolatedPoint[]>();
    for (const key of primary.sensors) {
      const sensor = session.sensorManifest.find((s) => s.key === key);
      if (sensor === undefined) {
        continue;
      }
      primaryMap.set(key, interpolateToGrid(telemetry, sensor, grid));
      // Reference interpolated onto the *same* grid as primary, per spec.
      if (referenceTelemetry !== undefined) {
        referenceMap.set(key, interpolateToGrid(referenceTelemetry, sensor, grid));
      }
    }
    const domain: ChartDomain | null =
      grid.length > 0 ? { dataMin: grid[0], dataMax: grid[grid.length - 1] } : null;

    // Delta trace: primary's elapsed lap time minus reference's, at each point on
    // the shared distance grid -- i.e. how far ahead/behind primary is at that
    // point on track, in seconds. Positive = primary is behind (took longer to
    // reach that distance); negative = primary is ahead. Only meaningful once a
    // reference lap is actually loaded.
    let deltaPoints: InterpolatedPoint[] | null = null;
    if (referenceTelemetry !== undefined) {
      const primaryTime = interpolateToGrid(telemetry, DELTA_SENSOR, grid);
      const referenceTime = interpolateToGrid(referenceTelemetry, DELTA_SENSOR, grid);
      deltaPoints = grid.map((lapDistance, i) => {
        const p = primaryTime[i].value;
        const r = referenceTime[i].value;
        return { lapDistance, value: p === null || r === null ? null : (p - r) / 1000 };
      });
    }

    return { primaryMap, referenceMap, domain, deltaPoints };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [telemetry, referenceTelemetry, session, primary.sensors.join(",")]);

  // Reported up rather than read directly by ChartArea/DistanceAxis --
  // interpolated (and the grid it's built from) is this component's own
  // memoized state, not something a sibling can reach into.
  useEffect(() => {
    onDomainChange(interpolated?.domain ?? null);
  }, [interpolated, onDomainChange]);

  if (primary.lapNumber === null) {
    return <EmptyState>Select a lap to begin</EmptyState>;
  }
  if (primary.sensors.length === 0) {
    return <EmptyState>Select sensors to view telemetry</EmptyState>;
  }
  if (error) {
    return (
      <div className="flex flex-col items-center gap-2 p-8 text-center text-sm text-red-400">
        <p>Failed to load telemetry: {error instanceof Error ? error.message : String(error)}</p>
        <button
          type="button"
          onClick={() => refetch()}
          className="rounded border border-red-800 px-3 py-1 text-red-300 hover:bg-red-950"
        >
          Retry
        </button>
      </div>
    );
  }
  if (telemetry === undefined || session === undefined || driver === undefined || interpolated === null) {
    return <EmptyState>Loading telemetry…</EmptyState>;
  }

  const color = PRIMARY_TRACE_COLOR;
  const referenceActive = reference !== null && reference.lapNumber !== null && referenceDriver !== undefined;
  const referenceColor = referenceActive ? COMPARISON_TRACE_COLOR : undefined;
  const showDelta = referenceActive && interpolated.deltaPoints !== null;

  const sensorManifest = session.sensorManifest;

  function resizeLane(key: string, deltaPx: number) {
    const sensor = sensorManifest.find((s) => s.key === key);
    if (sensor === undefined) {
      return;
    }
    setHeightOverrides((prev) => {
      const current = prev[key] ?? getLaneHeightPx(sensor);
      const next = Math.min(MAX_LANE_HEIGHT_PX, Math.max(MIN_LANE_HEIGHT_PX, current + deltaPx));
      return { ...prev, [key]: next };
    });
  }

  function moveLane(key: string, direction: -1 | 1) {
    setOrder((prev) => {
      const index = prev.indexOf(key);
      const swapWith = index + direction;
      if (index === -1 || swapWith < 0 || swapWith >= prev.length) {
        return prev;
      }
      const next = [...prev];
      [next[index], next[swapWith]] = [next[swapWith], next[index]];
      return next;
    });
  }

  // `order` is the display order; primary.sensors.map elsewhere is the
  // *selection*. Filter defensively in case order hasn't caught up with a
  // just-changed selection on this exact render (the sync effect runs after).
  const orderedKeys = order.filter((key) => primary.sensors.includes(key));

  return (
    <div className="relative" onMouseEnter={() => setIsHovering(true)} onMouseLeave={() => setIsHovering(false)}>
      {/* isFetching with data already present (from placeholderData -- see
          useTelemetry) means the lap/sensors just changed and the previous
          lap's chart is still showing underneath while the new one loads. */}
      {isFetching && (
        <div className="sticky top-0 z-10 flex justify-center bg-gradient-to-b from-slate-950 to-transparent py-2">
          <span className="rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-300 shadow">Loading…</span>
        </div>
      )}
      {showDelta && (
        <ChartLane
          key="__delta__"
          sensor={DELTA_SENSOR}
          primaryColor={DELTA_TRACE_COLOR}
          primaryPoints={interpolated.deltaPoints!}
          viewport={viewport}
          onViewportChange={setViewport}
          crosshairPosition={crosshairPosition}
          onCrosshairMove={onCrosshairMove}
          focusZone={activeSection}
          isBottomLane={false}
          // Not part of `order`/heightOverrides -- it's a synthetic lane, always
          // pinned above the real sensor lanes, so move/resize don't apply to it.
          onIncreaseHeight={() => {}}
          onDecreaseHeight={() => {}}
          onMoveUp={() => {}}
          onMoveDown={() => {}}
          canMoveUp={false}
          canMoveDown={false}
          showTooltip={isHovering}
        />
      )}
      {orderedKeys.map((key, index) => {
        const sensor = sensorManifest.find((s) => s.key === key);
        const points = interpolated.primaryMap.get(key);
        if (sensor === undefined || points === undefined) {
          return null;
        }
        return (
          <ChartLane
            key={key}
            sensor={sensor}
            primaryColor={color}
            primaryPoints={points}
            primaryVisible={visibility.primary}
            referenceColor={referenceColor}
            referencePoints={referenceActive ? interpolated.referenceMap.get(key) : undefined}
            referenceVisible={visibility.reference}
            viewport={viewport}
            onViewportChange={setViewport}
            crosshairPosition={crosshairPosition}
            onCrosshairMove={onCrosshairMove}
            focusZone={activeSection}
            isBottomLane={index === orderedKeys.length - 1}
            heightOverridePx={heightOverrides[key]}
            onIncreaseHeight={() => resizeLane(key, LANE_HEIGHT_STEP_PX)}
            onDecreaseHeight={() => resizeLane(key, -LANE_HEIGHT_STEP_PX)}
            onMoveUp={() => moveLane(key, -1)}
            onMoveDown={() => moveLane(key, 1)}
            canMoveUp={index > 0}
            canMoveDown={index < orderedKeys.length - 1}
            showTooltip={isHovering}
          />
        );
      })}
    </div>
  );
}
