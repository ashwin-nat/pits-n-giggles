import { createContext, useContext } from "react";
import type { LapAnalyzerProvider } from "./types";

// `id` exists purely so React Query hooks have something stable and unique
// to key off. Using the provider instance itself in a query key would rely
// on React Query's JSON.stringify-based hashing, which for LocalFileProvider
// would collide for two different files that happen to share a name (its
// only enumerable field) -- an explicit id sidesteps that entirely.
export interface ActiveProvider {
  provider: LapAnalyzerProvider;
  id: string;
}

// null = no file loaded yet / no backend configured. Populated by whatever
// component owns the "how did we get a provider" decision -- a dropped file
// for LocalFileProvider today, a RemoteApiProvider setup in Phase 6.
export const ProviderContext = createContext<ActiveProvider | null>(null);

export function useLapAnalyzerProvider(): ActiveProvider | null {
  return useContext(ProviderContext);
}
