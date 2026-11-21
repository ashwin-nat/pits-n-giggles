import { useQueries } from "@tanstack/react-query";
import { useDrivers } from "../../hooks/useDrivers";
import { useSessions } from "../../hooks/useSessions";
import { useLapAnalyzerProvider } from "../../providers/ProviderContext";
import { LAP_SLOT_COLORS, LAP_SLOT_LETTERS, MAX_COMPARISON_LAPS } from "../../lib/chartConstants";
import { formatGap, formatLapTime } from "../../lib/lapFormat";
import { useTelemetryStore } from "../../store/telemetryStore";
import { isCompleteLap, type LapSelection } from "../../types/store";

interface LapChipsProps {
  // Opens the Choose lap modal for a slot; a slot past the last lap adds one.
  onChoose: (slot: number) => void;
}

// Lap time of each slot's lap, from the same queries the pickers use.
function useLapTimes(laps: readonly LapSelection[]): (number | null)[] {
  const active = useLapAnalyzerProvider();
  const queries = useQueries({
    queries: laps.map((lap) => ({
      queryKey: ["laps", active?.id ?? null, lap.sessionId, lap.driverIndex],
      queryFn: () => {
        if (active === null || !isCompleteLap(lap)) {
          throw new Error("useLapTimes queried an incomplete lap");
        }
        return active.provider.getLaps(lap.sessionId, lap.driverIndex);
      },
      enabled: active !== null && isCompleteLap(lap),
    })),
  });
  return laps.map((lap, i) => queries[i]?.data?.find((l) => l.lapNumber === lap.lapNumber)?.lapTime ?? null);
}

function dateLabel(iso: string): string {
  const date = new Date(iso);
  return iso === "" || Number.isNaN(date.getTime())
    ? ""
    : date.toLocaleString(undefined, { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
}

interface ChipProps {
  slot: number;
  lap: LapSelection;
  timeMs: number | null;
  gapMs: number | null;
  fastest: boolean;
  onChoose: () => void;
  onRemove?: () => void;
}

function Chip({ slot, lap, timeMs, gapMs, fastest, onChoose, onRemove }: ChipProps) {
  const { data: sessions } = useSessions();
  const { data: drivers } = useDrivers(lap.sessionId);
  const session = sessions?.find((s) => s.id === lap.sessionId);
  const driver = drivers?.find((d) => d.index === lap.driverIndex);

  return (
    <div className="group flex items-center rounded-lg border border-tone-800 bg-tone-900/60 transition-colors hover:bg-tone-800/70">
      <button type="button" onClick={onChoose} className="flex items-center gap-2.5 py-1.5 pr-2 pl-2 text-left" title="Change this lap">
        <span
          className="flex size-6 shrink-0 items-center justify-center rounded-md text-xs font-bold text-tone-1000"
          style={{ backgroundColor: LAP_SLOT_COLORS[slot] }}
        >
          {LAP_SLOT_LETTERS[slot]}
        </span>
        <span className="flex flex-col items-start leading-tight">
          <span className="flex items-baseline gap-2">
            <span className={`font-mono text-base ${fastest ? "text-best" : "text-tone-50"}`}>{formatLapTime(timeMs)}</span>
            <span className="text-sm text-tone-200">{driver?.name ?? ""}</span>
            {gapMs !== null && (
              <span className={`font-mono text-xs ${gapMs > 0 ? "text-behind" : "text-ahead"}`}>{formatGap(gapMs)}</span>
            )}
          </span>
          <span className="text-2xs text-tone-500">
            {session?.type} · {session === undefined ? "" : dateLabel(session.date)} · Lap {lap.lapNumber}
          </span>
        </span>
        <span className="text-tone-500">⌄</span>
      </button>
      {onRemove !== undefined && (
        <button
          type="button"
          onClick={onRemove}
          title="Remove this lap"
          aria-label={`Remove lap ${LAP_SLOT_LETTERS[slot]}`}
          className="mr-1.5 rounded-md px-1.5 text-tone-500 hover:bg-tone-700 hover:text-tone-100"
        >
          ×
        </button>
      )}
    </div>
  );
}

// One chip per lap (A, then comparison laps) and a Compare button until
// there are MAX_COMPARISON_LAPS comparison laps.
export function LapChips({ onChoose }: LapChipsProps) {
  const laps = useTelemetryStore((s) => s.laps);
  const removeLap = useTelemetryStore((s) => s.removeLap);
  const times = useLapTimes(laps);

  if (!isCompleteLap(laps[0])) {
    return (
      <button
        type="button"
        onClick={() => onChoose(0)}
        className="rounded-xl border border-dashed border-tone-600 px-3 py-2 text-xs text-tone-300 hover:bg-tone-800"
      >
        Choose a lap
      </button>
    );
  }

  const known = times.filter((t): t is number => t !== null);
  const fastest = known.length > 1 ? Math.min(...known) : null;
  const timeA = times[0];

  return (
    <div className="flex flex-wrap items-center gap-2">
      {laps.map((lap, slot) =>
        isCompleteLap(lap) ? (
          <Chip
            key={slot}
            slot={slot}
            lap={lap}
            timeMs={times[slot]}
            gapMs={slot === 0 || times[slot] === null || timeA === null ? null : times[slot]! - timeA}
            fastest={fastest !== null && times[slot] === fastest}
            onChoose={() => onChoose(slot)}
            onRemove={slot === 0 ? undefined : () => removeLap(slot)}
          />
        ) : null
      )}
      {laps.length < 1 + MAX_COMPARISON_LAPS && (
        <button
          type="button"
          onClick={() => onChoose(laps.length)}
          className="rounded-lg border border-dashed border-tone-700 px-3 py-3 text-xs text-tone-300 hover:bg-tone-800"
        >
          + Compare with a lap
        </button>
      )}
    </div>
  );
}
