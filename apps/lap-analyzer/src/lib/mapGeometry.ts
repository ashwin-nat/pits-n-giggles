// Track map maths: edge smoothing, lap-fraction placement, view box zoom and
// the driven line. Pure functions (no React, no DOM) so mapGeometry.test.ts
// can cover them. World (x, z) is drawn directly as SVG (x, y).
import type { TelemetryPoint } from "../types/api";

export type Pt = [number, number];
// SVG view box: x, y, width, height.
export type Box = [number, number, number, number];

export interface MapGeometry {
  // Left and right white lines and each point's lap fraction, one entry per
  // subdivided gate. Same length, closed loop (last point joins the first).
  L: Pt[];
  R: Pt[];
  F: number[];
}

// Gates are 20 to 90 m apart; this many points per gate after smoothing.
const POINTS_PER_GATE = 4;

// Closed Catmull-Rom through `points`, `perGate` samples per span.
export function smoothClosed(points: readonly Pt[], perGate: number = POINTS_PER_GATE): Pt[] {
  const n = points.length;
  if (n < 3) {
    return [...points];
  }
  const out: Pt[] = [];
  for (let i = 0; i < n; i++) {
    const p0 = points[(i - 1 + n) % n];
    const p1 = points[i];
    const p2 = points[(i + 1) % n];
    const p3 = points[(i + 2) % n];
    for (let k = 0; k < perGate; k++) {
      const t = k / perGate;
      const t2 = t * t;
      const t3 = t2 * t;
      const at = (a: number, b: number, c: number, d: number) =>
        0.5 * (2 * b + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t2 + (-a + 3 * b - 3 * c + d) * t3);
      out.push([at(p0[0], p1[0], p2[0], p3[0]), at(p0[1], p1[1], p2[1], p3[1])]);
    }
  }
  return out;
}

// Lap fraction for each subdivided point: linear between gates, the last span
// running on to 1 where the lap closes.
export function subdivideFrac(frac: ArrayLike<number>, perGate: number = POINTS_PER_GATE): number[] {
  const n = frac.length;
  const out: number[] = [];
  for (let i = 0; i < n; i++) {
    const a = frac[i];
    const b = i + 1 < n ? frac[i + 1] : 1;
    for (let k = 0; k < perGate; k++) {
      out.push(a + ((b - a) * k) / perGate);
    }
  }
  return out;
}

// edges is (N, 6): left xyz then right xyz per gate. Null when there is too little to draw.
export function buildMapGeometry(edges: ArrayLike<number>, frac: ArrayLike<number>): MapGeometry | null {
  const n = edges.length / 6;
  if (n < 3 || frac.length !== n) {
    return null;
  }
  const left: Pt[] = [];
  const right: Pt[] = [];
  for (let i = 0; i < n; i++) {
    left.push([edges[i * 6], edges[i * 6 + 2]]);
    right.push([edges[i * 6 + 3], edges[i * 6 + 5]]);
  }
  return { L: smoothClosed(left), R: smoothClosed(right), F: subdivideFrac(frac) };
}

// Left and right edge at lap fraction `frac` (wraps), by binary search then lerp.
export function edgeAt(g: MapGeometry, frac: number): { l: Pt; r: Pt } {
  const { L, R, F } = g;
  frac = ((frac % 1) + 1) % 1;
  let lo = 0;
  let hi = F.length - 1;
  if (frac >= F[hi]) {
    lo = hi;
  } else {
    while (hi - lo > 1) {
      const m = (lo + hi) >> 1;
      if (F[m] <= frac) {
        lo = m;
      } else {
        hi = m;
      }
    }
  }
  const j = (lo + 1) % F.length;
  const f2 = lo + 1 < F.length ? F[lo + 1] : 1;
  const u = f2 === F[lo] ? 0 : (frac - F[lo]) / (f2 - F[lo]);
  const mix = (a: Pt, b: Pt): Pt => [a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u];
  return { l: mix(L[lo], L[j]), r: mix(R[lo], R[j]) };
}

// A tick across the road at `frac`, reaching `overhang` of the road width past each edge.
export function tickAt(g: MapGeometry, frac: number, overhang: number): [Pt, Pt] {
  const { l, r } = edgeAt(g, frac);
  const dx = r[0] - l[0];
  const dy = r[1] - l[1];
  return [
    [l[0] - dx * overhang, l[1] - dy * overhang],
    [r[0] + dx * overhang, r[1] + dy * overhang],
  ];
}

// The road between two lap fractions as one polygon: left edge forward, right edge back.
export function sectionPolygon(g: MapGeometry, startFrac: number, endFrac: number, samples: number = 40): Pt[] {
  const left: Pt[] = [];
  const right: Pt[] = [];
  for (let i = 0; i <= samples; i++) {
    const { l, r } = edgeAt(g, startFrac + ((endFrac - startFrac) * i) / samples);
    left.push(l);
    right.push(r);
  }
  return [...left, ...right.reverse()];
}

