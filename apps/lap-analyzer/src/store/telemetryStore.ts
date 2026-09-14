import { create } from "zustand";
import type { ActiveSection, SelectionState, Viewport } from "../types/store";

const emptySelection: SelectionState = {
  sessionId: null,
  driverIndex: null,
  lapNumber: null,
  sensors: [],
};

export interface TelemetryStore {
  // Primary selection
  primary: SelectionState;
  setPrimary: (patch: Partial<SelectionState>) => void;

  // Reference selection (null = no comparison active)
  reference: SelectionState | null;
  setReference: (patch: Partial<SelectionState> | null) => void;

  // Chart viewport -- shared across all chart lanes. null = full lap visible.
  viewport: Viewport | null;
  setViewport: (viewport: Viewport) => void;

  // Active track section -- drives both pill highlight and focus zone overlay.
  // null = full lap / no active section.
  activeSection: ActiveSection | null;
  setActiveSection: (section: ActiveSection | null) => void;

  // Whether to show the delta lane
  showDelta: boolean;
  toggleDelta: () => void;

  // Incidents panel
  incidentsPanelOpen: boolean;
  toggleIncidentsPanel: () => void;
}

export const useTelemetryStore = create<TelemetryStore>((set) => ({
  primary: emptySelection,
  setPrimary: (patch) =>
    set((state) => {
      // Changing sessionId invalidates any stale driverIndex/lapNumber/sensors
      // left over from the previous session's manifest -- but values passed
      // in this same patch (e.g. selecting session + driver together) must
      // still take effect, so reset to empty first and apply the patch on
      // top of that, rather than on top of the old state.
      if ("sessionId" in patch && patch.sessionId !== state.primary.sessionId) {
        return { primary: { ...emptySelection, ...patch } };
      }
      return { primary: { ...state.primary, ...patch } };
    }),

  reference: null,
  setReference: (patch) =>
    set((state) => {
      if (patch === null) {
        return { reference: null };
      }
      const base = state.reference ?? emptySelection;
      if ("sessionId" in patch && patch.sessionId !== base.sessionId) {
        return { reference: { ...emptySelection, ...patch } };
      }
      return { reference: { ...base, ...patch } };
    }),

  viewport: null,
  setViewport: (viewport) => set({ viewport }),

  activeSection: null,
  setActiveSection: (section) => set({ activeSection: section }),

  showDelta: false,
  toggleDelta: () => set((state) => ({ showDelta: !state.showDelta })),

  incidentsPanelOpen: false,
  toggleIncidentsPanel: () => set((state) => ({ incidentsPanelOpen: !state.incidentsPanelOpen })),
}));
