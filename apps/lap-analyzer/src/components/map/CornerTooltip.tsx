import type { CornerSpan } from "../../lib/segments";

const WIDTH_PX = 208;
const MARGIN_PX = 8;
const GAP_PX = 10;
// Enough room above the badge for the tooltip; below that it flips underneath.
const FLIP_BELOW_PX = 96;

// The corner's name, turn number and span, in the same panel style as the other tooltips. `anchor` is
// the badge's screen rect; the arrow points at it.
export function CornerTooltip({ corner, anchor }: { corner: CornerSpan; anchor: DOMRect }) {
  const cx = anchor.left + anchor.width / 2;
  const left = Math.min(Math.max(MARGIN_PX, cx - WIDTH_PX / 2), window.innerWidth - WIDTH_PX - MARGIN_PX);
  const below = anchor.top < FLIP_BELOW_PX;
  const arrowLeft = Math.min(Math.max(12, cx - left), WIDTH_PX - 12);

  return (
    <div
      role="tooltip"
      style={{
        left,
        width: WIDTH_PX,
        ...(below ? { top: anchor.bottom + GAP_PX } : { bottom: window.innerHeight - anchor.top + GAP_PX }),
      }}
      className="pointer-events-none fixed z-50 rounded-md border border-tone-700 bg-tone-800 px-3 py-2 text-left shadow-lg"
    >
      <p className="text-sm font-semibold leading-snug text-tone-50">
        {corner.name === "" ? `Turn ${corner.number}` : corner.name}
      </p>
      <p className="mt-0.5 text-xs text-tone-300">
        {corner.name === "" ? "" : `Turn ${corner.number} · `}
        {Math.round(corner.startM)} to {Math.round(corner.endM)} m
      </p>
      <span
        style={{ left: arrowLeft - 5 }}
        className={`absolute h-2.5 w-2.5 rotate-45 border-tone-700 bg-tone-800 ${
          below ? "-top-[6px] border-t border-l" : "-bottom-[6px] border-r border-b"
        }`}
      />
    </div>
  );
}
