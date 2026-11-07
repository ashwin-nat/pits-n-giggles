import { parse as parseNpy } from "npyjs";
import type { TelemetryPoint } from "../types/api";
import { MalformedSessionError } from "./pngtErrors";
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

// One lap's NPZ -> TelemetryPoint[]. lap_distance and lap_time_ms are mandatory pngt
// arrays, so they are always included (the chart derives the delta trace from
// lap_time_ms); a requested sensor missing from this NPZ is omitted from every point.
// NaN, the format's missing-sample marker, is kept as-is.
export function npzToTelemetryPoints(
  npzBytes: Uint8Array,
  sensors: string[],
  label: string
): TelemetryPoint[] {
  const keys = Array.from(new Set(["lap_distance", "lap_time_ms", ...sensors]));
  const arrays = parseNpzSensors(npzBytes, keys, label);
  const lapDistance = arrays["lap_distance"];
  if (lapDistance === undefined) {
    throw new MalformedSessionError(label, "lap NPZ is missing the required 'lap_distance' array");
  }
  const lapTimeMs = arrays["lap_time_ms"];

  const points: TelemetryPoint[] = [];
  for (let i = 0; i < lapDistance.length; i++) {
    const point: TelemetryPoint = { lapDistance: lapDistance[i] };
    if (lapTimeMs !== undefined) {
      point["lap_time_ms"] = lapTimeMs[i];
    }
    for (const sensor of sensors) {
      const array = arrays[sensor];
      if (array !== undefined) {
        point[sensor] = array[i];
      }
    }
    points.push(point);
  }
  return points;
}
