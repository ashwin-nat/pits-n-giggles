// Rate mode's two-step computation from the frontend spec's Rate section:
// moving-average smoothing, then a signed finite difference. Operates on an
// already-interpolated 1-metre grid (see interpolation.ts), which is why the
// smoothing window is expressed as a sample count rather than a distance --
// on this grid the two are numerically identical (see spec).
import type { InterpolatedPoint } from "./interpolation";
import { SMOOTHING_WINDOW_SAMPLES } from "./chartConstants";

// - Edge points use whatever window is available, no padding.
// - Nulls in the window are skipped, not treated as zero.
function movingAverage(points: InterpolatedPoint[], windowSamples: number): Array<number | null> {
  const half = Math.floor(windowSamples / 2);
  const smoothed: Array<number | null> = new Array(points.length).fill(null);
  for (let i = 0; i < points.length; i++) {
    const lo = Math.max(0, i - half);
    const hi = Math.min(points.length - 1, i + half);
    let sum = 0;
    let count = 0;
    for (let j = lo; j <= hi; j++) {
      const v = points[j].value;
      if (v !== null) {
        sum += v;
        count++;
      }
    }
    smoothed[i] = count > 0 ? sum / count : null;
  }
  return smoothed;
}

// rate[i] = smoothed[i+1] - smoothed[i] (spec's simplified form, since grid
// spacing is a constant 1m). The last grid point has no next sample, so its
// rate is a gap rather than a repeated/extrapolated value.
export function computeRateOfChange(
  points: InterpolatedPoint[],
  windowSamples: number = SMOOTHING_WINDOW_SAMPLES
): InterpolatedPoint[] {
  const smoothed = movingAverage(points, windowSamples);
  return points.map((point, i) => {
    const current = smoothed[i];
    const next = i + 1 < smoothed.length ? smoothed[i + 1] : null;
    const value = current !== null && next !== null ? next - current : null;
    return { lapDistance: point.lapDistance, value };
  });
}
