// Lap time and gap formatting for the lap chips and the Choose lap modal.

export function formatLapTime(ms: number | null): string {
  if (ms === null) {
    return "–:––.–––";
  }
  const minutes = Math.floor(ms / 60000);
  const rest = ms % 60000;
  const seconds = Math.floor(rest / 1000);
  const millis = Math.round(rest % 1000);
  return `${minutes}:${String(seconds).padStart(2, "0")}.${String(millis).padStart(3, "0")}`;
}

// Signed seconds, e.g. "+0.412" or "-0.100".
export function formatGap(ms: number): string {
  const seconds = ms / 1000;
  return `${seconds > 0 ? "+" : ""}${seconds.toFixed(3)}`;
}

// A lap can be picked only when it was recorded start to finish and timed.
export function isWholeLap(lap: { lapTime: number | null; complete?: boolean }): boolean {
  return lap.lapTime !== null && lap.complete !== false;
}
