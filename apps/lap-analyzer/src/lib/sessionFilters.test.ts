import { test } from "node:test";
import assert from "node:assert/strict";
import { comparableSessions, effectiveGame, gameLabel, listGames, newestFirst, sortTracks, summariseTracks } from "./sessionFilters";
import type { Session } from "../types/api";

function session(id: string, over: Partial<Session> = {}): Session {
  return {
    id,
    name: id,
    trackId: 7,
    trackName: "Monza",
    date: "2026-01-01T10:00:00Z",
    type: "Race",
    appVersion: "5",
    gameYear: 2025,
    formula: "F1",
    gameVersion: "1",
    sessionBest: null,
    sensorManifest: [],
    ...over,
  };
}

test("listGames counts sessions per game, newest year first", () => {
  const games = listGames([session("a"), session("b"), session("c", { gameYear: 2024 })]);
  assert.deepEqual(games, [
    { label: "F1 2025", count: 2 },
    { label: "F1 2024", count: 1 },
  ]);
  assert.equal(gameLabel(session("a")), "F1 2025");
  assert.equal(gameLabel(session("a", { formula: "F1 Modern" })), "F1 2025");
  assert.equal(gameLabel(session("a", { formula: "Supercars" })), "Supercars 2025");
  assert.equal(gameLabel(session("a", { formula: "F1 26", gameYear: 2026 })), "F1 26");
});

test("effectiveGame: the pick, else A's game, else the newest game", () => {
  const sessions = [session("a"), session("b", { gameYear: 2024 })];
  assert.equal(effectiveGame(sessions, "F1 2024", "a"), "F1 2024");
  assert.equal(effectiveGame(sessions, null, "b"), "F1 2024");
  assert.equal(effectiveGame(sessions, null, null), "F1 2025");
  assert.equal(effectiveGame([], null, null), null);
});

test("newestFirst orders by date descending without mutating the input", () => {
  const input = [session("old", { date: "2025-01-01" }), session("new", { date: "2026-01-01" })];
  assert.deepEqual(newestFirst(input).map((s) => s.id), ["new", "old"]);
  assert.equal(input[0].id, "old");
});

test("comparableSessions: same track and formula, any year", () => {
  const a = session("a");
  const list = [a, session("b", { gameYear: 2024 }), session("c", { trackId: 9 }), session("d", { formula: "F2" })];
  assert.deepEqual(comparableSessions(list, a).map((s) => s.id), ["a", "b"]);
});

test("summariseTracks: count, last date and the best race and time trial laps", () => {
  const tracks = summariseTracks([
    session("a", { sessionBest: { driverIndex: 0, lapNumber: 1, lapTimeMs: 82000 } }),
    session("b", { date: "2026-03-01", sessionBest: { driverIndex: 0, lapNumber: 1, lapTimeMs: 81000 } }),
    session("c", { type: "Time Trial", sessionBest: { driverIndex: 0, lapNumber: 1, lapTimeMs: 80000 } }),
    session("d", { trackId: 9, trackName: "Spa" }),
  ]);
  const monza = tracks.find((t) => t.trackId === 7)!;
  assert.equal(monza.sessionCount, 3);
  assert.equal(monza.lastDate, "2026-03-01");
  assert.equal(monza.raceBestMs, 81000);
  assert.equal(monza.timeTrialBestMs, 80000);
  assert.equal(tracks.find((t) => t.trackId === 9)!.raceBestMs, null);
});

test("sortTracks: calendar by id, recent by last date, driven by session count", () => {
  const tracks = [
    { trackId: 9, name: "Spa", sessionCount: 5, lastDate: "2026-01-01", raceBestMs: null, timeTrialBestMs: null },
    { trackId: 7, name: "Monza", sessionCount: 2, lastDate: "2026-02-01", raceBestMs: null, timeTrialBestMs: null },
  ];
  assert.deepEqual(sortTracks(tracks, "calendar").map((t) => t.trackId), [7, 9]);
  assert.deepEqual(sortTracks(tracks, "recent").map((t) => t.trackId), [7, 9]);
  assert.deepEqual(sortTracks(tracks, "driven").map((t) => t.trackId), [9, 7]);
});
