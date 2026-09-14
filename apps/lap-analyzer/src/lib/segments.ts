import { readFileSync, readdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
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

const moduleDir = dirname(fileURLToPath(import.meta.url));
const SEGMENTS_DIR = join(moduleDir, "..", "assets", "segments");

let cache: Map<number, TrackSection[]> | null = null;

function loadAll(): Map<number, TrackSection[]> {
  const map = new Map<number, TrackSection[]>();
  for (const file of readdirSync(SEGMENTS_DIR)) {
    if (!file.endsWith(".json")) {
      continue;
    }
    const data = JSON.parse(readFileSync(join(SEGMENTS_DIR, file), "utf-8")) as SegmentsFile;
    map.set(
      data.circuit_number,
      data.segments.map((s) => ({ label: s.name, distanceStart: s.start_m, distanceEnd: s.end_m }))
    );
  }
  return map;
}

export function getTrackSections(trackId: number): TrackSection[] {
  if (cache === null) {
    cache = loadAll();
  }
  return cache.get(trackId) ?? [];
}
