import { create } from "zustand";
import type { ActiveSection, SelectionState, Viewport } from "../types/store";

const emptySelection: SelectionState = {
  sessionId: null,
  driverIndex: null,
  lapNumber: null,
  sensors: [],
};

// Changing sessionId invalidates any stale driverIndex/lapNumber/sensors left
// over from the previous session's manifest -- but values passed in the same
// patch (e.g. selecting session + driver together) must still take effect, so
// reset to empty first and apply the patch on top of that, rather than on top
// of the old selection. Shared by setPrimary and setReference so this rule
// can't drift between the two.
function applySelectionPatch(current: SelectionState, patch: Partial<SelectionState>): SelectionState {
  if ("sessionId" in patch && patch.sessionId !== current.sessionId) {
    return { ...emptySelection, ...patch };
  }
  return { ...current, ...patch };
}

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

  // Clears all selection/UI state -- called when a new .pngt file is loaded,
  // since the previous file's sessionId/driverIndex/lapNumber mean nothing
  // in the new one.
  reset: () => void;
}

export const useTelemetryStore = create<TelemetryStore>((set) => ({
  primary: emptySelection,
  setPrimary: (patch) =>
    set((state) => {
      const nextPrimary = applySelectionPatch(state.primary, patch);
      if (nextPrimary.sessionId === state.primary.sessionId) {
        return { primary: nextPrimary };
      }
      // A reference lap must share primary's circuit+formula (see
      // SessionSelector's restrictToSessionId) -- an active reference's
      // session may no longer qualify once primary's session changes, so
      // drop it rather than leave it pointing at a now-invalid session.
      // The user re-adds a reference under the new circuit+formula.
      return { primary: nextPrimary, reference: null };
    }),

  reference: null,
  setReference: (patch) =>
    set((state) => {
      if (patch === null) {
        return { reference: null };
      }
      return { reference: applySelectionPatch(state.reference ?? emptySelection, patch) };
    }),

  viewport: null,
  setViewport: (viewport) => set({ viewport }),

  activeSection: null,
  setActiveSection: (section) => set({ activeSection: section }),

  showDelta: false,
  toggleDelta: () => set((state) => ({ showDelta: !state.showDelta })),

  incidentsPanelOpen: false,
  toggleIncidentsPanel: () => set((state) => ({ incidentsPanelOpen: !state.incidentsPanelOpen })),

  reset: () =>
    set({
      primary: emptySelection,
      reference: null,
      viewport: null,
      activeSection: null,
      showDelta: false,
      incidentsPanelOpen: false,
    }),
}));
