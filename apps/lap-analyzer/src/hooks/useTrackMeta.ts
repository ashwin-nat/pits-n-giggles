import { useEffect, useState } from "react";
import { getTrackMeta, type TrackMeta } from "../lib/segments";

// Not a React Query hook like useTrackSections -- getTrackMeta reads bundled
// static assets (see segments.ts), not provider/session data, and already
// caches internally, so a plain effect is enough.
export function useTrackMeta(trackId: number | null): TrackMeta | null {
  const [meta, setMeta] = useState<TrackMeta | null>(null);

  useEffect(() => {
    if (trackId === null) {
      setMeta(null);
      return;
    }
    let cancelled = false;
    getTrackMeta(trackId)
      .then((result) => {
        if (!cancelled) {
          setMeta(result);
        }
      })
      .catch((error: unknown) => {
        // No error state surfaced to callers (CurrentLocationLabel/
        // TrackProgressBar already treat a null meta as "nothing to show,"
        // same as the track just not having bundled segment data) -- this
        // exists so a rejection (e.g. a malformed segments/*.json) becomes
        // a visible console error instead of a silent unhandled rejection.
        if (!cancelled) {
          console.error(`useTrackMeta: failed to load track meta for trackId=${trackId}`, error);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [trackId]);

  return meta;
}
