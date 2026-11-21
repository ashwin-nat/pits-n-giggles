// Session and track grouping for the picker modals. Pure, for sessionFilters.test.ts.
import type { Session } from "../types/api";

// The game a session belongs to, e.g. "F1 2025". Filters every track and session list.
export function gameLabel(session: Pick<Session, "formula" | "gameYear">): string {
  return `${session.formula} ${session.gameYear}`.trim();
}

// Distinct games, newest year first.
export function listGames(sessions: readonly Session[]): { label: string; count: number }[] {
  const counts = new Map<string, { year: number; count: number }>();
  for (const s of sessions) {
    const label = gameLabel(s);
    const entry = counts.get(label) ?? { year: s.gameYear, count: 0 };
    entry.count++;
    counts.set(label, entry);
  }
  return [...counts.entries()]
    .sort((a, b) => b[1].year - a[1].year || a[0].localeCompare(b[0]))
    .map(([label, { count }]) => ({ label, count }));
}

// The game every list is filtered to: the user's pick, else the reference
// lap's game, else the newest game. null only when there are no sessions.
export function effectiveGame(
  sessions: readonly Session[],
  picked: string | null,
  referenceSessionId: string | null
): string | null {
  if (picked !== null) {
    return picked;
  }
  const reference = sessions.find((s) => s.id === referenceSessionId);
  return reference === undefined ? (listGames(sessions)[0]?.label ?? null) : gameLabel(reference);
}

export function newestFirst(sessions: readonly Session[]): Session[] {
  return [...sessions].sort((a, b) => b.date.localeCompare(a.date));
}

// Comparison laps come from the same circuit and formula as A. Formula only,
// not year: a formula is a regulation era and years can have gaps.
export function comparableSessions(sessions: readonly Session[], reference: Session): Session[] {
  return sessions.filter((s) => s.trackId === reference.trackId && s.formula === reference.formula);
}

export interface TrackSummary {
  trackId: number;
  name: string;
  sessionCount: number;
  lastDate: string;
  raceBestMs: number | null;
  timeTrialBestMs: number | null;
}

function bestOf(sessions: readonly Session[], type: string): number | null {
  const times = sessions.filter((s) => s.type === type && s.sessionBest !== null).map((s) => s.sessionBest!.lapTimeMs);
  return times.length > 0 ? Math.min(...times) : null;
}

export function summariseTracks(sessions: readonly Session[]): TrackSummary[] {
  const byTrack = new Map<number, Session[]>();
  for (const s of sessions) {
    byTrack.set(s.trackId, [...(byTrack.get(s.trackId) ?? []), s]);
  }
  return [...byTrack.entries()].map(([trackId, list]) => ({
    trackId,
    name: list[0].trackName,
    sessionCount: list.length,
    lastDate: list.reduce((a, s) => (s.date > a ? s.date : a), ""),
    raceBestMs: bestOf(list, "Race"),
    timeTrialBestMs: bestOf(list, "Time Trial"),
  }));
}

export type TrackOrder = "calendar" | "recent" | "driven";

// Calendar follows the game's track ids, which run in calendar order.
export function sortTracks(tracks: readonly TrackSummary[], order: TrackOrder): TrackSummary[] {
  const sorted = [...tracks];
  if (order === "calendar") {
    sorted.sort((a, b) => a.trackId - b.trackId);
  } else if (order === "recent") {
    sorted.sort((a, b) => b.lastDate.localeCompare(a.lastDate));
  } else {
    sorted.sort((a, b) => b.sessionCount - a.sessionCount || a.trackId - b.trackId);
  }
  return sorted;
}
