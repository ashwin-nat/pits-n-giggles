import type { ReactNode } from "react";
import { Sidebar } from "./Sidebar";

interface LayoutProps {
  children: ReactNode; // chart area content, wired in Phase 5
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="flex h-full w-full overflow-hidden">
      <Sidebar />
      {/* scrollbarGutter reserves the scrollbar's width up front, so content
          doesn't visibly shift/crowd the right edge when a vertical
          scrollbar appears once there are enough lanes to overflow. pr-3 and
          pb-12 give the content breathing room from the scrollbar and from
          the bottom of the viewport respectively. */}
      <main
        className="flex-1 overflow-auto bg-slate-950 pr-3 pb-12 text-slate-100"
        style={{ scrollbarGutter: "stable" }}
      >
        {children}
      </main>
    </div>
  );
}
