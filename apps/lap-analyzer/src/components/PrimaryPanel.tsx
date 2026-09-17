import { SelectionPanel } from "./SelectionPanel";

export function PrimaryPanel() {
  return (
    <section>
      <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">Primary</h2>
      <SelectionPanel variant="primary" />
    </section>
  );
}
