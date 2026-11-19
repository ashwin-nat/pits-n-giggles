import { parse as parseNpy } from "npyjs";
import { unzipArchive } from "./unzip";

export interface TrackGeometry {
  // Left then right white line, x y z per gate: flat array of length 6 * gateCount.
  edges: Float32Array;
  // Lap fraction (0..1) of each gate.
  frac: Float32Array;
}

// Bundled static asset synced by scripts/sync-segments.ts (POC, gitignored).
// Globbed so a missing file means "no geometry" rather than a build error.
const files = import.meta.glob<string>("../assets/track-data/track_geometry.npz", {
  query: "?url",
  import: "default",
});

let cachePromise: Promise<Map<number, TrackGeometry>> | null = null;

function toFloat32(entries: Record<string, Uint8Array>, key: string): Float32Array {
  const bytes = entries[`${key}.npy`];
  const buffer = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength) as ArrayBuffer;
  return parseNpy(buffer).data as unknown as Float32Array;
}

async function load(): Promise<Map<number, TrackGeometry>> {
  const map = new Map<number, TrackGeometry>();
  const loader = Object.values(files)[0];
  if (loader === undefined) {
    return map;
  }
  const response = await fetch(await loader());
  const entries = unzipArchive(new Uint8Array(await response.arrayBuffer()), "track_geometry.npz");
  for (const name of Object.keys(entries)) {
    const match = /^c(\d+)_edges\.npy$/.exec(name);
    if (match !== null) {
      const circuit = match[1];
      map.set(Number(circuit), {
        edges: toFloat32(entries, `c${circuit}_edges`),
        frac: toFloat32(entries, `c${circuit}_frac`),
      });
    }
  }
  return map;
}

export async function getTrackGeometry(trackId: number): Promise<TrackGeometry | null> {
  cachePromise ??= load();
  return (await cachePromise).get(trackId) ?? null;
}
