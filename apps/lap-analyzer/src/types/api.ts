// Shared data model types, mirrored field-for-field from the telemetry API spec's
// JSON models. Every provider implementation (LocalFileProvider, RemoteApiProvider)
// returns these shapes; every UI component consumes them. This is the one contract
// that must not drift between providers.

export interface SensorDefinition {
  key: string; // dotted-path, e.g. "tyre_temp.fl.inner"
  label: string;
  unit: string;
  type: "continuous" | "discrete";
}

export interface SessionBest {
  driverIndex: number;
  lapNumber: number;
  lapTimeMs: number;
}

export interface Session {
  id: string; // opaque string; derivation differs per provider, see LocalFileProvider
  name: string;
  trackId: number;
  trackName: string;
  date: string; // ISO 8601
  type: string; // e.g. "Race", "Qualifying", "Practice" -- open set, sim has ~18 session types
  appVersion: string;
  gameYear: number;
  formula: string;
  gameVersion: string;
  sessionBest: SessionBest | null;
  sensorManifest: SensorDefinition[];
}

export interface Driver {
  index: number;
  name: string;
  team: string;
  isAi: boolean;
  carNumber: number;
  nationality: string | null;
  platform: string | null;
  telemetrySettings: "Public" | "Restricted";
}

export interface Lap {
  lapNumber: number;
  lapTime: number | null; // ms; null if not completed
  valid: boolean;
  tyreCompound: string;
  tyreLaps: number;
  pitInLap: boolean;
  pitOutLap: boolean;
  isGood: boolean;
}

export interface TelemetryPoint {
  lapDistance: number;
  [sensorKey: string]: number;
}

export interface TrackSection {
  label: string;
  distanceStart: number;
  distanceEnd: number;
}
