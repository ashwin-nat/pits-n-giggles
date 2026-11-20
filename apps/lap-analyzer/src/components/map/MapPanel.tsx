import { useMemo } from "react";
import { useLapTelemetries } from "../../hooks/useLapTelemetries";
import { useSessions } from "../../hooks/useSessions";
import { useTrackGeometry } from "../../hooks/useTrackGeometry";
import { useTrackMeta } from "../../hooks/useTrackMeta";
import { LAP_SLOT_COLORS, LAP_SLOT_LETTERS } from "../../lib/chartConstants";
import { buildMapGeometry, drivenLine, POSITION_KEYS } from "../../lib/mapGeometry";
import { sectionCode, sectionViewport } from "../../lib/sectionStrip";
import { buildSectionRows } from "../../lib/sectionTable";
import { useTelemetryStore } from "../../store/telemetryStore";
import { isCompleteLap } from "../../types/store";
import type { TrackSection } from "../../types/api";
import { MapSvg } from "./MapSvg";

const SPEED_KEY = ["speed"];
// Past this many laps the table drops section names to keep the delta columns readable.
const NAME_COLUMN_MAX_LAPS = 3;

function formatDelta(value: number | null): string {
  if (value === null) {
    return "–";
  }
  return `${value > 0 ? "+" : ""}${value.toFixed(3)}`;
}

