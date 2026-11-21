import { useState, type ChangeEvent } from "react";
import { useSessions } from "../../hooks/useSessions";
import { useTelemetryStore } from "../../store/telemetryStore";
import { LapPickerModal } from "../picker/LapPickerModal";
import { TrackPickerModal } from "../picker/TrackPickerModal";
import { GameMenu } from "./GameMenu";
import { LapChips } from "./LapChips";
import { SensorsPopover, useDefaultSensors } from "./SensorsPopover";

interface HeaderProps {
  // Standalone mode only: a handler for the .pngt file input. Absent in backend mode.
  onFileChange?: (event: ChangeEvent<HTMLInputElement>) => void;
}

type Modal = { kind: "track" } | { kind: "lap"; slot: number; trackId?: number } | null;

// Brand, game menu, track button, lap chips, Sensors and Map. Everything the
// old sidebar held lives here or in its modals.
export function Header({ onFileChange }: HeaderProps) {
  const [modal, setModal] = useState<Modal>(null);
  const { data: sessions } = useSessions();
  const referenceSessionId = useTelemetryStore((s) => s.laps[0]?.sessionId ?? null);
  const mapOpen = useTelemetryStore((s) => s.mapOpen);
  const toggleMap = useTelemetryStore((s) => s.toggleMap);
  const showMarkers = useTelemetryStore((s) => s.showMarkers);
  const toggleMarkers = useTelemetryStore((s) => s.toggleMarkers);
  useDefaultSensors();

  const trackName = sessions?.find((s) => s.id === referenceSessionId)?.trackName;

  return (
    <>
      <header className="flex flex-wrap items-center gap-3 border-b border-tone-800/70 bg-canvas px-4 py-2.5">
        <p className="text-sm font-semibold text-tone-50">Lap Analyzer</p>
        <GameMenu />
        <button
          type="button"
          onClick={() => setModal({ kind: "track" })}
          disabled={sessions === undefined || sessions.length === 0}
          className="rounded-lg bg-tone-800 px-3 py-1.5 text-xs text-tone-100 hover:bg-tone-700 disabled:opacity-40"
        >
          {trackName ?? "Choose a track"} <span className="text-tone-500">▾</span>
        </button>
        <span className="h-6 w-px bg-tone-800" />
        <LapChips onChoose={(slot) => setModal({ kind: "lap", slot })} />
        <div className="ml-auto flex items-center gap-2">
          {onFileChange !== undefined && (
            <input
              type="file"
              accept=".pngt"
              onChange={onFileChange}
              className="cursor-pointer text-xs text-tone-400 file:mr-3 file:cursor-pointer file:rounded-lg file:border-0 file:bg-tone-800 file:px-3 file:py-1.5 file:text-xs file:font-medium file:text-tone-100 file:hover:bg-tone-700"
            />
          )}
          <SensorsPopover />
          <button
            type="button"
            onClick={toggleMap}
            aria-pressed={mapOpen}
            className="rounded-lg bg-tone-800 px-3 py-1.5 text-xs text-tone-100 hover:bg-tone-700 aria-pressed:bg-tone-700"
          >
            Map
          </button>
          <button
            type="button"
            onClick={toggleMarkers}
            aria-pressed={showMarkers}
            title="Zones, speed trap, overtake and brake boards on the map"
            className="rounded-lg bg-tone-800 px-3 py-1.5 text-xs text-tone-100 hover:bg-tone-700 aria-pressed:bg-tone-700"
          >
            Markers
          </button>
        </div>
      </header>
      {modal?.kind === "track" && (
        <TrackPickerModal
          onClose={() => setModal(null)}
          onPick={(trackId) => setModal({ kind: "lap", slot: 0, trackId })}
        />
      )}
      {modal?.kind === "lap" && (
        <LapPickerModal slot={modal.slot} trackId={modal.trackId} onClose={() => setModal(null)} />
      )}
    </>
  );
}
