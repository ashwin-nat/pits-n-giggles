import type { ReactNode } from "react";
import { Sidebar } from "./Sidebar";

interface LayoutProps {
  children: ReactNode; // chart area content, wired in Phase 5
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="flex h-full w-full overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-auto bg-slate-950 text-slate-100">{children}</main>
    </div>
  );
}
