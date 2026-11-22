import type { LapRef } from "../types/store";
import { MAX_COMPARISON_LAPS } from "./chartConstants";

// Parses `?laps=<sessionId>~<driverIndex>~<lapNumber>,...`, lap A first. The save viewer
// writes the same refs, so its links open here. Malformed and repeated refs are dropped.
export function parseLapsParam(param: string | null): LapRef[] {
  const refs: LapRef[] = [];
  for (const part of (param ?? "").split(",")) {
    const [sessionId, driver, lap, ...extra] = part.split("~");
    if (extra.length > 0 || !sessionId || !/^[A-Za-z0-9._-]+$/.test(sessionId) || !/^\d+$/.test(driver ?? "") || !/^\d+$/.test(lap ?? "")) {
      continue;
    }
    const ref = { sessionId, driverIndex: Number(driver), lapNumber: Number(lap) };
    if (!refs.some((r) => r.sessionId === ref.sessionId && r.driverIndex === ref.driverIndex && r.lapNumber === ref.lapNumber)) {
      refs.push(ref);
    }
  }
  return refs.slice(0, 1 + MAX_COMPARISON_LAPS);
}
