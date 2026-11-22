import { useState } from "react";
import { useSessions } from "../../hooks/useSessions";
import { effectiveGame, listGames } from "../../lib/sessionFilters";
import { useTelemetryStore } from "../../store/telemetryStore";
import { Popover } from "../ui/Popover";
import { listItemClass } from "../ui/surfaces";

// The game filter for every track and session list. Follows A's session until
// the user picks one.
export function GameMenu() {
  const { data: sessions } = useSessions();
  const game = useTelemetryStore((s) => s.game);
  const setGame = useTelemetryStore((s) => s.setGame);
  const referenceSessionId = useTelemetryStore((s) => s.laps[0]?.sessionId ?? null);
  const [open, setOpen] = useState(false);

  const games = listGames(sessions ?? []);
  const current = effectiveGame(sessions ?? [], game, referenceSessionId);

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        disabled={games.length === 0}
        className="rounded-lg bg-tone-800 px-3 py-1.5 text-xs text-tone-100 hover:bg-tone-700 disabled:opacity-40"
      >
        {current ?? "No sessions"} <span className="text-tone-500">⇅</span>
      </button>
      {open && (
        <Popover onClose={() => setOpen(false)} className="left-0 top-full mt-2 w-56">
          {games.map(({ label, count }) => (
            <button
              key={label}
              type="button"
              aria-pressed={label === current}
              onClick={() => {
                setGame(label);
                setOpen(false);
              }}
              className={`${listItemClass} text-xs`}
            >
              <span className="flex-1 text-tone-100">{label}</span>
              <span className="text-tone-500">{count}</span>
            </button>
          ))}
        </Popover>
      )}
    </div>
  );
}
