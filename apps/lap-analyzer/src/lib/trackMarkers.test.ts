import { test } from "node:test";
import assert from "node:assert/strict";
import { splitWrapped, zoneRanges } from "./trackMarkers";
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
