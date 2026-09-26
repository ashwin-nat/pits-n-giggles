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
const ALL_FORMULAS = "__all_formulas__";

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

export function SessionSelector({ selection, onChange, restrictToSessionId }: SessionSelectorProps) {
  const { data: sessions, isLoading, error } = useSessions();
  const [trackFilter, setTrackFilter] = useState(ALL_TRACKS);
  const [formulaFilter, setFormulaFilter] = useState(ALL_FORMULAS);

  const restricted = restrictToSessionId !== undefined;
  const restrictToSession = restricted ? sessions?.find((s) => s.id === restrictToSessionId) : undefined;

  const tracks = useMemo(() => Array.from(new Set((sessions ?? []).map((s) => s.trackName))).sort(), [sessions]);
  const formulas = useMemo(() => Array.from(new Set((sessions ?? []).map(formulaLabel))).sort(), [sessions]);

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
    return (sessions ?? []).filter((s) => {
      const trackOk = trackFilter === ALL_TRACKS || s.trackName === trackFilter;
      const formulaOk = formulaFilter === ALL_FORMULAS || formulaLabel(s) === formulaFilter;
      return trackOk && formulaOk;
    });
  }, [sessions, trackFilter, formulaFilter, restricted, restrictToSession]);

  if (isLoading) {
    return <LoadingSkeleton className="h-16" />;
  }
  if (error) {
    return <ErrorMessage what="sessions" error={error} />;
  }

  return (
    <div className="flex flex-col gap-2">
      {!restricted && (
        <div className="flex gap-2">
          <select
            value={formulaFilter}
            onChange={(e) => setFormulaFilter(e.target.value)}
            className="flex-1 rounded border border-slate-700 bg-slate-800 px-2 py-1 text-xs text-slate-200"
          >
            <option value={ALL_FORMULAS}>All Formulas</option>
            {formulas.map((f) => (
              <option key={f} value={f}>
                {f}
              </option>
            ))}
          </select>
          <select
            value={trackFilter}
            onChange={(e) => setTrackFilter(e.target.value)}
            className="flex-1 rounded border border-slate-700 bg-slate-800 px-2 py-1 text-xs text-slate-200"
          >
            <option value={ALL_TRACKS}>All Tracks</option>
            {tracks.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>
      )}
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
    </div>
  );
}
