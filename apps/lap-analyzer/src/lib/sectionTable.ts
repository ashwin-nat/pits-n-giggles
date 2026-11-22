// Section table under the map: A's minimum speed and each comparison lap's
// time delta per section. Pure functions for sectionTable.test.ts.
import type { TrackSection } from "../types/api";
import type { LoadedLap } from "./lapSeries";

const SPEED_KEY = "speed";
const TIME_KEY = "lap_time_ms";

// Real laps start and end a sample or two away from 0 and the track length,
// so a distance this close to the recorded range counts as its end sample.
const END_TOLERANCE_M = 25;

// Lap time at distance d, interpolated between samples; null outside the
// recorded range (plus END_TOLERANCE_M at each end).
export function timeAt(lap: LoadedLap, d: number): number | null {
  const pts = lap.points;
  if (pts.length === 0) {
    return null;
  }
  const first = pts[0].lapDistance;
  const last = pts[pts.length - 1].lapDistance;
  if (d < first - END_TOLERANCE_M || d > last + END_TOLERANCE_M) {
    return null;
  }
  d = Math.min(last, Math.max(first, d));
  let lo = 0;
  let hi = pts.length - 1;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (pts[mid].lapDistance < d) {
      lo = mid + 1;
    } else {
      hi = mid;
    }
  }
  const b = pts[lo];
  const a = pts[Math.max(0, lo - 1)];
  const span = b.lapDistance - a.lapDistance;
  const t = span === 0 ? 0 : (d - a.lapDistance) / span;
  // Recordings without lap_time_ms (older files) have no time to interpolate.
  const time = a[TIME_KEY] + t * (b[TIME_KEY] - a[TIME_KEY]);
  return Number.isFinite(time) ? time : null;
}

// Seconds the lap took to cover [start, end]; null if it did not record that stretch.
export function sectionTime(lap: LoadedLap, start: number, end: number): number | null {
  const t0 = timeAt(lap, start);
  const t1 = timeAt(lap, end);
  return t0 === null || t1 === null ? null : (t1 - t0) / 1000;
}

// Lowest speed inside [start, end]; null when the lap has no speed there.
export function minSpeed(lap: LoadedLap, start: number, end: number): number | null {
  let min: number | null = null;
  for (const p of lap.points) {
    const v = p[SPEED_KEY];
    if (p.lapDistance >= start && p.lapDistance <= end && v !== undefined && !Number.isNaN(v)) {
      min = min === null ? v : Math.min(min, v);
    }
  }
  return min;
}

// "+0.123" / "-0.050" seconds, "–" when the lap did not record the section.
export function formatSectionDelta(value: number | null): string {
  if (value === null) {
    return "–";
  }
  return `${value > 0 ? "+" : ""}${value.toFixed(3)}`;
}

export interface SectionRow {
  section: TrackSection;
  // A's minimum speed; null when A has no speed.
  minA: number | null;
  // One per slot (index 0 unused): (t_X - t_A) over the section, positive when the lap is slower than A.
  deltas: (number | null)[];
}

export function buildSectionRows(laps: readonly (LoadedLap | undefined)[], sections: readonly TrackSection[]): SectionRow[] {
  const a = laps[0];
  return [...sections]
    .sort((x, y) => x.distanceStart - y.distanceStart)
    .map((section) => {
      const { distanceStart: s, distanceEnd: e } = section;
      const timeA = a === undefined ? null : sectionTime(a, s, e);
      return {
        section,
        minA: a === undefined ? null : minSpeed(a, s, e),
        deltas: laps.map((lap, slot) => {
          if (slot === 0 || lap === undefined || timeA === null) {
            return null;
          }
          const timeX = sectionTime(lap, s, e);
          return timeX === null ? null : timeX - timeA;
        }),
      };
    });
}
