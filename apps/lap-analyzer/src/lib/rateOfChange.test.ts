import { test } from "node:test";
import assert from "node:assert/strict";
import { computeRateOfChange } from "./rateOfChange";
import type { InterpolatedPoint } from "./interpolation";

function series(values: number[]): InterpolatedPoint[] {
  return values.map((value, i) => ({ lapDistance: i, value }));
}

test("computeRateOfChange: constant series produces a zero rate everywhere but the last point", () => {
  const points = series([10, 10, 10, 10, 10]);

  const result = computeRateOfChange(points, 2);

  assert.deepEqual(
    result.map((p) => p.value),
    [0, 0, 0, 0, null]
  );
});

test("computeRateOfChange: monotonically increasing series produces a positive rate", () => {
  const points = series([0, 1, 2, 3, 4, 5]);

  // Window 0 (half = 0) means each smoothed point is just itself -- no
  // smoothing -- so the finite difference is a constant +1 (except the
  // trailing gap, which has no next point to difference against).
  const result = computeRateOfChange(points, 0);

  assert.deepEqual(
    result.map((p) => p.value),
    [1, 1, 1, 1, 1, null]
  );
});

test("computeRateOfChange: a fluctuating series produces signed (positive and negative) rates", () => {
  const points = series([0, 10, 0, 10, 0]);

  const result = computeRateOfChange(points, 0); // no smoothing

  const values = result.map((p) => p.value);
  assert.equal(values[0], 10);
  assert.equal(values[1], -10);
  assert.equal(values[2], 10);
  assert.equal(values[3], -10);
  assert.equal(values[4], null);
});

test("computeRateOfChange: edge points use whatever window is available rather than padding", () => {
  // Window of 10 (half = 5) on a 3-point series -- every point's window is
  // clamped to the full available range, not padded with zeros/NaN.
  const points = series([10, 20, 30]);

  const result = computeRateOfChange(points, 10);

  // All three points average the same full [10,20,30] window (mean = 20),
  // so the smoothed series is flat and the rate is 0 except the trailing gap.
  assert.deepEqual(
    result.map((p) => p.value),
    [0, 0, null]
  );
});

test("computeRateOfChange: null samples inside the window are skipped, not treated as zero", () => {
  const points: InterpolatedPoint[] = [
    { lapDistance: 0, value: 10 },
    { lapDistance: 1, value: null },
    { lapDistance: 2, value: 10 },
  ];

  const result = computeRateOfChange(points, 2);

  // The window average at every point skips the null and averages only the
  // real 10s -- if null were treated as 0, the average would drop below 10.
  assert.deepEqual(
    result.map((p) => p.value),
    [0, 0, null]
  );
});

test("computeRateOfChange: an entirely-null series produces an all-null rate", () => {
  const points: InterpolatedPoint[] = [
    { lapDistance: 0, value: null },
    { lapDistance: 1, value: null },
  ];

  const result = computeRateOfChange(points, 2);

  assert.deepEqual(
    result.map((p) => p.value),
    [null, null]
  );
});
