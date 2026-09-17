import { PrimaryPanel } from "../PrimaryPanel";
import { ReferencePanel } from "../ReferencePanel";

export function Sidebar() {
  return (
    <aside className="flex w-80 shrink-0 flex-col gap-4 overflow-y-auto border-r border-slate-800 bg-slate-900 p-4">
      <PrimaryPanel />
      <ReferencePanel />
    </aside>
  );
}
