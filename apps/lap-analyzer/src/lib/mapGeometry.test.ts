import { test } from "node:test";
import assert from "node:assert/strict";
import {
  buildMapGeometry,
  centreOn,
  clampZoom,
  drivenLine,
  edgeAt,
  pointAt,
  sectionBox,
  sectionPolygon,
  smoothClosed,
  subdivideFrac,
  tickAt,
  toMap,
  zoomAbout,
  type Box,
  type MapGeometry,
} from "./mapGeometry";
import type { TelemetryPoint } from "../types/api";

// A 100 x 100 square circuit, road 10 wide, 8 gates, one gate per 1/8 lap.
function squareEdges(): { edges: Float32Array; frac: Float32Array } {
  const mids: [number, number][] = [
    [0, 0], [50, 0], [100, 0], [100, 50], [100, 100], [50, 100], [0, 100], [0, 50],
  ];
  const edges: number[] = [];
  mids.forEach(([x, z]) => edges.push(x - 5, 0, z - 5, x + 5, 0, z + 5));
  return { edges: Float32Array.from(edges), frac: Float32Array.from(mids.map((_, i) => i / 8)) };
}

function geometry(): MapGeometry {
  const { edges, frac } = squareEdges();
  const g = buildMapGeometry(edges, frac);
  assert.ok(g);
  return g;
}

test("smoothClosed passes through every input point and closes the loop", () => {
  const pts: [number, number][] = [[0, 0], [10, 0], [10, 10], [0, 10]];
  const out = smoothClosed(pts, 4);
  assert.equal(out.length, 16);
  pts.forEach((p, i) => assert.deepEqual(out[i * 4], p));
});

test("subdivideFrac runs linearly between gates and on to 1 after the last", () => {
  assert.deepEqual(subdivideFrac([0, 0.5], 2), [0, 0.25, 0.5, 0.75]);
});

test("buildMapGeometry keeps the edge arrays and fractions the same length", () => {
  const g = geometry();
  assert.equal(g.L.length, g.R.length);
  assert.equal(g.L.length, g.F.length);
  assert.equal(g.L.length, 32);
});

test("buildMapGeometry rejects too few gates or a mismatched fraction array", () => {
  assert.equal(buildMapGeometry(new Float32Array(12), new Float32Array(2)), null);
  assert.equal(buildMapGeometry(new Float32Array(36), new Float32Array(5)), null);
});

test("edgeAt at a gate fraction returns that gate's smoothed edges", () => {
  const g = geometry();
  const { l, r } = edgeAt(g, 0.5);
  // Gate 4 is the (100, 100) corner; its edges are 10 apart.
  assert.ok(Math.abs(Math.hypot(r[0] - l[0], r[1] - l[1]) - Math.hypot(10, 10)) < 1e-6);
});

test("edgeAt wraps: 1.25 and -0.75 are the same place as 0.25", () => {
  const g = geometry();
  assert.deepEqual(edgeAt(g, 1.25), edgeAt(g, 0.25));
  const a = edgeAt(g, -0.75);
  const b = edgeAt(g, 0.25);
  assert.ok(Math.abs(a.l[0] - b.l[0]) < 1e-9 && Math.abs(a.r[1] - b.r[1]) < 1e-9);
});

test("edgeAt past the last subdivided point interpolates back to the first (the closed loop)", () => {
  const g = geometry();
  const last = g.F[g.F.length - 1];
  const { l } = edgeAt(g, (last + 1) / 2);
  const from = g.L[g.L.length - 1];
  const to = g.L[0];
  assert.ok(Math.abs(l[0] - (from[0] + to[0]) / 2) < 1e-9);
});

test("tickAt reaches the overhang fraction past each edge", () => {
  const g = geometry();
  const { l, r } = edgeAt(g, 0.3);
  const [a, b] = tickAt(g, 0.3, 0.5);
  const width = Math.hypot(r[0] - l[0], r[1] - l[1]);
  assert.ok(Math.abs(Math.hypot(b[0] - a[0], b[1] - a[1]) - width * 2) < 1e-6);
});

test("sectionPolygon covers the road between the two fractions", () => {
  const g = geometry();
  const poly = sectionPolygon(g, 0.1, 0.2, 10);
  assert.equal(poly.length, 22);
});

test("sectionBox is a square holding the whole section, padded", () => {
  const g = geometry();
  const box = sectionBox(g, 0.0, 0.25);
  assert.ok(box);
  assert.equal(box[2], box[3]);
  const poly = sectionPolygon(g, 0, 0.25);
  for (const [x, y] of poly) {
    assert.ok(x >= box[0] && x <= box[0] + box[2] && y >= box[1] && y <= box[1] + box[3]);
  }
});

test("toMap undoes the uniform scale and the centring of a non-matching aspect", () => {
  const rect = { left: 10, top: 20, width: 400, height: 400 };
  // 200x100 box in a 400x400 rect: scale 2, 100px margin above and below.
  assert.deepEqual(toMap(rect, [0, 0, 200, 100], 10 + 100, 20 + 100 + 50), [50, 25]);
});

test("zoomAbout keeps the point under the pointer", () => {
  const rect = { left: 0, top: 0, width: 400, height: 400 };
  const vb: Box = [0, 0, 200, 200];
  const p = toMap(rect, vb, 300, 100);
  const zoomed = zoomAbout(vb, p, 0.5);
  assert.deepEqual(zoomed, [75, 25, 100, 100]);
  assert.deepEqual(toMap(rect, zoomed, 300, 100), p);
});

test("centreOn keeps the size and moves the centre", () => {
  assert.deepEqual(centreOn([0, 0, 100, 50], [200, 200]), [150, 175, 100, 50]);
});

test("clampZoom holds the view between 36 units and the whole track", () => {
  const whole: Box = [0, 0, 1000, 800];
  assert.equal(clampZoom([0, 0, 10, 10], whole)[2], 36);
  assert.equal(clampZoom([0, 0, 5000, 5000], whole)[2], 1000);
  assert.deepEqual(clampZoom([0, 0, 200, 200], whole), [0, 0, 200, 200]);
});

test("drivenLine skips samples with no position, and pointAt is null outside the recorded range", () => {
  const pts: TelemetryPoint[] = [
    { lapDistance: 0, "motion.position.x": 1, "motion.position.z": 2 },
    { lapDistance: 10, "motion.position.x": NaN, "motion.position.z": 3 },
    { lapDistance: 20, "motion.position.x": 5, "motion.position.z": 6 },
    { lapDistance: 30 },
  ];
  const line = drivenLine(pts);
  assert.deepEqual(line.dist, [0, 20]);
  assert.deepEqual(pointAt(line, 20), [5, 6]);
  assert.equal(pointAt(line, 25), null);
  assert.equal(pointAt(line, null), null);
  assert.deepEqual(drivenLine(undefined), { pts: [], dist: [] });
});
