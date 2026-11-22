import { test } from "node:test";
import assert from "node:assert/strict";
import { toMeta, type SegmentsFile } from "./segments";

const base: SegmentsFile = {
  circuit_name: "Test",
  circuit_number: 1,
  track_length: 5000,
  segments: [],
  sectors: { s1: 1500, s2: 3000 },
};

test("toMeta: a file with none of the optional v2 fields loads", () => {
  const meta = toMeta(base);
  assert.equal(meta.speedTrapM, null);
  assert.equal(meta.overtake, null);
  assert.deepEqual(meta.drsZones, []);
  assert.deepEqual(meta.activeAeroZones, []);
  assert.deepEqual(meta.brakeBoards, []);
});

test("toMeta: explicit empty zone lists, as Monaco has, load", () => {
  const meta = toMeta({ ...base, speed_trap_m: 900, drs_zones: [], active_aero_zones: [] });
  assert.equal(meta.speedTrapM, 900);
  assert.deepEqual(meta.activeAeroZones, []);
});

test("toMeta: a sub-corner's own name wins, else the complex corner's name", () => {
  const meta = toMeta({
    ...base,
    segments: [
      {
        type: "complex_corner",
        name: "Esses",
        start_m: 100,
        end_m: 300,
        corner_numbers: [4, 5],
        corners: [
          { corner_number: 4, name: "Degner 1", start_m: 100, end_m: 200 },
          { corner_number: 5, start_m: 200, end_m: 300 },
        ],
      },
    ],
  });
  assert.deepEqual(meta.corners.map((c) => c.name), ["Degner 1", "Esses"]);
});
