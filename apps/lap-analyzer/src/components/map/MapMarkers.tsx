import { useMemo } from "react";
import { edgeAt, lineAlong, toPath, type MapGeometry, type Pt } from "../../lib/mapGeometry";
import type { DistanceRange, TrackMeta } from "../../lib/segments";
import type { FormulaRules } from "../../lib/formulas";
import { buildMarkers, MARKER_COLORS, type MarkerPoint } from "../../lib/trackMarkers";

// Zone lines run outside the road by a fixed number of screen pixels: full aero 6 px past the left
// edge, partial 11 px, DRS 6 px past the right edge.
const AERO_FULL_PX = 6;
const AERO_PARTIAL_PX = 11;
const DRS_PX = 6;

const BOARD_REACH = 0.4; // how far a board mark stands out from the edge, as a share of the road width
const DOT_PX = 5;
const ROAD_FILL = "#131a26";
// Point labels show only past this many pixels per metre.
const LABEL_MIN_SCALE = 0.6;
// Brake boards and their labels show only past this many pixels per metre, or they pile up.
const BOARD_MIN_SCALE = 2;

interface MapMarkersProps {
  geometry: MapGeometry;
  meta: TrackMeta;
  // Pixels per map unit.
  scale: number;
  // Which marks this session's formula has. The speed trap is always drawn.
  rules: FormulaRules;
}

// Zone lines beside the road, plus speed trap, overtake and brake board marks.
export function MapMarkers({ geometry, meta, scale, rules }: MapMarkersProps) {
  const frac = (m: number) => m / meta.trackLength;
  const markers = useMemo(() => buildMarkers(meta, rules), [meta, rules]);

  // A dot on the road centre at `m`: filled for a detection point or the speed trap, a ring for activation.
  const dot = ({ m, color, ring, label: text }: MarkerPoint, key: string) => {
    const { l, r } = edgeAt(geometry, frac(m));
    const x = (l[0] + r[0]) / 2;
    const y = (l[1] + r[1]) / 2;
    return (
      <g key={key}>
        <circle
          cx={x} cy={y} r={DOT_PX / scale}
          fill={ring ? ROAD_FILL : color} stroke={ring ? color : "white"} strokeWidth={ring ? 3 : 1.5}
          vectorEffect="non-scaling-stroke"
        />
        {scale >= LABEL_MIN_SCALE && (
          <text
            x={x + (DOT_PX + 4) / scale} y={y}
            fill={color} fontSize={11 / scale} dominantBaseline="middle"
            stroke={ROAD_FILL} strokeWidth={3} paintOrder="stroke" vectorEffect="non-scaling-stroke"
          >
            {text}
          </text>
        )}
      </g>
    );
  };

  const line = (ranges: DistanceRange[], edge: 0 | 1, px: number, color: string, key: string, dash?: string) =>
    ranges.map((r, i) => (
      <path
        key={`${key}-${i}`}
        d={toPath(lineAlong(geometry, frac(r.startM), frac(r.endM), edge, (edge === 0 ? -px : px) / scale), false)}
        fill="none" stroke={color} strokeWidth={2.5} strokeDasharray={dash} vectorEffect="non-scaling-stroke"
      />
    ));

  return (
    <g>
      {line(markers.aeroPartial, 0, AERO_PARTIAL_PX, MARKER_COLORS.aero, "aero-p", "2 4")}
      {line(markers.aeroFull, 0, AERO_FULL_PX, MARKER_COLORS.aero, "aero-f")}
      {line(markers.drs, 1, DRS_PX, MARKER_COLORS.drs, "drs")}
      {markers.points.map((pt, i) => dot(pt, `pt-${i}`))}
      {scale >= BOARD_MIN_SCALE &&
        markers.boards.map((b, i) => {
          const { l, r } = edgeAt(geometry, frac(b.m));
          const dx = r[0] - l[0];
          const dy = r[1] - l[1];
          const marks: Pt[][] = [];
          if (b.side !== "right") {
            marks.push([l, [l[0] - dx * BOARD_REACH, l[1] - dy * BOARD_REACH]]);
          }
          if (b.side !== "left") {
            marks.push([r, [r[0] + dx * BOARD_REACH, r[1] + dy * BOARD_REACH]]);
          }
          return marks.map(([from, to], k) => (
            <g key={`board-${i}-${k}`}>
              <line
                x1={from[0]} y1={from[1]} x2={to[0]} y2={to[1]}
                stroke={MARKER_COLORS.board} strokeWidth={3} vectorEffect="non-scaling-stroke"
              />
              <text
                x={to[0]} y={to[1]}
                fill={MARKER_COLORS.board}
                fontSize={11 / scale}
                textAnchor="middle"
                dy={-4 / scale}
              >
                {b.label}
              </text>
            </g>
          ));
        })}
    </g>
  );
}
