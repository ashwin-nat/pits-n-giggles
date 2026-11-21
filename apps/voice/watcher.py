"""Independent session sampling and deterministic, evidence-bound callouts."""

import asyncio
import json
import logging
import threading
import time
from collections.abc import Callable, Mapping
from uuid import uuid4

from .contracts import Answer, CalloutCondition, Intent, RadioWork, SourceStamp
from .session_tracker import SessionProgressTracker, finite
from .telemetry import TelemetryAdapter

LOGGER = logging.getLogger(__name__)
SESSION = "get_session_info"
TYRES = "get_player_tyre_wear"
FUEL = "get_player_fuel_info"


class TelemetryWatcher:
    """Sample SESSION every second, even with proactive radio disabled.

    Each MCP client gets its own adapter, sharing only the explicit locked tracker.
    ``refresh_callout`` is a synchronous worker-thread API, not an async-loop API.
    """

    def __init__(
        self,
        mcp_url: str,
        on_callout: Callable[[RadioWork], None],
        poll_sec: float = 5.0,
        wear_threshold: float = 80.0,
        *,
        tracker: SessionProgressTracker,
        proactive: bool = True,
        on_session: Callable[[int | None, int], None] | None = None,
        epoch_clock=time.time,
        mono_clock=time.monotonic,
        adapter=None,
    ):
        self.mcp_url = mcp_url
        self.on_callout = on_callout
        self.poll_sec = max(1.0, poll_sec)
        self.wear_threshold = wear_threshold
        self.tracker = tracker
        self.proactive = proactive
        self.on_session = on_session
        self._epoch = epoch_clock
        self._mono = mono_clock
        self._adapter = adapter
        self._stop = threading.Event()
        self._thread = None
        self._state_lock = threading.Lock()
        self._state = {}
        self._generation = tracker.current_generation()
        self._session_reason = "Session not sampled"
        self._uid = None
        self._next_callouts = 0.0

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=lambda: asyncio.run(self._run()),
            daemon=True,
            name="TelemetryWatcher",
        )
        self._thread.start()

    def stop(self):
        self._stop.set()

    def _adapter_for(self, client):
        return TelemetryAdapter(
            client, self.tracker, epoch_clock=self._epoch, mono_clock=self._mono
        )

    def _sync_generation(self):
        generation = self.tracker.current_generation()
        with self._state_lock:
            changed = generation != self._generation
            if changed:
                self._state.clear()
                self._generation = generation
        if changed and self.on_session:
            self.on_session(self._uid, generation)

    async def _sample_session(self, client):
        """Use the public MCP/tracker boundary; no heavyweight topic collection."""
        try:
            response = await asyncio.wait_for(
                client.call_tool(SESSION, {}, raise_on_error=False), timeout=1.0
            )
            epoch, mono = self._epoch(), self._mono()
            data = getattr(response, "structured_content", None)
            if data is None:
                data = getattr(response, "data", None)
            if data is None:
                data = json.loads(response.content[0].text)
            if not isinstance(data, Mapping):
                raise ValueError("Unknown session schema")
            received = data.get("last-update-timestamp")
            if not finite(received) or not 0 <= epoch - received <= 2:
                raise ValueError("Session receipt stale or unavailable")
            stamp = SourceStamp(SESSION, received, mono)
            if data.get("connected") is False:
                _, _, self._session_reason = self.tracker.observe(data, stamp=stamp)
                self._uid = None
            elif (
                data.get("connected") is True
                and data.get("available") is True
                and type(data.get("ok")) is bool
                and not data.get("error")
                and isinstance(data.get("identity"), Mapping)
                and isinstance(data.get("progress"), Mapping)
            ):
                self._uid = data["identity"].get("session_uid")
                _, _, self._session_reason = self.tracker.observe(data, stamp=stamp)
            else:
                raise ValueError("Session unavailable")
        except Exception as exc:  # reconnect without permitting old-session speech
            self._uid = None
            self._session_reason = str(exc) or type(exc).__name__
            self.tracker.invalidate(self._session_reason)
        self._sync_generation()

    async def poll_once(self, client):
        await self._sample_session(client)
        now = self._mono()
        if not self.proactive or now < self._next_callouts:
            return
        self._next_callouts = now + self.poll_sec
        adapter = self._adapter or self._adapter_for(client)
        for topic in ("weather", "tyres", "fuel"):
            ev = await adapter.collect(Intent(topic), self._mono() + 2.0)
            self._sync_generation()
            await self.evaluate(ev)

    async def _sampling_loop(self, client):
        while not self._stop.is_set():
            started = self._mono()
            await self._sample_session(client)
            await asyncio.sleep(max(0.01, 1.0 - (self._mono() - started)))

    async def _callout_loop(self, client):
        adapter = self._adapter or self._adapter_for(client)
        while not self._stop.is_set():
            started = self._mono()
            for topic in ("weather", "tyres", "fuel"):
                if self._stop.is_set():
                    break
                ev = await adapter.collect(Intent(topic), self._mono() + 2.0)
                self._sync_generation()
                await self.evaluate(ev)
            await asyncio.sleep(max(0.01, self.poll_sec - (self._mono() - started)))

    async def _run(self):
        from fastmcp import Client

        while not self._stop.is_set():
            try:
                # Separate clients/tasks keep slow topic collection from starving
                # the <=3-second progress-pair window, even at a 5-second poll.
                async with Client(self.mcp_url) as session_client:
                    if not self.proactive:
                        await self._sampling_loop(session_client)
                    else:
                        async with Client(self.mcp_url) as topic_client:
                            async with asyncio.TaskGroup() as tasks:
                                tasks.create_task(self._sampling_loop(session_client))
                                tasks.create_task(self._callout_loop(topic_client))
            except Exception as exc:
                LOGGER.debug("Watcher reconnecting: %s", exc)
                self._uid = None
                self.tracker.invalidate("Telemetry disconnected")
                self._sync_generation()
                await asyncio.sleep(1.0)

    def _valid(self, ev):
        return (
            ev.reason is None
            and ev.generation == self.tracker.current_generation()
            and self._mono() < min(ev.expires_mono, ev.progress_valid_until_mono)
        )

    def _value(self, event, ev):
        if event == "tyre_wear":
            data = ev.facts.get(TYRES, {})
            values = [
                data.get(k)
                for k in ("fl_wear_pct", "fr_wear_pct", "rl_wear_pct", "rr_wear_pct")
            ]
            values = [v for v in values if finite(v) and 0 <= v <= 100]
            return max(values) if values else None
        if event == "fuel_deficit":
            value = ev.facts.get(FUEL, {}).get("surplus_laps_live")
            return value if finite(value) else None
        session = ev.facts.get(SESSION, {})
        if event == "safety_car":
            return session.get("race_control", {}).get("safety_car_status")
        return session.get("environment", {}).get("weather_forecast")

    def _render(self, event, ev, baseline):
        value = self._value(event, ev)
        if value is None:
            return None
        if event == "tyre_wear":
            if value <= self.wear_threshold:
                return None
            text = f"Tyre wear is high, up to {value:.0f} percent. Monitor the tyres."
            path = TYRES
        elif event == "fuel_deficit":
            if value >= -0.2:
                return None
            text = (
                f"Live fuel estimate is {abs(value):.2f} laps short. "
                "Consider fuel saving."
            )
            path = FUEL + ".surplus_laps_live"
        else:
            if "previous" not in baseline or "current" not in baseline:
                return None
            if value == baseline["previous"] or value != baseline["current"]:
                return None
            if event == "safety_car":
                text = f"Safety car status changed to {value}."
                path = SESSION + ".race_control.safety_car_status"
            else:
                # Do not turn arbitrary forecast payloads into radio prose.
                text = "Weather forecast has changed. Check the forecast."
                path = SESSION + ".environment.weather_forecast"
        return Answer(
            text, "estimate" if event == "fuel_deficit" else "fact", ev, (path,), ()
        )

    async def evaluate(self, ev):
        self._sync_generation()
        if not self._valid(ev):
            # A later change needs two valid observations, not an unavailable baseline.
            with self._state_lock:
                if ev.topic == "weather":
                    self._state.pop("safety_car", None)
                    self._state.pop("weather", None)
            return
        events = {
            "tyres": ("tyre_wear",),
            "fuel": ("fuel_deficit",),
            "weather": ("safety_car", "weather"),
        }.get(ev.topic, ())
        for event in events:
            value = self._value(event, ev)
            if value is None:
                with self._state_lock:
                    self._state.pop(event, None)
                continue
            baseline = None
            with self._state_lock:
                old = self._state.get(event)
                if event in ("tyre_wear", "fuel_deficit"):
                    trigger = (
                        value > self.wear_threshold
                        if event == "tyre_wear"
                        else value < -0.2
                    )
                    clear = (
                        value <= self.wear_threshold - 2
                        if event == "tyre_wear"
                        else value >= 0
                    )
                    if trigger and not old:
                        baseline = {
                            "threshold": (
                                self.wear_threshold if event == "tyre_wear" else -0.2
                            )
                        }
                        self._state[event] = True
                    elif clear:
                        self._state[event] = False
                else:
                    if old is not None and value != old:
                        baseline = {"previous": old, "current": value}
                    self._state[event] = value
            if baseline is None:
                continue
            condition = CalloutCondition(event, baseline)
            answer = self._render(event, ev, condition.baseline)
            if answer is not None:
                received = min(
                    (s.collected_mono for s in ev.stamps), default=self._mono()
                )
                work = RadioWork(
                    uuid4().hex,
                    "callout",
                    "",
                    ev.generation,
                    received,
                    received + 3,
                    answer,
                    event,
                    condition,
                )
                self.on_callout(work)

    def refresh_callout(self, work: RadioWork) -> Answer | None:
        """Recollect and rerender, bounded by the ORIGINAL pending-work TTL."""
        if (
            work.condition is None
            or work.answer is None
            or work.answer.evidence is None
        ):
            return None

        def baseline_present():
            with self._state_lock:
                value = self._state.get(work.condition.event)
                if work.condition.event in ("tyre_wear", "fuel_deficit"):
                    return value is True
                return value is not None and value == work.condition.baseline.get(
                    "current"
                )

        async def refresh(adapter):
            if (
                not baseline_present()
                or self._mono() >= work.expires_mono
                or work.generation != self.tracker.current_generation()
            ):
                return None
            ev = await adapter.collect(
                Intent(work.answer.evidence.topic), work.expires_mono
            )
            self._sync_generation()
            if (
                not self._valid(ev)
                or ev.generation != work.generation
                or ev.session_uid != work.answer.evidence.session_uid
                or ev.player_index != work.answer.evidence.player_index
            ):
                return None
            answer = self._render(work.condition.event, ev, work.condition.baseline)
            if answer is None:
                return None
            checked = await adapter.revalidate(ev, deadline_mono=work.expires_mono)
            if (
                not baseline_present()
                or not self._valid(checked)
                or self._mono() >= work.expires_mono
            ):
                return None
            return Answer(
                answer.text,
                answer.kind,
                checked,
                answer.evidence_paths,
                answer.card_ids,
            )

        async def run():
            if self._adapter is not None:
                return await refresh(self._adapter)
            from fastmcp import Client

            async with Client(self.mcp_url) as client:
                return await refresh(self._adapter_for(client))

        return asyncio.run(run())
