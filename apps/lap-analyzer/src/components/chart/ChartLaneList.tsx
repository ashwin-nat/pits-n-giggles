import { useEffect, useMemo, useState, type DragEvent, type ReactNode } from "react";
import { useLapTelemetries } from "../../hooks/useLapTelemetries";
import { useTelemetryStore } from "../../store/telemetryStore";
import { buildDeltas, buildLapSeries } from "../../lib/lapSeries";
import { isCompleteLap } from "../../types/store";
import { DELTA_LANE_HEIGHT_PX, LANE_HEIGHT_PX, SPEED_LANE_HEIGHT_PX } from "../../lib/chartConstants";
import { useSessions } from "../../hooks/useSessions";
import { useTrackMeta } from "../../hooks/useTrackMeta";
import { ChartLane, type LaneSeries } from "./ChartLane";
import type { SensorDefinition } from "../../types/api";

// Synthetic sensor -- not part of any session's manifest. Drawn as one line
// per comparison lap from buildDeltas.
const DELTA_SENSOR: SensorDefinition = {
  key: "lap_time_ms",
  label: "Delta to A",
  unit: "s",
  type: "continuous",
};

interface ChartLaneListProps {
  // Lifted to ChartArea so TrackProgressBar's cursor marker can share the
  // same crosshair position -- see ChartArea.
  crosshairPosition: number | null;
  onCrosshairMove: (position: number | null) => void;
}

function EmptyState({ children }: { children: ReactNode }) {
  return <div className="p-8 text-center text-sm text-tone-500">{children}</div>;
}

// Renders one ChartLane per selected sensor, plus a delta lane when there is
// a comparison lap. Owns interpolation, lane order and heights (view-local
// state, reset on remount) and the loading/empty/error states.
export function ChartLaneList({ crosshairPosition, onCrosshairMove }: ChartLaneListProps) {
  const laps = useTelemetryStore((state) => state.laps);
  const sensors = useTelemetryStore((state) => state.sensors);
  const viewport = useTelemetryStore((state) => state.viewport);
  const setViewport = useTelemetryStore((state) => state.setViewport);
  const activeSection = useTelemetryStore((state) => state.activeSection);
  const hoverSection = useTelemetryStore((state) => state.hoverSection);

  // Lane order and per-lane height overrides. The effect keeps order in sync
  // as sensors are added/removed without reshuffling lanes that stay selected.
  const [order, setOrder] = useState<string[]>(() => [...sensors]);
  const [heights, setHeights] = useState<Record<string, number>>({});
  const [dragKey, setDragKey] = useState<string | null>(null);

  useEffect(() => {
    setOrder((prev) => {
      const kept = prev.filter((key) => sensors.includes(key));
      const added = sensors.filter((key) => !kept.includes(key));
      return [...kept, ...added];
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sensors.join(",")]);

  const { laps: loaded, isFetching, error } = useLapTelemetries(laps, sensors);

  // Corners are shaded behind the traces, lining up with the strip's pills.
  const { data: sessions } = useSessions();
  const trackId = sessions?.find((s) => s.id === laps[0]?.sessionId)?.trackId ?? null;
  const meta = useTrackMeta(trackId);
  const bands = useMemo(() => (meta?.sections ?? []).filter((s) => s.type !== "straight"), [meta]);

  const series = useMemo(() => buildLapSeries(loaded, sensors), [loaded, sensors]);
  const deltas = useMemo<LaneSeries[]>(
    () => (series === null ? [] : buildDeltas(loaded, series.grid)),
    [loaded, series]
  );

  if (!isCompleteLap(laps[0])) {
    return <EmptyState>Select a lap to begin</EmptyState>;
  }
  if (sensors.length === 0) {
    return <EmptyState>Select sensors to view telemetry</EmptyState>;
  }
  if (error !== null) {
    return (
      <div className="p-8 text-center text-sm text-red-400">
        Failed to load telemetry: {error instanceof Error ? error.message : String(error)}
      </div>
    );
  }
  if (series === null) {
    return <EmptyState>Loading telemetry…</EmptyState>;
  }

  const allSlots = laps.map((_, slot) => slot);
  const orderedKeys = order.filter((key) => series.bySensor.has(key));

  function moveBefore(from: string, to: string) {
    setOrder((prev) => {
      if (from === to) {
        return prev;
      }
      const next = prev.filter((key) => key !== from);
      next.splice(next.indexOf(to), 0, from);
      return next;
    });
  }

  return (
    <div className="relative">
      {/* isFetching with data already present (placeholderData) means the lap
          just changed and the previous chart is still showing. */}
      {isFetching && (
        <div className="sticky top-0 z-10 flex justify-center bg-gradient-to-b from-canvas to-transparent py-2">
          <span className="rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-300 shadow">Loading…</span>
        </div>
      )}
      {deltas.length > 0 && (
        <ChartLane
          key="__delta__"
          sensor={DELTA_SENSOR}
          series={deltas}
          slots={allSlots.slice(1)}
          signColored
          viewport={viewport}
          onViewportChange={setViewport}
          crosshairPosition={crosshairPosition}
          onCrosshairMove={onCrosshairMove}
          focusZone={activeSection}
          hoverZone={hoverSection}
          bands={bands}
          heightPx={DELTA_LANE_HEIGHT_PX}
        />
      )}
      {orderedKeys.map((key) => {
        const sensor = series.defs.get(key);
        const laneSeries = series.bySensor.get(key);
        if (sensor === undefined || laneSeries === undefined) {
          return null;
        }
        return (
          <div
            key={key}
            onDragOver={(e: DragEvent) => {
              if (dragKey !== null) {
                e.preventDefault();
              }
            }}
            onDrop={(e: DragEvent) => {
              e.preventDefault();
              if (dragKey !== null) {
                moveBefore(dragKey, key);
              }
              setDragKey(null);
            }}
            className={dragKey === key ? "opacity-40" : undefined}
          >
            <ChartLane
              sensor={sensor}
              series={laneSeries}
              slots={allSlots}
              viewport={viewport}
              onViewportChange={setViewport}
              crosshairPosition={crosshairPosition}
              onCrosshairMove={onCrosshairMove}
              focusZone={activeSection}
              hoverZone={hoverSection}
              bands={bands}
              showXAxis={key === orderedKeys[orderedKeys.length - 1]}
              heightPx={heights[key] ?? (key === "speed" ? SPEED_LANE_HEIGHT_PX : LANE_HEIGHT_PX)}
              onHeightChange={(px) => setHeights((prev) => ({ ...prev, [key]: px }))}
              gripProps={{
                onDragStart: (e: DragEvent) => {
                  e.dataTransfer.effectAllowed = "move";
                  setDragKey(key);
                },
                onDragEnd: () => setDragKey(null),
              }}
            />
          </div>
        );
      })}
    </div>
  );
}
