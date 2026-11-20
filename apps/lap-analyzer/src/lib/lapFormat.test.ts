import { test } from "node:test";
import assert from "node:assert/strict";
import { formatGap, formatLapTime, isWholeLap } from "./lapFormat";

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

test("isWholeLap needs a time and a complete recording; absent complete counts as complete", () => {
  assert.equal(isWholeLap({ lapTime: 80000 }), true);
  assert.equal(isWholeLap({ lapTime: 80000, complete: true }), true);
  assert.equal(isWholeLap({ lapTime: 80000, complete: false }), false);
  assert.equal(isWholeLap({ lapTime: null }), false);
});
