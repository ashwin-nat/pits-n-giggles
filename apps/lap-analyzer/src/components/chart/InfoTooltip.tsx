import { useRef, useState, type CSSProperties, type ReactNode } from "react";

interface InfoTooltipProps {
  text: string;
  children: ReactNode;
  // Forwarded onto the wrapping span, so a caller can lay it out as a flex/grid item.
  className?: string;
  style?: CSSProperties;
  // Preferred side; flips when that side has no room.
  placement?: "top" | "bottom";
}

const TOOLTIP_WIDTH_PX = 256;
// A generous upper estimate of the popup's height, used only to pick a side.
const TOOLTIP_MAX_HEIGHT_PX = 160;
const MARGIN_PX = 12;

interface Pos {
  left: number;
  // Exactly one is set: the popup hangs below `top` or sits above `bottom`.
  top?: number;
  bottom?: number;
}

// A readable tooltip for its own trigger only. Positioned `fixed` from the
// trigger's rect, so no scroll container or neighbouring lane can clip it.
export function InfoTooltip({ text, children, className, style, placement = "top" }: InfoTooltipProps) {
  const triggerRef = useRef<HTMLSpanElement>(null);
  const [pos, setPos] = useState<Pos | null>(null);

  function open() {
    const rect = triggerRef.current?.getBoundingClientRect();
    if (rect === undefined) {
      return;
    }
    const left = Math.min(Math.max(MARGIN_PX, rect.left), window.innerWidth - TOOLTIP_WIDTH_PX - MARGIN_PX);
    const needed = TOOLTIP_MAX_HEIGHT_PX + MARGIN_PX;
    const spaceAbove = rect.top;
    const spaceBelow = window.innerHeight - rect.bottom;
    const preferredSpace = placement === "bottom" ? spaceBelow : spaceAbove;
    const otherSpace = placement === "bottom" ? spaceAbove : spaceBelow;
    const below = preferredSpace >= needed ? placement === "bottom" : otherSpace > preferredSpace ? placement !== "bottom" : placement === "bottom";
    setPos(below ? { left, top: rect.bottom + 8 } : { left, bottom: window.innerHeight - rect.top + 8 });
  }

  return (
    <span
      ref={triggerRef}
      className={`relative inline-flex items-center ${className ?? ""}`}
      style={style}
      onMouseEnter={open}
      onMouseLeave={() => setPos(null)}
    >
      {children}
      {pos !== null && (
        <span
          role="tooltip"
          style={{ left: pos.left, top: pos.top, bottom: pos.bottom, width: TOOLTIP_WIDTH_PX }}
          className="pointer-events-none fixed z-50 rounded-md border border-tone-700 bg-tone-800 p-2.5 text-sm leading-snug text-tone-100 shadow-lg"
        >
          {text}
        </span>
      )}
    </span>
  );
}
