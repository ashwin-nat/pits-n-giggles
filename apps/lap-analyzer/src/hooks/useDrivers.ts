import { useQuery } from "@tanstack/react-query";
import { useLapAnalyzerProvider } from "../providers/ProviderContext";

export function useDrivers(sessionId: string | null) {
  const active = useLapAnalyzerProvider();

  return useQuery({
    queryKey: ["drivers", active?.id ?? null, sessionId],
    queryFn: () => {
      if (active === null || sessionId === null) {
        throw new Error("useDrivers called with no provider or sessionId set");
      }
      return active.provider.getDrivers(sessionId);
    },
    enabled: active !== null && sessionId !== null,
  });
}
