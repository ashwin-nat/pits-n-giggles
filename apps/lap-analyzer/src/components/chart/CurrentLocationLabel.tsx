import { useSessions } from "../../hooks/useSessions";
import { useTrackMeta } from "../../hooks/useTrackMeta";
import { useTelemetryStore } from "../../store/telemetryStore";
import type { TrackSection } from "../../types/api";

interface CurrentLocationLabelProps {
  // The shared chart crosshair -- see ChartArea.
  crosshairPosition: number | null;
}

function segmentAt(sections: TrackSection[], distance: number): TrackSection | null {
  return sections.find((s) => distance >= s.distanceStart && distance < s.distanceEnd) ?? null;
}

function sectorNameAt(distance: number, sectorBoundaries: { s1: number; s2: number }): string {
  if (distance < sectorBoundaries.s1) {
    return "Sector 1";
  }
  if (distance < sectorBoundaries.s2) {
    return "Sector 2";
  }
  return "Sector 3";
}

// A thin readout above TrackProgressBar -- named segments have real gaps
// between them (see TrackProgressBar's grey filler blocks), so "current
// segment" isn't always answerable; sector is always answerable (every
// distance falls in exactly one of the three), so it's the fallback rather
// than leaving the label blank in those gaps. Called "location," not
// "position" -- position already means something else (race position) in
// motorsport.
export function CurrentLocationLabel({ crosshairPosition }: CurrentLocationLabelProps) {
  const primarySessionId = useTelemetryStore((state) => state.primary.sessionId);
  const { data: sessions } = useSessions();
  const trackId = sessions?.find((s) => s.id === primarySessionId)?.trackId ?? null;
  const meta = useTrackMeta(trackId);

  if (primarySessionId === null) {
    return null;
  }

  let label: string | null = null;
  if (crosshairPosition !== null && meta !== null) {
    const segment = segmentAt(meta.sections, crosshairPosition);
    label = segment !== null ? segment.label : sectorNameAt(crosshairPosition, meta.sectorBoundaries);
  }

  return (
    <div className="border-b border-slate-800 bg-slate-900 px-4 py-1.5 text-center text-sm font-medium text-slate-200">
      {/* A real non-breaking space (not a plain " ", which the browser
          whitespace-collapses to nothing) so this div always has a line box
          to render, whether label is null (no segment/meta yet) or ""
          (a real but unnamed TrackSection -- see track_segments_classifier).
          Without it, an empty div has no content to establish a line height,
          so the row shrinks to just its padding as you hover across an
          unnamed corner. */}
      {label || " "}
    </div>
  );
}
