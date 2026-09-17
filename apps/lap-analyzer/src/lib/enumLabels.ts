// Frontend-owned mapping for discrete sensors whose integer values represent
// named states rather than raw magnitudes -- see the frontend spec's
// "Enum-backed sensor labels" section. Not part of the API response or the
// .pngt file; the set of enum-backed sensors is small and stable across
// sessions for a given game version, same reasoning as TEAM_COLORS.
export const ENUM_LABELS: Record<string, Record<number, string>> = {
  "ers.deploy_mode": { 0: "None", 1: "Medium", 2: "Hotlap", 3: "Overtake" },
  // TODO - update after producer implementation of surface type enum
  "track.surface_type": { 0: "Tarmac", 1: "Gravel", 2: "Grass", 3: "Rumble Strip" },
};

// Header value displays and hover tooltips resolve through this; the y-axis
// itself keeps showing raw step positions (see spec) so this is never used
// for tick labels.
export function resolveEnumLabel(sensorKey: string, value: number): string | null {
  return ENUM_LABELS[sensorKey]?.[value] ?? null;
}
