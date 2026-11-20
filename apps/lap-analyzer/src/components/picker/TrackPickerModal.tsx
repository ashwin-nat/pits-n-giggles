import { useEffect, useMemo, useState } from "react";
import { useSessions } from "../../hooks/useSessions";
import { formatLapTime } from "../../lib/lapFormat";
import { buildMapGeometry, toPath, type Pt } from "../../lib/mapGeometry";
import { getAllTrackMeta, type TrackMeta } from "../../lib/segments";
import { gameLabel, sortTracks, summariseTracks, type TrackOrder, type TrackSummary } from "../../lib/sessionFilters";
import { getTrackGeometry } from "../../lib/trackGeometry";
import { useTelemetryStore } from "../../store/telemetryStore";
import { Modal } from "../ui/Modal";
import { cardSurface } from "../ui/surfaces";

interface TrackPickerModalProps {
  // Called with the chosen track; the caller opens the lap picker for it.
  onPick: (trackId: number) => void;
  onClose: () => void;
}

const ORDERS: { value: TrackOrder; label: string }[] = [
  { value: "calendar", label: "Calendar" },
  { value: "recent", label: "Recent" },
  { value: "driven", label: "Most driven" },
];

// The track's outline from its geometry, or a dashed placeholder when the
// layout has none (custom and modded tracks).
function TrackOutline({ trackId }: { trackId: number }) {
  const [outline, setOutline] = useState<{ path: string; box: string } | null | undefined>(undefined);

  useEffect(() => {
    let cancelled = false;
    getTrackGeometry(trackId)
      .then((geometry) => {
        if (cancelled) {
          return;
        }
        const g = geometry === null ? null : buildMapGeometry(geometry.edges, geometry.frac);
        if (g === null) {
          setOutline(null);
          return;
        }
        // The centreline, thinned: a card is small.
        const mid: Pt[] = g.L.filter((_, i) => i % 3 === 0).map((l, i) => {
          const r = g.R[i * 3];
          return [(l[0] + r[0]) / 2, (l[1] + r[1]) / 2];
        });
        const xs = mid.map((p) => p[0]);
        const ys = mid.map((p) => p[1]);
        const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
        const pad = Math.max(x1 - x0, y1 - y0) * 0.08;
        setOutline({ path: toPath(mid, true), box: `${x0 - pad} ${y0 - pad} ${x1 - x0 + 2 * pad} ${y1 - y0 + 2 * pad}` });
      })
      .catch(() => !cancelled && setOutline(null));
    return () => {
      cancelled = true;
    };
  }, [trackId]);

  if (outline === null) {
    return <div className="flex h-20 items-center justify-center rounded-lg border border-dashed border-tone-700 text-2xs text-tone-500">Outline not available</div>;
  }
  if (outline === undefined) {
    return <div className="h-20 animate-pulse rounded-lg bg-tone-800/60" />;
  }
  return (
    <svg viewBox={outline.box} className="h-20 w-full" aria-hidden="true">
      <path d={outline.path} fill="none" stroke="#e5e7eb" strokeWidth={3} strokeLinejoin="round" vectorEffect="non-scaling-stroke" />
    </svg>
  );
}

function TrackCard({ track, onPick }: { track: TrackSummary; onPick: () => void }) {
  return (
    <button
      type="button"
      onClick={onPick}
      className={`${cardSurface} flex flex-col gap-2 rounded-xl p-3 text-left transition-shadow hover:ring-tone-600`}
    >
      <TrackOutline trackId={track.trackId} />
      <span className="text-sm font-medium text-tone-50">{track.name}</span>
      <span className="flex flex-col gap-0.5 text-2xs text-tone-500">
        {track.raceBestMs !== null && (
          <span>
            Race <span className="font-mono text-best">{formatLapTime(track.raceBestMs)}</span>
          </span>
        )}
        {track.timeTrialBestMs !== null && (
          <span>
            Time Trial <span className="font-mono text-best">{formatLapTime(track.timeTrialBestMs)}</span>
          </span>
        )}
        <span>
          {track.sessionCount} {track.sessionCount === 1 ? "session" : "sessions"}
          {track.lastDate !== "" && ` · ${new Date(track.lastDate).toLocaleDateString(undefined, { day: "2-digit", month: "short" })}`}
        </span>
      </span>
    </button>
  );
}

// Every track the current game has sessions for, as cards, plus the bundled
// layouts nothing has been recorded on yet.
export function TrackPickerModal({ onPick, onClose }: TrackPickerModalProps) {
  const { data: sessions } = useSessions();
  const game = useTelemetryStore((s) => s.game);
  const [order, setOrder] = useState<TrackOrder>("calendar");
  const [calendar, setCalendar] = useState<Map<number, TrackMeta>>(new Map());

  useEffect(() => {
    getAllTrackMeta().then(setCalendar).catch(() => undefined);
  }, []);

  const inGame = useMemo(
    () => (sessions ?? []).filter((s) => game === null || gameLabel(s) === game),
    [sessions, game]
  );
  const tracks = useMemo(() => sortTracks(summariseTracks(inGame), order), [inGame, order]);
  const notDriven = useMemo(() => {
    const driven = new Set(tracks.map((t) => t.trackId));
    return [...calendar.entries()].filter(([id]) => !driven.has(id)).sort((a, b) => a[0] - b[0]);
  }, [calendar, tracks]);

  return (
    <Modal onClose={onClose} title="Choose a track" description={game ?? "All games"}>
      <div className="flex items-center gap-1 border-t border-tone-800 px-5 py-2">
        {ORDERS.map((o) => (
          <button
            key={o.value}
            type="button"
            aria-pressed={order === o.value}
            onClick={() => setOrder(o.value)}
            className="rounded-md px-2.5 py-1 text-xs text-tone-400 hover:bg-tone-800 aria-pressed:bg-tone-800 aria-pressed:text-tone-100"
          >
            {o.label}
          </button>
        ))}
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto px-5 pb-5">
        {tracks.length === 0 ? (
          <p className="py-6 text-sm text-tone-500">No sessions recorded for this game yet.</p>
        ) : (
          <div className="grid grid-cols-[repeat(auto-fill,minmax(170px,1fr))] gap-3">
            {tracks.map((t) => (
              <TrackCard key={t.trackId} track={t} onPick={() => onPick(t.trackId)} />
            ))}
          </div>
        )}
        {notDriven.length > 0 && (
          <>
            <h3 className="mt-5 mb-2 text-2xs font-semibold tracking-wide text-tone-500 uppercase">Not driven yet</h3>
            <div className="flex flex-wrap gap-1.5">
              {notDriven.map(([id, meta]) => (
                <span key={id} className="rounded-full border border-dashed border-tone-700 px-2.5 py-0.5 text-2xs text-tone-500">
                  {meta.name.replaceAll("_", " ")}
                </span>
              ))}
            </div>
          </>
        )}
      </div>
    </Modal>
  );
}
