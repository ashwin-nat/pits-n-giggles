import { useEffect, useState } from "react";
import { getTrackGeometry, type TrackGeometry } from "../lib/trackGeometry";

export function useTrackGeometry(trackId: number | null): TrackGeometry | null {
  const [geometry, setGeometry] = useState<TrackGeometry | null>(null);

  useEffect(() => {
    if (trackId === null) {
      setGeometry(null);
      return;
    }
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
        }
      });
    return () => {
      cancelled = true;
    };
  }, [trackId]);

  return geometry;
}
