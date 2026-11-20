import type { TrackSection } from "../types/api";

// Short pill text: the turn numbers for a corner, the section's own label for
// a straight.
export function sectionCode(section: TrackSection): string {
  const turns = section.cornerNumbers;
  if (turns.length === 0) {
    return section.label;
  }
  return turns.length === 1 ? `T${turns[0]}` : `T${turns[0]}-${turns[turns.length - 1]}`;
}

// A pill shows its text only when its share of the track is wide enough for it.
export function labelFits(spanPct: number, text: string): boolean {
  return spanPct >= Math.max(2.5, text.length * 0.9);
}

// Viewport for a selected section: its span plus 10% each side, clamped at 0.
export function sectionViewport(start: number, end: number): { distanceStart: number; distanceEnd: number } {
  const pad = (end - start) * 0.1;
  return { distanceStart: Math.max(0, start - pad), distanceEnd: end + pad };
}