export function boundsOf(points: readonly Pt[]): Box | null {
  if (points.length === 0) {
    return null;
  }
  let x0 = Infinity;
  let x1 = -Infinity;
  let y0 = Infinity;
  let y1 = -Infinity;
  for (const [x, y] of points) {
    x0 = Math.min(x0, x);
    x1 = Math.max(x1, x);
    y0 = Math.min(y0, y);
    y1 = Math.max(y1, y);
  }
  return [x0, y0, x1 - x0, y1 - y0];
}

// Bounding square of a point set, padded by `pad` of its size on each side.
export function squareBox(points: readonly Pt[], pad: number): Box | null {
  const b = boundsOf(points);
  if (b === null) {
    return null;
  }
  const side = Math.max(b[2], b[3]) * (1 + 2 * pad);
  const cx = b[0] + b[2] / 2;
  const cy = b[1] + b[3] / 2;
  return [cx - side / 2, cy - side / 2, side, side];
}

// The box for a section: its road between startFrac and endFrac, padded 25%.
export function sectionBox(g: MapGeometry, startFrac: number, endFrac: number): Box | null {
  return squareBox(sectionPolygon(g, startFrac, endFrac), 0.25);
}

export function padBox(box: Box, pad: number): Box {
  return [box[0] - pad, box[1] - pad, box[2] + 2 * pad, box[3] + 2 * pad];
}

// Client pixels to map units. The SVG scales the view box uniformly and
// centres it ("xMidYMid meet"), so undo both.
export function toMap(rect: { left: number; top: number; width: number; height: number }, vb: Box, clientX: number, clientY: number): Pt {
  const sc = Math.min(rect.width / vb[2], rect.height / vb[3]);
  const ox = (rect.width - vb[2] * sc) / 2;
  const oy = (rect.height - vb[3] * sc) / 2;
  return [vb[0] + (clientX - rect.left - ox) / sc, vb[1] + (clientY - rect.top - oy) / sc];
}

// Pixels per map unit for a view box drawn in `rect`.
export function pixelsPerUnit(rect: { width: number; height: number }, vb: Box): number {
  return Math.min(rect.width / vb[2], rect.height / vb[3]);
}

// Zoom by k about point p, keeping p under the pointer. k < 1 zooms in.
export function zoomAbout(vb: Box, p: Pt, k: number): Box {
  return [p[0] - (p[0] - vb[0]) * k, p[1] - (p[1] - vb[1]) * k, vb[2] * k, vb[3] * k];
}

// Keeps `vb`'s size, centred on p.
export function centreOn(vb: Box, p: Pt): Box {
  return [p[0] - vb[2] / 2, p[1] - vb[3] / 2, vb[2], vb[3]];
}

// Zoom limits as view box width: about 36 m up to the whole track.
export const MIN_VIEW_UNITS = 36;

export function clampZoom(vb: Box, whole: Box): Box {
  const maxW = Math.max(whole[2], whole[3]);
  const k = Math.min(Math.max(vb[2], MIN_VIEW_UNITS), maxW) / vb[2];
  if (k === 1) {
    return vb;
  }
  const cx = vb[0] + vb[2] / 2;
  const cy = vb[1] + vb[3] / 2;
  return [cx - (vb[2] * k) / 2, cy - (vb[3] * k) / 2, vb[2] * k, vb[3] * k];
}

export interface DrivenLine {
  pts: Pt[];
  dist: number[];
}

export const POSITION_KEYS = ["motion.position.x", "motion.position.z"] as const;

// The car's path from its recorded position; samples without a position are skipped.
export function drivenLine(telemetry: readonly TelemetryPoint[] | undefined): DrivenLine {
  const pts: Pt[] = [];
  const dist: number[] = [];
  for (const p of telemetry ?? []) {
    const x = p[POSITION_KEYS[0]];
    const z = p[POSITION_KEYS[1]];
    if (x !== undefined && z !== undefined && !Number.isNaN(x) && !Number.isNaN(z)) {
      pts.push([x, z]);
      dist.push(p.lapDistance);
    }
  }
  return { pts, dist };
}

// The car's position at lap distance d; null outside what was recorded.
export function pointAt(line: DrivenLine, d: number | null): Pt | null {
  if (d === null || line.dist.length === 0 || d < line.dist[0] || d > line.dist[line.dist.length - 1]) {
    return null;
  }
  let lo = 0;
  let hi = line.dist.length - 1;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (line.dist[mid] < d) {
      lo = mid + 1;
    } else {
      hi = mid;
    }
  }
  return line.pts[lo];
}

export function toPath(points: readonly Pt[], close: boolean): string {
  if (points.length === 0) {
    return "";
  }
  return "M" + points.map((p) => `${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join("L") + (close ? "Z" : "");
}
