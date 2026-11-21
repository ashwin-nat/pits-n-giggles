import { useEffect, useMemo, useRef, useState, type PointerEvent } from "react";
import {
  boundsOf,
  centreOn,
  clampZoom,
  padBox,
  pixelsPerUnit,
  pointAt,
  sectionBox,
  sectionPolygon,
  tickAt,
  toMap,
  toPath,
  zoomAbout,
  type Box,
  type DrivenLine,
  type MapGeometry,
  type Pt,
} from "../../lib/mapGeometry";
import { formulaRules } from "../../lib/formulas";
import { MARKER_COLORS } from "../../lib/trackMarkers";
import { MapMarkers } from "./MapMarkers";
import { LAP_SLOT_COLORS, LAP_SLOT_LETTERS } from "../../lib/chartConstants";
import type { TrackMeta } from "../../lib/segments";
import { useTelemetryStore } from "../../store/telemetryStore";
import type { ActiveSection } from "../../types/store";

const WHOLE_PAD_M = 80;
const SEGMENT_TICK_OVERHANG = 0.6;
const SECTOR_TICK_OVERHANG = 0.9;
const WHEEL_ZOOM = 0.85;

interface MapSvgProps {
  geometry: MapGeometry;
  meta: TrackMeta | null;
  // The session's formula string; decides which zone marks are drawn.
  formula: string;
  // One driven line per lap slot; an empty line means that lap has no position data.
  lines: DrivenLine[];
  // Which slots hold a complete lap (an empty slot gets no legend entry).
  lapPresent: boolean[];
  // Legend text per slot, e.g. "A L3".
  labels: string[];
  crosshairPosition: number | null;
  activeSection: ActiveSection | null;
  hoverSection: ActiveSection | null;
}

const BUTTON = "rounded-md bg-tone-800/80 px-2 py-1 text-2xs text-tone-300 hover:bg-tone-700 hover:text-white";

