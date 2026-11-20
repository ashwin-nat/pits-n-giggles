import { useEffect, useRef, type ReactNode } from "react";
import { menuSurfaceClass } from "./surfaces";

interface PopoverProps {
  onClose: () => void;
  children: ReactNode;
  // Positioning and size classes, e.g. "right-0 top-full mt-2 w-80".
  className?: string;
}

// A panel anchored to its (relative) parent. Escape or a press outside closes it.
export function Popover({ onClose, children, className = "left-0 top-full mt-2" }: PopoverProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    const onDown = (e: MouseEvent) => {
      const el = ref.current;
      // The anchor's own button toggles the popover; ignore presses inside the anchor.
      if (el !== null && !el.parentElement?.contains(e.target as Node)) {
        onClose();
      }
    };
    window.addEventListener("keydown", onKey);
    window.addEventListener("mousedown", onDown);
    return () => {
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("mousedown", onDown);
    };
  }, [onClose]);

  return (
    <div ref={ref} className={`absolute z-40 ${menuSurfaceClass} ${className}`}>
      {children}
    </div>
  );
}
