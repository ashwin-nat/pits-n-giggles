import type { TrackSection } from "../types/api";

// Short pill text: the turn numbers for a corner, the section's own label for
// a straight. With `trackLength` a straight is shortened: S/F for the one
// crossing the line, else its last word cut to 4 letters ("Serr.").
export function sectionCode(section: TrackSection, trackLength?: number): string {
  const turns = section.cornerNumbers;
  if (turns.length === 0) {
    if (trackLength === undefined) {
      return section.label;
    }
    if (section.distanceStart <= 0 || section.distanceEnd >= trackLength - 1) {
      return "S/F";
    }
    const word = section.label.split(" ").pop() ?? section.label;
    return word.length > 5 ? `${word.slice(0, 4)}.` : word;
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
