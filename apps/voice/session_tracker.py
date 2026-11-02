"""Shared, ordered observations of progress, not proof of game-packet age."""

import math
from collections.abc import Mapping
from threading import Lock

from .contracts import SourceStamp


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


class SessionProgressTracker:
    def __init__(self):
        self._lock = Lock()
        self._generation = 0
        self._uid = None
        self._player = None
        self._stamp = None
        self._disconnected = False
        self._progress = (None, None)
        self._progress_mono = (None, None)
        self._valid_until = 0.0
        self._reason = "Session progress not yet demonstrated"

    def current_generation(self) -> int:
        with self._lock:
            return self._generation

    def invalidate(self, reason: str) -> int:
        with self._lock:
            self._invalidate(reason)
            return self._generation

    def _invalidate(self, reason):
        if not self._disconnected:
            self._generation += 1
        self._disconnected = True
        self._progress = (None, None)
        self._progress_mono = (None, None)
        self._valid_until = 0.0
        self._reason = reason

    def observe(
        self, session: Mapping[str, object], *, stamp: SourceStamp
    ) -> tuple[int, float, str | None]:
        with self._lock:
            return self._observe(session, stamp)

    def _observe(self, session, stamp):
        epoch, mono = stamp.cache_received_epoch, stamp.collected_mono
        if not finite(epoch) or not finite(mono):
            return self._generation, 0.0, "Invalid observation clock"
        if self._stamp is not None:
            old_epoch, old_mono = self._stamp
            if epoch < old_epoch or mono < old_mono:
                return self._generation, 0.0, "Out-of-order session observation"
            if epoch == old_epoch:
                self._stamp = (epoch, mono)
                if session.get("connected") is False:
                    self._invalidate("Telemetry disconnected")
                if self._disconnected:
                    return self._generation, 0.0, self._reason
                # Same cache generation cannot demonstrate new progress or identity.
                if session.get("identity", {}).get("session_uid") != self._uid:
                    return self._generation, 0.0, "Incoherent session identity"
                player = session.get("player_index", self._player)
                if self._player is not None and player != self._player:
                    self._generation += 1
                    self._progress = (None, None)
                    self._progress_mono = (None, None)
                    self._valid_until = 0.0
                    self._reason = "Player changed; progress not yet demonstrated"
                self._player = player
                return self._generation, self._valid_until, self._reason
        self._stamp = (epoch, mono)
        if session.get("connected") is False:
            self._invalidate("Telemetry disconnected")
            return self._generation, 0.0, self._reason
        identity = session.get("identity", {})
        uid = identity.get("session_uid")
        if type(uid) is not int or uid <= 0:
            return self._generation, 0.0, "Invalid session UID"
        player = session.get("player_index", self._player)
        if (self._uid is not None and uid != self._uid) or (
            self._player is not None and player != self._player
        ):
            self._generation += 1
            self._progress = (None, None)
            self._progress_mono = (None, None)
            self._valid_until = 0.0
        if self._disconnected:
            self._progress = (None, None)
            self._progress_mono = (None, None)
        self._disconnected = False
        self._uid, self._player = uid, player
        progress = session.get("progress", {})
        values = (
            progress.get("duration_elapsed_sec"),
            progress.get("time_remaining_sec"),
        )
        values = tuple(v if finite(v) and v >= 0 else None for v in values)
        old = self._progress
        regression = any(
            a is not None and b is not None and (a < b if i == 0 else a > b)
            for i, (a, b) in enumerate(zip(values, old))
        )
        advancing = any(
            a is not None
            and b is not None
            and observed_mono is not None
            and mono - observed_mono <= 3.0
            and (a > b if i == 0 else a < b)
            for i, (a, b, observed_mono) in enumerate(
                zip(values, old, self._progress_mono)
            )
        )
        if not regression:
            # Missing counters must not erase independently valid watermarks.
            self._progress = tuple(
                value if value is not None else previous
                for value, previous in zip(values, old)
            )
            self._progress_mono = tuple(
                mono if value is not None else previous_mono
                for value, previous_mono in zip(values, self._progress_mono)
            )
        if all(v is None for v in values):
            self._valid_until = 0.0
            self._reason = "Session progress unavailable"
        elif regression:
            self._valid_until = 0.0
            self._reason = "Session progress regressed"
        elif advancing:
            self._valid_until = mono + 3.0
            self._reason = None
        elif mono >= self._valid_until:
            self._reason = "Session progress frozen or not yet demonstrated"
        return self._generation, self._valid_until, self._reason
