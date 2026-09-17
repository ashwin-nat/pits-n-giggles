import { useQuery } from "@tanstack/react-query";
import { useLapAnalyzerProvider } from "../providers/ProviderContext";

export function useSessions() {
  const active = useLapAnalyzerProvider();

  return useQuery({
    queryKey: ["sessions", active?.id ?? null],
    queryFn: () => {
      if (active === null) {
        throw new Error("useSessions called with no provider set");
      }
      return active.provider.getSessions();
    },
    enabled: active !== null,
  });
}
