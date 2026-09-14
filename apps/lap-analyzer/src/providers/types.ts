import type { Session, Driver, Lap, TelemetryPoint, TrackSection } from "../types/api";

export interface ProviderCapabilities {
  mutations: boolean; // rename / mark-good / delete
  incidents: boolean; // collisions / overtakes
  segments: boolean; // track section pills
}

// Every method here is something every implementation can actually do.
// No mutation methods and no getIncidents on this interface, ever -- the UI
// checks provider.capabilities instead of calling something that would throw
// or silently no-op on LocalFileProvider.
export interface LapAnalyzerProvider {
  readonly capabilities: ProviderCapabilities;

  getSessions(): Promise<Session[]>;
  getDrivers(sessionId: string): Promise<Driver[]>;
  getLaps(sessionId: string, driverIndex: number): Promise<Lap[]>;
  getTelemetry(
    sessionId: string,
    driverIndex: number,
    lapNumber: number,
    sensors: string[]
  ): Promise<TelemetryPoint[]>;
  getTrackSections(trackId: number): Promise<TrackSection[]>;
}
