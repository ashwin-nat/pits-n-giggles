// Helpers for drawing the v2 track markers: DRS, active aero, overtake, speed trap, brake boards.
import type { AeroMode, DistanceRange, TrackMeta } from "./segments";

// Splits a range that crosses the start/finish line into two plain ranges.
export function splitWrapped(range: DistanceRange, trackLength: number): DistanceRange[] {
  if (range.endM >= range.startM) {
    return [{ startM: range.startM, endM: range.endM }];
  }
  return [
    { startM: range.startM, endM: trackLength },
    { startM: 0, endM: range.endM },
  ];
}

export interface ZoneRanges {
  drs: DistanceRange[];
  aeroFull: DistanceRange[];
  aeroPartial: DistanceRange[];
}

// Every zone as plain, non-wrapping ranges, grouped by kind.
export function zoneRanges(meta: TrackMeta): ZoneRanges {
  const aero = (mode: AeroMode) =>
    meta.activeAeroZones.filter((z) => z.mode === mode).flatMap((z) => splitWrapped(z, meta.trackLength));
  return {
    drs: meta.drsZones.flatMap((z) => z.activation).flatMap((r) => splitWrapped(r, meta.trackLength)),
    aeroFull: aero("full"),
    aeroPartial: aero("partial"),
  };
}
