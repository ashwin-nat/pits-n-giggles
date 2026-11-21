import { test } from "node:test";
import assert from "node:assert/strict";
import { bestValidLapMs, formatGap, formatLapTime, isPartialLap } from "./lapFormat";

test("formatLapTime renders m:ss.mmm and a placeholder for a missing time", () => {
  assert.equal(formatLapTime(81900), "1:21.900");
  assert.equal(formatLapTime(60005), "1:00.005");
  assert.equal(formatLapTime(null), "–:––.–––");
});

test("formatGap is signed seconds", () => {
  assert.equal(formatGap(412), "+0.412");
  assert.equal(formatGap(-100), "-0.100");
  assert.equal(formatGap(0), "0.000");
});

test("isPartialLap is a timed lap recorded in part; absent complete counts as complete", () => {
  assert.equal(isPartialLap({ lapTime: 80000 }), false);
  assert.equal(isPartialLap({ lapTime: 80000, complete: true }), false);
  assert.equal(isPartialLap({ lapTime: 80000, complete: false }), true);
  assert.equal(isPartialLap({ lapTime: null, complete: false }), false);
});

test("bestValidLapMs ignores invalid and untimed laps", () => {
  const laps = [
    { lapTime: 88900, valid: false },
    { lapTime: 89500, valid: true },
    { lapTime: null, valid: true },
    { lapTime: 90100, valid: true },
  ];
  assert.equal(bestValidLapMs(laps), 89500);
  assert.equal(bestValidLapMs([{ lapTime: 88900, valid: false }]), null);
});
