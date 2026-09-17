// Team color is a rendering concern, not session data (see API and file
// format specs) -- the frontend owns this mapping outright, same pattern as
// ENUM_LABELS for chart-side enum sensors. Keyed by `driver.team` exactly as
// given by the sim (always uppercase in the .pngt format); update when team
// names/liveries change.
//
// Values carried over from apps/frontend/js/utils.js's getF1TeamColor, the
// existing source of truth for team colors elsewhere in this app -- re-keyed
// to uppercase and including legacy names (VCARB, Alpha Tauri, Alfa Romeo)
// for older recordings.
export const TEAM_COLORS: Record<string, string> = {
  "RED BULL RACING": "rgba(54,113,198,1)",
  "RED BULL": "rgba(54,113,198,1)",
  VCARB: "rgba(102,146,255,1)",
  RB: "rgba(102,146,255,1)",
  MERCEDES: "rgba(39,244,210,1)",
  FERRARI: "rgba(232,0,45,1)",
  MCLAREN: "rgba(255,128,0,1)",
  "ASTON MARTIN": "rgba(34,153,113,1)",
  ALPINE: "rgba(255,135,188,1)",
  "ALPHA TAURI": "rgba(30,40,80,1)",
  "ALFA ROMEO": "rgba(155,0,0,1)",
  HAAS: "rgba(182,186,189,1)",
  WILLIAMS: "rgba(100,196,255,1)",
  SAUBER: "rgba(82,226,82,1)",
};

export const DEFAULT_TEAM_COLOR = "rgba(128,128,128,1)";

export function getTeamColor(team: string): string {
  return TEAM_COLORS[team] ?? DEFAULT_TEAM_COLOR;
}
