import { LAP_SLOT_COLORS, LAP_SLOT_LETTERS } from "../../lib/chartConstants";
import type { LoadedLap } from "../../lib/lapSeries";
import { formatSectionDelta, sectionTime } from "../../lib/sectionTable";
import type { TrackSection } from "../../types/api";

interface SegmentTooltipContentProps {
  title: string;
  section: TrackSection;
  // One per lap slot, A first; undefined while that lap is still loading.
  laps: readonly (LoadedLap | undefined)[];
  // A lap change is still loading, so the times held belong to the previous laps.
  loading: boolean;
}

// A segment's name over each lap's time through it, and who was faster than A. Rendered only while the
// tooltip is open, so the times are worked out on hover.
export function SegmentTooltipContent({ title, section, laps, loading }: SegmentTooltipContentProps) {
  const times = laps.map((lap) => (lap === undefined ? null : sectionTime(lap, section.distanceStart, section.distanceEnd)));
  const timeA = times[0] ?? null;
  const rows = laps.map((_, slot) => slot);

  return (
    <span className="block">
      <span className="block font-medium text-tone-50">{title}</span>
      {loading && <span className="mt-1 block text-xs text-tone-400">Loading…</span>}
      {!loading && timeA !== null && (
        <span className="mt-1.5 flex flex-col gap-0.5 font-mono text-xs">
          {rows.map((slot) => {
            const time = times[slot];
            const delta = slot === 0 || time === null ? null : time - timeA;
            return (
              <span key={slot} className="flex items-baseline gap-2">
                <span className="w-3 font-semibold" style={{ color: LAP_SLOT_COLORS[slot] }}>
                  {LAP_SLOT_LETTERS[slot]}
                </span>
                <span className="w-16 text-right text-tone-100">{time === null ? "–" : `${time.toFixed(3)} s`}</span>
                {delta !== null && (
                  <span className={delta > 0 ? "text-behind" : delta < 0 ? "text-ahead" : "text-tone-400"}>
                    {formatSectionDelta(delta)}
                  </span>
                )}
              </span>
            );
          })}
        </span>
      )}
    </span>
  );
}
