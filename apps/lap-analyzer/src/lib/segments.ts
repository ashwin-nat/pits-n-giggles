import type { TrackSection } from "../types/api";

// Bundled static asset, synced from the main repo's assets/track-segments/
// via scripts/sync-segments.ts (see that script's header comment). Segments
// are keyed by circuit_number *inside* each file, not by filename -- mirrors
// lib/track_segment_info/database.py's TrackSegmentsDatabase.
interface SegmentEntry {
  type: "straight" | "corner" | "complex_corner";
  name?: string; // written only when set: unnamed corners have no key
  start_m: number;
  end_m: number;
  corner_number?: number;
  corner_numbers?: number[];
  brake_boards?: RawBrakeBoard[];
  // Sub-corners of a complex corner, each with its own boards.
  corners?: { corner_number: number; start_m: number; end_m: number; brake_boards?: RawBrakeBoard[] }[];
}

interface RawBrakeBoard {
  distance_m: number;
  at_m: number;
  side: BrakeBoardSide;
}

interface SegmentsFile {
  circuit_name: string;
  circuit_number: number;
  track_length: number;
  speed_trap_m: number;
  drs_zones: { id: number; detection_m: number; activation: { start_m: number; end_m: number }[] }[];
  overtake_dist: { detection_m: number; activation_m: number };
  active_aero_zones: { mode: AeroMode; start_m: number; end_m: number }[];
  segments: SegmentEntry[];
  sectors: { s1: number; s2: number };
}

export type BrakeBoardSide = "left" | "right" | "both";
export type AeroMode = "full" | "partial";

// A range of lap distance in metres. end < start means it crosses the start/finish line.
export interface DistanceRange {
  startM: number;
  endM: number;
}

export interface DrsZone {
  id: number;
  detectionM: number;
  activation: DistanceRange[];
}

export interface AeroZone extends DistanceRange {
  mode: AeroMode;
}

// A "150 / 100 / 50" board: `distanceM` is its marked distance to the corner, `atM` where it stands.
export interface BrakeBoard {
  cornerNumber: number;
  distanceM: number;
  atM: number;
  side: BrakeBoardSide;
}

// One numbered corner's span, sub-corners of a complex corner counted separately.
export interface CornerSpan {
  number: number;
  // The segment's name; a complex corner's sub-corners share it. Empty when the segment is unnamed.
  name: string;
  startM: number;
  endM: number;
}

export interface TrackMeta {
  name: string;
  trackLength: number;
  sections: TrackSection[];
  // Sector *boundaries* -- s1/s2 are the distances where sector 1 ends and
  // sector 2 ends; sector 3 runs from s2 to trackLength. Matches the file
  // format's own s1/s2-only shape (no s3 key), not a full 3-tuple.
  sectorBoundaries: { s1: number; s2: number };
  speedTrapM: number;
  drsZones: DrsZone[];
  overtake: { detectionM: number; activationM: number };
  activeAeroZones: AeroZone[];
  brakeBoards: BrakeBoard[];
  corners: CornerSpan[];
}

function toBoards(data: SegmentsFile): BrakeBoard[] {
  const out: BrakeBoard[] = [];
  const add = (cornerNumber: number, boards: RawBrakeBoard[] | undefined) => {
    for (const b of boards ?? []) {
      out.push({ cornerNumber, distanceM: b.distance_m, atM: b.at_m, side: b.side });
    }
  };
  for (const s of data.segments) {
    if (s.corners !== undefined) {
      s.corners.forEach((c) => add(c.corner_number, c.brake_boards));
    } else if (s.corner_number !== undefined) {
      add(s.corner_number, s.brake_boards);
    }
  }
  return out;
}

function toCorners(data: SegmentsFile): CornerSpan[] {
  const out: CornerSpan[] = [];
  for (const s of data.segments) {
    if (s.corners !== undefined) {
      s.corners.forEach((c) => out.push({ number: c.corner_number, name: s.name ?? "", startM: c.start_m, endM: c.end_m }));
    } else if (s.corner_number !== undefined) {
      out.push({ number: s.corner_number, name: s.name ?? "", startM: s.start_m, endM: s.end_m });
    }
  }
  return out;
}

function toSections(data: SegmentsFile): TrackSection[] {
  return data.segments.map((s) => ({
    label: s.name ?? "",
    distanceStart: s.start_m,
    distanceEnd: s.end_m,
    type: s.type,
    cornerNumbers: s.corner_numbers ?? (s.corner_number !== undefined ? [s.corner_number] : []),
  }));
}

function toMeta(data: SegmentsFile): TrackMeta {
  return {
    name: data.circuit_name,
    trackLength: data.track_length,
    sections: toSections(data),
    sectorBoundaries: data.sectors,
    speedTrapM: data.speed_trap_m,
    drsZones: data.drs_zones.map((z) => ({
      id: z.id,
      detectionM: z.detection_m,
      activation: z.activation.map((a) => ({ startM: a.start_m, endM: a.end_m })),
    })),
    overtake: { detectionM: data.overtake_dist.detection_m, activationM: data.overtake_dist.activation_m },
    activeAeroZones: data.active_aero_zones.map((z) => ({ mode: z.mode, startM: z.start_m, endM: z.end_m })),
    brakeBoards: toBoards(data),
    corners: toCorners(data),
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

// Every bundled layout, keyed by track id -- the calendar the track picker
// lists "not driven yet" from.
export async function getAllTrackMeta(): Promise<Map<number, TrackMeta>> {
  return getCache();
}
