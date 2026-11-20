import { test } from "node:test";
import assert from "node:assert/strict";
import { buildSectionRows, minSpeed, sectionTime, timeAt } from "./sectionTable";
import type { LoadedLap } from "./lapSeries";
import type { SensorDefinition, TrackSection } from "../types/api";

const manifest: SensorDefinition[] = [];

// Samples every 100 m; `msPerM` of lap time per metre.
function lap(msPerM: number, speeds: number[]): LoadedLap {
  return {
    manifest,
    points: speeds.map((speed, i) => ({ lapDistance: i * 100, lap_time_ms: i * 100 * msPerM, speed })),
  };
}

const sections: TrackSection[] = [
  { label: "T2", distanceStart: 200, distanceEnd: 300, type: "corner", cornerNumbers: [2] },
  { label: "T1", distanceStart: 0, distanceEnd: 200, type: "corner", cornerNumbers: [1] },
];

test("timeAt interpolates between samples and is null outside the recorded range", () => {
  const l = lap(10, [100, 100, 100, 100]);
  assert.equal(timeAt(l, 150), 1500);
  assert.equal(timeAt(l, 300), 3000);
  assert.equal(timeAt(l, 301), null);
});

test("sectionTime is the seconds between the section's ends", () => {
  assert.equal(sectionTime(lap(10, [0, 0, 0, 0]), 100, 300), 2);
});

test("minSpeed is the lowest value inside the section, null with no speed", () => {
  assert.equal(minSpeed(lap(10, [200, 90, 150, 80]), 0, 200), 90);
  assert.equal(minSpeed({ manifest, points: [{ lapDistance: 0, lap_time_ms: 0 }] }, 0, 10), null);
});

test("buildSectionRows: rows in track order, delta positive when A is slower", () => {
  const a = lap(10, [200, 90, 150, 80]);
  const faster = lap(9, [200, 90, 150, 80]);
  const rows = buildSectionRows([a, faster, undefined], sections);
  assert.deepEqual(rows.map((r) => r.section.label), ["T1", "T2"]);
  assert.equal(rows[0].minA, 90);
  assert.ok(Math.abs((rows[0].deltas[1] ?? 0) - 0.2) < 1e-9);
  assert.equal(rows[0].deltas[2], null);
  assert.equal(rows[0].deltas[0], null);
});

test("buildSectionRows without A has no values", () => {
  const rows = buildSectionRows([undefined, lap(9, [1, 1, 1, 1])], sections);
  assert.equal(rows[0].minA, null);
  assert.equal(rows[0].deltas[1], null);
});

test("a lap with no lap_time_ms has no section time or delta", () => {
  const noTime: LoadedLap = { manifest, points: [0, 100, 200, 300].map((d) => ({ lapDistance: d, speed: 100 })) };
  assert.equal(timeAt(noTime, 150), null);
  const rows = buildSectionRows([lap(10, [1, 1, 1, 1]), noTime], sections);
  assert.equal(rows[0].deltas[1], null);
});
