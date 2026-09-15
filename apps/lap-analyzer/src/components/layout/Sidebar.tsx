import { PrimaryPanel } from "../PrimaryPanel";

// ReferencePanel joins PrimaryPanel here once it exists (Phase 4, commit 6).
export function Sidebar() {
  return (
    <aside className="flex w-80 shrink-0 flex-col gap-4 overflow-y-auto border-r border-slate-800 bg-slate-900 p-4">
      <PrimaryPanel />
    </aside>
  );
}
