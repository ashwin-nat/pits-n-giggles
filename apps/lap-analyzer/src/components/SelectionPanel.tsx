import { useTelemetryStore } from "../store/telemetryStore";
import { SessionSelector } from "./SessionSelector";
import { SessionInfo } from "./SessionInfo";
import { DriverSelector } from "./DriverSelector";
import { LapSelector } from "./LapSelector";

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
  const setPrimary = useTelemetryStore((state) => state.setPrimary);
  const setReference = useTelemetryStore((state) => state.setReference);
  const setSelection = variant === "primary" ? setPrimary : setReference;

  if (selection === null) {
    // Only reachable if ReferencePanel renders this before reference is set.
    return null;
  }

  const sessionSelected = selection.sessionId !== null;
  const driverSelected = selection.driverIndex !== null;
  const lapSelected = selection.lapNumber !== null;

  return (
    <div className="flex flex-col gap-3">
      <SessionSelector selection={selection} onChange={setSelection} />
      {selection.sessionId !== null && <SessionInfo sessionId={selection.sessionId} />}
      <DriverSelector selection={selection} onChange={setSelection} disabled={!sessionSelected} />
      <LapSelector selection={selection} onChange={setSelection} disabled={!driverSelected} />
      {variant === "primary" && <SelectorPlaceholder name="SensorSelector" disabled={!lapSelected} />}
    </div>
  );
}
