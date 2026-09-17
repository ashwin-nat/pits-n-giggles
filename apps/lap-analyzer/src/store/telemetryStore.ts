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
  setViewport: (viewport: Viewport | null) => void;

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

  // Clears primary/reference selection plus viewport/activeSection -- for
  // when the underlying provider itself changes (a new file loaded), where
  // every distance/index in the old state may no longer mean anything
  // against the new data. Leaves showDelta/incidentsPanelOpen alone -- those
  // are user display preferences, not data tied to the loaded session.
  reset: () => void;
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
        // A reference lap must share primary's circuit+formula (see
        // SessionSelector's restrictToSessionId) -- an active reference's
        // session may no longer qualify once primary's session changes, so
        // drop it rather than leave it pointing at a now-invalid session.
        // The user re-adds a reference under the new circuit+formula.
        // viewport/activeSection are distance-in-metres state scoped to the
        // *old* circuit -- a shorter new track can leave both pointing past
        // the end of the real data (empty chart, focus zone off-screen).
        return { primary: { ...emptySelection, ...patch }, reference: null, viewport: null, activeSection: null };
      }
      // A reference lap must share primary's circuit+formula (see
      // SessionSelector's restrictToSessionId) -- an active reference's
      // session may no longer qualify once primary's session changes, so
      // drop it rather than leave it pointing at a now-invalid session.
      // The user re-adds a reference under the new circuit+formula.
      return { primary: applySelectionPatch(state.primary, patch), reference: null };
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

  reset: () => set({ primary: emptySelection, reference: null, viewport: null, activeSection: null }),
}));
