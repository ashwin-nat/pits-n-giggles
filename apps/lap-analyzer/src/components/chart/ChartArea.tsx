import { useState } from "react";
import { TrackProgressBar } from "./TrackProgressBar";
import { ChartLaneList } from "./ChartLaneList";
import { MapPanel } from "../map/MapPanel";

// Composes the chart area's pieces. Owns the shared crosshair position --
// TrackProgressBar's cursor marker, every ChartLane and the map's cursor dots
// need the same value, and ChartArea is their lowest common ancestor.
export function ChartArea() {
  const [crosshairPosition, setCrosshairPosition] = useState<number | null>(null);

  return (
    <div className="flex items-start">
      <div className="min-w-0 flex-1">
        {/* Pinned to the top of Layout's scrollable <main> so the progress bar
            stays visible while the lane list below scrolls. */}
        <div className="sticky top-0 z-20 bg-chart-surface">
          <TrackProgressBar crosshairPosition={crosshairPosition} />
        </div>
        <ChartLaneList crosshairPosition={crosshairPosition} onCrosshairMove={setCrosshairPosition} />
      </div>
      <MapPanel crosshairPosition={crosshairPosition} />
    </div>
  );
}
