"""Bounded, thread-safe pending radio work. Never holds locks across I/O."""

from dataclasses import replace
from threading import Lock

from .contracts import RadioWork

TTL = {"question": 10.0, "callout": 3.0, "ack": 2.0, "greeting": 2.0}
PRIORITY = {"question": 0, "ack": 1, "callout": 2, "greeting": 3}


class RadioQueue:
    """Eight pending slots: four questions, three callouts, one ack/greeting."""

    def __init__(self):
        self._lock = Lock()
        self._generation = 0
        self._items: list[RadioWork] = []

    def _prune(self, now):
        self._items = [w for w in self._items if now < w.expires_mono]

    def submit(self, item: RadioWork, *, now_mono: float) -> bool:
        if item.kind not in TTL:
            return False
        expiry = min(item.expires_mono, item.created_mono + TTL[item.kind])
        if item.kind == "callout":
            if not item.condition or not item.answer or not item.answer.evidence:
                return False
            ev = item.answer.evidence
            if (
                ev.reason is not None
                or ev.generation != item.generation
                or now_mono >= min(ev.expires_mono, ev.progress_valid_until_mono)
            ):
                return False
            # The old answer is never spoken. Dequeue must recollect/rerender
            # within the original work TTL, not renew it via revalidation.
        if not now_mono < expiry or item.created_mono > now_mono:
            return False
        item = replace(item, expires_mono=expiry)
        with self._lock:
            self._prune(now_mono)
            if item.generation != self._generation:
                return False
            items = list(self._items)
            if item.dedupe_key:
                items = [
                    w
                    for w in items
                    if not (w.kind == item.kind and w.dedupe_key == item.dedupe_key)
                ]
            if item.kind in ("ack", "greeting"):
                if item.kind == "greeting" and any(w.kind == "ack" for w in items):
                    return False
                items = [w for w in items if w.kind not in ("ack", "greeting")]
            quota = {"question": 4, "callout": 3, "ack": 1, "greeting": 1}
            if sum(w.kind == item.kind for w in items) >= quota[item.kind]:
                return False
            if len(items) >= 8:
                victim = next(
                    (w for w in items if w.kind in ("callout", "greeting")), None
                )
                if item.kind != "question" or victim is None:
                    return False
                items.remove(victim)
            items.append(item)
            self._items = items
            return True

    def take(self, *, now_mono: float) -> RadioWork | None:
        with self._lock:
            self._prune(now_mono)
            if not self._items:
                return None
            index = min(
                range(len(self._items)), key=lambda i: PRIORITY[self._items[i].kind]
            )
            return self._items.pop(index)

    def reset(self, generation: int) -> None:
        with self._lock:
            self._generation = generation
            self._items.clear()
