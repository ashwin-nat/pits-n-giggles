"""Hermetic Step0 gates; real MCP readers run over synthetic cache entries."""

import asyncio
import importlib
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError, fields, replace
from types import SimpleNamespace

import pytest


class Clock:
    def __init__(self):
        self.epoch = 1000.0
        self.mono = 10.0

    def advance(self, seconds):
        self.epoch += seconds
        self.mono += seconds


@pytest.fixture
def api():
    from apps.voice import contracts
    from apps.voice.session_tracker import SessionProgressTracker
    from apps.voice.telemetry import TelemetryAdapter

    return contracts, SessionProgressTracker, TelemetryAdapter


@pytest.fixture
def readers(monkeypatch):
    root = "apps.mcp_server.mcp_server.tools."
    common = importlib.import_module(root + "common")
    session = importlib.import_module(root + "get_session_info")
    table = importlib.import_module(root + "get_race_table")
    tyre = importlib.import_module(root + "get_tyre_wear")
    fuel = importlib.import_module(root + "get_fuel_info")
    clock = Clock()
    row = {
        "driver-info": {
            "index": 3,
            "name": "Driver",
            "position": 2,
            "is-player": True,
            "dnf-status": "",
        },
        "tyre-info": {
            "visual-tyre-compound": "Medium",
            "tyre-age": 4,
            "current-wear": {"average": 12, "front-left-wear": 13},
        },
        "fuel-info": {
            "fuel-in-tank": 0.0,
            "surplus-laps-game": 0.0,
            "current-fuel-rate": 2.1,
        },
    }
    raw = {
        "session-uid": 42,
        "event-type": "Race",
        "race-ended": False,
        "is-spectating": False,
        "session-duration-so-far": 20.0,
        "session-time-left": 100.0,
        "table-entries": [row],
        "weather-forecast-samples": [],
    }
    entry = SimpleNamespace(data=raw, ts=clock.epoch)
    connected = SimpleNamespace(data=True)
    monkeypatch.setattr(
        common,
        "get_state_data",
        lambda key, *args: entry if key == "race-table-update" else connected,
    )
    logger = logging.getLogger(__name__)
    builders = {
        "get_session_info": lambda: session.get_session_info(logger),
        "get_race_table": lambda: table.get_race_table(logger),
        "get_player_tyre_wear": lambda: tyre.get_tyre_wear(logger, 3),
        "get_player_fuel_info": lambda: fuel.get_fuel_info(logger, 3),
    }

    class Client:
        def __init__(self):
            self.calls = []
            self.hook = None

        async def call_tool(self, tool, args, raise_on_error=False):
            self.calls.append(tool)
            await asyncio.sleep(0)
            if self.hook:
                self.hook(tool)
            return SimpleNamespace(structured_content=builders[tool]())

    return SimpleNamespace(
        clock=clock,
        raw=raw,
        row=row,
        entry=entry,
        connected=connected,
        client=Client(),
        builders=builders,
    )


def adapter(api, readers, tracker=None):
    c, tracker_type, adapter_type = api
    tracker = tracker if tracker is not None else tracker_type()
    return (
        adapter_type(
            readers.client,
            tracker,
            epoch_clock=lambda: readers.clock.epoch,
            mono_clock=lambda: readers.clock.mono,
        ),
        tracker,
        c,
    )


async def primed(api, readers, topic="weather"):
    a, tracker, c = adapter(api, readers)
    first = await a.collect(c.Intent(topic), 12)
    assert first.reason is not None
    readers.clock.advance(0.1)
    readers.entry.ts = readers.clock.epoch
    readers.raw["session-duration-so-far"] += 0.1
    readers.raw["session-time-left"] -= 0.1
    evidence = await a.collect(c.Intent(topic), 12)
    return a, tracker, c, evidence


