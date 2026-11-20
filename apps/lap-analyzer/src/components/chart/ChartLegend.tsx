import { useDrivers } from "../../hooks/useDrivers";
import { useSessions } from "../../hooks/useSessions";
import { LAP_SLOT_COLORS, LAP_SLOT_LETTERS } from "../../lib/chartConstants";
import { useTelemetryStore } from "../../store/telemetryStore";
import { isCompleteLap, type LapRef } from "../../types/store";

function sessionLabel(session: { trackName: string; type: string; gameYear: number } | undefined): string {
  return session === undefined ? "" : `${session.trackName} ${session.type} ${session.gameYear}`;
}

function LegendEntry({ slot, lap }: { slot: number; lap: LapRef }) {
  const { data: sessions } = useSessions();
  const { data: drivers } = useDrivers(lap.sessionId);
  const session = sessions?.find((s) => s.id === lap.sessionId);
  const driver = drivers?.find((d) => d.index === lap.driverIndex);
  if (driver === undefined) {
    return null;
  }
  return (
    <span className="flex items-center gap-2 text-xs text-slate-100">
      <span className="font-semibold" style={{ color: LAP_SLOT_COLORS[slot] }}>
        {LAP_SLOT_LETTERS[slot]}
      </span>
      {`${driver.name}  Lap ${lap.lapNumber}  •  ${sessionLabel(session)}`}
    </span>
  );
}

// One entry per lap, coloured by slot. Interim: the lap chips in the header
// replace this, and traces are chosen from the Sensors menu, not toggled here.
export function ChartLegend() {
  const laps = useTelemetryStore((state) => state.laps);
  if (!isCompleteLap(laps[0])) {
    return null;
  }
  return (
    <div className="flex flex-wrap items-center gap-4 border-b border-slate-800 bg-slate-900 px-4 py-2">
      {laps.map((lap, slot) => (isCompleteLap(lap) ? <LegendEntry key={slot} slot={slot} lap={lap} /> : null))}
    </div>
  );
}
