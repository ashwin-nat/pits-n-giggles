import { useMemo } from "react";
import { keepPreviousData, useQueries } from "@tanstack/react-query";
import { useLapAnalyzerProvider } from "../providers/ProviderContext";
import { isCompleteLap, type LapSelection } from "../types/store";
import type { TelemetryPoint } from "../types/api";
import { useSessions } from "./useSessions";
import type { LoadedLap } from "../lib/lapSeries";

// One telemetry query per lap slot, keyed by lap alone and carrying every
// sensor its session recorded. The charts, the section table and the map all
// read the same query, so each lap is downloaded once and toggling a sensor
// does not refetch. `laps[i]` is slot i; `undefined` while that slot is
// incomplete or still loading.
export function useLapTelemetries(laps: readonly LapSelection[]) {
  const active = useLapAnalyzerProvider();
  const { data: sessions } = useSessions();

  const queries = useQueries({
    queries: laps.map((lap) => {
      const manifest = sessions?.find((s) => s.id === lap.sessionId)?.sensorManifest;
      return {
        queryKey: ["telemetry", active?.id ?? null, lap.sessionId, lap.driverIndex, lap.lapNumber],
        queryFn: (): Promise<TelemetryPoint[]> => {
          if (active === null || !isCompleteLap(lap) || manifest === undefined) {
            throw new Error("useLapTelemetries queried an incomplete lap");
          }
          return active.provider.getTelemetry(
            lap.sessionId,
            lap.driverIndex,
            lap.lapNumber,
            manifest.map((s) => s.key)
          );
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
  // One dependency that changes whenever any slot's data does; a spread of the
  // data would change the deps array's length with the lap count.
  const dataKey = queries.map((q) => `${q.dataUpdatedAt}:${q.data === undefined ? 0 : 1}`).join(",");
  const loaded = useMemo<(LoadedLap | undefined)[]>(
    () =>
      data.map((points, slot) => {
        const manifest = sessions?.find((s) => s.id === laps[slot]?.sessionId)?.sensorManifest;
        return points === undefined || manifest === undefined ? undefined : { points, manifest };
      }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [dataKey, sessions, laps]
  );

  return {
    laps: loaded,
    isFetching: queries.some((q) => q.isFetching),
    // Per slot, so one failed comparison lap does not take the others down.
    errors: queries.map((q) => (q.error instanceof Error ? q.error : q.error ? new Error(String(q.error)) : null)),
    // Refetches only the slots that failed.
    retry: () => queries.forEach((q) => q.error && void q.refetch()),
  };
}
