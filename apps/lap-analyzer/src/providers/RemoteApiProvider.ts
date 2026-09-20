import type { Session, Driver, Lap, TelemetryPoint, TrackSection } from "../types/api";
import type { LapAnalyzerProvider, ProviderCapabilities } from "./types";

const API_ROOT = "/lap-analyzer/api/v1";

interface ApiErrorEnvelope {
  error?: { code?: string; message?: string };
}

// Thrown for both a non-2xx response (code/message read from the API's own
// {error: {code, message}} envelope, per the API spec) and a malformed one
// (fetch/JSON failure) -- callers (see selectorStates.tsx's ErrorMessage) only
// ever read `.message`, so both cases collapse to the same shape.
export class ApiError extends Error {
  constructor(readonly code: string, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function getJson<T>(path: string): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path);
  } catch (cause) {
    throw new ApiError("NETWORK_ERROR", `Request to ${path} failed: ${String(cause)}`);
  }
  if (!response.ok) {
    const body = (await response.json().catch(() => undefined)) as ApiErrorEnvelope | undefined;
    const code = body?.error?.code ?? "UNKNOWN_ERROR";
    const message = body?.error?.message ?? `Request to ${path} failed with status ${response.status}`;
    throw new ApiError(code, message);
  }
  return (await response.json()) as T;
}

interface TelemetryResponse {
  points: TelemetryPoint[];
}

// Implements LapAnalyzerProvider against the Phase 6 backend
// (/lap-analyzer/api/v1/*) instead of a locally-parsed .pngt file. Every
// response field is already the API's camelCase shape (see the backend's
// lap_analyzer_api.py), so unlike LocalFileProvider there is no field mapping
// here -- just the fetch and the error envelope translation above.
export class RemoteApiProvider implements LapAnalyzerProvider {
  readonly capabilities: ProviderCapabilities = {
    mutations: false,
    incidents: false,
    segments: true,
  };

  async getSessions(): Promise<Session[]> {
    return getJson<Session[]>(`${API_ROOT}/sessions`);
  }

  async getDrivers(sessionId: string): Promise<Driver[]> {
    return getJson<Driver[]>(`${API_ROOT}/sessions/${encodeURIComponent(sessionId)}/drivers`);
  }

  async getLaps(sessionId: string, driverIndex: number): Promise<Lap[]> {
    return getJson<Lap[]>(
      `${API_ROOT}/sessions/${encodeURIComponent(sessionId)}/drivers/${driverIndex}/laps`
    );
  }

  async getTelemetry(
    sessionId: string,
    driverIndex: number,
    lapNumber: number,
    sensors: string[]
  ): Promise<TelemetryPoint[]> {
    const params = new URLSearchParams({ sensors: sensors.join(",") });
    const { points } = await getJson<TelemetryResponse>(
      `${API_ROOT}/telemetry/${encodeURIComponent(sessionId)}/${driverIndex}/${lapNumber}?${params}`
    );
    return points;
  }

  async getTrackSections(trackId: number): Promise<TrackSection[]> {
    return getJson<TrackSection[]>(`${API_ROOT}/tracks/${trackId}/sections`);
  }
}
