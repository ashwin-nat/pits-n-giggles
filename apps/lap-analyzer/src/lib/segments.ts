import type { TrackSection } from "../types/api";

// Bundled static asset, synced from the main repo's assets/track-segments/
// via scripts/sync-segments.ts (see that script's header comment). Segments
// are keyed by circuit_number *inside* each file, not by filename -- mirrors
// lib/track_segment_info/database.py's TrackSegmentsDatabase.
interface SegmentEntry {
  type: string;
  name: string;
  start_m: number;
  end_m: number;
}

interface SegmentsFile {
  circuit_name: string;
  circuit_number: number;
  track_length: number;
  segments: SegmentEntry[];
}

function toSections(data: SegmentsFile): TrackSection[] {
  return data.segments.map((s) => ({ label: s.name, distanceStart: s.start_m, distanceEnd: s.end_m }));
}

// Two loading strategies for the same directory, picked at runtime:
//
// - In the browser bundle (LocalFileProvider, via App.tsx), Vite resolves
//   import.meta.glob at *build* time into eagerly-bundled modules -- no
//   filesystem access happens in the shipped browser code, which is required
//   since Node builtins are stubbed to `{}` there and any actual fs call
//   throws on module load (see git history for the incident this fixes).
// - Under `pnpm dev:manual-test` (plain tsx, no Vite transform at all),
//   import.meta.glob doesn't exist -- that path uses real fs/path/url.
//
// `import.meta.env` is always defined when a module is processed by Vite
// and always undefined under plain tsx/Node, so it's used as the feature
// check for which branch actually runs.
const runningUnderVite = typeof import.meta.env !== "undefined";

async function loadViaVite(): Promise<Map<number, TrackSection[]>> {
  const modules = import.meta.glob<{ default: SegmentsFile }>("../assets/segments/*.json");
  const map = new Map<number, TrackSection[]>();
  for (const load of Object.values(modules)) {
    const { default: data } = await load();
    map.set(data.circuit_number, toSections(data));
  }
  return map;
}

async function loadViaNodeFs(): Promise<Map<number, TrackSection[]>> {
  const { readFileSync, readdirSync } = await import("node:fs");
  const { dirname, join } = await import("node:path");
  const { fileURLToPath } = await import("node:url");
  const moduleDir = dirname(fileURLToPath(import.meta.url));
  const segmentsDir = join(moduleDir, "..", "assets", "segments");

  const map = new Map<number, TrackSection[]>();
  for (const file of readdirSync(segmentsDir)) {
    if (!file.endsWith(".json")) {
      continue;
    }
    const data = JSON.parse(readFileSync(join(segmentsDir, file), "utf-8")) as SegmentsFile;
    map.set(data.circuit_number, toSections(data));
  }
  return map;
}

let cachePromise: Promise<Map<number, TrackSection[]>> | null = null;

export async function getTrackSections(trackId: number): Promise<TrackSection[]> {
  if (cachePromise === null) {
    cachePromise = runningUnderVite ? loadViaVite() : loadViaNodeFs();
  }
  const cache = await cachePromise;
  return cache.get(trackId) ?? [];
}
