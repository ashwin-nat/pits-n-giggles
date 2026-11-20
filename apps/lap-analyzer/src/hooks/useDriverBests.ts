import { useQueries } from "@tanstack/react-query";
import { useLapAnalyzerProvider } from "../providers/ProviderContext";
import { isWholeLap } from "../lib/lapFormat";
import type { Driver, Lap } from "../types/api";
import { useDrivers } from "./useDrivers";

export interface DriverBest {
  driver: Driver;
  laps: Lap[];
  // Fastest whole lap, null when the driver has none.
  bestMs: number | null;
}

// Every driver of a session with their laps. One getLaps call per driver, on
// the same query keys as useLaps so the cache is shared. Drivers with
// restricted telemetry are not fetched and come back with no laps.
export function useDriverBests(sessionId: string | null) {
  const active = useLapAnalyzerProvider();
  const { data: drivers, isLoading: driversLoading } = useDrivers(sessionId);
  const list = drivers ?? [];

  const queries = useQueries({
    queries: list.map((driver) => ({
      queryKey: ["laps", active?.id ?? null, sessionId, driver.index],
      queryFn: () => {
        if (active === null || sessionId === null) {
          throw new Error("useDriverBests queried with no provider or session");
        }
        return active.provider.getLaps(sessionId, driver.index);
      },
      enabled: active !== null && sessionId !== null && driver.telemetrySettings !== "Restricted",
    })),
  });

  const rows: DriverBest[] = list.map((driver, i) => {
    const laps: Lap[] = queries[i]?.data ?? [];
    const times = laps.filter(isWholeLap).map((l) => l.lapTime as number);
    return { driver, laps, bestMs: times.length > 0 ? Math.min(...times) : null };
  });

  return { rows, isLoading: driversLoading || queries.some((q) => q.isLoading) };
}
