import type { TrackSection } from "../types/api";

// Bundled static asset, synced from the main repo's assets/track-segments/
// via scripts/sync-segments.ts (see that script's header comment). Segments
// are keyed by circuit_number *inside* each file, not by filename -- mirrors
// lib/track_segment_info/database.py's TrackSegmentsDatabase.
interface SegmentEntry {
  type: "straight" | "corner" | "complex_corner";
  name: string;
  start_m: number;
  end_m: number;
  corner_number?: number;
  corner_numbers?: number[];
}

interface SegmentsFile {
  circuit_name: string;
  circuit_number: number;
  track_length: number;
  segments: SegmentEntry[];
  sectors: { s1: number; s2: number };
}

export interface TrackMeta {
  trackLength: number;
  sections: TrackSection[];
  // Sector *boundaries* -- s1/s2 are the distances where sector 1 ends and
  // sector 2 ends; sector 3 runs from s2 to trackLength. Matches the file
  // format's own s1/s2-only shape (no s3 key), not a full 3-tuple.
  sectorBoundaries: { s1: number; s2: number };
}

function toSections(data: SegmentsFile): TrackSection[] {
  return data.segments.map((s) => ({
    label: s.name,
    distanceStart: s.start_m,
    distanceEnd: s.end_m,
    type: s.type,
    cornerNumbers: s.corner_numbers ?? (s.corner_number !== undefined ? [s.corner_number] : []),
  }));
}

function toMeta(data: SegmentsFile): TrackMeta {
  return {
    trackLength: data.track_length,
    sections: toSections(data),
    sectorBoundaries: data.sectors,
  };
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

async function loadViaVite(): Promise<Map<number, TrackMeta>> {
  const modules = import.meta.glob<{ default: SegmentsFile }>("../assets/segments/*.json");
  const map = new Map<number, TrackMeta>();
  for (const load of Object.values(modules)) {
    const { default: data } = await load();
    map.set(data.circuit_number, toMeta(data));
  }
  return map;
}

async function loadViaNodeFs(): Promise<Map<number, TrackMeta>> {
  const { readFileSync, readdirSync } = await import("node:fs");
  const { dirname, join } = await import("node:path");
  const { fileURLToPath } = await import("node:url");
  const moduleDir = dirname(fileURLToPath(import.meta.url));
  const segmentsDir = join(moduleDir, "..", "assets", "segments");

  const map = new Map<number, TrackMeta>();
  for (const file of readdirSync(segmentsDir)) {
    if (!file.endsWith(".json")) {
      continue;
    }
    const data = JSON.parse(readFileSync(join(segmentsDir, file), "utf-8")) as SegmentsFile;
    map.set(data.circuit_number, toMeta(data));
  }
  return map;
}

let cachePromise: Promise<Map<number, TrackMeta>> | null = null;

async function getCache(): Promise<Map<number, TrackMeta>> {
  if (cachePromise === null) {
    cachePromise = runningUnderVite ? loadViaVite() : loadViaNodeFs();
  }
  return cachePromise;
}

// Part of the LapAnalyzerProvider interface (providers/types.ts) -- every
// provider, including a future backend-backed one, must be able to answer
// this the same way.
export async function getTrackSections(trackId: number): Promise<TrackSection[]> {
  const cache = await getCache();
  return cache.get(trackId)?.sections ?? [];
}

// Not part of the provider interface -- track length and sector boundaries
// are bundled static data same as segments themselves (see the file-level
// comment), and TrackProgressBar/CurrentPositionLabel read them directly
// rather than through the provider abstraction. If a future RemoteApiProvider
// needs this too, it can grow its own endpoint for it then; nothing here
// depends on session/driver/lap data the way the rest of the provider
// interface does.
export async function getTrackMeta(trackId: number): Promise<TrackMeta | null> {
  const cache = await getCache();
  return cache.get(trackId) ?? null;
}