function SectionTable({ sections, trackLength }: { sections: TrackSection[]; trackLength: number }) {
  const laps = useTelemetryStore((s) => s.laps);
  const activeSection = useTelemetryStore((s) => s.activeSection);
  const hoverSection = useTelemetryStore((s) => s.hoverSection);
  const setActiveSection = useTelemetryStore((s) => s.setActiveSection);
  const setHoverSection = useTelemetryStore((s) => s.setHoverSection);
  const setViewport = useTelemetryStore((s) => s.setViewport);

  // Speed is fetched here whether or not the user charts it.
  const { laps: loaded } = useLapTelemetries(laps, SPEED_KEY);
  const rows = useMemo(() => buildSectionRows(loaded, sections), [loaded, sections]);

  const hasSpeed = rows.some((r) => r.minA !== null);
  const showName = laps.length <= NAME_COLUMN_MAX_LAPS;
  const comparisonSlots = laps.map((_, slot) => slot).slice(1);
  const same = (a: typeof activeSection, s: TrackSection) =>
    a !== null && a.label === s.label && a.distanceStart === s.distanceStart;

  if (rows.length === 0) {
    return null;
  }
  return (
    <table className="w-full border-t border-tone-800 text-xs">
      <thead>
        <tr className="text-left text-tone-500">
          <th className="px-3 py-1.5 font-medium" colSpan={2}>Section</th>
          {hasSpeed && <th className="px-2 py-1.5 text-right font-medium whitespace-nowrap" style={{ color: LAP_SLOT_COLORS[0] }}>Min A</th>}
          {comparisonSlots.map((slot) => (
            <th key={slot} className="px-2 py-1.5 text-right font-medium" style={{ color: LAP_SLOT_COLORS[slot] }}>
              Δ{LAP_SLOT_LETTERS[slot]}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map(({ section, minA, deltas }) => (
          <tr
            key={`${section.label}-${section.distanceStart}`}
            onClick={() => {
              if (same(activeSection, section)) {
                setActiveSection(null);
                setViewport(null);
              } else {
                setActiveSection(section);
                setViewport(sectionViewport(section.distanceStart, section.distanceEnd));
              }
            }}
            onMouseEnter={() => setHoverSection(section)}
            onMouseLeave={() => setHoverSection(null)}
            className={`cursor-pointer text-tone-100 hover:bg-tone-800 ${
              same(activeSection, section) ? "bg-tone-800" : same(hoverSection, section) ? "bg-tone-800/60" : ""
            }`}
          >
            <td className="py-1.5 pr-2 pl-3 font-mono text-tone-400">{sectionCode(section, trackLength)}</td>
            <td className="w-full max-w-0 truncate py-1.5 pr-2">{showName ? section.label : ""}</td>
            {hasSpeed && (
              <td className="px-2 py-1.5 text-right font-mono">{minA === null ? "–" : Math.round(minA)}</td>
            )}
            {comparisonSlots.map((slot) => {
              const delta = deltas[slot];
              return (
                <td
                  key={slot}
                  className={`px-2 py-1.5 text-right font-mono ${
                    delta === null ? "text-tone-600" : delta > 0 ? "text-behind" : delta < 0 ? "text-ahead" : ""
                  }`}
                >
                  {formatDelta(delta)}
                </td>
              );
            })}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

// Pinned side panel: track map above, section table below. Collapses to a slim button.
export function MapPanel({ crosshairPosition }: { crosshairPosition: number | null }) {
  const laps = useTelemetryStore((s) => s.laps);
  const mapOpen = useTelemetryStore((s) => s.mapOpen);
  const toggleMap = useTelemetryStore((s) => s.toggleMap);
  const activeSection = useTelemetryStore((s) => s.activeSection);
  const hoverSection = useTelemetryStore((s) => s.hoverSection);

  const { data: sessions } = useSessions();
  const trackId = sessions?.find((s) => s.id === laps[0]?.sessionId)?.trackId ?? null;
  const rawGeometry = useTrackGeometry(trackId);
  const meta = useTrackMeta(trackId);
  const geometry = useMemo(
    () => (rawGeometry ? buildMapGeometry(rawGeometry.edges, rawGeometry.frac) : rawGeometry),
    [rawGeometry]
  );

  const { laps: positions } = useLapTelemetries(laps, POSITION_KEYS);
  const lines = useMemo(() => positions.map((lap) => drivenLine(lap?.points)), [positions]);

  if (!isCompleteLap(laps[0])) {
    return null;
  }
  if (!mapOpen) {
    return (
      <button
        type="button"
        onClick={toggleMap}
        className="sticky top-0 shrink-0 self-start border-l border-tone-800/70 bg-chart-panel px-2 py-3 text-xs text-tone-300 hover:text-white [writing-mode:vertical-rl]"
      >
        Track map ‹
      </button>
    );
  }

  const sectionName = (activeSection ?? hoverSection)?.label;

  return (
    <aside className="sticky top-0 flex max-h-screen w-[380px] shrink-0 flex-col self-start overflow-y-auto border-l border-tone-800/70 bg-chart-panel">
      <div className="flex items-center justify-between px-3 py-2 text-xs">
        <span className="font-semibold text-tone-50">
          Track
          <span className="ml-2 font-normal text-tone-400">
            {sessions?.find((s) => s.id === laps[0]?.sessionId)?.trackName}
            {meta !== null && ` · ${Math.round(meta.trackLength).toLocaleString()} m`}
          </span>
          {sectionName !== undefined && <span className="ml-2 font-normal text-tone-300">· {sectionName}</span>}
        </span>
        <button type="button" onClick={toggleMap} className="text-tone-400 hover:text-white" title="Collapse the map">
          ›
        </button>
      </div>
      {geometry === undefined ? (
        <p className="p-6 text-center text-xs text-slate-500">Loading map…</p>
      ) : geometry === null ? (
        <p className="p-6 text-center text-xs text-slate-500">Track map not available for this track</p>
      ) : (
        <MapSvg
          geometry={geometry}
          meta={meta}
          lines={lines}
          lapPresent={laps.map((lap) => isCompleteLap(lap))}
          labels={laps.map((lap, slot) => `${LAP_SLOT_LETTERS[slot]} L${lap.lapNumber ?? ""}`)}
          crosshairPosition={crosshairPosition}
          activeSection={activeSection}
          hoverSection={hoverSection}
        />
      )}
      <SectionTable sections={meta?.sections ?? []} trackLength={meta?.trackLength ?? 0} />
    </aside>
  );
}
