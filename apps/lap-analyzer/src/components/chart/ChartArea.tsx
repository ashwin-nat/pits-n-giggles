import { useState } from "react";
import { TrackProgressBar } from "./TrackProgressBar";
import { CurrentLocationLabel } from "./CurrentLocationLabel";
import { ChartLegend, type ChartTraceVisibility } from "./ChartLegend";
import { ChartLaneList } from "./ChartLaneList";

// Composes the chart area's pieces. Owns trace visibility (a legend toggle
// is view-local UI state, not store state -- see ChartLegend) since it's the
// lowest common ancestor of the component that renders the toggle
// (ChartLegend) and the component that needs to act on it (ChartLaneList).
// Also owns the shared crosshair position -- TrackProgressBar's cursor
// marker and every ChartLane need the same value, and ChartArea is their
// lowest common ancestor too.
export function ChartArea() {
  const [visibility, setVisibility] = useState<ChartTraceVisibility>({ primary: true, reference: true });
  const [crosshairPosition, setCrosshairPosition] = useState<number | null>(null);

  function toggleTrace(trace: keyof ChartTraceVisibility) {
    setVisibility((prev) => ({ ...prev, [trace]: !prev[trace] }));
  }

  return (
    <div>
      {/* Pinned to the top of Layout's scrollable <main> so the progress
          bar and legend stay visible while the lane list below scrolls --
          these are the chart area's shared context, not any one lane's. */}
      <div className="sticky top-0 z-20 bg-slate-950">
        <CurrentLocationLabel crosshairPosition={crosshairPosition} />
        <TrackProgressBar crosshairPosition={crosshairPosition} />
        <ChartLegend visibility={visibility} onToggle={toggleTrace} />
      </div>
      <ChartLaneList
        visibility={visibility}
        crosshairPosition={crosshairPosition}
        onCrosshairMove={setCrosshairPosition}
      />
    </div>
  );
}
