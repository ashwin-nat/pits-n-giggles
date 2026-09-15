import { useQuery } from "@tanstack/react-query";
import { useLapAnalyzerProvider } from "../providers/ProviderContext";

export function useLaps(sessionId: string | null, driverIndex: number | null) {
  const active = useLapAnalyzerProvider();

  return useQuery({
    queryKey: ["laps", active?.id ?? null, sessionId, driverIndex],
    queryFn: () => {
      if (active === null || sessionId === null || driverIndex === null) {
        throw new Error("useLaps called with no provider, sessionId, or driverIndex set");
      }
      return active.provider.getLaps(sessionId, driverIndex);
    },
    enabled: active !== null && sessionId !== null && driverIndex !== null,
  });
}
