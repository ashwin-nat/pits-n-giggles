// Frontend-internal state shapes for the Zustand store. Distinct from
// types/api.ts, which mirrors the provider/API data model verbatim -- these
// types describe UI selection and interaction state that never crosses a
// provider boundary.

// One complete lap. laps[0] is the reference lap (A); laps[1..3] are comparison laps.
export interface LapRef {
  sessionId: string;
  driverIndex: number;
  lapNumber: number;
}

// A slot's selection, any field null while unset. The Choose lap modal only
// ever produces a complete LapRef.
export type LapSelection = { [K in keyof LapRef]: LapRef[K] | null };

export function isCompleteLap(lap: LapSelection | undefined): lap is LapRef {
  return lap !== undefined && lap.sessionId !== null && lap.driverIndex !== null && lap.lapNumber !== null;
}

export interface Viewport {
  distanceStart: number;
  distanceEnd: number;
}

export interface ActiveSection {
  label: string;
  distanceStart: number;
  distanceEnd: number;
}

interface PersonInfo {
  name: string;
  team: string;
  driverNumber: number;
}

// The frontend-internal camelCase shape. The API returns kebab-case
// (`lap-number`, `message-type`, etc. -- see the API spec's documented
// naming exception for this endpoint); a single adapter, normalizeIncident(),
// converts each event to this shape once at fetch time in useSessionEvents().
// No component downstream of that hook ever sees a kebab-case key.
export interface Incident {
  id: number;
  lapNumber: number;
  messageType: "COLLISION" | "OVERTAKE";
  involvedDrivers: number[];
  lapDistance: number;
  segmentInfo: { type: string; name: string; cornerNumber: number };
  sector: string;
  // COLLISION only
  severity?: "LOW" | "MEDIUM" | "HIGH" | null;
  driver1Info?: PersonInfo;
  driver2Info?: PersonInfo;
  // OVERTAKE only
  overtakerIndex?: number;
  overtakenIndex?: number;
  overtakerPitting?: boolean;
  overtakenPitting?: boolean;
  overtakerInfo?: PersonInfo;
  overtakenInfo?: PersonInfo;
}
