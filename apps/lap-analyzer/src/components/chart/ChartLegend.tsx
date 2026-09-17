import { useDrivers } from "../../hooks/useDrivers";
import { useSessions } from "../../hooks/useSessions";
import { COMPARISON_TRACE_COLOR, PRIMARY_TRACE_COLOR } from "../../lib/chartConstants";
import { useTelemetryStore } from "../../store/telemetryStore";

export interface ChartTraceVisibility {
  primary: boolean;
  reference: boolean;
}

interface ChartLegendProps {
  visibility: ChartTraceVisibility;
  onToggle: (trace: "primary" | "reference") => void;
}

function sessionLabel(session: { trackName: string; type: string; gameYear: number } | undefined): string {
  return session === undefined ? "" : `${session.trackName} ${session.type} ${session.gameYear}`;
}

interface LegendEntryProps {
  dashed: boolean;
  color: string;
  label: string;
  active: boolean;
  onClick: () => void;
}

function LegendEntry({ dashed, color, label, active, onClick }: LegendEntryProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex items-center gap-2 text-xs ${active ? "text-slate-100" : "text-slate-500 line-through"}`}
    >
      <svg width="20" height="4" aria-hidden="true">
        <line x1="0" y1="2" x2="20" y2="2" stroke={color} strokeWidth={2} strokeDasharray={dashed ? "4 3" : undefined} />
      </svg>
      {label}
    </button>
  );
}

// One entry per active trace -- primary always, reference when set. Visibility
// is owned by whichever component renders this (ChartArea, from commit 4),
// not the store -- toggling a trace's visibility is view-local UI state, not
// selection state that needs to survive a remount.
export function ChartLegend({ visibility, onToggle }: ChartLegendProps) {
  const primary = useTelemetryStore((state) => state.primary);
  const reference = useTelemetryStore((state) => state.reference);

  const { data: sessions } = useSessions();
  const { data: primaryDrivers } = useDrivers(primary.sessionId);
  const { data: referenceDrivers } = useDrivers(reference?.sessionId ?? null);

  const primarySession = sessions?.find((s) => s.id === primary.sessionId);
  const primaryDriver = primaryDrivers?.find((d) => d.index === primary.driverIndex);

  const referenceSession = sessions?.find((s) => s.id === reference?.sessionId);
  const referenceDriver = referenceDrivers?.find((d) => d.index === reference?.driverIndex);

  const primaryReady = primary.lapNumber !== null && primaryDriver !== undefined;
  const referenceReady =
    reference !== null && reference.lapNumber !== null && referenceDriver !== undefined;

  if (!primaryReady) {
    return null;
  }

  return (
    <div className="flex flex-wrap items-center gap-4 border-b border-slate-800 bg-slate-900 px-4 py-2">
      <LegendEntry
        dashed={false}
        color={PRIMARY_TRACE_COLOR}
        label={`${primaryDriver.name}  Lap ${primary.lapNumber}  •  ${sessionLabel(primarySession)}`}
        active={visibility.primary}
        onClick={() => onToggle("primary")}
      />
      {referenceReady && (
        <LegendEntry
          dashed
          color={COMPARISON_TRACE_COLOR}
          label={`${referenceDriver.name}  Lap ${reference.lapNumber}  •  ${sessionLabel(referenceSession)}`}
          active={visibility.reference}
          onClick={() => onToggle("reference")}
        />
      )}
    </div>
  );
}
