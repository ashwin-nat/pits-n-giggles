import { useTelemetryStore } from "../store/telemetryStore";

interface SelectionPanelProps {
  variant: "primary" | "reference";
}

// Placeholder stand-in for a selector not yet built. Each one is replaced by
// its real component in a later Phase 4 commit -- this establishes the
// cascading enabled/disabled flow ahead of the components that fill it in.
function SelectorPlaceholder({ name, disabled }: { name: string; disabled: boolean }) {
  return (
    <div
      className={`rounded border border-dashed border-slate-700 p-2 text-xs text-slate-500 ${disabled ? "opacity-40" : ""}`}
    >
      {name}
      {disabled && " (disabled)"}
    </div>
  );
}

// Cascading selectors for one lap (primary or reference). See the frontend
// spec's SelectionPanel section for the enabled-when table.
export function SelectionPanel({ variant }: SelectionPanelProps) {
  const selection = useTelemetryStore((state) => (variant === "primary" ? state.primary : state.reference));

  if (selection === null) {
    // Only reachable if ReferencePanel renders this before reference is set.
    return null;
  }

  const sessionSelected = selection.sessionId !== null;
  const driverSelected = selection.driverIndex !== null;
  const lapSelected = selection.lapNumber !== null;

  return (
    <div className="flex flex-col gap-3">
      <SelectorPlaceholder name="SessionSelector" disabled={false} />
      {sessionSelected && <SelectorPlaceholder name="SessionInfo" disabled={false} />}
      <SelectorPlaceholder name="DriverSelector" disabled={!sessionSelected} />
      <SelectorPlaceholder name="LapSelector" disabled={!driverSelected} />
      {variant === "primary" && <SelectorPlaceholder name="SensorSelector" disabled={!lapSelected} />}
    </div>
  );
}
