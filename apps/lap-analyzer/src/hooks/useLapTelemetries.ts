import { useMemo } from "react";
import { keepPreviousData, useQueries } from "@tanstack/react-query";
import { useLapAnalyzerProvider } from "../providers/ProviderContext";
import { isCompleteLap, type LapSelection } from "../types/store";
import type { TelemetryPoint } from "../types/api";
import { useSessions } from "./useSessions";
import type { LoadedLap } from "../lib/lapSeries";

// One telemetry query per lap slot. Each lap is asked only for the sensors its
// session recorded, so a comparison lap from a recording with fewer sensors
// yields a missing series rather than a failed fetch. `laps[i]` is slot i;
// `undefined` while that slot is incomplete or still loading.
export function useLapTelemetries(laps: readonly LapSelection[], sensors: readonly string[]) {
  const active = useLapAnalyzerProvider();
  const { data: sessions } = useSessions();

  const queries = useQueries({
    queries: laps.map((lap) => {
      const manifest = sessions?.find((s) => s.id === lap.sessionId)?.sensorManifest;
      const wanted = manifest === undefined ? [] : sensors.filter((key) => manifest.some((s) => s.key === key));
      return {
        queryKey: ["telemetry", active?.id ?? null, lap.sessionId, lap.driverIndex, lap.lapNumber, wanted],
        queryFn: (): Promise<TelemetryPoint[]> => {
          if (active === null || !isCompleteLap(lap)) {
            throw new Error("useLapTelemetries queried an incomplete lap");
          }
          return active.provider.getTelemetry(lap.sessionId, lap.driverIndex, lap.lapNumber, wanted);
        },
        enabled: active !== null && manifest !== undefined && isCompleteLap(lap),
        // A recorded lap never changes.
        staleTime: Infinity,
        // Keep the previous lap on screen while a change loads.
        placeholderData: keepPreviousData,
      };
    }),
  });

  const data = queries.map((q) => q.data);
  const loaded = useMemo<(LoadedLap | undefined)[]>(
    () =>
      data.map((points, slot) => {
        const manifest = sessions?.find((s) => s.id === laps[slot]?.sessionId)?.sensorManifest;
        return points === undefined || manifest === undefined ? undefined : { points, manifest };
      }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [...data, sessions, laps]
  );

  return {
    laps: loaded,
    isFetching: queries.some((q) => q.isFetching),
    error: queries.find((q) => q.error)?.error ?? null,
  };
}
