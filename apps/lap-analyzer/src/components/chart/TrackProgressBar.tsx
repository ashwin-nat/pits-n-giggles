import { useSessions } from "../../hooks/useSessions";
import { useTrackMeta } from "../../hooks/useTrackMeta";
import { useTelemetryStore } from "../../store/telemetryStore";
import type { TrackSection } from "../../types/api";
import type { ActiveSection } from "../../types/store";
import { InfoTooltip } from "./InfoTooltip";

interface TrackProgressBarProps {
  // The shared chart crosshair (ChartLaneList/ChartArea-owned) -- drives the
  // position marker. null when nothing is hovered.
  crosshairPosition: number | null;
}

const SEGMENT_COLOR: Record<TrackSection["type"], string> = {
  straight: "bg-emerald-600 hover:bg-emerald-500",
  corner: "bg-sky-700 hover:bg-sky-600",
  complex_corner: "bg-indigo-700 hover:bg-indigo-600",
};

type BarSegment =
  | { kind: "section"; section: TrackSection }
  | { kind: "gap"; distanceStart: number; distanceEnd: number };

// Segment data has real holes between named segments (e.g. a short unnamed
// straight between two corners) -- rendering only the named segments would
// make the bar's flex-grow proportions skip that distance entirely, which
// throws off both the visual scale and the crosshair marker's percentage
// (computed against the *full* track length). These gaps get their own grey,
// non-interactive filler blocks so the bar's total width always equals the
// track's actual length.
function buildBarSegments(sections: TrackSection[], trackLength: number): BarSegment[] {
  const sorted = [...sections].sort((a, b) => a.distanceStart - b.distanceStart);
  const result: BarSegment[] = [];
  let cursor = 0;
  for (const section of sorted) {
    if (section.distanceStart > cursor) {
      result.push({ kind: "gap", distanceStart: cursor, distanceEnd: section.distanceStart });
    }
    result.push({ kind: "section", section });
    cursor = Math.max(cursor, section.distanceEnd);
  }
  if (cursor < trackLength) {
    result.push({ kind: "gap", distanceStart: cursor, distanceEnd: trackLength });
  }
  return result;
}

function isSameSection(active: ActiveSection | null, section: TrackSection): boolean {
  return (
    active !== null && active.label === section.label && active.distanceStart === section.distanceStart
  );
}

function segmentTooltip(section: TrackSection): string {
  if (section.cornerNumbers.length === 0) {
    return section.label;
  }
  if (section.cornerNumbers.length === 1) {
    return `${section.label} -- Turn ${section.cornerNumbers[0]}`;
  }
  const first = section.cornerNumbers[0];
  const last = section.cornerNumbers[section.cornerNumbers.length - 1];
  return `${section.label} -- Turns ${first}-${last}`;
}

// Replaces the old one-pill-per-segment row: segments are drawn proportional
// to their actual distance span (from the same start_m/end_m the pills used)
// and color-coded by type, so the bar reads as a miniature track layout
// instead of a wrapping list of buttons. Clicking a segment still sets
// store.activeSection (focus zone); the bar doesn't change the viewport.
export function TrackProgressBar({ crosshairPosition }: TrackProgressBarProps) {
  const primarySessionId = useTelemetryStore((state) => state.primary.sessionId);
  const activeSection = useTelemetryStore((state) => state.activeSection);
  const setActiveSection = useTelemetryStore((state) => state.setActiveSection);
  const viewport = useTelemetryStore((state) => state.viewport);
  const setViewport = useTelemetryStore((state) => state.setViewport);

  const { data: sessions } = useSessions();
  const trackId = sessions?.find((s) => s.id === primarySessionId)?.trackId ?? null;
  const meta = useTrackMeta(trackId);

  if (primarySessionId === null) {
    return null;
  }

  const sectionList = meta?.sections ?? [];
  const trackLength = meta?.trackLength ?? 0;
  const barSegments = buildBarSegments(sectionList, trackLength);
  const sectorMarkerPcts =
    meta !== null && trackLength > 0
      ? [meta.sectorBoundaries.s1, meta.sectorBoundaries.s2].map((d) => (d / trackLength) * 100)
      : [];
  const markerPct =
    crosshairPosition !== null && trackLength > 0
      ? Math.min(100, Math.max(0, (crosshairPosition / trackLength) * 100))
      : null;
  const viewportRange =
    viewport !== null && trackLength > 0
      ? {
          leftPct: Math.min(100, Math.max(0, (viewport.distanceStart / trackLength) * 100)),
          rightPct: Math.min(100, Math.max(0, (viewport.distanceEnd / trackLength) * 100)),
        }
      : null;

  function handleSegmentClick(section: TrackSection) {
    // No dedicated "Full Lap" reset button -- clicking the already-active
    // segment again clears it instead, same toggle-off pattern as the
    // legend's visibility dots.
    if (isSameSection(activeSection, section)) {
      setActiveSection(null);
      setViewport(null);
    } else {
      setActiveSection(section);
    }
  }

  return (
    <div className="border-b border-slate-800 bg-slate-900 px-4 py-2">
      <div className="relative h-6 w-full">
        {/* No overflow-hidden on this row -- it would clip InfoTooltip's
            popup, which renders outside the row's box (bottom-full). Rounded
            ends come from the first/last block's own corners instead. */}
        <div className="flex h-full w-full">
          {barSegments.map((bar, index) => {
            const roundedClass = `${index === 0 ? "rounded-l-full" : ""} ${
              index === barSegments.length - 1 ? "rounded-r-full" : ""
            }`;
            const span =
              bar.kind === "gap"
                ? bar.distanceEnd - bar.distanceStart
                : bar.section.distanceEnd - bar.section.distanceStart;
            const flexStyle = { flexGrow: span, flexBasis: 0 };

            if (bar.kind === "gap") {
              return (
                <div
                  key={`gap-${bar.distanceStart}`}
                  style={flexStyle}
                  className={`h-full border-r border-slate-950/40 bg-slate-700 last:border-r-0 ${roundedClass}`}
                />
              );
            }
            const { section } = bar;
            return (
              <InfoTooltip
                key={`${section.label}-${section.distanceStart}`}
                text={segmentTooltip(section)}
                style={flexStyle}
                className="h-full"
                placement="bottom"
              >
                <button
                  type="button"
                  onClick={() => handleSegmentClick(section)}
                  className={`h-full w-full border-r border-slate-950/40 last:border-r-0 ${roundedClass} ${
                    SEGMENT_COLOR[section.type]
                  } ${isSameSection(activeSection, section) ? "brightness-150" : ""}`}
                />
              </InfoTooltip>
            );
          })}
        </div>
        {sectorMarkerPcts.map((pct, i) => (
          <div
            key={`sector-${i}`}
            className="pointer-events-none absolute top-0 h-full w-1 bg-amber-400 shadow-[0_0_6px_rgba(251,191,36,0.9)]"
            style={{ left: `${pct}%` }}
          />
        ))}
        {viewportRange !== null && (
          <div
            className="pointer-events-none absolute top-0 h-full rounded-full border-2 border-white/80 bg-white/10"
            style={{
              left: `${viewportRange.leftPct}%`,
              width: `${viewportRange.rightPct - viewportRange.leftPct}%`,
            }}
          />
        )}
        {markerPct !== null && (
          <div
            className="pointer-events-none absolute top-0 h-full w-0.5 bg-white shadow-[0_0_4px_rgba(255,255,255,0.8)]"
            style={{ left: `${markerPct}%` }}
          />
        )}
      </div>
    </div>
  );
}
