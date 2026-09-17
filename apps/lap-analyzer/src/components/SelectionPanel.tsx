import { useTelemetryStore } from "../store/telemetryStore";
import { SessionSelector } from "./SessionSelector";
import { SessionInfo } from "./SessionInfo";
import { DriverSelector } from "./DriverSelector";
import { LapSelector } from "./LapSelector";
import { SensorSelector } from "./SensorSelector";

interface SelectionPanelProps {
  variant: "primary" | "reference";
}

// Cascading selectors for one lap (primary or reference). See the frontend
// spec's SelectionPanel section for the enabled-when table.
//
// Deviation from spec: for the reference variant, SessionSelector hides its
// track/formula filters and restricts the session list to primary's
// circuit+formula (see SessionSelector's restrictToSessionId) -- a reference
// lap must share primary's circuit and formula, so there's no point letting
// the user filter to something else. The session itself can still differ
// (e.g. comparing against a Qualifying lap while primary is a Race).
export function SelectionPanel({ variant }: SelectionPanelProps) {
  const selection = useTelemetryStore((state) => (variant === "primary" ? state.primary : state.reference));
  const primarySessionId = useTelemetryStore((state) => state.primary.sessionId);
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
      <SessionSelector
        selection={selection}
        onChange={setSelection}
        restrictToSessionId={variant === "reference" ? primarySessionId : undefined}
      />
      {selection.sessionId !== null && <SessionInfo sessionId={selection.sessionId} />}
      <DriverSelector selection={selection} onChange={setSelection} disabled={!sessionSelected} />
      <LapSelector selection={selection} onChange={setSelection} disabled={!driverSelected} />
      {variant === "primary" && <SensorSelector selection={selection} onChange={setSelection} disabled={!lapSelected} />}
    </div>
  );
}
