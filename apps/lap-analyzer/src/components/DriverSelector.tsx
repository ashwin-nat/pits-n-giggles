import { useDrivers } from "../hooks/useDrivers";
import { getTeamColor } from "../lib/teamColors";
import { DisabledSelect, LoadingSkeleton, ErrorMessage } from "./selectorStates";
import type { Driver } from "../types/api";
import type { SelectionState } from "../types/store";

interface DriverSelectorProps {
  selection: SelectionState;
  onChange: (patch: Partial<SelectionState>) => void;
  disabled: boolean;
}

function driverLabel(driver: Driver): string {
  const prefix = driver.telemetrySettings === "Restricted" ? "🔒" : "🔓";
  // No [AI] tag: is_ai was removed from the data entirely (unreliable at the
  // sim level -- m_aiControlled flips true on pause/disconnect, m_driverId
  // can't be checked against a max in single-player/co-op). Revisit if a
  // more reliable AI-detection signal ever surfaces.
  const parts = [`#${driver.carNumber}`, driver.name];
  return `${prefix} ${parts.join(" ")}`;
}

// Selecting a driver invalidates the previously selected lap -- a lap number
// selected for one driver has no meaning for another.
export function DriverSelector({ selection, onChange, disabled }: DriverSelectorProps) {
  const { data: drivers, isLoading, error } = useDrivers(selection.sessionId);

  if (disabled) {
    return <DisabledSelect message="Select a session first" />;
  }
  if (isLoading) {
    return <LoadingSkeleton />;
  }
  if (error) {
    return <ErrorMessage what="drivers" error={error} />;
  }

  return (
    <select
      value={selection.driverIndex ?? ""}
      onChange={(e) => {
        const driverIndex = e.target.value === "" ? null : Number(e.target.value);
        onChange({ driverIndex, lapNumber: null });
      }}
      className="rounded border border-slate-700 bg-slate-800 px-2 py-1 text-sm text-slate-100"
    >
      <option value="" disabled>
        Select a driver...
      </option>
      {/* TODO: the spec's mockup implies a richer list item (colored team dot + name +
          tags as separate styled elements). A native <option> can't render that --
          this tints the whole row's text via `color` as a stand-in. Revisit with a
          custom (non-native) listbox if the team-color signal needs to be clearer. */}
      {(drivers ?? []).map((driver) => (
        <option key={driver.index} value={driver.index} style={{ color: getTeamColor(driver.team) }}>
          {driverLabel(driver)}
        </option>
      ))}
    </select>
  );
}
