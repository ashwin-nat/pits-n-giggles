import { useQuery } from "@tanstack/react-query";
import { useLapAnalyzerProvider } from "../providers/ProviderContext";

export function useTrackSections(trackId: number | null) {
  const active = useLapAnalyzerProvider();

  return useQuery({
    queryKey: ["trackSections", active?.id ?? null, trackId],
    queryFn: () => {
      if (active === null || trackId === null) {
        throw new Error("useTrackSections called with no provider or trackId set");
      }
      return active.provider.getTrackSections(trackId);
    },
    enabled: active !== null && trackId !== null,
  });
}
