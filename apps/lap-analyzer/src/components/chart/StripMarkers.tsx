import { useMemo } from "react";
import { formulaRules } from "../../lib/formulas";
import type { TrackMeta } from "../../lib/segments";
import { buildMarkers, MARKER_COLORS } from "../../lib/trackMarkers";

const ROAD_FILL = "#131a26";

// Zone bars and point dots under the pill bar, on the same distance scale, so they line up with the pills.
// Full aero and DRS share the top row; partial aero sits under it, dotted.
export function StripMarkers({ meta, formula }: { meta: TrackMeta; formula: string }) {
  const markers = useMemo(() => buildMarkers(meta, formulaRules(formula)), [meta, formula]);
  const pct = (m: number) => `${(m / meta.trackLength) * 100}%`;
  const bar = (ranges: { startM: number; endM: number }[], key: string, color: string, top: number, dotted: boolean) =>
    ranges.map((r, i) => (
      <div
        key={`${key}-${i}`}
        className="absolute h-[3px]"
        style={{
          left: pct(r.startM),
          width: `${((r.endM - r.startM) / meta.trackLength) * 100}%`,
          top,
          background: dotted ? `repeating-linear-gradient(90deg, ${color} 0 2px, transparent 2px 5px)` : color,
        }}
      />
    ));

  return (
    <div className="pointer-events-none relative mt-1 h-[11px]">
      {bar(markers.drs, "drs", MARKER_COLORS.drs, 0, false)}
      {bar(markers.aeroFull, "aero-f", MARKER_COLORS.aero, 0, false)}
      {bar(markers.aeroPartial, "aero-p", MARKER_COLORS.aero, 5, true)}
      {markers.points.map((pt, i) => (
        <div
          key={`pt-${i}`}
          title={pt.label}
          className="pointer-events-auto absolute top-0 h-[9px] w-[9px] -translate-x-1/2 rounded-full"
          style={{
            left: pct(pt.m),
            backgroundColor: pt.ring ? ROAD_FILL : pt.color,
            border: `${pt.ring ? 2 : 1}px solid ${pt.ring ? pt.color : "white"}`,
          }}
        />
      ))}
    </div>
  );
}
