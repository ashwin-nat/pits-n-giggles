import { useMemo } from "react";
import { useDrivers } from "../hooks/useDrivers";
import { useLaps } from "../hooks/useLaps";
import { useSessions } from "../hooks/useSessions";
import type { Lap } from "../types/api";
import type { SelectionState } from "../types/store";

interface LapSelectorProps {
  selection: SelectionState;
  onChange: (patch: Partial<SelectionState>) => void;
  disabled: boolean;
}

// Colored-circle emoji stand-in for the "tyre dot" -- a native <option> can't
// render an <img>, so this can't use the real tyre SVGs at
// assets/tyre-icons/ (soft/medium/hard/intermediate/wet/super_soft/default)
// until LapSelector moves off a native <select> to a custom listbox (see the
// same tradeoff noted in DriverSelector for the team-color dot).
const TYRE_EMOJI: Record<string, string> = {
  Soft: "🔴",
  Medium: "🟡",
  Hard: "⚪",
  Inter: "🟢",
  Wet: "🔵",
};
const DEFAULT_TYRE_EMOJI = "⚫";

const SESSION_BEST_COLOR = "#a855f7";
const PERSONAL_BEST_COLOR = "#22c55e";

function formatLapTime(ms: number | null): string {
  if (ms === null) {
    return "--:--.---";
  }
  const minutes = Math.floor(ms / 60000);
  const secondsMs = ms % 60000;
  const seconds = Math.floor(secondsMs / 1000);
  const millis = secondsMs % 1000;
  return `${minutes}:${String(seconds).padStart(2, "0")}.${String(millis).padStart(3, "0")}`;
}

function lapLabel(lap: Lap, isSessionBest: boolean): string {
  const parts = [
    `${isSessionBest ? "⚡ " : ""}Lap ${lap.lapNumber}`,
    formatLapTime(lap.lapTime),
    `${TYRE_EMOJI[lap.tyreCompound] ?? DEFAULT_TYRE_EMOJI} ${lap.tyreCompound}`,
  ];
  if (!lap.valid) {
    parts.push("⚠");
  }
  if (lap.pitInLap || lap.pitOutLap) {
    parts.push("🔧");
  }
  return parts.join("  •  ");
}

// Good-laps filter, mark-as-good, and delete are deferred to Phase 6 --
// they need a mutating provider (RemoteApiProvider) to mean anything, and
// LocalFileProvider.capabilities.mutations is always false.
export function LapSelector({ selection, onChange, disabled }: LapSelectorProps) {
  const { data: sessions } = useSessions();
  const { data: drivers } = useDrivers(selection.sessionId);
  const session = sessions?.find((s) => s.id === selection.sessionId);
  const selectedDriver = drivers?.find((d) => d.index === selection.driverIndex);
  const restricted = selectedDriver?.telemetrySettings === "Restricted";

  const { data: laps, isLoading, error } = useLaps(
    restricted ? null : selection.sessionId,
    restricted ? null : selection.driverIndex
  );

  const personalBestMs = useMemo(() => {
    const validTimes = (laps ?? [])
      .filter((l) => l.valid && l.lapTime !== null)
      .map((l) => l.lapTime as number);
    return validTimes.length > 0 ? Math.min(...validTimes) : null;
  }, [laps]);

  const sessionBest = session?.sessionBest ?? null;

  if (disabled) {
    return (
      <select disabled className="rounded border border-slate-800 bg-slate-900 px-2 py-1 text-sm text-slate-600">
        <option>Select a driver first</option>
      </select>
    );
  }

  if (restricted) {
    return (
      <div className="rounded border border-dashed border-slate-700 p-2 text-xs text-slate-500">
        🔒 Telemetry restricted by driver
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      {isLoading ? (
        <div className="h-8 animate-pulse rounded bg-slate-800" />
      ) : error ? (
        <p className="text-xs text-red-400">
          Failed to load laps: {error instanceof Error ? error.message : String(error)}
        </p>
      ) : (
        <select
          value={selection.lapNumber ?? ""}
          onChange={(e) => onChange({ lapNumber: e.target.value === "" ? null : Number(e.target.value) })}
          className="rounded border border-slate-700 bg-slate-800 px-2 py-1 text-sm text-slate-100"
        >
          <option value="" disabled>
            Select a lap...
          </option>
          {(laps ?? []).map((lap) => {
            const isSessionBest =
              sessionBest !== null &&
              lap.lapTime === sessionBest.lapTimeMs &&
              selection.driverIndex === sessionBest.driverIndex;
            const isPersonalBest = !isSessionBest && lap.lapTime !== null && lap.lapTime === personalBestMs;
            const color = isSessionBest ? SESSION_BEST_COLOR : isPersonalBest ? PERSONAL_BEST_COLOR : undefined;
            return (
              <option key={lap.lapNumber} value={lap.lapNumber} style={{ color }}>
                {lapLabel(lap, isSessionBest)}
              </option>
            );
          })}
        </select>
      )}
    </div>
  );
}
