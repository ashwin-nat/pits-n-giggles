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

// One height for every sensor type -- a shorter discrete lane next to a
// taller continuous one read as a layout bug, not a deliberate difference.
export const LANE_HEIGHT_PX = 100;

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

// Lap slots: A is the reference lap, B to D comparison laps (C0 spec). Hex
// mirrors --color-slot-* in index.css because uPlot and SVG need literals.
export const MAX_COMPARISON_LAPS = 3;
export const LAP_SLOT_COLORS = ["#0aa2c6", "#ea580c", "#facc15", "#f472b6"] as const;
export const LAP_SLOT_LETTERS = ["A", "B", "C", "D"] as const;
