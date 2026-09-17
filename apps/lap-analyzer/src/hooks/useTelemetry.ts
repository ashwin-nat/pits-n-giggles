import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { useLapAnalyzerProvider } from "../providers/ProviderContext";

export function useTelemetry(
  sessionId: string | null,
  driverIndex: number | null,
  lapNumber: number | null,
  sensors: string[]
) {
  const active = useLapAnalyzerProvider();
  const enabled = active !== null && sessionId !== null && driverIndex !== null && lapNumber !== null && sensors.length > 0;

  return useQuery({
    queryKey: ["telemetry", active?.id ?? null, sessionId, driverIndex, lapNumber, sensors],
    queryFn: () => {
      if (active === null || sessionId === null || driverIndex === null || lapNumber === null) {
        throw new Error("useTelemetry called with no provider, sessionId, driverIndex, or lapNumber set");
      }
      return active.provider.getTelemetry(sessionId, driverIndex, lapNumber, sensors);
    },
    enabled,
    // Telemetry for a given session/driver/lap is immutable once recorded --
    // fetch once, never revalidate.
    staleTime: Infinity,
    // Switching lap/sensors changes the query key entirely -- without this,
    // the chart area would drop back to empty on every lap change instead of
    // keeping the previous lap's chart visible under a loading overlay (see
    // ChartLaneList's loading state).
    placeholderData: keepPreviousData,
  });
}
