import type { Session, Driver, Lap, TelemetryPoint, TrackSection, SensorDefinition, SessionBest } from "../types/api";
import type { LapAnalyzerProvider, ProviderCapabilities } from "./types";
import { unzipArchive, readJsonEntry, type ZipEntries } from "../lib/unzip";
import { parseNpzSensors } from "../lib/parseNpy";
import { getTrackSections as getBundledTrackSections } from "../lib/segments";
import {
  InvalidHeaderError,
  InvalidManifestError,
  UnsupportedFormatError,
  UnsupportedVersionError,
  MalformedSessionError,
  DriverNotFoundError,
} from "../lib/pngtErrors";

const SUPPORTED_VERSION = 1;

interface HeaderJson {
  format?: string;
  version?: number;
}

interface ManifestJson {
  sensors?: Record<string, { label?: string; unit?: string; type?: string }>;
}

interface SessionJson {
  session_uid?: number;
  session_name?: string;
  session_type?: string;
  app_version?: string;
  game_year?: number;
  formula?: string;
  game_version?: string;
  timestamp?: string;
  track?: { id?: number; name?: string };
  laps?: {
    count?: number;
    session_best?: { driver_index: number; lap_number: number; lap_time_ms: number } | null;
  };
}

interface DriversJson {
  drivers?: Array<{
    driver_index: number;
    name: string;
    team: string;
    is_ai: boolean;
    car_number: number;
    nationality: string | null;
    platform: string | null;
    telemetry_settings: string;
  }>;
}

interface LapsJson {
  laps?: Array<{
    lap_number: number;
    lap_time_ms: number | null;
    valid: boolean;
    tyre_compound: string;
    tyre_laps: number;
    pit_in_lap: boolean;
    pit_out_lap: boolean;
    is_good: boolean;
  }>;
}

interface ParsedArchive {
  label: string;
  entries: ZipEntries;
  session: Session;
  drivers: Driver[];
}

// session_type is documented in the pngt format spec as an intentionally open
// string (new sim session types must not require a format change). The
// shared Session type models it as a closed union for UI convenience; this
// only capitalizes the raw value rather than validating it against the union,
// so an unrecognized value still round-trips instead of throwing.
function titleCaseSessionType(raw: string): Session["type"] {
  const words = raw.split(/[_\s]+/).filter(Boolean);
  const titled = words.map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(" ");
  return titled as Session["type"];
}

function pad(n: number, width: number): string {
  return String(n).padStart(width, "0");
}

export class LocalFileProvider implements LapAnalyzerProvider {
  readonly capabilities: ProviderCapabilities = {
    mutations: false,
    incidents: false,
    segments: true,
  };

  private readonly file: File;
  private readonly label: string;
  private initPromise: Promise<ParsedArchive> | null = null;

  constructor(file: File) {
    this.file = file;
    this.label = file.name || "<uploaded file>";
  }

  private async init(): Promise<ParsedArchive> {
    if (this.initPromise === null) {
      this.initPromise = this.parse();
    }
    return this.initPromise;
  }

