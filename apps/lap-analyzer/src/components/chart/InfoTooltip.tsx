import { useRef, useState, type CSSProperties, type ReactNode } from "react";

interface InfoTooltipProps {
  text: string;
  children: ReactNode;
  // Forwarded onto the wrapping span -- lets a caller lay this element out
  // as a flex/grid item itself (see TrackProgressBar) instead of needing an
  // extra wrapper just to size the hover target.
  className?: string;
  style?: CSSProperties;
  // "top" (default) opens the popup above its trigger -- fine everywhere
  // except when the trigger itself sits at the very top of the scrollable
  // chart area (TrackProgressBar), where an upward popup gets clipped by
  // Layout's `overflow-auto` <main> with no way to scroll up into it.
  placement?: "top" | "bottom";
}

// Matches the popup's w-64. Height varies with text (two-sentence Rate
// tooltip vs. a one-line segment name), so this is a generous upper estimate
// rather than a measured value -- good enough to decide "does the preferred
// side have room," not pixel-exact.
const TOOLTIP_WIDTH_PX = 256;
const TOOLTIP_MAX_HEIGHT_PX = 160;
const VIEWPORT_MARGIN_PX = 12;

// A readable, always-hoverable tooltip -- native `title` attributes are tiny,
// low-contrast, and (contrary to how they read) don't reliably feel
// "available" to hover in every state. This renders our own styled panel via
// Tailwind's group-hover pattern instead.
export function InfoTooltip({ text, children, className, style, placement = "top" }: InfoTooltipProps) {
  const triggerRef = useRef<HTMLSpanElement>(null);
  // Both default from `placement`/right-alignment, then flip on hover if
  // that side doesn't have room -- e.g. the first segment in
  // TrackProgressBar's bar (or any trigger near the left edge in a narrow
  // window) would push a right-aligned popup off-screen; the topmost
  // ChartLane's Rate tooltip, opening upward by default, has nothing above
  // it but the progress bar/legend and gets clipped by Layout's
  // `overflow-auto` <main>. Measured on hover since neither the trigger's
  // position nor the popup's size is known ahead of time here.
  const [alignLeft, setAlignLeft] = useState(false);
  const [openBelow, setOpenBelow] = useState(placement === "bottom");

  function handleMouseEnter() {
    const trigger = triggerRef.current;
    if (trigger === null) {
      return;
    }
    const rect = trigger.getBoundingClientRect();
    // The real constraint is "don't overlap the sidebar," not "don't cross
    // the browser window's edge" -- the sidebar is well inside the window,
    // so a window-edge-only check missed it (a right-aligned popup could
    // sit entirely on-screen while still overlapping the sidebar to its
    // left). <main> is the scrollable content area everything here renders
    // into; its left edge is the real boundary a leftward-opening popup
    // must respect.
    const contentLeft = trigger.closest("main")?.getBoundingClientRect().left ?? 0;
    setAlignLeft(rect.right - TOOLTIP_WIDTH_PX < contentLeft + VIEWPORT_MARGIN_PX);

    const spaceAbove = rect.top;
    const spaceBelow = window.innerHeight - rect.bottom;
    const preferredBelow = placement === "bottom";
    const preferredSpace = preferredBelow ? spaceBelow : spaceAbove;
    const otherSpace = preferredBelow ? spaceAbove : spaceBelow;
    const fitsPreferred = preferredSpace >= TOOLTIP_MAX_HEIGHT_PX + VIEWPORT_MARGIN_PX;
    setOpenBelow(fitsPreferred ? preferredBelow : otherSpace > preferredSpace ? !preferredBelow : preferredBelow);
  }

  const verticalClass = openBelow ? "top-full mt-2" : "bottom-full mb-2";
  const horizontalClass = alignLeft ? "left-0" : "right-0";

  return (
    <span
      ref={triggerRef}
      className={`group relative inline-flex items-center ${className ?? ""}`}
      style={style}
      onMouseEnter={handleMouseEnter}
    >
      {children}
      <span
        role="tooltip"
        className={`pointer-events-none absolute z-10 hidden w-64 rounded-md border border-slate-700 bg-slate-800 p-2.5 text-sm leading-snug text-slate-100 shadow-lg group-hover:block ${verticalClass} ${horizontalClass}`}
      >
        {text}
      </span>
    </span>
  );
}
