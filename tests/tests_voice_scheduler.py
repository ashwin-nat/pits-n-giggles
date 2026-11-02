"""Hermetic controller/watcher collaboration using the frozen public APIs."""

import asyncio
import threading
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from apps.voice import voice_controller as vc
from apps.voice.contracts import Answer, Evidence
from apps.voice.session_tracker import SessionProgressTracker
from apps.voice.watcher import TelemetryWatcher


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def evidence(topic="tyres", **facts):
    return Evidence(topic, 1, 0, 0, 20, 20, None, facts, (), ())


class Adapter:
    def __init__(self, ev):
        self.ev = ev
        self.collected = []

    async def collect(self, intent, deadline_mono):
        self.collected.append(intent.topic)
        return self.ev

    async def revalidate(self, ev, *, deadline_mono):
        return ev


@pytest.fixture
def controller(monkeypatch):
    import sys
    from apps.voice.engineer import DEFAULT_CONFIG

    monkeypatch.setattr(
        vc, "load_config", lambda: dict(DEFAULT_CONFIG, proactive=False)
    )
    monkeypatch.setattr(vc, "select_headset_mic", Mock())
    monkeypatch.setattr(vc, "_pick_device_index", lambda *_: 0)
    monkeypatch.setattr(vc.sr, "Microphone", Mock())
    monkeypatch.setattr(vc, "Speaker", Mock())
    monkeypatch.setitem(
        sys.modules, "apps.voice.stt", SimpleNamespace(WhisperSTT=Mock())
    )
    engineer = Mock()
    monkeypatch.setattr(vc, "make_engineer", Mock(return_value=engineer))
    clock = Clock()
    obj = vc.VoiceController(mono_clock=clock)
    obj._speak = Mock()
    return obj, clock, engineer


def test_shared_tracker_even_without_proactive(controller):
    obj, _, _ = controller
    assert obj.watcher.tracker is obj.tracker
    assert obj.watcher.proactive is False
    assert vc.make_engineer.call_args.kwargs["tracker"] is obj.tracker


def test_new_question_cancels_active_context(controller):
    obj, _, engineer = controller
    cancelled = threading.Event()
    obj._active = ("old", cancelled)
    assert obj.submit_question("fuel?")
    assert cancelled.is_set()
    engineer.cancel_request.assert_called_once_with("old")


def test_question_quota_busy_is_coalesced(controller):
    obj, _, _ = controller
    for _ in range(4):
        assert obj.submit_question("fuel?")
    for _ in range(3):
        assert not obj.submit_question("extra")
    assert obj._busy_pending
    obj.process_next()
    assert not obj._busy_pending
    assert obj._speak.call_count <= 1


def test_generation_reset_cancels_and_clears(controller):
    obj, _, engineer = controller
    obj.submit_question("fuel?")
    cancelled = threading.Event()
    obj._active = ("old", cancelled)
    obj.tracker.invalidate("disconnect")
    obj.reset_session(None, 1)
    assert cancelled.is_set()
    assert obj._work.take(now_mono=0) is None
    engineer.reset_session.assert_called_once_with(None, 1)


def test_revalidation_immediately_before_speech(controller):
    obj, _, engineer = controller
    answer = Answer("original", "fact", evidence(), (), ())
    fresh = replace(answer, text="checked")
    engineer.ask_stream.return_value = iter([answer])
    engineer.revalidate_answer.return_value = fresh
    obj.submit_question("tyres?")
    obj.process_next()
    obj._speak.assert_called_once_with("checked")
    request = engineer.ask_stream.call_args.kwargs["request"]
    assert engineer.revalidate_answer.call_args.kwargs["request"] is request


def test_cancel_during_revalidation_drops_speech(controller):
    obj, _, engineer = controller
    answer = Answer("old", "fact", evidence(), (), ())
    engineer.ask_stream.return_value = iter([answer])

    def revalidate(answer, *, request):
        obj.submit_question("new")
        assert request.cancelled()
        return answer

    engineer.revalidate_answer.side_effect = revalidate
    obj.submit_question("old")
    obj.process_next()
    obj._speak.assert_not_called()


def test_local_legacy_string_never_speaks(controller):
    obj, _, engineer = controller
    engineer.ask_stream.return_value = iter(["unsafe legacy"])
    obj.submit_question("tyres?")
    obj.process_next()
    obj._speak.assert_not_called()


@pytest.mark.parametrize("wear,expected", [(78, False), (80, False), (81, True)])
async def test_wear_threshold(wear, expected):
    clock = Clock()
    adapter = Adapter(evidence(get_player_tyre_wear={"fl_wear_pct": wear}))
    fired = []
    watcher = TelemetryWatcher(
        "unused",
        fired.append,
        tracker=SessionProgressTracker(),
        mono_clock=clock,
        adapter=adapter,
    )
    await watcher.evaluate(adapter.ev)
    assert bool(fired) is expected