// Top-down map: road, white lines, segment and sector ticks, one driven line
// and cursor dot per lap. The view box is state (null = the whole track).
export function MapSvg({ geometry, meta, formula, lines, lapPresent, labels, crosshairPosition, activeSection, hoverSection }: MapSvgProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [size, setSize] = useState({ width: 400, height: 320 });
  const [view, setView] = useState<Box | null>(null);
  const [follow, setFollow] = useState(false);
  const showMarkers = useTelemetryStore((state) => state.showMarkers);
  const rules = formulaRules(formula);
  const drag = useRef<{ x: number; y: number } | null>(null);

  const whole = useMemo<Box>(() => {
    const b = boundsOf([...geometry.L, ...geometry.R]) ?? [0, 0, 1, 1];
    return padBox(b, WHOLE_PAD_M);
  }, [geometry]);

  const trackLength = meta?.trackLength ?? 0;
  const frac = (d: number) => d / trackLength;

  // Selecting a section zooms to it; clearing it fits the whole track.
  useEffect(() => {
    if (activeSection === null || trackLength === 0) {
      setView(null);
      return;
    }
    setView(sectionBox(geometry, frac(activeSection.distanceStart), frac(activeSection.distanceEnd)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeSection, geometry, trackLength]);

  useEffect(() => {
    const el = svgRef.current;
    if (el === null) {
      return;
    }
    const observer = new ResizeObserver(() => {
      const r = el.getBoundingClientRect();
      setSize({ width: r.width, height: r.height });
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const dots = lines.map((line) => pointAt(line, crosshairPosition));
  const canFollow = lines[0] !== undefined && lines[0].pts.length > 0;
  // Follow only applies while zoomed in; it centres the view on A's dot.
  let vb: Box = view ?? whole;
  if (follow && canFollow && view !== null && dots[0] !== null && dots[0] !== undefined) {
    vb = centreOn(vb, dots[0]);
  }
  const vbRef = useRef(vb);
  vbRef.current = vb;
  const viewRef = useRef({ view, whole });
  viewRef.current = { view, whole };

  // Wheel zoom about the pointer. A native listener: React's onWheel is passive
  // and cannot stop the page scrolling.
  useEffect(() => {
    const el = svgRef.current;
    if (el === null) {
      return;
    }
    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      const k = e.deltaY < 0 ? WHEEL_ZOOM : 1 / WHEEL_ZOOM;
      const current = vbRef.current;
      const p = toMap(el.getBoundingClientRect(), current, e.clientX, e.clientY);
      const next = clampZoom(zoomAbout(current, p, k), viewRef.current.whole);
      setView(next[2] >= Math.max(viewRef.current.whole[2], viewRef.current.whole[3]) ? null : next);
    };
    el.addEventListener("wheel", onWheel, { passive: false });
    return () => el.removeEventListener("wheel", onWheel);
  }, []);

  function onPointerDown(e: PointerEvent<SVGSVGElement>) {
    drag.current = { x: e.clientX, y: e.clientY };
    e.currentTarget.setPointerCapture(e.pointerId);
  }
  function onPointerMove(e: PointerEvent<SVGSVGElement>) {
    if (drag.current === null) {
      return;
    }
    const sc = pixelsPerUnit(size, vb);
    const dx = (e.clientX - drag.current.x) / sc;
    const dy = (e.clientY - drag.current.y) / sc;
    drag.current = { x: e.clientX, y: e.clientY };
    setFollow(false);
    setView([vb[0] - dx, vb[1] - dy, vb[2], vb[3]]);
  }

  function zoomButton(k: number) {
    const centre: Pt = [vb[0] + vb[2] / 2, vb[1] + vb[3] / 2];
    const next = clampZoom(zoomAbout(vb, centre, k), whole);
    setView(next[2] >= Math.max(whole[2], whole[3]) ? null : next);
  }

  const sc = pixelsPerUnit(size, vb);
  const dotRadius = (px: number) => px / sc;

  const road =
    toPath(geometry.L, true) + toPath(geometry.R, true);

  const polygons: [ActiveSection | null, string][] = [
    [hoverSection, "rgba(255,255,255,0.30)"],
    [activeSection, "rgba(255,255,255,0.20)"],
  ];

  // Segment boundaries, minus any that coincide with a sector boundary.
  const sectorDistances = meta === null ? [] : [meta.sectorBoundaries.s1, meta.sectorBoundaries.s2];
  const segmentDistances = useMemo(() => {
    if (meta === null) {
      return [];
    }
    const set = new Set<number>();
    for (const s of meta.sections) {
      set.add(s.distanceStart);
      set.add(s.distanceEnd);
    }
    return [...set].filter(
      (d) => d > 0 && d < meta.trackLength && !sectorDistances.some((sd) => Math.abs(sd - d) < 1)
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [meta]);

  return (
    <div className="relative">
      <svg
        ref={svgRef}
        viewBox={vb.join(" ")}
        preserveAspectRatio="xMidYMid meet"
        className="mt-9 h-[400px] w-full cursor-grab touch-none select-none active:cursor-grabbing"
        role="img"
        aria-label="Track map"
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={() => (drag.current = null)}
        onPointerCancel={() => (drag.current = null)}
        onLostPointerCapture={() => (drag.current = null)}
        onDoubleClick={() => {
          setView(null);
          setFollow(false);
        }}
      >
        <path d={road} fill="#131a26" fillRule="evenodd" />
        {trackLength > 0 &&
          polygons.map(([section, fill], i) =>
            section === null ? null : (
              <path
                key={i}
                d={toPath(sectionPolygon(geometry, frac(section.distanceStart), frac(section.distanceEnd)), true)}
                fill={fill}
              />
            )
          )}
        {showMarkers && meta !== null && (
          <MapMarkers geometry={geometry} meta={meta} scale={sc} rules={rules} />
        )}
        <path d={toPath(geometry.L, true)} fill="none" stroke="#94a3b8" strokeWidth={1.5} vectorEffect="non-scaling-stroke" />
        <path d={toPath(geometry.R, true)} fill="none" stroke="#94a3b8" strokeWidth={1.5} vectorEffect="non-scaling-stroke" />
        {segmentDistances.map((d) => {
          const [a, b] = tickAt(geometry, frac(d), SEGMENT_TICK_OVERHANG);
          return (
            <line
              key={`seg-${d}`}
              x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]}
              stroke="#cbd5e1" strokeWidth={1.5} vectorEffect="non-scaling-stroke"
            />
          );
        })}
        {sectorDistances.map((d) => {
          const [a, b] = tickAt(geometry, frac(d), SECTOR_TICK_OVERHANG);
          return (
            <line
              key={`sector-${d}`}
              x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]}
              stroke="#fbbf24" strokeWidth={1.5} strokeDasharray="4 3" vectorEffect="non-scaling-stroke"
            />
          );
        })}
        {lines.map((line, slot) =>
          line.pts.length === 0 ? null : (
            <path
              key={`line-${slot}`}
              d={toPath(line.pts, false)}
              fill="none"
              stroke={LAP_SLOT_COLORS[slot]}
              strokeWidth={slot === 0 ? 1.75 : 1.25}
              vectorEffect="non-scaling-stroke"
            />
          )
        )}
        {dots.map((dot, slot) =>
          dot === null ? null : (
            <circle
              key={`dot-${slot}`}
              cx={dot[0]} cy={dot[1]}
              r={dotRadius(slot === 0 ? 6 : 4.5)}
              fill={LAP_SLOT_COLORS[slot]}
              stroke="white" strokeWidth={slot === 0 ? 2 : 1.5}
              vectorEffect="non-scaling-stroke"
            />
          )
        )}
      </svg>

      <div className="flex flex-wrap items-center gap-x-3 gap-y-0.5 px-3 py-2 text-2xs text-tone-300">
        {lapPresent.map((present, slot) =>
          present ? (
            <span key={slot} className="flex items-center gap-1.5">
              <span className="h-0.5 w-3.5 rounded-full" style={{ backgroundColor: LAP_SLOT_COLORS[slot] }} />
              {labels[slot] ?? LAP_SLOT_LETTERS[slot]}
              {(lines[slot]?.pts.length ?? 0) === 0 && <span className="text-tone-500">(no position data)</span>}
            </span>
          ) : null
        )}
      </div>

      {showMarkers && meta !== null && (
        <div className="flex flex-wrap items-center gap-x-3 gap-y-0.5 px-3 pb-2 text-2xs text-tone-300">
          {(
            [
              [rules.drs, "DRS zone and detection", MARKER_COLORS.drs],
              [rules.activeAero, "Aero full (solid)", MARKER_COLORS.aero],
              [rules.activeAero, "Aero partial (dotted)", MARKER_COLORS.aero],
              [true, "Speed trap", MARKER_COLORS.speedTrap],
              [rules.overtake, "Overtake detection, ring = activation", MARKER_COLORS.overtake],
              [true, "Brake boards (zoom in)", MARKER_COLORS.board],
            ] as const
          )
            .filter(([applies]) => applies)
            .map(([, name, color]) => (
            <span key={name} className="flex items-center gap-1.5">
              <span className="h-2 w-3.5 rounded-sm" style={{ backgroundColor: color }} />
              {name}
            </span>
          ))}
        </div>
      )}

      <div className="absolute right-3 top-2 flex items-center gap-1">
        <button type="button" className={BUTTON} onClick={() => zoomButton(WHEEL_ZOOM)} title="Zoom in">
          +
        </button>
        <button type="button" className={BUTTON} onClick={() => zoomButton(1 / WHEEL_ZOOM)} title="Zoom out">
          −
        </button>
        <button
          type="button"
          className={BUTTON}
          onClick={() => {
            setView(null);
            setFollow(false);
          }}
        >
          Fit
        </button>
        <button
          type="button"
          disabled={!canFollow}
          title={canFollow ? "Keep the car centred while hovering the charts" : "A has no position data"}
          onClick={() => setFollow((f) => !f)}
          className={`${BUTTON} disabled:cursor-not-allowed disabled:opacity-40 ${follow && canFollow ? "bg-tone-100 text-tone-900 hover:bg-tone-100 hover:text-tone-900" : ""}`}
        >
          Follow
        </button>
      </div>

      <div className="absolute top-3 left-3 text-2xs text-tone-500">↔ {Math.round(size.width / sc)} m across</div>
    </div>
  );
}
