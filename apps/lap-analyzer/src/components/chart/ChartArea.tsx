import { useCallback, useState } from "react";
import { useTelemetryStore } from "../../store/telemetryStore";
import { TrackProgressBar } from "./TrackProgressBar";
import { CurrentLocationLabel } from "./CurrentLocationLabel";
import { ChartLegend, type ChartTraceVisibility } from "./ChartLegend";
import { ChartLaneList, type ChartDomain } from "./ChartLaneList";
import { DistanceAxis } from "./DistanceAxis";

// Composes the chart area's pieces. Owns trace visibility (a legend toggle
// is view-local UI state, not store state -- see ChartLegend) since it's the
// lowest common ancestor of the component that renders the toggle
// (ChartLegend) and the component that needs to act on it (ChartLaneList).
// Also owns the shared crosshair position -- TrackProgressBar's cursor
// marker and every ChartLane need the same value, and ChartArea is their
// lowest common ancestor too. Same reasoning for `domain` (ChartLaneList
// reports it, DistanceAxis needs it).
export function ChartArea() {
  const [visibility, setVisibility] = useState<ChartTraceVisibility>({ primary: true, reference: true });
  const [crosshairPosition, setCrosshairPosition] = useState<number | null>(null);
  const [domain, setDomain] = useState<ChartDomain | null>(null);
  const viewport = useTelemetryStore((state) => state.viewport);

  function toggleTrace(trace: keyof ChartTraceVisibility) {
    setVisibility((prev) => ({ ...prev, [trace]: !prev[trace] }));
  }

  // Stable identity -- passed to ChartLaneList as a effect dependency there;
  // a new function every render would re-fire that effect every render.
  const handleDomainChange = useCallback((next: ChartDomain | null) => setDomain(next), []);

  return (
    <div>
      {/* Pinned to the top of Layout's scrollable <main> so the progress
          bar, legend, and distance ruler stay visible while the lane list
          below scrolls -- these three are the chart area's shared context,
          not any one lane's. */}
      <div className="sticky top-0 z-20 bg-slate-950">
        <CurrentLocationLabel crosshairPosition={crosshairPosition} />
        <TrackProgressBar crosshairPosition={crosshairPosition} />
        <ChartLegend visibility={visibility} onToggle={toggleTrace} />
        {domain !== null && <DistanceAxis dataMin={domain.dataMin} dataMax={domain.dataMax} viewport={viewport} />}
      </div>
      <ChartLaneList
        visibility={visibility}
        crosshairPosition={crosshairPosition}
        onCrosshairMove={setCrosshairPosition}
        onDomainChange={handleDomainChange}
      />
    </div>
  );
}