async def test_wear_hysteresis():
    fired = []
    watcher = TelemetryWatcher(
        "unused", fired.append, tracker=SessionProgressTracker(), mono_clock=Clock()
    )
    for wear in (81, 79, 81, 78, 81):
        await watcher.evaluate(evidence(get_player_tyre_wear={"fl_wear_pct": wear}))
    assert len(fired) == 2


async def test_fuel_hysteresis():
    fired = []
    watcher = TelemetryWatcher(
        "unused", fired.append, tracker=SessionProgressTracker(), mono_clock=Clock()
    )
    for surplus in (-0.3, -0.1, -0.3, 0, -0.3):
        await watcher.evaluate(
            evidence("fuel", get_player_fuel_info={"surplus_laps_live": surplus})
        )
    assert len(fired) == 2


async def test_refresh_rerenders_current_values():
    clock = Clock()
    adapter = Adapter(evidence(get_player_tyre_wear={"fl_wear_pct": 85}))
    fired = []
    watcher = TelemetryWatcher(
        "unused",
        fired.append,
        tracker=SessionProgressTracker(),
        mono_clock=clock,
        adapter=adapter,
    )
    await watcher.evaluate(adapter.ev)
    adapter.ev = evidence(get_player_tyre_wear={"fl_wear_pct": 91})
    answer = await asyncio.to_thread(watcher.refresh_callout, fired[0])
    # refresh is synchronous for the controller's plain worker thread.
    assert "91" in answer.text
    adapter.ev = evidence(get_player_tyre_wear={"fl_wear_pct": 78})
    assert await asyncio.to_thread(watcher.refresh_callout, fired[0]) is None


async def test_change_requires_baseline():
    fired = []
    watcher = TelemetryWatcher(
        "unused", fired.append, tracker=SessionProgressTracker(), mono_clock=Clock()
    )
    for status in ("NONE", "FULL"):
        await watcher.evaluate(
            evidence(
                "weather",
                get_session_info={
                    "race_control": {"safety_car_status": status},
                    "environment": {},
                },
            )
        )
    assert len(fired) == 1
    assert fired[0].condition.baseline["previous"] == "NONE"


async def test_independent_lightweight_sampling():
    clock = Clock()
    tracker = SessionProgressTracker()
    client = Mock()

    async def call(*args, **kwargs):
        return SimpleNamespace(
            structured_content={
                "connected": True,
                "available": True,
                "ok": True,
                "last-update-timestamp": clock.now,
                "identity": {"session_uid": 1},
                "progress": {"duration_elapsed_sec": clock.now},
            }
        )

    client.call_tool = Mock(side_effect=call)
    watcher = TelemetryWatcher(
        "unused",
        Mock(),
        tracker=tracker,
        proactive=False,
        mono_clock=clock,
        epoch_clock=clock,
    )
    await watcher.poll_once(client)
    clock.now = 1
    await watcher.poll_once(client)
    assert [c.args[0] for c in client.call_tool.call_args_list] == [
        "get_session_info",
        "get_session_info",
    ]
    assert watcher._session_reason is None


def test_expired_question_never_infers(controller):
    obj, clock, engineer = controller
    obj.submit_question("old")
    clock.now = 10
    obj.process_next()
    engineer.ask_stream.assert_not_called()


def test_queue_lock_not_held_during_inference(controller):
    obj, _, engineer = controller

    def stream(question, *, request):
        done = threading.Event()
        thread = threading.Thread(
            target=lambda: (obj.submit_question("new"), done.set())
        )
        thread.start()
        assert done.wait(1)
        thread.join()
        return iter(())

    engineer.ask_stream.side_effect = stream
    obj.submit_question("old")
    obj.process_next()


async def test_refresh_drops_lost_change_baseline():
    clock = Clock()
    adapter = Adapter(
        evidence(
            "weather",
            get_session_info={
                "race_control": {"safety_car_status": "NONE"},
                "environment": {},
            },
        )
    )
    fired = []
    watcher = TelemetryWatcher(
        "unused",
        fired.append,
        tracker=SessionProgressTracker(),
        mono_clock=clock,
        adapter=adapter,
    )
    await watcher.evaluate(adapter.ev)
    adapter.ev = evidence(
        "weather",
        get_session_info={
            "race_control": {"safety_car_status": "FULL"},
            "environment": {},
        },
    )
    await watcher.evaluate(adapter.ev)
    await watcher.evaluate(replace(adapter.ev, reason="unavailable"))
    assert await asyncio.to_thread(watcher.refresh_callout, fired[0]) is None


