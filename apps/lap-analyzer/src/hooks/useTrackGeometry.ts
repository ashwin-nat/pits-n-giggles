import { useEffect, useState } from "react";
import { getTrackGeometry, type TrackGeometry } from "../lib/trackGeometry";

// undefined while loading, null when there is no geometry for this track.
export function useTrackGeometry(trackId: number | null): TrackGeometry | null | undefined {
  const [geometry, setGeometry] = useState<TrackGeometry | null | undefined>(undefined);

  useEffect(() => {
    if (trackId === null) {
      setGeometry(null);
      return;
    }
    setGeometry(undefined);
    let cancelled = false;
    getTrackGeometry(trackId)
      .then((result) => {
        if (!cancelled) {
          setGeometry(result);
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          console.error(`useTrackGeometry: failed to load geometry for trackId=${trackId}`, error);
          setGeometry(null);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [trackId]);

  return geometry;
}
