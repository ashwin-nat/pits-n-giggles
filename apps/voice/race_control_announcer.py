"""Speak new race-control messages as they arrive during a live session.

Polls the dashboard's ``/race-info`` endpoint, which carries the session's
race-control messages under ``race-control``. The first successful poll only
records the current high-water mark so that messages already present when the
engineer starts are not replayed. Later polls speak every message whose ``id``
is above that mark, in id order.
"""

import logging
import threading
from collections.abc import Callable
from typing import Any, Dict, List, Optional

import requests

LOGGER = logging.getLogger(__name__)

REQUEST_TIMEOUT_SEC = 2.0


def describe_message(msg: Dict[str, Any]) -> str:
    """Build the spoken sentence for one race-control message."""
    kind = str(msg.get("message-type", "race control")).replace("_", " ").lower()
    parts = [kind]
    driver = msg.get("driver-info") or {}
    if driver.get("name"):
        parts.append(str(driver["name"]).title())
    lap = msg.get("lap-number")
    if lap is not None:
        parts.append(f"lap {lap}")
    segment = msg.get("segment-info") or {}
    if segment.get("name"):
        parts.append(f"at {segment['name']}")
    return ", ".join(parts)


class RaceControlAnnouncer:
    """Background poller that hands new race-control messages to ``speak``."""

    def __init__(
        self,
        speak: Callable[[str], None],
        url: str,
        poll_sec: float = 2.0,
        *,
        fetch: Optional[Callable[[], Any]] = None,
    ) -> None:
        self._speak = speak
        self._url = url
        self._poll_sec = poll_sec
        self._fetch = fetch or self._http_fetch
        self._last_id: Optional[int] = None
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def _http_fetch(self) -> Any:
        resp = requests.get(self._url, timeout=REQUEST_TIMEOUT_SEC)
        resp.raise_for_status()
        return resp.json()

    def poll_once(self) -> List[str]:
        """Fetch once, speak anything new, and return the spoken texts."""
        data = self._fetch()
        messages = data.get("race-control") if isinstance(data, dict) else None
        if not isinstance(messages, list):
            return []
        ids = [m["id"] for m in messages if isinstance(m.get("id"), int)]
        if not ids:
            return []
        newest = max(ids)

        if self._last_id is None or newest < self._last_id:
            # First poll, or the backend restarted with a new session:
            # adopt the current position without speaking.
            self._last_id = newest
            return []

        fresh = sorted(
            (
                m
                for m in messages
                if isinstance(m.get("id"), int) and m["id"] > self._last_id
            ),
            key=lambda m: m["id"],
        )
        spoken = []
        for msg in fresh:
            text = describe_message(msg)
            self._speak(text)
            spoken.append(text)
        self._last_id = newest
        return spoken

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                self.poll_once()
            except Exception as exc:  # pylint: disable=broad-except
                LOGGER.debug("race-control poll failed: %s", exc)
            self._stop.wait(self._poll_sec)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run, daemon=True, name="RaceControlAnnounce"
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread and self._thread is not threading.current_thread():
            self._thread.join(timeout=5)