async def test_refresh_revalidation_reason_is_not_truthiness():
    clock = Clock()
    adapter = Adapter(evidence(get_player_tyre_wear={"fl_wear_pct": 85}))
    fired = []
    watcher = TelemetryWatcher(
        "unused",
        fired.append,
        tracker=SessionProgressTracker(),
        mono_clock=clock,
        adapter=adapter,
    )
    await watcher.evaluate(adapter.ev)

    async def reject(ev, *, deadline_mono):
        return replace(ev, reason="expired")

    adapter.revalidate = reject
    assert await asyncio.to_thread(watcher.refresh_callout, fired[0]) is None


@pytest.mark.parametrize("generation,now", [(1, 0), (0, 3)])
async def test_refresh_rejects_original_generation_or_ttl(generation, now):
    clock = Clock()
    tracker = SessionProgressTracker()
    adapter = Adapter(evidence(get_player_tyre_wear={"fl_wear_pct": 85}))
    fired = []
    watcher = TelemetryWatcher(
        "unused", fired.append, tracker=tracker, mono_clock=clock, adapter=adapter
    )
    await watcher.evaluate(adapter.ev)
    clock.now = now
    if generation:
        tracker.invalidate("disconnect")
    assert await asyncio.to_thread(watcher.refresh_callout, fired[0]) is None
    assert adapter.collected == []


async def test_slow_callout_collection_does_not_block_session_sampler(monkeypatch):
    from apps.voice import watcher as module

    clock = Clock()
    entered = asyncio.Event()
    release = asyncio.Event()
    sampled = asyncio.Event()
    adapter = Adapter(evidence())

    async def collect(intent, deadline_mono):
        entered.set()
        await release.wait()
        return replace(adapter.ev, reason="test complete")

    adapter.collect = collect
    watcher = TelemetryWatcher(
        "unused",
        Mock(),
        tracker=SessionProgressTracker(),
        mono_clock=clock,
        epoch_clock=clock,
        adapter=adapter,
    )
    calls = []

    async def call(*args, **kwargs):
        calls.append(clock.now)
        if len(calls) == 2:
            sampled.set()
        return SimpleNamespace(
            structured_content={
                "connected": True,
                "available": True,
                "ok": True,
                "last-update-timestamp": clock.now,
                "identity": {"session_uid": 1},
                "progress": {"duration_elapsed_sec": clock.now},
            }
        )

    sleep = asyncio.sleep

    async def advance(seconds):
        clock.now += seconds
        await sleep(0)

    monkeypatch.setattr(module.asyncio, "sleep", advance)
    session_client = SimpleNamespace(call_tool=call)
    topics = asyncio.create_task(watcher._callout_loop(object()))
    await entered.wait()
    sampler = asyncio.create_task(watcher._sampling_loop(session_client))
    await asyncio.wait_for(sampled.wait(), 1)
    watcher.stop()
    release.set()
    await asyncio.gather(topics, sampler)
    assert calls[1] - calls[0] == 1
    assert watcher._session_reason is None


def test_each_chunk_rechecks_deadline(controller):
    obj, clock, engineer = controller
    answer = Answer("one", "fact", evidence(), (), ())

    def stream(question, *, request):
        yield answer
        clock.now = 10
        yield replace(answer, text="two")

    engineer.ask_stream.side_effect = stream
    engineer.revalidate_answer.side_effect = lambda answer, **kw: answer
    obj.submit_question("test")
    obj.process_next()
    obj._speak.assert_called_once_with("one")


def test_revalidation_none_discards_answer(controller):
    obj, _, engineer = controller
    engineer.ask_stream.return_value = iter([Answer("old", "fact", evidence(), (), ())])
    engineer.revalidate_answer.return_value = None
    obj.submit_question("test")
    obj.process_next()
    obj._speak.assert_not_called()


def test_rejected_question_does_not_cancel_active(controller):
    obj, _, engineer = controller
    for i in range(4):
        obj.submit_question(str(i))
    cancelled = threading.Event()
    obj._active = ("active", cancelled)
    assert not obj.submit_question("overflow")
    assert not cancelled.is_set()
    engineer.cancel_request.assert_not_called()


def test_timing_logs_label_proxy_not_first_audio(controller, caplog):
    obj, clock, engineer = controller
    answer = Answer("one", "fact", evidence(), (), ())
    engineer.ask_stream.return_value = iter([answer])
    engineer.revalidate_answer.return_value = answer
    with caplog.at_level("INFO"):
        obj.submit_question("test")
        clock.now = 1
        obj.process_next()
    assert "queue_wait=1.000" in caplog.text
    assert "first_text" in caplog.text
    assert "physical_first_audio=unmeasured" in caplog.text
    assert "first_audio_duration" not in caplog.text
