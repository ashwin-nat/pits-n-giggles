import { parse as parseNpy } from "npyjs";
import { unzipArchive } from "./unzip";

// NPZ is itself a ZIP of .npy files, one per array name -- unzip again, then
// run each requested sensor's bytes through npyjs.
export function parseNpzSensors(
  npzBytes: Uint8Array,
  keys: string[],
  label: string
): Record<string, ArrayLike<number>> {
  const entries = unzipArchive(npzBytes, label);
  const result: Record<string, ArrayLike<number>> = {};
  for (const key of keys) {
    const bytes = entries[`${key}.npy`];
    if (bytes === undefined) {
      continue; // sensor not present in this lap's NPZ -- caller skips it
    }
    const buffer = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength) as ArrayBuffer;
    result[key] = parseNpy(buffer).data as unknown as ArrayLike<number>;
  }
  return result;
}
