import { useEffect, useMemo, useRef, useState, type PointerEvent } from "react";
import { useSessions } from "../../hooks/useSessions";
import { useTelemetry } from "../../hooks/useTelemetry";
import { useTrackGeometry } from "../../hooks/useTrackGeometry";
import { useTrackMeta } from "../../hooks/useTrackMeta";
import { useTelemetryStore } from "../../store/telemetryStore";
import { COMPARISON_TRACE_COLOR, PRIMARY_TRACE_COLOR } from "../../lib/chartConstants";
import type { TelemetryPoint } from "../../types/api";

// POC. World (x, z) is drawn directly as SVG (x, y): SVG's y axis points down, so
// this is the top-down view (x, -z) the game's coordinates need.
const POS_KEYS = ["motion.position.x", "motion.position.z"];
const PAD_M = 30;

type Pt = [number, number];

function toPath(points: Pt[], close: boolean): string {
  if (points.length === 0) {
    return "";
  }
  return "M" + points.map((p) => `${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join("L") + (close ? "Z" : "");
}

function drivenLine(telemetry: TelemetryPoint[] | undefined): { pts: Pt[]; dist: number[] } {
  const pts: Pt[] = [];
  const dist: number[] = [];
  for (const p of telemetry ?? []) {
    const x = p[POS_KEYS[0]];
    const z = p[POS_KEYS[1]];
    if (x !== undefined && z !== undefined && !Number.isNaN(x) && !Number.isNaN(z)) {
      pts.push([x, z]);
      dist.push(p.lapDistance);
    }
  }
  return { pts, dist };
}

function at(line: { pts: Pt[]; dist: number[] }, d: number | null): Pt | null {
  if (d === null || line.dist.length === 0 || d < line.dist[0] || d > line.dist[line.dist.length - 1]) {
    return null;
  }
  let lo = 0;
  let hi = line.dist.length - 1;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (line.dist[mid] < d) {
      lo = mid + 1;
    } else {
      hi = mid;
    }
  }
  return line.pts[lo];
}

function bounds(pts: Pt[]): [number, number, number, number] | null {
  if (pts.length === 0) {
    return null;
  }
  let x0 = Infinity, x1 = -Infinity, z0 = Infinity, z1 = -Infinity;
  for (const [x, z] of pts) {
    x0 = Math.min(x0, x); x1 = Math.max(x1, x); z0 = Math.min(z0, z); z1 = Math.max(z1, z);
  }
  return [x0, z0, x1, z1];
}

export function TrackMap({ crosshairPosition }: { crosshairPosition: number | null }) {
  const primary = useTelemetryStore((s) => s.primary);
  const reference = useTelemetryStore((s) => s.reference);
  const activeSection = useTelemetryStore((s) => s.activeSection);
  const { data: sessions } = useSessions();
  const trackId = sessions?.find((s) => s.id === primary.sessionId)?.trackId ?? null;
  const geometry = useTrackGeometry(trackId);
  const meta = useTrackMeta(trackId);

  const { data: primaryTelemetry } = useTelemetry(primary.sessionId, primary.driverIndex, primary.lapNumber, POS_KEYS);
  const { data: referenceTelemetry } = useTelemetry(
    reference?.sessionId ?? null, reference?.driverIndex ?? null, reference?.lapNumber ?? null, POS_KEYS
  );
  const primaryLine = useMemo(() => drivenLine(primaryTelemetry), [primaryTelemetry]);
  const referenceLine = useMemo(() => drivenLine(referenceTelemetry), [referenceTelemetry]);

  const edges = useMemo(() => {
    if (geometry === null) {
      return null;
    }
    const n = geometry.edges.length / 6;
    const left: Pt[] = [];
    const right: Pt[] = [];
    for (let i = 0; i < n; i++) {
      left.push([geometry.edges[i * 6], geometry.edges[i * 6 + 2]]);
      right.push([geometry.edges[i * 6 + 3], geometry.edges[i * 6 + 5]]);
    }
    return { left, right };
  }, [geometry]);

  // Base view: the selected section's driven line (or its gates when there is no
  // position data), otherwise the whole circuit. [x, z, width, height].
  const baseView = useMemo((): [number, number, number, number] | null => {
    if (edges === null || geometry === null) {
      return null;
    }
    let view = bounds([...edges.left, ...edges.right]);
    if (activeSection !== null) {
      let pts = primaryLine.pts.filter(
        (_, i) => primaryLine.dist[i] >= activeSection.distanceStart && primaryLine.dist[i] <= activeSection.distanceEnd
      );
      if (pts.length === 0 && meta !== null) {
        const f0 = activeSection.distanceStart / meta.trackLength;
        const f1 = activeSection.distanceEnd / meta.trackLength;
        geometry.frac.forEach((f, i) => {
          if (f >= f0 && f <= f1) {
            pts.push(edges.left[i], edges.right[i]);
          }
        });
      }
      view = bounds(pts) ?? view;
    }
    if (view === null) {
      return null;
    }
    return [view[0] - PAD_M, view[1] - PAD_M, view[2] - view[0] + 2 * PAD_M, view[3] - view[1] + 2 * PAD_M];
  }, [edges, geometry, activeSection, primaryLine, meta]);

  // Manual wheel/drag zoom on top of the base view; cleared when the base view changes.
  const [manual, setManual] = useState<[number, number, number, number] | null>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const drag = useRef<{ x: number; y: number } | null>(null);
  useEffect(() => setManual(null), [baseView]);

  const view = manual ?? baseView;
  if (primary.lapNumber === null || edges === null || view === null) {
    return null;
  }

  // Slider zoom, keeping the current view centre.
  const zoom = baseView === null ? 1 : baseView[2] / view[2];
  function setZoom(next: number) {
    if (baseView === null || view === null) {
      return;
    }
    const w = baseView[2] / next;
    const h = baseView[3] / next;
    setManual([view[0] + view[2] / 2 - w / 2, view[1] + view[3] / 2 - h / 2, w, h]);
  }

  function onPointerDown(e: PointerEvent<SVGSVGElement>) {
    drag.current = { x: e.clientX, y: e.clientY };
    e.currentTarget.setPointerCapture(e.pointerId);
  }
  function onPointerMove(e: PointerEvent<SVGSVGElement>) {
    const ctm = e.currentTarget.getScreenCTM();
    if (drag.current === null || ctm === null || view === null) {
      return;
    }
    const dx = (e.clientX - drag.current.x) / ctm.a;
    const dy = (e.clientY - drag.current.y) / ctm.d;
    drag.current = { x: e.clientX, y: e.clientY };
    setManual([view[0] - dx, view[1] - dy, view[2], view[3]]);
  }

  const viewBox = view.join(" ");
  // Markers scale with the view so they stay visible at any zoom level.
  const dotR = Math.max(view[2], view[3]) / 60;

  const road = toPath([...edges.left, ...[...edges.right].reverse()], true);
  const primaryDot = at(primaryLine, crosshairPosition);
  const referenceDot = at(referenceLine, crosshairPosition);
  const noPosition = primaryLine.pts.length === 0;

  return (
    <div className="border-b border-slate-800 px-3 py-2">
      <div className="relative">
      <svg
        ref={svgRef}
        viewBox={viewBox}
        className="h-80 w-full cursor-grab touch-none active:cursor-grabbing"
        role="img"
        aria-label="Track map"
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={() => (drag.current = null)}
      >
        <path d={road} fill="#1e293b" fillRule="evenodd" />
        <path d={toPath(edges.left, true)} fill="none" stroke="#94a3b8" strokeWidth={1.5} vectorEffect="non-scaling-stroke" />
        <path d={toPath(edges.right, true)} fill="none" stroke="#94a3b8" strokeWidth={1.5} vectorEffect="non-scaling-stroke" />
        {referenceLine.pts.length > 0 && (
          <path d={toPath(referenceLine.pts, false)} fill="none" stroke={COMPARISON_TRACE_COLOR} strokeWidth={1.5} vectorEffect="non-scaling-stroke" />
        )}
        {!noPosition && (
          <path d={toPath(primaryLine.pts, false)} fill="none" stroke={PRIMARY_TRACE_COLOR} strokeWidth={1.5} vectorEffect="non-scaling-stroke" />
        )}
        {referenceDot !== null && <circle cx={referenceDot[0]} cy={referenceDot[1]} r={dotR} fill={COMPARISON_TRACE_COLOR} stroke="white" strokeWidth={2} vectorEffect="non-scaling-stroke" />}
        {primaryDot !== null && <circle cx={primaryDot[0]} cy={primaryDot[1]} r={dotR} fill={PRIMARY_TRACE_COLOR} stroke="white" strokeWidth={2} vectorEffect="non-scaling-stroke" />}
      </svg>
      <div className="absolute right-2 top-2 flex items-center gap-2 rounded bg-slate-800 px-2 py-1 text-xs text-slate-300">
        <span>Zoom</span>
        <input
          type="range"
          min={1}
          max={20}
          step={0.1}
          value={zoom}
          onChange={(e) => setZoom(Number(e.target.value))}
        />
        <button type="button" onClick={() => setManual(null)} className="hover:text-white">
          Reset
        </button>
      </div>
      </div>
      {noPosition && <p className="text-xs text-slate-500">No position data in this recording; showing the white lines only.</p>}
    </div>
  );
}
