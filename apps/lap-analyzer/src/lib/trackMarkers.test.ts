import { test } from "node:test";
import assert from "node:assert/strict";
import { buildMarkers, splitWrapped, zoneRanges } from "./trackMarkers";
import { formulaRules } from "./formulas";
import type { TrackMeta } from "./segments";

test("splitWrapped keeps a plain range", () => {
  assert.deepEqual(splitWrapped({ startM: 100, endM: 200 }, 5000), [{ startM: 100, endM: 200 }]);
});

test("splitWrapped cuts a range at the start/finish line", () => {
  assert.deepEqual(splitWrapped({ startM: 5502.6, endM: 881.3 }, 5798), [
    { startM: 5502.6, endM: 5798 },
    { startM: 0, endM: 881.3 },
  ]);
});

test("zoneRanges groups and unwraps", () => {
  const meta = {
    trackLength: 5798,
    drsZones: [{ id: 2, detectionM: 5502.6, activation: [{ startM: 5600, endM: 881.3 }] }],
    activeAeroZones: [
      { mode: "full", startM: 10, endM: 20 },
      { mode: "partial", startM: 30, endM: 40 },
    ],
  } as unknown as TrackMeta;
  const z = zoneRanges(meta);
  assert.equal(z.drs.length, 2);
  assert.deepEqual(z.aeroFull, [{ startM: 10, endM: 20 }]);
  assert.deepEqual(z.aeroPartial, [{ startM: 30, endM: 40 }]);
});

const full = {
  trackLength: 5798,
  speedTrapM: 716.3,
  drsZones: [{ id: 1, detectionM: 2757.6, activation: [{ startM: 3055.8, endM: 3889.1 }] }],
  overtake: { detectionM: 5154.4, activationM: 5253.6 },
  activeAeroZones: [{ mode: "full", startM: 1158.3, endM: 2113.1 }],
  brakeBoards: [{ cornerNumber: 1, distanceM: 150, atM: 776.3, side: "both" }],
} as unknown as TrackMeta;

test("buildMarkers: F1 26 has aero and overtake, no DRS", () => {
  const m = buildMarkers(full, formulaRules("F1 26"));
  assert.equal(m.aeroFull.length, 1);
  assert.equal(m.drs.length, 0);
  assert.deepEqual(m.points.map((p) => p.label), ["Overtake detection", "Overtake activation", "Speed trap"]);
  assert.deepEqual(m.boards, [{ m: 776.3, label: "150", side: "both" }]);
});

test("buildMarkers: other formulas have DRS, no aero or overtake", () => {
  const m = buildMarkers(full, formulaRules("F2"));
  assert.equal(m.aeroFull.length, 0);
  assert.equal(m.drs.length, 1);
  assert.deepEqual(m.points.map((p) => p.label), ["DRS detection 1", "Speed trap"]);
});

test("buildMarkers: a track with no speed trap or overtake gets no such points", () => {
  const bare = { ...full, speedTrapM: null, overtake: null } as unknown as TrackMeta;
  assert.deepEqual(buildMarkers(bare, formulaRules("F1 26")).points, []);
});
