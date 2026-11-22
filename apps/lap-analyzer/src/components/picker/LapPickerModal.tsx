import { useMemo, useState } from "react";
import { useDriverBests } from "../../hooks/useDriverBests";
import { useSessions } from "../../hooks/useSessions";
import { LAP_SLOT_COLORS, LAP_SLOT_LETTERS } from "../../lib/chartConstants";
import { formatLapTime, isPartialLap } from "../../lib/lapFormat";
import { comparableSessions, effectiveGame, gameLabel, newestFirst } from "../../lib/sessionFilters";
import { useTelemetryStore } from "../../store/telemetryStore";
import type { Lap, Session } from "../../types/api";
import type { LapSelection } from "../../types/store";
import { Modal } from "../ui/Modal";
import { listItemClass } from "../ui/surfaces";

interface LapPickerModalProps {
  // The slot to fill or replace. A slot past the last lap adds a comparison lap.
  slot: number;
  // Limits the session list to one track (set when A is picked from the track picker).
  trackId?: number;
  onClose: () => void;
}

type LapOrder = "lap" | "time";

function formatDate(iso: string): string {
  const date = new Date(iso);
  if (iso === "" || Number.isNaN(date.getTime())) {
    return "";
  }
  return date.toLocaleString(undefined, { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
}

// Slot letters of the laps held in `laps` that match the given session and, optionally, driver and lap.
function holders(laps: readonly LapSelection[], sessionId: string, driverIndex?: number, lapNumber?: number): number[] {
  return laps.flatMap((l, slot) =>
    l.sessionId === sessionId &&
    (driverIndex === undefined || l.driverIndex === driverIndex) &&
    (lapNumber === undefined || l.lapNumber === lapNumber)
      ? [slot]
      : []
  );
}

function SlotBadges({ slots }: { slots: number[] }) {
  return (
    <>
      {slots.map((s) => (
        <span key={s} className="text-2xs font-semibold" style={{ color: LAP_SLOT_COLORS[s] }}>
          {LAP_SLOT_LETTERS[s]}
        </span>
      ))}
    </>
  );
}

function Column({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="flex min-h-0 min-w-0 flex-1 flex-col border-l border-tone-800 first:border-l-0">
      <h3 className="shrink-0 px-4 py-2 text-2xs font-semibold tracking-wide text-tone-500 uppercase">{title}</h3>
      <div className="min-h-0 flex-1 space-y-0.5 overflow-y-auto px-2 pb-3">{children}</div>
    </div>
  );
}

function Empty({ children }: { children: React.ReactNode }) {
  return <p className="px-2.5 py-3 text-xs text-tone-500">{children}</p>;
}

// Session, then driver, then lap. Replaces the sidebar's three cascading selects.
export function LapPickerModal({ slot, trackId, onClose }: LapPickerModalProps) {
  const laps = useTelemetryStore((s) => s.laps);
  const game = useTelemetryStore((s) => s.game);
  const pickLap = useTelemetryStore((s) => s.pickLap);
  const { data: sessions } = useSessions();

  const current = laps[slot];
  const reference = sessions?.find((s) => s.id === laps[0]?.sessionId);
  const isComparison = slot > 0 && reference !== undefined;

  // Comparison laps come from A's circuit and formula; A comes from the
  // chosen track, or any track in the current game.
  const sessionList = useMemo<Session[]>(() => {
    if (sessions === undefined) {
      return [];
    }
    if (isComparison) {
      return newestFirst(comparableSessions(sessions, reference));
    }
    const currentGame = effectiveGame(sessions, game, laps[0]?.sessionId ?? null);
    return newestFirst(
      sessions.filter(
        (s) => (trackId === undefined || s.trackId === trackId) && (currentGame === null || gameLabel(s) === currentGame)
      )
    );
  }, [sessions, isComparison, reference, game, laps, trackId]);

  // Defaults to the slot's own session, else A's, else the newest.
  const [pickedSession, setPickedSession] = useState<string | null>(null);
  const sessionId =
    pickedSession ??
    [current?.sessionId, laps[0]?.sessionId].find((id) => id != null && sessionList.some((s) => s.id === id)) ??
    sessionList[0]?.id ??
    null;
  const session = sessionList.find((s) => s.id === sessionId);

  const [pickedDriver, setPickedDriver] = useState<number | null>(null);
  const [order, setOrder] = useState<LapOrder>("lap");
  const { rows, isLoading } = useDriverBests(sessionId);
  // Every driver with laps, fastest personal best first; drivers with no valid timed lap last.
  const drivers = useMemo(
    () =>
      rows
        .filter((r) => r.laps.length > 0)
        .sort((a, b) => (a.bestMs ?? Infinity) - (b.bestMs ?? Infinity) || a.driver.index - b.driver.index),
    [rows]
  );
  const driverIndex =
    pickedDriver !== null && drivers.some((d) => d.driver.index === pickedDriver)
      ? pickedDriver
      : current?.sessionId === sessionId && drivers.some((d) => d.driver.index === current.driverIndex)
        ? current.driverIndex
        : null;
  const driver = drivers.find((d) => d.driver.index === driverIndex);

  const sessionBest = session?.sessionBest ?? null;
  const shownLaps = useMemo<Lap[]>(() => {
    const list = [...(driver?.laps ?? [])];
    return order === "lap"
      ? list.sort((a, b) => a.lapNumber - b.lapNumber)
      : list.sort((a, b) => (a.lapTime ?? Infinity) - (b.lapTime ?? Infinity));
  }, [driver, order]);

  function pick(lap: Lap) {
    if (sessionId === null || driverIndex === null) {
      return;
    }
    pickLap(slot, { sessionId, driverIndex, lapNumber: lap.lapNumber });
    onClose();
  }

  const title = slot === 0 ? "Choose the reference lap" : slot < laps.length ? `Replace lap ${LAP_SLOT_LETTERS[slot]}` : "Compare with a lap";

  return (
    <Modal
      onClose={onClose}
      title={title}
      description={
        isComparison && reference !== undefined
          ? `Sessions at ${reference.trackName}, ${reference.formula}`
          : trackId !== undefined
            ? "Sessions at the chosen track"
            : "Session, then driver, then lap"
      }
    >
      <div className="flex h-[min(520px,64vh)] min-h-0 border-t border-tone-800">
        <Column title="Session">
          {sessions === undefined ? (
            <Empty>Loading…</Empty>
          ) : sessionList.length === 0 ? (
            <Empty>No sessions</Empty>
          ) : (
            sessionList.map((s) => (
              <button
                key={s.id}
                type="button"
                aria-pressed={s.id === sessionId}
                onClick={() => {
                  setPickedSession(s.id);
                  setPickedDriver(null);
                }}
                className={`${listItemClass} flex-col items-start gap-0`}
              >
                <span className="flex w-full items-center gap-2 text-sm text-tone-100">
                  {s.type}
                  <SlotBadges slots={holders(laps, s.id)} />
                </span>
                <span className="text-2xs text-tone-500">
                  {s.trackName} · {formatDate(s.date)}
                </span>
              </button>
            ))
          )}
        </Column>

        <Column title="Driver">
          {sessionId === null ? (
            <Empty>Pick a session</Empty>
          ) : isLoading && drivers.length === 0 ? (
            <Empty>Loading…</Empty>
          ) : drivers.length === 0 ? (
            <Empty>No driver has laps in this session</Empty>
          ) : (
            drivers.map(({ driver: d, bestMs }, rank) => {
              const isSessionBest = sessionBest !== null && sessionBest.driverIndex === d.index && sessionBest.lapTimeMs === bestMs;
              const isPlayer = session?.playerIndex === d.index;
              return (
                <button
                  key={d.index}
                  type="button"
                  aria-pressed={d.index === driverIndex}
                  onClick={() => setPickedDriver(d.index)}
                  className={`${listItemClass} border ${isPlayer ? "border-tone-400" : "border-transparent"}`}
                >
                  <span className="w-5 shrink-0 text-right font-mono text-2xs text-tone-500">{rank + 1}</span>
                  <span className="min-w-0 flex-1 truncate text-sm text-tone-100">
                    {d.name}
                    {isPlayer && <span className="ml-1.5 text-2xs text-tone-500">You</span>}
                  </span>
                  <SlotBadges slots={holders(laps, sessionId, d.index)} />
                  <span className={`font-mono text-xs ${isSessionBest ? "text-best" : "text-tone-400"}`}>
                    {formatLapTime(bestMs)}
                  </span>
                </button>
              );
            })
          )}
        </Column>

        <Column title="Lap">
          {driver === undefined ? (
            <Empty>Pick a driver</Empty>
          ) : (
            <>
              <div className="flex gap-1 px-1 pb-1.5">
                {(["lap", "time"] as const).map((o) => (
                  <button
                    key={o}
                    type="button"
                    aria-pressed={order === o}
                    onClick={() => setOrder(o)}
                    className="rounded-md px-2 py-0.5 text-2xs text-tone-400 hover:bg-tone-800 aria-pressed:bg-tone-800 aria-pressed:text-tone-100"
                  >
                    {o === "lap" ? "Lap" : "Time"}
                  </button>
                ))}
              </div>
              {shownLaps.map((lap) => {
                const partial = isPartialLap(lap);
                const isSessionBest =
                  sessionBest !== null &&
                  sessionBest.driverIndex === driver.driver.index &&
                  sessionBest.lapNumber === lap.lapNumber;
                const isPersonalBest = !isSessionBest && lap.valid && lap.lapTime !== null && lap.lapTime === driver.bestMs;
                const held = sessionId === null ? [] : holders(laps, sessionId, driver.driver.index, lap.lapNumber);
                return (
                  <button
                    key={lap.lapNumber}
                    type="button"
                    aria-pressed={held.includes(slot)}
                    onClick={() => pick(lap)}
                    title={partial ? `Partly recorded: ${lap.incompleteReason ?? "not captured in full"}` : undefined}
                    className={listItemClass}
                  >
                    <span className="w-6">
                      <SlotBadges slots={held} />
                    </span>
                    <span
                      className={`font-mono text-sm ${isSessionBest ? "text-best" : isPersonalBest ? "text-ahead" : "text-tone-100"}`}
                    >
                      {formatLapTime(lap.lapTime)}
                    </span>
                    <span className="text-2xs text-tone-500">Lap {lap.lapNumber}</span>
                    <span className="ml-auto flex items-center gap-1.5 text-2xs text-tone-400">
                      {lap.tyreCompound}
                      {lap.lapNumber === 1 && session?.type === "Race" && <span className="text-tone-500">Start</span>}
                      {(lap.pitInLap || lap.pitOutLap) && <span className="text-tone-500">Pit</span>}
                      {!lap.valid && <span className="text-behind">Invalid</span>}
                      {partial && <span className="text-amber-400">Partly recorded</span>}
                    </span>
                  </button>
                );
              })}
            </>
          )}
        </Column>
      </div>
    </Modal>
  );
}