def test_frozen_exact_contracts(api):
    c, _, _ = api
    assert [f.name for f in fields(c.Evidence)] == [
        "topic",
        "session_uid",
        "generation",
        "player_index",
        "expires_mono",
        "progress_valid_until_mono",
        "reason",
        "facts",
        "sources",
        "stamps",
    ]
    original = {"nested": [{"set": {1, 2}}]}
    condition = c.CalloutCondition("weather", original)
    original["nested"].clear()
    assert condition.baseline["nested"][0]["set"] == frozenset({1, 2})
    with pytest.raises(TypeError):
        condition.baseline["new"] = 1
    with pytest.raises(FrozenInstanceError):
        condition.event = "fuel_deficit"
    with pytest.raises(TypeError):
        c.CalloutCondition("weather", {"bad": bytearray(b"a")})
    card = c.KnowledgeCard(
        "a",
        ["weather"],
        "text",
        "source",
        "general",
        "all",
        [],
        "2026-10-16",
        "non-live",
    )
    assert card.topics == ("weather",)
    assert card.game_seasons == ()


async def test_reader_backed_fuel_zero_no_phantom_estimates(api, readers):
    _, _, _, e = await primed(api, readers, "fuel")
    assert e.reason is None
    facts = e.facts["get_player_fuel_info"]
    assert facts["fuel_in_tank_kg"] == 0
    assert facts["surplus_laps_builtin"] == 0
    assert facts["data_sufficient"] is False
    assert "avg_burn_rate_kg_per_lap" not in facts
    assert "get_player_tyre_wear" not in e.facts
    assert len(e.stamps) == 4
    assert e.stamps[0].tool == e.stamps[-1].tool == "get_session_info"
    assert e.expires_mono == pytest.approx(12.1)


@pytest.mark.parametrize("topic", ["weather", "tyres", "gaps", "pit"])
async def test_topics_reader_backed(api, readers, topic):
    _, _, _, e = await primed(api, readers, topic)
    assert e.reason is None
    assert e.player_index == 3
    assert e.session_uid == 42
    assert "delta_to_leader_ms" not in repr(e.facts)
    assert "pit_window" not in repr(e.facts)
    with pytest.raises(TypeError):
        e.facts["x"] = 2


@pytest.mark.parametrize(
    "age,accepted",
    [
        (0, True),
        (2, False),
        (2.001, False),
        (-0.01, False),
        (float("nan"), False),
        (float("inf"), False),
        (True, False),
    ],
)
async def test_receipt_age_boundaries(api, readers, age, accepted):
    a, _, c, _ = await primed(api, readers)
    readers.entry.ts = True if age is True else readers.clock.epoch - age
    e = await a.collect(c.Intent("weather"), 12)
    assert (e.reason is None) is accepted


async def test_revalidation_never_renews(api, readers):
    a, _, _, e = await primed(api, readers)
    assert await a.revalidate(e, 12) is e
    readers.clock.advance(0.2)
    readers.entry.ts = readers.clock.epoch
    readers.raw["session-duration-so-far"] += 1
    assert await a.revalidate(e, 12) is e
    readers.clock.advance(2)
    invalid = await a.revalidate(e, 20)
    assert invalid.reason
    assert replace(invalid, reason=None) == e
    assert await a.revalidate(invalid, 20) is invalid


async def test_completion_clock_sampling(api, readers):
    a, _, c, _ = await primed(api, readers)
    readers.client.hook = lambda tool: readers.clock.advance(0.8)
    e = await a.collect(c.Intent("weather"), 20)
    assert e.reason
    assert any(s.collected_mono > 10.1 for s in e.stamps)


@pytest.mark.parametrize(
    "change",
    ["disconnect", "ended", "spectator", "uid", "player", "status", "timestamp"],
)
async def test_fail_closed(api, readers, change):
    a, _, c, original = await primed(api, readers, "tyres")
    if change == "disconnect":
        readers.connected.data = False
    elif change == "ended":
        readers.raw["race-ended"] = True
    elif change == "spectator":
        readers.raw["is-spectating"] = True
    elif change == "uid":
        readers.raw["session-uid"] = 44
    elif change == "player":
        readers.row["driver-info"]["is-player"] = False
    elif change == "status":
        readers.builders["get_player_tyre_wear"] = lambda: {
            "available": True,
            "connected": True,
            "ok": False,
            "last-update-timestamp": readers.entry.ts,
        }
    else:
        build = readers.builders["get_player_tyre_wear"]
        readers.builders["get_player_tyre_wear"] = lambda: {
            **build(),
            "last-update-timestamp": readers.entry.ts - 0.01,
        }
    assert (await a.revalidate(original, 12)).reason
    assert (await a.collect(c.Intent("tyres"), 12)).reason


