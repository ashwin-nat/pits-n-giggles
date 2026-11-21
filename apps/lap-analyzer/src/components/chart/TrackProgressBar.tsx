import { useSessions } from "../../hooks/useSessions";
import { useTrackMeta } from "../../hooks/useTrackMeta";
import { useTelemetryStore } from "../../store/telemetryStore";
import type { TrackSection } from "../../types/api";
import type { ActiveSection } from "../../types/store";
import { labelFits, sectionCode, sectionViewport } from "../../lib/sectionStrip";
import { useLapTelemetries } from "../../hooks/useLapTelemetries";
import { InfoTooltip } from "./InfoTooltip";
import { SegmentTooltipContent } from "./SegmentTooltipContent";
import { StripMarkers } from "./StripMarkers";

interface TrackProgressBarProps {
  // The shared chart crosshair (ChartLaneList/ChartArea-owned) -- drives the
  // position marker. null when nothing is hovered.
  crosshairPosition: number | null;
}

// Every named section is the same navy pill; unnamed gaps stay empty.
const PILL = "bg-tone-800 hover:bg-tone-700";

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

function isSameSection(active: ActiveSection | null, section: { label: string; distanceStart: number }): boolean {
  return (
    active !== null && active.label === section.label && active.distanceStart === section.distanceStart
  );
}

const UNCLASSIFIED_LABEL = "Unclassified";

function gapToActiveSection(gap: { distanceStart: number; distanceEnd: number }): ActiveSection {
  return { label: UNCLASSIFIED_LABEL, distanceStart: gap.distanceStart, distanceEnd: gap.distanceEnd };
}

export function segmentTooltip(section: TrackSection): string {
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
  const primarySessionId = useTelemetryStore((state) => state.laps[0]?.sessionId ?? null);
  const activeSection = useTelemetryStore((state) => state.activeSection);
  const setActiveSection = useTelemetryStore((state) => state.setActiveSection);
  const viewport = useTelemetryStore((state) => state.viewport);
  const setViewport = useTelemetryStore((state) => state.setViewport);
  const setHoverSection = useTelemetryStore((state) => state.setHoverSection);
  const showMarkers = useTelemetryStore((state) => state.showMarkers);
  const laps = useTelemetryStore((state) => state.laps);
  const { laps: loadedLaps } = useLapTelemetries(laps);

  const { data: sessions } = useSessions();
  const session = sessions?.find((s) => s.id === primarySessionId);
  const trackId = session?.trackId ?? null;
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

  // Selecting zooms the charts to the section; selecting it again clears it.
  function select(section: ActiveSection) {
    setActiveSection(section);
    setViewport(sectionViewport(section.distanceStart, section.distanceEnd));
  }

  function clear() {
    setActiveSection(null);
    setViewport(null);
  }

  function handleSegmentClick(section: TrackSection) {
    if (isSameSection(activeSection, section)) {
      clear();
    } else {
      select(section);
    }
  }

  function handleGapClick(gap: { distanceStart: number; distanceEnd: number }) {
    if (isSameSection(activeSection, { label: UNCLASSIFIED_LABEL, distanceStart: gap.distanceStart })) {
      clear();
    } else {
      select(gapToActiveSection(gap));
    }
  }

  // Prev / next step through the named sections in track order.
  const named = [...sectionList].sort((a, b) => a.distanceStart - b.distanceStart);
  const activeIndex = named.findIndex((section) => isSameSection(activeSection, section));
  function step(direction: -1 | 1) {
    if (named.length === 0) {
      return;
    }
    const next =
      activeIndex === -1
        ? direction === 1
          ? 0
          : named.length - 1
        : (activeIndex + direction + named.length) % named.length;
    select(named[next]);
  }

  return (
    <div className="flex items-center border-b border-tone-800/70 bg-chart-surface py-1.5">
      {/* Same width as the lane headers, so the strip lines up with the plots. */}
      <div className="flex w-[168px] shrink-0 items-center gap-1 px-2 text-xs text-tone-300">
        <button
          type="button"
          onClick={() => step(-1)}
          title="Previous section"
          className="rounded px-1.5 py-0.5 hover:bg-tone-700"
        >
          ‹
        </button>
        <button
          type="button"
          onClick={clear}
          title="Show the whole lap"
          className={`rounded px-2 py-0.5 hover:bg-tone-700 ${activeSection === null ? "bg-tone-700 text-tone-100" : ""}`}
        >
          Full lap
        </button>
        <button
          type="button"
          onClick={() => step(1)}
          title="Next section"
          className="rounded px-1.5 py-0.5 hover:bg-tone-700"
        >
          ›
        </button>
      </div>
      <div className="min-w-0 flex-1">
      <div className="relative h-7">
        {/* No overflow-hidden on this row -- it would clip InfoTooltip's
            popup, which renders outside the row's box (bottom-full). */}
        <div className="flex h-full w-full">
          {barSegments.map((bar) => {
            const span =
              bar.kind === "gap"
                ? bar.distanceEnd - bar.distanceStart
                : bar.section.distanceEnd - bar.section.distanceStart;
            const flexStyle = { flexGrow: span, flexBasis: 0 };

            if (bar.kind === "gap") {
              const gapActive = isSameSection(activeSection, {
                label: UNCLASSIFIED_LABEL,
                distanceStart: bar.distanceStart,
              });
              return (
                <button
                  key={`gap-${bar.distanceStart}`}
                  type="button"
                  onClick={() => handleGapClick(bar)}
                  onMouseEnter={() => setHoverSection(gapToActiveSection(bar))}
                  onMouseLeave={() => setHoverSection(null)}
                  style={flexStyle}
                  title="Unclassified"
                  className={`h-full w-[calc(100%-2px)] rounded-md border border-dashed border-tone-700 hover:bg-white/10 ${
                    gapActive ? "bg-white/15" : "bg-white/[0.04]"
                  }`}
                />
              );
            }
            const { section } = bar;
            return (
              <InfoTooltip
                key={`${section.label}-${section.distanceStart}`}
                text={<SegmentTooltipContent title={segmentTooltip(section)} section={section} laps={loadedLaps} />}
                style={flexStyle}
                className="h-full"
                placement="bottom"
              >
                <button
                  type="button"
                  onClick={() => handleSegmentClick(section)}
                  onMouseEnter={() => setHoverSection(section)}
                  onMouseLeave={() => setHoverSection(null)}
                  className={`h-full w-[calc(100%-2px)] overflow-hidden rounded-md whitespace-nowrap text-xs font-medium text-tone-100 ${PILL} ${
                    isSameSection(activeSection, section) ? "ring-1 ring-sky-400" : ""
                  }`}
                >
                  {trackLength > 0 && labelFits((span / trackLength) * 100, sectionCode(section, trackLength))
                    ? sectionCode(section, trackLength)
                    : null}
                </button>
              </InfoTooltip>
            );
          })}
        </div>
        {sectorMarkerPcts.map((pct, i) => (
          <div
            key={`sector-${i}`}
            className="pointer-events-none absolute top-[-2px] h-[calc(100%+4px)] w-[3px] rounded-full bg-amber-400"
            style={{ left: `${pct}%` }}
          />
        ))}
        {viewportRange !== null && (
          <div
            className="pointer-events-none absolute top-0 h-full rounded-md border border-white/70 bg-white/10"
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
      {showMarkers && meta !== null && trackLength > 0 && <StripMarkers meta={meta} formula={session?.formula ?? ""} />}
      </div>
    </div>
  );
}
