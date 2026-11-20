import { useState } from "react";
import { TrackProgressBar } from "./TrackProgressBar";
import { CurrentLocationLabel } from "./CurrentLocationLabel";
import { ChartLegend } from "./ChartLegend";
import { ChartLaneList } from "./ChartLaneList";
import { TrackMap } from "./TrackMap";

// Composes the chart area's pieces. Owns the shared crosshair position --
// TrackProgressBar's cursor marker and every ChartLane need the same value,
// and ChartArea is their lowest common ancestor.
export function ChartArea() {
  const [crosshairPosition, setCrosshairPosition] = useState<number | null>(null);

  return (
    <div>
      {/* Pinned to the top of Layout's scrollable <main> so the progress bar
          and legend stay visible while the lane list below scrolls. */}
      <div className="sticky top-0 z-20 bg-slate-950">
        <CurrentLocationLabel crosshairPosition={crosshairPosition} />
        <TrackProgressBar crosshairPosition={crosshairPosition} />
        <ChartLegend />
      </div>
      <TrackMap crosshairPosition={crosshairPosition} />
      <ChartLaneList crosshairPosition={crosshairPosition} onCrosshairMove={setCrosshairPosition} />
    </div>
  );
}