async def test_clock_jump(api, readers):
    a, _, c, _ = await primed(api, readers)
    readers.client.hook = lambda tool: setattr(
        readers.clock, "epoch", readers.clock.epoch + 0.5
    )
    assert (await a.collect(c.Intent("weather"), 12)).reason


def test_tracker_order_disconnect_rollover(api):
    c, tracker_type, _ = api
    t = tracker_type()

    def observe(uid, progress, epoch, mono):
        return t.observe(
            {
                "identity": {"session_uid": uid},
                "progress": {"duration_elapsed_sec": progress},
            },
            stamp=c.SourceStamp("get_session_info", epoch, mono),
        )

    g, _, reason = observe(42, 1, 1000, 10)
    assert reason
    assert observe(42, 2, 1001, 11) == (g, 14, None)
    assert observe(43, 0, 999, 12)[2]
    assert t.current_generation() == g
    assert observe(42, 2, 1001, 11) == (g, 14, None)
    assert observe(42, 1, 1002, 12)[2]
    disconnected = t.invalidate("disconnected")
    assert t.invalidate("disconnected") == disconnected
    assert observe(42, 4, 1002, 12)[2]
    assert observe(42, 4, 1003, 13)[2]
    assert observe(42, 5, 1004, 14) == (disconnected, 17, None)
    assert observe(43, 0, 1005, 15)[0] == disconnected + 1


def test_tracker_concurrent_atomic_generation(api):
    c, tracker_type, _ = api
    t = tracker_type()
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: t.invalidate("disconnect"), range(100)))
    assert len(set(results)) == 1
    assert t.current_generation() == results[0]
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(
            pool.map(
                lambda i: t.observe(
                    {
                        "identity": {"session_uid": 42},
                        "progress": {"duration_elapsed_sec": i},
                    },
                    stamp=c.SourceStamp("get_session_info", 1000 + i, 10 + i),
                ),
                range(100),
            )
        )
    assert t.current_generation() == results[0]


async def test_frozen_progress_no_watcher(api, readers):
    a, _, c, e = await primed(api, readers)
    readers.clock.advance(3.1)
    readers.entry.ts = readers.clock.epoch
    assert (await a.collect(c.Intent("weather"), 20)).reason
    assert (await a.revalidate(e, 20)).reason


async def test_shared_tracker_player_change_invalidates(api, readers):
    a, tracker, c, original = await primed(api, readers)
    readers.row["driver-info"]["index"] = 4
    readers.clock.advance(0.1)
    readers.entry.ts = readers.clock.epoch
    readers.raw["session-duration-so-far"] += 0.1
    other, _, _ = adapter(api, readers, tracker)
    changed = await other.collect(c.Intent("weather"), 12)
    assert changed.reason
    assert tracker.current_generation() > original.generation
    assert (await a.revalidate(original, 12)).reason


def test_tracker_regression_does_not_lower_high_watermark(api):
    c, tracker_type, _ = api
    tracker = tracker_type()

    def observe(value, second):
        return tracker.observe(
            {
                "identity": {"session_uid": 42},
                "progress": {"duration_elapsed_sec": value},
            },
            stamp=c.SourceStamp("get_session_info", 1000 + second, second),
        )

    observe(20, 1)
    assert observe(21, 2)[2] is None
    assert observe(10, 3)[2]
    assert observe(11, 4)[2]


async def test_malformed_table_fails_closed(api, readers):
    a, _, c, _ = await primed(api, readers)
    build = readers.builders["get_race_table"]
    readers.builders["get_race_table"] = lambda: {**build(), "identity": None}
    assert (await a.collect(c.Intent("weather"), 12)).reason


def test_tracker_equal_cache_still_orders_completions(api):
    c, tracker_type, _ = api
    t = tracker_type()
    session = {"identity": {"session_uid": 42}, "progress": {"duration_elapsed_sec": 1}}
    t.observe(session, stamp=c.SourceStamp("session", 1000, 10))
    t.observe(session, stamp=c.SourceStamp("session", 1000, 12))
    assert t.observe(session, stamp=c.SourceStamp("session", 1001, 11))[2]
    assert t.observe(
        {**session, "connected": False}, stamp=c.SourceStamp("session", 1000, 13)
    )[2]
    assert t.current_generation() == 1


