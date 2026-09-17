// Shared-distance-grid interpolation, per the frontend spec's Interpolation
// section. Pure functions -- no React, no store access -- so ChartLaneList
// (Phase 5 commit 4) can call these inside a useMemo and so they're directly
// unit-testable (see interpolation.test.ts).
import type { SensorDefinition, TelemetryPoint } from "../types/api";
import { DISTANCE_GRID_RESOLUTION_M } from "./chartConstants";

export interface InterpolatedPoint {
  lapDistance: number;
  value: number | null; // null = gap, rendered with spanGaps: false
}

interface Sample {
  distance: number;
  value: number;
}

// - Range is ceil(firstPoint) to floor(lastPoint) of what was recorded --
//   never 0 or an assumed circuit length.
// - lap_distance is a 60Hz sample, so real laps don't start/end exactly on
//   0 or the finish line.
// - This leaves a ~1 sample-interval gap at each end. That's expected, not
//   a bug -- extrapolating past real data would be worse.
export function buildDistanceGrid(
  points: readonly TelemetryPoint[],
  resolution: number = DISTANCE_GRID_RESOLUTION_M
): number[] {
  if (points.length === 0) {
    return [];
  }
  const start = Math.ceil(points[0].lapDistance / resolution) * resolution;
  const end = Math.floor(points[points.length - 1].lapDistance / resolution) * resolution;

  const grid: number[] = [];
  for (let d = start; d <= end; d += resolution) {
    grid.push(d);
  }
  return grid;
}

// A missing key and a raw NaN (the format's missing-value sentinel, see
// lib/pngt's SensorDtype) both mean "no sample here" -- treated the same way.
function extractSamples(points: TelemetryPoint[], sensorKey: string): Sample[] {
  const samples: Sample[] = [];
  for (const point of points) {
    const value = point[sensorKey];
    if (value !== undefined && !Number.isNaN(value)) {
      samples.push({ distance: point.lapDistance, value });
    }
  }
  return samples;
}

function interpolateLinear(samples: Sample[], grid: readonly number[]): InterpolatedPoint[] {
  if (samples.length === 0) {
    return grid.map((lapDistance) => ({ lapDistance, value: null }));
  }

  const result: InterpolatedPoint[] = [];
  let cursor = 0;
  for (const d of grid) {
    // Clamp to the nearest known bound rather than extrapolating past the
    // edge of the recorded data.
    if (d <= samples[0].distance) {
      result.push({ lapDistance: d, value: samples[0].value });
      continue;
    }
    const last = samples[samples.length - 1];
    if (d >= last.distance) {
      result.push({ lapDistance: d, value: last.value });
      continue;
    }
    while (cursor < samples.length - 1 && samples[cursor + 1].distance < d) {
      cursor++;
    }
    const a = samples[cursor];
    const b = samples[cursor + 1];
    const span = b.distance - a.distance;
    const t = span === 0 ? 0 : (d - a.distance) / span;
    result.push({ lapDistance: d, value: a.value + t * (b.value - a.value) });
  }
  return result;
}

function interpolateNearestNeighbour(samples: Sample[], grid: readonly number[]): InterpolatedPoint[] {
  if (samples.length === 0) {
    return grid.map((lapDistance) => ({ lapDistance, value: null }));
  }

  const result: InterpolatedPoint[] = [];
  let cursor = 0;
  for (const d of grid) {
    while (cursor < samples.length - 1 && samples[cursor + 1].distance <= d) {
      cursor++;
    }
    const current = samples[cursor];
    const next = samples[cursor + 1];
    let nearest = current;
    if (next !== undefined && next.distance - d < d - current.distance) {
      nearest = next;
    }
    result.push({ lapDistance: d, value: nearest.value });
  }
  return result;
}

export function interpolateToGrid(
  points: TelemetryPoint[],
  sensor: SensorDefinition,
  grid: readonly number[]
): InterpolatedPoint[] {
  const samples = extractSamples(points, sensor.key);
  return sensor.type === "discrete" ? interpolateNearestNeighbour(samples, grid) : interpolateLinear(samples, grid);
}