  private async parse(): Promise<ParsedArchive> {
    const buffer = await this.file.arrayBuffer();
    const entries = unzipArchive(new Uint8Array(buffer), this.label);

    const header = readJsonEntry<HeaderJson>(entries, "header.json");
    if (header === undefined) {
      throw new InvalidHeaderError(this.label, "header.json is missing");
    }
    if (header.format === undefined || header.version === undefined) {
      throw new InvalidHeaderError(this.label, "missing 'format' or 'version' key");
    }
    if (header.format !== "pngt") {
      throw new UnsupportedFormatError(this.label, header.format);
    }
    if (header.version !== SUPPORTED_VERSION) {
      throw new UnsupportedVersionError(this.label, header.version, SUPPORTED_VERSION);
    }

    const manifest = readJsonEntry<ManifestJson>(entries, "manifest.json");
    if (manifest === undefined || manifest.sensors === undefined) {
      throw new InvalidManifestError(this.label, "manifest.json is missing or has no 'sensors' key");
    }
    const sensorManifest: SensorDefinition[] = Object.entries(manifest.sensors).map(([key, def]) => {
      if (def.label === undefined || def.unit === undefined || (def.type !== "continuous" && def.type !== "discrete")) {
        throw new InvalidManifestError(this.label, `sensor '${key}' is missing required fields or has an invalid type`);
      }
      return { key, label: def.label, unit: def.unit, type: def.type };
    });

    const sessionJson = readJsonEntry<SessionJson>(entries, "session.json");
    if (sessionJson === undefined) {
      throw new MalformedSessionError(this.label, "session.json is missing");
    }
    if (
      sessionJson.session_uid === undefined ||
      sessionJson.session_name === undefined ||
      sessionJson.track?.id === undefined ||
      sessionJson.track?.name === undefined
    ) {
      throw new MalformedSessionError(this.label, "session.json is missing required fields");
    }

    const driversJson = readJsonEntry<DriversJson>(entries, "drivers.json");
    if (driversJson === undefined || driversJson.drivers === undefined) {
      throw new MalformedSessionError(this.label, "drivers.json is missing");
    }

    const sessionBest: SessionBest | null = sessionJson.laps?.session_best
      ? {
          driverIndex: sessionJson.laps.session_best.driver_index,
          lapNumber: sessionJson.laps.session_best.lap_number,
          lapTimeMs: sessionJson.laps.session_best.lap_time_ms,
        }
      : null;

    const session: Session = {
      id: `${sessionJson.session_uid}-${sessionJson.track.id}-${sessionJson.timestamp ?? ""}`,
      name: sessionJson.session_name,
      trackId: sessionJson.track.id,
      trackName: sessionJson.track.name,
      date: sessionJson.timestamp ?? "",
      type: titleCaseSessionType(sessionJson.session_type ?? ""),
      appVersion: sessionJson.app_version ?? "",
      gameYear: sessionJson.game_year ?? 0,
      formula: sessionJson.formula ?? "",
      gameVersion: sessionJson.game_version ?? "",
      sessionBest,
      sensorManifest,
    };

    const drivers: Driver[] = driversJson.drivers.map((d) => ({
      index: d.driver_index,
      name: d.name,
      team: d.team,
      isAi: d.is_ai,
      carNumber: d.car_number,
      nationality: d.nationality,
      platform: d.platform,
      telemetrySettings: d.telemetry_settings === "Restricted" ? "Restricted" : "Public",
    }));

    return { label: this.label, entries, session, drivers };
  }

  async getSessions(): Promise<Session[]> {
    const { session } = await this.init();
    return [session];
  }

  async getDrivers(_sessionId: string): Promise<Driver[]> {
    const { drivers } = await this.init();
    return drivers;
  }

  async getLaps(_sessionId: string, driverIndex: number): Promise<Lap[]> {
    const { entries, label } = await this.init();
    const path = `drivers/${pad(driverIndex, 2)}/laps.json`;
    const lapsJson = readJsonEntry<LapsJson>(entries, path);
    if (lapsJson === undefined) {
      // Restricted or scope-excluded driver -- no drivers/{index}/ folder at all.
      return [];
    }
    if (lapsJson.laps === undefined) {
      throw new MalformedSessionError(label, `${path} is missing the 'laps' key`);
    }
    return lapsJson.laps.map((l) => ({
      lapNumber: l.lap_number,
      lapTime: l.lap_time_ms,
      valid: l.valid,
      tyreCompound: l.tyre_compound,
      tyreLaps: l.tyre_laps,
      pitInLap: l.pit_in_lap,
      pitOutLap: l.pit_out_lap,
      isGood: l.is_good,
    }));
  }

  async getTelemetry(
    _sessionId: string,
    driverIndex: number,
    lapNumber: number,
    sensors: string[]
  ): Promise<TelemetryPoint[]> {
    const { entries, label } = await this.init();
    const path = `drivers/${pad(driverIndex, 2)}/lap_${pad(lapNumber, 3)}.npz`;
    const npzBytes = entries[path];
    if (npzBytes === undefined) {
      throw new DriverNotFoundError(label, driverIndex);
    }

    const keys = Array.from(new Set(["lap_distance", ...sensors]));
    const arrays = parseNpzSensors(npzBytes, keys, label);
    const lapDistance = arrays["lap_distance"];
    if (lapDistance === undefined) {
      throw new MalformedSessionError(label, `${path} is missing the required 'lap_distance' array`);
    }

    const points: TelemetryPoint[] = [];
    for (let i = 0; i < lapDistance.length; i++) {
      const point: TelemetryPoint = { lapDistance: lapDistance[i] };
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

  async getTrackSections(trackId: number): Promise<TrackSection[]> {
    return getBundledTrackSections(trackId);
  }
}