async def test_earliest_receipt_owns_expiry(api, readers):
    a, _, c, _ = await primed(api, readers, "fuel")
    first_epoch = readers.entry.ts

    def advance_after_first(tool):
        if tool == "get_race_table":
            readers.clock.advance(0.4)
            readers.entry.ts = readers.clock.epoch
            readers.raw["session-duration-so-far"] += 0.4

    readers.client.hook = advance_after_first
    e = await a.collect(c.Intent("fuel"), 12)
    assert e.reason is None
    assert e.stamps[0].cache_received_epoch == first_epoch
    assert e.stamps[1].cache_received_epoch > first_epoch
    assert e.expires_mono == pytest.approx(12.1)
    assert len(e.sources) > 0
    assert "get_player_fuel_info.fuel_in_tank_kg" in e.sources


async def test_torn_flat_retries_once(api, readers):
    a, _, c, _ = await primed(api, readers, "tyres")
    build = readers.builders["get_player_tyre_wear"]
    calls = []

    def torn_once():
        calls.append(1)
        payload = build()
        if len(calls) == 1:
            payload["driver_index"] = 9
        return payload

    readers.builders["get_player_tyre_wear"] = torn_once
    e = await a.collect(c.Intent("tyres"), 12)
    assert e.reason is None
    assert len(calls) == 2
    assert len(e.stamps) == 8


async def test_deadline_no_calls(api, readers):
    a, _, c = adapter(api, readers)
    e = await a.collect(c.Intent("weather"), 10)
    assert e.reason
    assert not readers.client.calls


async def test_reader_exception_refuses(api, readers):
    a, _, c = adapter(api, readers)

    def broken(tool):
        raise RuntimeError("offline")

    readers.client.hook = broken
    assert (await a.collect(c.Intent("weather"), 12)).reason


def test_tracker_requires_recent_progress_pair(api):
    c, tracker_type, _ = api
    t = tracker_type()
    for elapsed, mono in [(1, 1), (2, 10)]:
        result = t.observe(
            {
                "identity": {"session_uid": 42},
                "progress": {"duration_elapsed_sec": elapsed},
            },
            stamp=c.SourceStamp("session", 1000 + mono, mono),
        )
        assert result[2]


async def test_duplicate_driver_index_refuses(api, readers):
    a, _, c, _ = await primed(api, readers)
    readers.raw["table-entries"].append(
        {"driver-info": {"index": 3, "is-player": False, "position": 3}}
    )
    assert (await a.collect(c.Intent("weather"), 12)).reason


async def test_missing_progress_refuses_even_with_previous_validity(api, readers):
    a, _, c, _ = await primed(api, readers)
    readers.clock.advance(0.1)
    readers.entry.ts = readers.clock.epoch
    readers.raw["session-duration-so-far"] = True
    readers.raw["session-time-left"] = float("nan")
    assert (await a.collect(c.Intent("weather"), 12)).reason


async def test_facts_exclude_unknown_session_fields(api, readers):
    a, _, c, _ = await primed(api, readers)
    build = readers.builders["get_session_info"]

    def expanded():
        data = build()
        data["identity"]["unsupported"] = "not evidence"
        return data

    readers.builders["get_session_info"] = expanded
    e = await a.collect(c.Intent("weather"), 12)
    assert e.reason is None
    assert "unsupported" not in e.facts["get_session_info"]["identity"]


async def test_malformed_environment_refuses(api, readers):
    a, _, c, _ = await primed(api, readers)
    build = readers.builders["get_session_info"]
    readers.builders["get_session_info"] = lambda: {**build(), "environment": None}
    assert (await a.collect(c.Intent("weather"), 12)).reason


