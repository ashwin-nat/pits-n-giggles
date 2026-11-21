import type { ReactNode } from "react";

// The scrollable body under the header: the chart area and the map panel.
export function Layout({ children }: { children: ReactNode }) {
  return (
    <main
      className="h-full overflow-auto bg-canvas text-tone-100"
      // Reserves the scrollbar's width up front so content does not shift when a
      // vertical scrollbar appears once there are enough lanes to overflow.
      style={{ scrollbarGutter: "stable" }}
    >
      {children}
    </main>
  );
}
