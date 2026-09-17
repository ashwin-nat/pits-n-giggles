import { test } from "node:test";
import assert from "node:assert/strict";
import { buildDistanceGrid, interpolateToGrid } from "./interpolation";
import type { SensorDefinition, TelemetryPoint } from "../types/api";

const continuousSensor: SensorDefinition = { key: "speed", label: "Speed", unit: "km/h", type: "continuous" };
const discreteSensor: SensorDefinition = { key: "gear", label: "Gear", unit: "", type: "discrete" };

function points(distances: number[]): TelemetryPoint[] {
  return distances.map((lapDistance) => ({ lapDistance }));
}

test("buildDistanceGrid steps by the given resolution across the recorded range", () => {
  assert.deepEqual(buildDistanceGrid(points([0, 5]), 1), [0, 1, 2, 3, 4, 5]);
  assert.deepEqual(buildDistanceGrid(points([0, 4.5]), 2), [0, 2, 4]);
});

test("buildDistanceGrid derives its bounds from ceil(first) and floor(last), not 0 or an assumed lap length", () => {
  // lap_distance is a 60Hz progress sample -- the first/last recorded points
  // land wherever the car happened to be on the nearest tick, not exactly on
  // 0 or the circuit's true length (e.g. 7.2 to 5998.4 on a "6000m" circuit).
  assert.deepEqual(buildDistanceGrid(points([7.2, 12.9]), 1), [8, 9, 10, 11, 12]);
});

test("buildDistanceGrid returns an empty array when there are no points", () => {
  assert.deepEqual(buildDistanceGrid([]), []);
});

test("buildDistanceGrid returns an empty array when the recorded range is narrower than one resolution step", () => {
  assert.deepEqual(buildDistanceGrid(points([7.2, 7.9]), 1), []);
});

test("interpolateToGrid: linear interpolation for continuous sensors", () => {
  const points: TelemetryPoint[] = [
    { lapDistance: 0, speed: 100 },
    { lapDistance: 10, speed: 200 },
  ];
  const grid = [0, 2.5, 5, 7.5, 10];

  const result = interpolateToGrid(points, continuousSensor, grid);

  assert.deepEqual(
    result.map((p) => p.value),
    [100, 125, 150, 175, 200]
  );
});

test("interpolateToGrid: nearest-neighbour for discrete sensors", () => {
  const points: TelemetryPoint[] = [
    { lapDistance: 0, gear: 1 },
    { lapDistance: 10, gear: 2 },
  ];
  const grid = [0, 3, 5, 6, 10];

  const result = interpolateToGrid(points, discreteSensor, grid);

  // 3 -> nearer to 0 (dist 3 vs 7); 5 -> tie goes to the earlier sample;
  // 6 -> nearer to 10 (dist 4 vs 6).
  assert.deepEqual(
    result.map((p) => p.value),
    [1, 1, 1, 2, 2]
  );
});

test("interpolateToGrid: clamps to the nearest bound instead of extrapolating", () => {
  const points: TelemetryPoint[] = [
    { lapDistance: 4, speed: 50 },
    { lapDistance: 8, speed: 60 },
  ];
  const grid = [0, 4, 8, 12];

  const result = interpolateToGrid(points, continuousSensor, grid);

  assert.deepEqual(
    result.map((p) => p.value),
    [50, 50, 60, 60]
  );
});

test("interpolateToGrid: a sensor with no samples produces an all-null (gap) series", () => {
  const points: TelemetryPoint[] = [{ lapDistance: 0 }, { lapDistance: 10 }];
  const grid = [0, 5, 10];

  const result = interpolateToGrid(points, continuousSensor, grid);

  assert.deepEqual(
    result.map((p) => p.value),
    [null, null, null]
  );
});

test("interpolateToGrid: NaN samples (the missing-value sentinel) are treated as absent", () => {
  const points: TelemetryPoint[] = [
    { lapDistance: 0, speed: 100 },
    { lapDistance: 5, speed: NaN },
    { lapDistance: 10, speed: 200 },
  ];
  const grid = [0, 5, 10];

  const result = interpolateToGrid(points, continuousSensor, grid);

  assert.deepEqual(
    result.map((p) => p.value),
    [100, 150, 200]
  );
});