@pytest.mark.parametrize("missing", [None, float("nan"), float("inf"), True, -1])
@pytest.mark.parametrize("counter", [0, 1], ids=["elapsed", "remaining"])
def test_tracker_preserves_each_counter_watermark(api, missing, counter):
    c, tracker_type, _ = api
    tracker = tracker_type()
    observations = [(20, 100), (21, 99)]
    observations.append((missing, 98) if counter == 0 else (22, missing))
    observations.append((10, 97) if counter == 0 else (23, 110))
    for second, (elapsed, remaining) in enumerate(observations):
        result = tracker.observe(
            {
                "identity": {"session_uid": 42},
                "progress": {
                    "duration_elapsed_sec": elapsed,
                    "time_remaining_sec": remaining,
                },
            },
            stamp=c.SourceStamp("get_session_info", 1000 + second, 10 + second),
        )
        if second in (1, 2):
            assert result[2] is None
    assert result[1] == 0.0
    assert result[2] == "Session progress regressed"


@pytest.mark.parametrize("tool", ["get_session_info", "get_race_table"])
@pytest.mark.parametrize("age", [0.2, 2.001], ids=["out_of_order", "expired"])
async def test_stale_disconnect_cannot_invalidate_newer_connected(
    api, readers, tool, age
):
    a, tracker, c, _ = await primed(api, readers)
    readers.raw["session-uid"] = 43
    readers.clock.advance(0.1)
    readers.entry.ts = readers.clock.epoch
    assert (await a.collect(c.Intent("weather"), 12)).reason is not None
    readers.clock.advance(0.1)
    readers.entry.ts = readers.clock.epoch
    readers.raw["session-duration-so-far"] += 0.1
    newer = await a.collect(c.Intent("weather"), 12)
    assert newer.reason is None
    generation = tracker.current_generation()
    build = readers.builders[tool]
    delayed = {
        **build(),
        "connected": False,
        "last-update-timestamp": readers.clock.epoch - age,
    }
    readers.builders[tool] = lambda: delayed
    refused = await a.collect(c.Intent("weather"), 12)
    assert refused.reason is not None
    assert tracker.current_generation() == generation
    readers.builders[tool] = build
    assert await a.revalidate(newer, 12) is newer


@pytest.mark.parametrize("missing", [None, float("nan"), float("inf"), True, -1])
@pytest.mark.parametrize("counter", [0, 1], ids=["elapsed", "remaining"])
def test_tracker_missing_counter_cannot_refresh_advance_pair(api, missing, counter):
    c, tracker_type, _ = api
    tracker = tracker_type()
    observations = (
        [(1, 100, 1), (missing, 100, 10), (2, 100, 11), (3, 100, 12)]
        if counter == 0
        else [(1, 100, 1), (1, missing, 10), (1, 99, 11), (1, 98, 12)]
    )
    for elapsed, remaining, mono in observations:
        generation, valid_until, reason = tracker.observe(
            {
                "identity": {"session_uid": 42},
                "progress": {
                    "duration_elapsed_sec": elapsed,
                    "time_remaining_sec": remaining,
                },
            },
            stamp=c.SourceStamp("get_session_info", 1000 + mono, mono),
        )
        assert generation == 0
        if mono == 11:
            assert reason == "Session progress frozen or not yet demonstrated"
            assert valid_until == 0.0
        elif mono == 12:
            assert reason is None
            assert valid_until == 15.0


@pytest.mark.parametrize("counter", [0, 1], ids=["elapsed", "remaining"])
@pytest.mark.parametrize("gap,accepted", [(3.0, True), (3.001, False)])
def test_tracker_counter_pair_age_boundary(api, counter, gap, accepted):
    c, tracker_type, _ = api
    tracker = tracker_type()
    for value, mono in [(1, 1), (2, 1 + gap)]:
        _, _, reason = tracker.observe(
            {
                "identity": {"session_uid": 42},
                "progress": {
                    "duration_elapsed_sec": value if counter == 0 else None,
                    "time_remaining_sec": 100 - value if counter == 1 else None,
                },
            },
            stamp=c.SourceStamp("get_session_info", 1000 + mono, mono),
        )
    assert (reason is None) is accepted


async def test_snapshot_compatibility(readers):
    from apps.voice.telemetry import snapshot

    text = await snapshot(readers.client, "weather")
    assert isinstance(text, str)
    assert "SESSION:" in text
