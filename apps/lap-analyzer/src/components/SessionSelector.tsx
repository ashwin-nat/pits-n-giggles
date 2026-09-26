import { useMemo, useState } from "react";
import { useSessions } from "../hooks/useSessions";
import { LoadingSkeleton, ErrorMessage } from "./selectorStates";
import type { Session } from "../types/api";
import type { SelectionState } from "../types/store";

interface SessionSelectorProps {
  selection: SelectionState;
  onChange: (patch: Partial<SelectionState>) => void;
  // When set (reference variant), the track/formula filters are hidden and
  // the session list is restricted to sessions sharing this session's
  // circuit and formula -- a reference lap must come from the same
  // circuit+formula as primary, so there's no point offering the choice.
  restrictToSessionId?: string | null;
}

const ALL_TRACKS = "__all_tracks__";

function formatDate(iso: string): string {
  const date = new Date(iso);
  if (iso === "" || Number.isNaN(date.getTime())) {
    return "";
  }
  return date.toLocaleString(undefined, {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formulaLabel(session: Session): string {
  return `${session.formula} ${session.gameYear}`.trim();
}

// Distinct from ALL_TRACKS -- "unset" hides the session list, ALL_TRACKS
// is an active choice that reveals it.
const UNSET = "";

export function SessionSelector({ selection, onChange, restrictToSessionId }: SessionSelectorProps) {
  const { data: sessions, isLoading, error } = useSessions();
  const [formulaFilter, setFormulaFilter] = useState(UNSET);
  const [trackFilter, setTrackFilter] = useState(UNSET);

  const restricted = restrictToSessionId !== undefined;
  const restrictToSession = restricted ? sessions?.find((s) => s.id === restrictToSessionId) : undefined;

  const formulas = useMemo(() => Array.from(new Set((sessions ?? []).map(formulaLabel))).sort(), [sessions]);
  // Only tracks that actually have a session under the selected formula --
  // "applicable" tracks, not every track in the full session list.
  const tracks = useMemo(
    () =>
      Array.from(
        new Set((sessions ?? []).filter((s) => formulaLabel(s) === formulaFilter).map((s) => s.trackName))
      ).sort(),
    [sessions, formulaFilter]
  );

  const filtered = useMemo(() => {
    if (restricted) {
      if (restrictToSession === undefined) {
        return [];
      }
      // Formula only, not gameYear -- each formula is a regulation era, not
      // tied to a specific year, and there may be gaps between recorded
      // years for the same circuit+formula. Year is cosmetic here (it still
      // drives the separate, combined "F1 2025"-style filter option below).
      return (sessions ?? []).filter(
        (s) => s.trackId === restrictToSession.trackId && s.formula === restrictToSession.formula
      );
    }
    if (formulaFilter === UNSET || trackFilter === UNSET) {
      return [];
    }
    return (sessions ?? []).filter(
      (s) => formulaLabel(s) === formulaFilter && (trackFilter === ALL_TRACKS || s.trackName === trackFilter)
    );
  }, [sessions, formulaFilter, trackFilter, restricted, restrictToSession]);

  if (isLoading) {
    return <LoadingSkeleton className="h-16" />;
  }
  if (error) {
    return <ErrorMessage what="sessions" error={error} />;
  }

  // Changing a filter invalidates whatever was picked below it.
  function handleFormulaChange(value: string) {
    setFormulaFilter(value);
    setTrackFilter(UNSET);
    onChange({ sessionId: null });
  }

  function handleTrackChange(value: string) {
    setTrackFilter(value);
    onChange({ sessionId: null });
  }

  return (
    <div className="flex flex-col gap-2">
      {!restricted && (
        <div className="flex gap-2">
          <select
            value={formulaFilter}
            onChange={(e) => handleFormulaChange(e.target.value)}
            className="flex-1 rounded border border-slate-700 bg-slate-800 px-2 py-1 text-xs text-slate-200"
          >
            <option value={UNSET} disabled>
              Select formula...
            </option>
            {formulas.map((f) => (
              <option key={f} value={f}>
                {f}
              </option>
            ))}
          </select>
          {formulaFilter !== UNSET && (
            <select
              value={trackFilter}
              onChange={(e) => handleTrackChange(e.target.value)}
              className="flex-1 rounded border border-slate-700 bg-slate-800 px-2 py-1 text-xs text-slate-200"
            >
              <option value={UNSET} disabled>
                Select track...
              </option>
              <option value={ALL_TRACKS}>All Tracks</option>
              {tracks.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          )}
        </div>
      )}
      {(restricted || trackFilter !== UNSET) && (
        <select
          value={selection.sessionId ?? ""}
          onChange={(e) => onChange({ sessionId: e.target.value || null })}
          className="rounded border border-slate-700 bg-slate-800 px-2 py-1 text-sm text-slate-100"
        >
          <option value="" disabled>
            Select a session...
          </option>
          {filtered.map((s) => (
            <option key={s.id} value={s.id}>
              {s.trackName} {s.type} • {formatDate(s.date)}
            </option>
          ))}
        </select>
      )}
    </div>
  );
}
