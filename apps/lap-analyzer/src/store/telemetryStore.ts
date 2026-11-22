import { create } from "zustand";
import { MAX_COMPARISON_LAPS } from "../lib/chartConstants";
import type { ActiveSection, LapRef, LapSelection, Viewport } from "../types/store";

const emptyLap: LapSelection = { sessionId: null, driverIndex: null, lapNumber: null };

// Slots hold at most the reference lap plus MAX_COMPARISON_LAPS comparison laps.
const MAX_LAPS = 1 + MAX_COMPARISON_LAPS;

// A new session invalidates the driver and lap left over from the old one,
// but values in the same patch still apply.
function patchLap(current: LapSelection, patch: Partial<LapSelection>): LapSelection {
  const base = "sessionId" in patch && patch.sessionId !== current.sessionId ? emptyLap : current;
  return { ...base, ...patch };
}

function derive(laps: LapSelection[], sensors: string[]) {
  return { laps, sensors };
}

export interface TelemetryStore {
  // laps[0] is the reference lap (A); laps[1..3] are comparison laps (B to D).
  laps: LapSelection[];
  // Sensor keys drawn for every lap.
  sensors: string[];
  setSensors: (sensors: string[]) => void;
  // Patches slot `slot`; a slot one past the end appends (up to the cap).
  // Changing A's session drops the comparison laps, the sensors and the
  // viewport: all three are tied to the old session's circuit and manifest.
  setLap: (slot: number, patch: Partial<LapSelection>) => void;
  // Removing A promotes nothing: it clears the whole selection.
  removeLap: (slot: number) => void;
  // The Choose lap modal's result. A lap already held in another slot swaps
  // with `slot` (nothing happens if `slot` is a new one); otherwise it is set.
  pickLap: (slot: number, ref: LapRef) => void;
  // Moves a lap held in another slot to `toSlot`, swapping the two.
  moveLap: (fromSlot: number, toSlot: number) => void;

  // Game filter for the track and session lists, e.g. "F1 2025"; null = follow A's session.
  game: string | null;
  setGame: (game: string | null) => void;

  // Chart viewport -- shared across all chart lanes. null = full lap visible.
  viewport: Viewport | null;
  setViewport: (viewport: Viewport | null) => void;

  // Active track section -- drives both pill highlight and focus zone overlay.
  // null = full lap / no active section.
  activeSection: ActiveSection | null;
  setActiveSection: (section: ActiveSection | null) => void;

  // Section under the pointer on the strip or the section table. Read by the
  // charts and the map; null when nothing is hovered.
  hoverSection: ActiveSection | null;
  setHoverSection: (section: ActiveSection | null) => void;

  // Track map side panel: open, or collapsed to a slim button.
  mapOpen: boolean;
  toggleMap: () => void;

  // Track markers (zones, speed trap, overtake, brake boards) on the map.
  showMarkers: boolean;
  toggleMarkers: () => void;

  // Whether to show the delta lane
  showDelta: boolean;
  toggleDelta: () => void;

  // Incidents panel
  incidentsPanelOpen: boolean;
  toggleIncidentsPanel: () => void;

  // Clears the lap selection, game filter plus viewport/activeSection -- for when the
  // underlying provider itself changes (a new file loaded), where every
  // distance/index in the old state may no longer mean anything against the
  // new data. Leaves showDelta/incidentsPanelOpen alone -- those are user
  // display preferences, not data tied to the loaded session.
  reset: () => void;
}

export const useTelemetryStore = create<TelemetryStore>((set, get) => ({
  ...derive([], []),

  setSensors: (sensors) => set((state) => derive(state.laps, sensors)),

  setLap: (slot, patch) =>
    set((state) => {
      if (slot < 0 || slot > state.laps.length || slot >= MAX_LAPS) {
        return state;
      }
      const current = state.laps[slot] ?? emptyLap;
      if (slot === 0 && "sessionId" in patch && patch.sessionId !== current.sessionId) {
        return {
          ...derive([{ ...emptyLap, ...patch }], []),
          viewport: null,
          activeSection: null,
          hoverSection: null,
        };
      }
      const laps = [...state.laps];
      laps[slot] = patchLap(current, patch);
      return derive(laps, state.sensors);
    }),

  removeLap: (slot) =>
    set((state) => {
      if (slot < 0 || slot >= state.laps.length) {
        return state;
      }
      if (slot === 0) {
        return { ...derive([], []), viewport: null, activeSection: null, hoverSection: null };
      }
      return derive(
        state.laps.filter((_, i) => i !== slot),
        state.sensors
      );
    }),

  pickLap: (slot, ref) => {
    const { laps, moveLap, setLap } = get();
    const held = laps.findIndex(
      (l) => l.sessionId === ref.sessionId && l.driverIndex === ref.driverIndex && l.lapNumber === ref.lapNumber
    );
    if (held === slot) {
      return;
    }
    if (held !== -1) {
      if (slot < laps.length) {
        moveLap(held, slot);
      }
      return;
    }
    setLap(slot, ref);
  },

  moveLap: (fromSlot, toSlot) =>
    set((state) => {
      const { laps } = state;
      if (fromSlot === toSlot || fromSlot < 0 || toSlot < 0 || fromSlot >= laps.length || toSlot >= laps.length) {
        return state;
      }
      const next = [...laps];
      [next[fromSlot], next[toSlot]] = [next[toSlot], next[fromSlot]];
      return derive(next, state.sensors);
    }),

  game: null,
  setGame: (game) => set({ game }),

  viewport: null,
  setViewport: (viewport) => set({ viewport }),

  activeSection: null,
  setActiveSection: (section) => set({ activeSection: section }),

  hoverSection: null,
  setHoverSection: (section) => set({ hoverSection: section }),

  mapOpen: true,
  toggleMap: () => set((state) => ({ mapOpen: !state.mapOpen })),

  showMarkers: true,
  toggleMarkers: () => set((state) => ({ showMarkers: !state.showMarkers })),

  showDelta: false,
  toggleDelta: () => set((state) => ({ showDelta: !state.showDelta })),

  incidentsPanelOpen: false,
  toggleIncidentsPanel: () => set((state) => ({ incidentsPanelOpen: !state.incidentsPanelOpen })),

  reset: () => set({ ...derive([], []), game: null, viewport: null, activeSection: null, hoverSection: null }),
}));
