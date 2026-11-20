import { test } from "node:test";
import assert from "node:assert/strict";
import { buildDeltas, buildLapSeries, sensorAvailability, type LoadedLap } from "./lapSeries";
import type { SensorDefinition, TelemetryPoint } from "../types/api";

const speed: SensorDefinition = { key: "speed", label: "Speed", unit: "km/h", type: "continuous" };
const gear: SensorDefinition = { key: "gear", label: "Gear", unit: "", type: "discrete" };

// A lap covering 0..4 m at 1 s per metre, plus offsetMs more per metre.
function lap(manifest: SensorDefinition[], speedValue: number, offsetMs = 0): LoadedLap {
  const points: TelemetryPoint[] = [0, 1, 2, 3, 4].map((d) => ({
    lapDistance: d,
    lap_time_ms: d * 1000 + offsetMs * d,
    speed: speedValue,
    gear: 3,
  }));
  return { points, manifest };
}

test("buildLapSeries returns null until A is loaded", () => {
  assert.equal(buildLapSeries([undefined, lap([speed], 100)], ["speed"]), null);
});

test("buildLapSeries gives one series per lap that has the sensor, keyed by slot", () => {
  const result = buildLapSeries(
    [lap([speed, gear], 100), lap([speed], 110), undefined, lap([speed, gear], 120)],
    ["speed", "gear"]
  );
  assert.ok(result);
  assert.deepEqual(result.grid, [0, 1, 2, 3, 4]);
  assert.deepEqual(result.bySensor.get("speed")?.map((s) => s.slot), [0, 1, 3]);
  assert.deepEqual(result.bySensor.get("gear")?.map((s) => s.slot), [0, 3]);
  assert.equal(result.bySensor.get("speed")?.[1].points[2].value, 110);
});

test("buildLapSeries charts a sensor only a comparison lap has, using that lap's definition", () => {
  const result = buildLapSeries([lap([speed], 100), lap([speed, gear], 110)], ["gear"]);
  assert.ok(result);
  assert.deepEqual(result.bySensor.get("gear")?.map((s) => s.slot), [1]);
  assert.equal(result.defs.get("gear")?.type, "discrete");
});

test("buildLapSeries leaves a sensor out when no lap has it", () => {
  const result = buildLapSeries([lap([speed], 100)], ["gear"]);
  assert.ok(result);
  assert.equal(result.bySensor.has("gear"), false);
});

test("buildLapSeries clamps to A's grid: a longer comparison lap does not extend it", () => {
  const long: LoadedLap = {
    manifest: [speed],
    points: [0, 1, 2, 3, 4, 5, 6].map((d) => ({ lapDistance: d, lap_time_ms: d * 1000, speed: 90 })),
  };
  const result = buildLapSeries([lap([speed], 100), long], ["speed"]);
  assert.ok(result);
  assert.equal(result.bySensor.get("speed")?.[1].points.length, 5);
});

test("buildDeltas: one line per loaded comparison lap, positive when A is behind", () => {
  const a = lap([speed], 100, 0);
  const sooner = lap([speed], 100, -100); // X reaches each point sooner, so A is behind
  const later = lap([speed], 100, 100); // X reaches each point later, so A is ahead
  const deltas = buildDeltas([a, sooner, undefined, later], [0, 1, 2, 3, 4]);
  assert.deepEqual(deltas.map((d) => d.slot), [1, 3]);
  assert.equal(deltas[0].points[4].value, 0.4);
  assert.equal(deltas[1].points[4].value, -0.4);
  assert.equal(deltas[0].points[0].value, 0);
});

test("buildDeltas returns nothing without A", () => {
  assert.deepEqual(buildDeltas([undefined, lap([speed], 100)], [0, 1]), []);
});

test("sensorAvailability names the slots missing each sensor, over the union of manifests", () => {
  const result = sensorAvailability([lap([speed], 100), lap([speed, gear], 100), undefined, lap([gear], 100)]);
  assert.deepEqual(result.get("speed"), [3]);
  assert.deepEqual(result.get("gear"), [0]);
});

test("buildDeltas leaves out a lap with no lap_time_ms (older recordings)", () => {
  const noTime: LoadedLap = { manifest: [speed], points: [0, 1, 2, 3, 4].map((d) => ({ lapDistance: d, speed: 100 })) };
  assert.deepEqual(buildDeltas([lap([speed], 100), noTime], [0, 1, 2, 3, 4]), []);
  assert.deepEqual(buildDeltas([noTime, lap([speed], 100)], [0, 1, 2, 3, 4]), []);
});
