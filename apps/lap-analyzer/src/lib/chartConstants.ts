// Hardcoded chart tuning constants -- "hardcode now, make configurable later
// if needed" per the frontend spec (see its Rate section). Nothing here reads
// from the sensor manifest or a settings source.
import type { SensorDefinition } from "../types/api";

// The shared distance grid interpolation/rate-of-change operate on. 1 metre
// per the frontend spec's Interpolation section.
export const DISTANCE_GRID_RESOLUTION_M = 1;

// Moving-average window (in grid samples) used by the Rate mode smoothing
// pass, before the finite-difference step. See the frontend spec's Rate
// section for why this is a sample count rather than a distance.
export const SMOOTHING_WINDOW_SAMPLES = 10;

// Taller than the frontend spec's original 120/80/60 table -- that felt
// visibly squished in practice, especially for discrete step lines.
export const CONTINUOUS_LANE_HEIGHT_PX = 160;
export const CONTINUOUS_SMALL_LANE_HEIGHT_PX = 110;
export const DISCRETE_LANE_HEIGHT_PX = 90;

// The frontend spec calls out throttle/brake/ERS as "continuous small" by
// example, but the real sensor catalog doesn't exist yet -- it's built by
// the ingest layer in Phase 7. This is a provisional key list matched
// against the fixture's sensors, meant to be revisited once real sensor keys
// are known, not a final catalog.
const SMALL_CONTINUOUS_SENSOR_KEYS = new Set(["throttle", "brake"]);

export function getLaneHeightPx(sensor: SensorDefinition): number {
  if (sensor.type === "discrete") {
    return DISCRETE_LANE_HEIGHT_PX;
  }
  return SMALL_CONTINUOUS_SENSOR_KEYS.has(sensor.key) ? CONTINUOUS_SMALL_LANE_HEIGHT_PX : CONTINUOUS_LANE_HEIGHT_PX;
}

// The x-axis (tick labels + "Distance (m)" title, shown only on the
// bottom-most lane per spec) needs its own vertical space on top of the
// plot area -- it isn't optional headroom the lane height already includes.
// Without this, whichever lane ends up on the bottom loses most of its
// already-small height to axis text, squeezing the actual data line flush
// against the top border (most visible on a short discrete lane).
export const X_AXIS_EXTRA_HEIGHT_PX = 40;

export function getChartHeightPx(sensor: SensorDefinition, isBottomLane: boolean, heightOverridePx?: number): number {
  return (heightOverridePx ?? getLaneHeightPx(sensor)) + (isBottomLane ? X_AXIS_EXTRA_HEIGHT_PX : 0);
}

// Per-lane resize step/bounds -- view-local state (ChartLaneList), not
// persisted across a reload, same as legend visibility and the crosshair.
export const LANE_HEIGHT_STEP_PX = 20;
export const MIN_LANE_HEIGHT_PX = 60;
export const MAX_LANE_HEIGHT_PX = 400;

// Fixed, not derived from team livery (TEAM_COLORS/getTeamColor() in
// teamColors.ts, still used elsewhere -- e.g. the driver selector). Team
// color meant two same-team drivers rendered in the *identical* color here,
// distinguished only by solid-vs-dashed line style -- easy to miss. Every
// chart trace is just "primary" or "comparison" now, no per-driver variation.
export const PRIMARY_TRACE_COLOR = "#ef4444"; // red-500
export const COMPARISON_TRACE_COLOR = "#3b82f6"; // blue-500
