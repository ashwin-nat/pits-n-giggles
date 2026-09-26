// Hardcoded chart tuning constants -- "hardcode now, make configurable later
// if needed" per the frontend spec (see its Rate section). Nothing here reads
// from the sensor manifest or a settings source.

// The shared distance grid interpolation/rate-of-change operate on. 1 metre
// per the frontend spec's Interpolation section.
export const DISTANCE_GRID_RESOLUTION_M = 1;

// Moving-average window (in grid samples) used by the Rate mode smoothing
// pass, before the finite-difference step. See the frontend spec's Rate
// section for why this is a sample count rather than a distance.
export const SMOOTHING_WINDOW_SAMPLES = 10;

// Taller than the frontend spec's original 120/80/60 table -- that felt
// visibly squished in practice, especially for discrete step lines. One
// height for every sensor regardless of type -- a discrete lane (e.g. Gear)
// sitting visibly shorter than a continuous one (e.g. Speed) right next to
// it read as a layout bug, not a deliberate size difference.
export const LANE_HEIGHT_PX = 160;

// The x-axis (tick labels + "Distance (m)" title) needs its own vertical
// space on top of the plot area -- it isn't optional headroom the lane
// height already includes. Every lane renders its own axis now (ChartLane),
// so this is unconditional; without it the data line would sit flush
// against the plot's bottom edge, squeezed by axis text drawn over it.
export const X_AXIS_EXTRA_HEIGHT_PX = 40;

export function getChartHeightPx(heightOverridePx?: number): number {
  return (heightOverridePx ?? LANE_HEIGHT_PX) + X_AXIS_EXTRA_HEIGHT_PX;
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
export const DELTA_TRACE_COLOR = "#facc15"; // amber-400 -- distinct from both above
