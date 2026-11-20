// Per-lap series and deltas for up to four laps (A to D) on A's distance grid.
// Pure functions: no React, no store, so they are unit-testable
// (lapSeries.test.ts) and ChartLaneList can call them inside a useMemo.
import type { SensorDefinition, TelemetryPoint } from "../types/api";
import { buildDistanceGrid, interpolateToGrid, type InterpolatedPoint } from "./interpolation";

// Mandatory in every lap (lib/pngt MANDATORY_TELEMETRY_KEYS), so always available for the delta.
const LAP_TIME_SENSOR: SensorDefinition = { key: "lap_time_ms", label: "Delta", unit: "s", type: "continuous" };

// One loaded lap. `manifest` is its session's sensor manifest.
export interface LoadedLap {
  points: TelemetryPoint[];
  manifest: readonly SensorDefinition[];
}

// `slot` indexes the laps array (0 = A). A lap that lacks the sensor has no entry.
export interface SlotSeries {
  slot: number;
  points: InterpolatedPoint[];
}

export interface LapSeries {
  grid: number[];
  // The definition each sensor is charted with: the first lap's manifest that has it.
  defs: Map<string, SensorDefinition>;
  bySensor: Map<string, SlotSeries[]>;
}

// Laps that are not loaded yet are `undefined` and keep their slot. A's
// telemetry sets the grid; without it there is nothing to chart.
export function buildLapSeries(laps: readonly (LoadedLap | undefined)[], sensors: readonly string[]): LapSeries | null {
  const a = laps[0];
  if (a === undefined) {
    return null;
  }
  const grid = buildDistanceGrid(a.points);
  const defs = new Map<string, SensorDefinition>();
  const bySensor = new Map<string, SlotSeries[]>();

  for (const key of sensors) {
    const series: SlotSeries[] = [];
    laps.forEach((lap, slot) => {
      const def = lap?.manifest.find((s) => s.key === key);
      if (lap === undefined || def === undefined) {
        return;
      }
      if (!defs.has(key)) {
        defs.set(key, def);
      }
      series.push({ slot, points: interpolateToGrid(lap.points, def, grid) });
    });
    if (series.length > 0) {
      bySensor.set(key, series);
    }
  }
  return { grid, defs, bySensor };
}

// t_A(d) - t_X(d) in seconds for every comparison lap that is loaded. Positive
// means A took longer to reach that distance, i.e. A is behind.
export function buildDeltas(laps: readonly (LoadedLap | undefined)[], grid: readonly number[]): SlotSeries[] {
  const a = laps[0];
  if (a === undefined) {
    return [];
  }
  const timeA = interpolateToGrid(a.points, LAP_TIME_SENSOR, grid);
  const deltas: SlotSeries[] = [];
  laps.forEach((lap, slot) => {
    if (slot === 0 || lap === undefined) {
      return;
    }
    const timeX = interpolateToGrid(lap.points, LAP_TIME_SENSOR, grid);
    const points = grid.map((lapDistance, i) => {
      const x = timeX[i].value;
      const base = timeA[i].value;
      return { lapDistance, value: x === null || base === null ? null : (base - x) / 1000 };
    });
    // Older recordings carry no lap_time_ms: nothing to draw, so no lane for them.
    if (points.some((p) => p.value !== null)) {
      deltas.push({ slot, points });
    }
  });
  return deltas;
}

// For every sensor any loaded lap has: the slots whose lap lacks it. Feeds the
// Sensors popover note ("missing on B, D") and the lane header's dash.
export function sensorAvailability(laps: readonly (LoadedLap | undefined)[]): Map<string, number[]> {
  const loaded = laps.flatMap((lap, slot) => (lap === undefined ? [] : [{ lap, slot }]));
  const missing = new Map<string, number[]>();
  for (const { lap } of loaded) {
    for (const sensor of lap.manifest) {
      missing.set(sensor.key, []);
    }
  }
  for (const [key, slots] of missing) {
    for (const { lap, slot } of loaded) {
      if (!lap.manifest.some((s) => s.key === key)) {
        slots.push(slot);
      }
    }
  }
  return missing;
}
