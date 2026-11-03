// Frontend-owned mapping for discrete sensors whose integer values represent
// named states rather than raw magnitudes -- see the frontend spec's
// "Enum-backed sensor labels" section. Not part of the API response or the
// .pngt file; the set of enum-backed sensors is small and stable across
// sessions for a given game version, same reasoning as TEAM_COLORS.
// Mirrors CarTelemetryData.SurfaceType in lib/f1_types. 255 is the producer's
// UNKNOWN sentinel for any ID the game adds later.
const SURFACE_TYPE_LABELS: Record<number, string> = {
  0: "Tarmac", 1: "Rumble Strip", 2: "Concrete", 3: "Rock", 4: "Gravel", 5: "Mud",
  6: "Sand", 7: "Grass", 8: "Water", 9: "Cobblestone", 10: "Metal", 11: "Ridged",
  255: "Unknown",
};

export const ENUM_LABELS: Record<string, Record<number, string>> = {
  "ers.deploy_mode": { 0: "None", 1: "Medium", 2: "Hotlap", 3: "Overtake" },
  "surface_type.fl": SURFACE_TYPE_LABELS,
  "surface_type.fr": SURFACE_TYPE_LABELS,
  "surface_type.rl": SURFACE_TYPE_LABELS,
  "surface_type.rr": SURFACE_TYPE_LABELS,
};

// Header value displays and hover tooltips resolve through this; the y-axis
// itself keeps showing raw step positions (see spec) so this is never used
// for tick labels.
export function resolveEnumLabel(sensorKey: string, value: number): string | null {
  return ENUM_LABELS[sensorKey]?.[value] ?? null;
}
