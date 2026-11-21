// Helpers for drawing the v2 track markers: DRS, active aero, overtake, speed trap, brake boards.
import type { FormulaRules } from "./formulas";
import type { AeroMode, BrakeBoardSide, DistanceRange, TrackMeta } from "./segments";

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

export const MARKER_COLORS = {
  drs: "#22c55e",
  aero: "#e6100a",
  speedTrap: "#d946ef",
  overtake: "#34d399",
  board: "#f87171",
} as const;

// A point on the lap: speed trap, DRS detection, overtake detection (filled) or activation (ring).
export interface MarkerPoint {
  m: number;
  color: string;
  ring: boolean;
  label: string;
}

// Everything the map and the chart lanes draw, already limited to what the formula has.
export interface TrackMarkers {
  aeroFull: DistanceRange[];
  aeroPartial: DistanceRange[];
  drs: DistanceRange[];
  points: MarkerPoint[];
  boards: { m: number; label: string; side: BrakeBoardSide }[];
}

export function buildMarkers(meta: TrackMeta, rules: FormulaRules): TrackMarkers {
  const zones = zoneRanges(meta);
  const points: MarkerPoint[] = [];
  if (rules.drs) {
    for (const z of meta.drsZones) {
      points.push({ m: z.detectionM, color: MARKER_COLORS.drs, ring: false, label: `DRS detection ${z.id}` });
    }
  }
  if (rules.overtake) {
    points.push({ m: meta.overtake.detectionM, color: MARKER_COLORS.overtake, ring: false, label: "Overtake detection" });
    points.push({ m: meta.overtake.activationM, color: MARKER_COLORS.overtake, ring: true, label: "Overtake activation" });
  }
  points.push({ m: meta.speedTrapM, color: MARKER_COLORS.speedTrap, ring: false, label: "Speed trap" });
  return {
    aeroFull: rules.activeAero ? zones.aeroFull : [],
    aeroPartial: rules.activeAero ? zones.aeroPartial : [],
    drs: rules.drs ? zones.drs : [],
    points,
    boards: meta.brakeBoards.map((b) => ({ m: b.atM, label: String(b.distanceM), side: b.side })),
  };
}
