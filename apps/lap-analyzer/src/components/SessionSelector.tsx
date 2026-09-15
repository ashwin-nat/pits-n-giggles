import { useMemo, useState } from "react";
import { useSessions } from "../hooks/useSessions";
import type { Session } from "../types/api";
import type { SelectionState } from "../types/store";

interface SessionSelectorProps {
  selection: SelectionState;
  onChange: (patch: Partial<SelectionState>) => void;
}

const ALL_TRACKS = "__all_tracks__";
const ALL_FORMULAS = "__all_formulas__";

function formatDate(iso: string): string {
  const date = new Date(iso);
  if (iso === "" || Number.isNaN(date.getTime())) {
    return "";
  }
  return date.toLocaleDateString(undefined, { day: "2-digit", month: "short", year: "numeric" });
}

function formulaLabel(session: Session): string {
  return `${session.formula} ${session.gameYear}`.trim();
}

export function SessionSelector({ selection, onChange }: SessionSelectorProps) {
  const { data: sessions, isLoading, error } = useSessions();
  const [trackFilter, setTrackFilter] = useState(ALL_TRACKS);
  const [formulaFilter, setFormulaFilter] = useState(ALL_FORMULAS);

  const tracks = useMemo(() => Array.from(new Set((sessions ?? []).map((s) => s.trackName))).sort(), [sessions]);
  const formulas = useMemo(() => Array.from(new Set((sessions ?? []).map(formulaLabel))).sort(), [sessions]);

  const filtered = useMemo(
    () =>
      (sessions ?? []).filter((s) => {
        const trackOk = trackFilter === ALL_TRACKS || s.trackName === trackFilter;
        const formulaOk = formulaFilter === ALL_FORMULAS || formulaLabel(s) === formulaFilter;
        return trackOk && formulaOk;
      }),
    [sessions, trackFilter, formulaFilter]
  );

  if (isLoading) {
    return <div className="h-16 animate-pulse rounded bg-slate-800" />;
  }
  if (error) {
    return (
      <p className="text-xs text-red-400">
        Failed to load sessions: {error instanceof Error ? error.message : String(error)}
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex gap-2">
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
      </div>
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
            {s.trackName} {s.type} • {formatDate(s.date)} • v{s.appVersion}
          </option>
        ))}
      </select>
    </div>
  );
}
