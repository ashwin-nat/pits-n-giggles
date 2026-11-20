import { useEffect, type ReactNode } from "react";
import { floatingSurface } from "./surfaces";

interface ModalProps {
  onClose: () => void;
  title: ReactNode;
  description?: ReactNode;
  children: ReactNode;
  // Sizing classes for the panel.
  className?: string;
}

// A dialog over a dimmed backdrop. Escape and a backdrop click close it.
export function Modal({ onClose, title, description, children, className = "w-[min(960px,92vw)]" }: ModalProps) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={typeof title === "string" ? title : undefined}
        className={`relative flex max-h-[86vh] flex-col overflow-hidden rounded-2xl ${floatingSurface} ${className}`}
      >
        <button
          type="button"
          onClick={onClose}
          aria-label="Close"
          className="absolute top-3.5 right-3.5 z-10 rounded-md px-1.5 text-tone-500 transition-colors hover:bg-tone-800 hover:text-tone-200"
        >
          ✕
        </button>
        <div className="shrink-0 px-5 pt-4 pb-3 pr-12">
          <h2 className="font-semibold text-tone-50">{title}</h2>
          {description !== undefined && <p className="mt-0.5 text-xs text-tone-500">{description}</p>}
        </div>
        {children}
      </div>
    </div>
  );
}
