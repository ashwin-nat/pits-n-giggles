import { useTelemetryStore } from "../store/telemetryStore";
import { SelectionPanel } from "./SelectionPanel";

// Renders AddReferenceButton when no reference is active, otherwise the
// reference SelectionPanel with a RemoveReferenceButton in its header.
export function ReferencePanel() {
  const primarySessionId = useTelemetryStore((state) => state.primary.sessionId);
  const reference = useTelemetryStore((state) => state.reference);
  const setReference = useTelemetryStore((state) => state.setReference);

  if (reference === null) {
    // A reference lap must share primary's circuit+formula (see
    // SessionSelector's restrictToSessionId) -- nothing to restrict to until
    // primary has a session.
    return (
      <section>
        <button
          type="button"
          disabled={primarySessionId === null}
          onClick={() => setReference({})}
          className="w-full rounded border border-dashed border-slate-700 p-2 text-xs text-slate-400 hover:border-slate-500 hover:text-slate-200 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:border-slate-700 disabled:hover:text-slate-400"
        >
          + Add Reference
        </button>
      </section>
    );
  }

  return (
    <section>
      <div className="mb-2 flex items-center justify-between">
        <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-400">Reference</h2>
        <button type="button" onClick={() => setReference(null)} className="text-xs text-slate-500 hover:text-red-400">
          Remove
        </button>
      </div>
      <SelectionPanel variant="reference" />
    </section>
  );
}
