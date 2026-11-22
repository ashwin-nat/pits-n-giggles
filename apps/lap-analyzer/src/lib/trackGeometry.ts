import { parse as parseNpy } from "npyjs";
import { unzipArchive } from "./unzip";

export interface TrackGeometry {
  // Left then right white line, x y z per gate: flat array of length 6 * gateCount.
  edges: Float32Array;
  // Lap fraction (0..1) of each gate.
  frac: Float32Array;
  // F1 game year the geometry was extracted from, e.g. 25.
  sourceYear: number;
}

// Format version written by apps/dev_tools/extract_track_data.py; a file with another version is rejected.
export const GEOMETRY_VERSION = 1;

// One file per layout, c<circuit>.npz, synced by scripts/sync-track-data.ts, read from the bundle (README, "Track data"). Globbed so a missing
// file means "no geometry" rather than a build error.
const files = import.meta.glob<string>("../assets/track-data/c*.npz", {
  query: "?url",
  import: "default",
});

const cache = new Map<number, Promise<TrackGeometry | null>>();

function toArray<T>(entries: Record<string, Uint8Array>, key: string): T {
  const bytes = entries[`${key}.npy`];
  const buffer = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength) as ArrayBuffer;
  return parseNpy(buffer).data as unknown as T;
}

async function load(trackId: number): Promise<TrackGeometry | null> {
  const loader = Object.entries(files).find(([path]) => path.endsWith(`/c${trackId}.npz`))?.[1];
  if (loader === undefined) {
    return null;
  }
  const response = await fetch(await loader());
  if (!response.ok) {
    throw new Error(`c${trackId}.npz: HTTP ${response.status}`);
  }
  const entries = unzipArchive(new Uint8Array(await response.arrayBuffer()), `c${trackId}.npz`);
  const version = Number(toArray<ArrayLike<number>>(entries, "version")[0]);
  if (version !== GEOMETRY_VERSION) {
    throw new Error(`c${trackId}.npz has format version ${version}, expected ${GEOMETRY_VERSION}`);
  }
  return {
    edges: toArray<Float32Array>(entries, "edges"),
    frac: toArray<Float32Array>(entries, "frac"),
    sourceYear: Number(toArray<ArrayLike<number>>(entries, "source_year")[0]),
  };
}

export function getTrackGeometry(trackId: number): Promise<TrackGeometry | null> {
  let cached = cache.get(trackId);
  if (cached === undefined) {
    cached = load(trackId);
    cache.set(trackId, cached);
    // A failed load is retried on the next call rather than cached for the session.
    cached.catch(() => cache.delete(trackId));
  }
  return cached;
}
