"""Hermetic voice safety regressions: no hardware, models, keys, or cloud."""

import sys

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from apps.voice import engineer, tts, voice_controller as vc
from apps.voice.session_tracker import SessionProgressTracker


@pytest.fixture
def controller_env(monkeypatch):
    cfg = dict(engineer.DEFAULT_CONFIG, proactive=False)
    monkeypatch.setattr(vc, "load_config", lambda: cfg)
    monkeypatch.setattr(vc, "select_headset_mic", Mock())
    monkeypatch.setattr(vc, "_pick_device_index", lambda *args: 0)
    monkeypatch.setattr(vc.sr, "Microphone", Mock())
    monkeypatch.setattr(vc, "Speaker", Mock())
    monkeypatch.setattr(vc, "make_engineer", Mock(return_value=Mock()))
    whisper = Mock()
    monkeypatch.setitem(
        sys.modules, "apps.voice.stt", SimpleNamespace(WhisperSTT=whisper)
    )
    return cfg, whisper


def test_local_stt_load_failure_is_explicit(controller_env):
    _, whisper = controller_env
    whisper.side_effect = RuntimeError("missing local model")
    with pytest.raises(RuntimeError, match="(?i)(local|whisper)"):
        vc.VoiceController()


def test_controller_passes_explicit_offline_policy(controller_env):
    controller = vc.VoiceController()
    assert controller.local
    assert vc.Speaker.call_args.kwargs["offline"] is True


def test_cloud_controller_does_not_load_whisper(controller_env):
    cfg, whisper = controller_env
    cfg["backend"] = "cloud"
    controller = vc.VoiceController()
    assert not controller.local
    whisper.assert_not_called()


@pytest.mark.parametrize("piper_voice", ["missing", ""])
def test_local_tts_failure_never_uses_edge(monkeypatch, piper_voice):
    monkeypatch.setattr(tts.Speaker, "_load_piper", Mock())
    speaker = tts.Speaker(piper_voice=piper_voice, offline=True)
    speaker._say_piper = Mock(return_value=False)
    speaker._say_edge = Mock(return_value=True)
    speaker._say_fallback = Mock()
    speaker.say("Radio check")
    speaker._say_edge.assert_not_called()
    speaker._say_fallback.assert_called_once_with("Radio check")
    assert not speaker.speaking.is_set()


def test_explicit_cloud_tts_keeps_edge(monkeypatch):
    monkeypatch.setattr(tts.shutil, "which", lambda name: None)
    speaker = tts.Speaker(offline=False)
    speaker._say_edge = Mock(return_value=True)
    speaker._say_fallback = Mock()
    speaker.say("Radio check")
    speaker._say_edge.assert_called_once()
    speaker._say_fallback.assert_not_called()


@pytest.fixture
def pactl(monkeypatch):
    def setup(sources, default, cards="0 bluez_card.unrelated module\n"):
        monkeypatch.setenv("PULSE_SOURCE", "")
        calls = []

        def run(args, **kwargs):
            calls.append(args[1:])
            output = {
                ("list", "short", "sources"): sources,
                ("get-default-source",): default,
                ("list", "short", "cards"): cards,
            }.get(tuple(args[1:]), "")
            return SimpleNamespace(stdout=output, returncode=0)

        monkeypatch.setattr(vc.shutil, "which", lambda name: "/fake/pactl")
        monkeypatch.setattr(vc.subprocess, "run", run)
        monkeypatch.setattr(vc.time, "sleep", lambda seconds: None)
        return calls

    return setup


def test_absent_headset_preserves_valid_default(pactl):
    calls = pactl(
        "0 alsa_input.usb module\n1 bluez_input.unrelated module\n", "alsa_input.usb"
    )
    vc.select_headset_mic("jabra")
    assert not any(call[0].startswith("set-") for call in calls)


def test_monitor_default_selects_real_input_not_unrelated_bluetooth(pactl):
    calls = pactl(
        "0 alsa_output.speaker.monitor module\n1 bluez_input.other module\n2 alsa_input.usb module\n",
        "alsa_output.speaker.monitor",
    )
    vc.select_headset_mic("jabra")
    assert ["set-default-source", "alsa_input.usb"] in calls
    assert not any(call[0] == "set-card-profile" for call in calls)


def test_only_monitor_or_unrelated_bluetooth_fails_actionably(pactl):
    calls = pactl(
        "0 alsa_output.jabra.monitor module\n1 bluez_input.other module\n",
        "alsa_output.jabra.monitor",
    )
    with pytest.raises(
        RuntimeError, match="(?i)(microphone|input).*(connect|select|configure)"
    ):
        vc.select_headset_mic("jabra")
    assert not any(call[0].startswith("set-") for call in calls)


@pytest.mark.parametrize(
    "listener,worker,expected",
    [
        (True, True, True),
        (True, False, False),
        (False, True, False),
        (False, False, False),
    ],
)
def test_readiness_requires_both_threads(controller_env, listener, worker, expected):
    controller = vc.VoiceController()
    controller._running.set()
    controller._thread = Mock(is_alive=Mock(return_value=listener))
    controller._worker_thread = Mock(is_alive=Mock(return_value=worker))
    assert controller.is_alive is expected


def test_start_stores_worker(controller_env, monkeypatch):
    controller = vc.VoiceController()
    monkeypatch.setattr(vc.threading, "Thread", Mock(side_effect=[Mock(), Mock()]))
    controller.start()
    assert controller._worker_thread is not None
    controller._worker_thread.start.assert_called_once()


@pytest.mark.parametrize("busy", [False, True])
def test_stop_joins_workers_before_cleanup(controller_env, busy):
    controller = vc.VoiceController()
    controller.watcher = Mock()
    controller._thread = Mock(is_alive=Mock(return_value=False))
    controller._worker_thread = Mock(is_alive=Mock(return_value=busy))
    controller._running.set()
    controller.stop()
    controller.watcher.stop.assert_called_once()
    for thread in (controller._thread, controller._worker_thread):
        thread.join.assert_called_once()
        assert 0 < thread.join.call_args.kwargs["timeout"] <= 5
    if busy:
        controller.engineer.close.assert_not_called()
    else:
        controller.engineer.close.assert_called_once()
    assert not controller._running.is_set()


def test_local_engineer_close_releases_loop(monkeypatch):
    monkeypatch.setitem(
        sys.modules, "requests", SimpleNamespace(post=Mock(return_value=Mock()))
    )
    local = engineer.LocalEngineer(
        dict(engineer.DEFAULT_CONFIG), tracker=SessionProgressTracker()
    )
    mcp = Mock()

    async def exit_mcp(*args):
        mcp.closed = True

    mcp.closed = False
    mcp.__aexit__ = exit_mcp
    local._mcp = mcp
    try:
        local.close()
        local.close()
        assert mcp.closed
        assert not local._thread.is_alive()
        assert local._loop.is_closed()
    finally:
        if not local._loop.is_closed():
            local._loop.call_soon_threadsafe(local._loop.stop)


@pytest.mark.parametrize(
    "default,requested,expected",
    [(1, None, 1), (0, None, 1), (0, 0, None), (0, 2, None)],
)
def test_device_selection_rejects_non_inputs(monkeypatch, default, requested, expected):
    devices = [
        dict(name="speaker.monitor", maxInputChannels=2, index=0),
        dict(name="USB microphone", maxInputChannels=1, index=1),
        dict(name="HDMI output", maxInputChannels=0, index=2),
    ]
    audio = Mock()
    audio.get_device_count.return_value = len(devices)
    audio.get_device_info_by_index.side_effect = devices.__getitem__
    audio.get_default_input_device_info.return_value = devices[default]
    monkeypatch.setattr(
        vc.sr.Microphone, "get_pyaudio", lambda: SimpleNamespace(PyAudio=lambda: audio)
    )
    if expected is None:
        with pytest.raises(RuntimeError, match="(?i)(input|microphone)"):
            vc._pick_device_index(requested)
    else:
        assert vc._pick_device_index(requested) == expected
    audio.terminate.assert_called_once()


def test_no_input_devices_fails_without_opening_stream(monkeypatch):
    audio = Mock()
    audio.get_device_count.return_value = 0
    audio.get_default_input_device_info.side_effect = OSError("No default input")
    monkeypatch.setattr(
        vc.sr.Microphone, "get_pyaudio", lambda: SimpleNamespace(PyAudio=lambda: audio)
    )
    with pytest.raises(RuntimeError, match="(?i)(input|microphone)"):
        vc._pick_device_index()
    audio.open.assert_not_called()
    audio.terminate.assert_called_once()


def test_local_engineer_construction_is_lazy(monkeypatch):
    post = Mock(side_effect=RuntimeError("model unavailable"))
    monkeypatch.setitem(sys.modules, "requests", SimpleNamespace(post=post))
    local = engineer.LocalEngineer(
        dict(engineer.DEFAULT_CONFIG), tracker=SessionProgressTracker()
    )
    post.assert_not_called()
    local.close()


def test_source_binding_survives_monitor_default(pactl):
    import os

    pactl(
        "0 alsa_output.speaker.monitor module\n1 alsa_input.front module\n",
        "alsa_output.speaker.monitor",
    )
    vc.select_headset_mic("jabra")
    assert os.environ["PULSE_SOURCE"] == "alsa_input.front"


@pytest.mark.parametrize("exact,expected", [(True, 2), (False, 1)])
def test_bound_microphone_avoids_pipewire_default(monkeypatch, exact, expected):
    monkeypatch.setenv("PULSE_SOURCE", "alsa_input.front")
    devices = [
        dict(name="pipewire", maxInputChannels=2, index=0),
        dict(name="pulse", maxInputChannels=2, index=1),
    ]
    if exact:
        devices.append(dict(name="alsa_input.front", maxInputChannels=2, index=2))
    audio = Mock()
    audio.get_device_count.return_value = len(devices)
    audio.get_device_info_by_index.side_effect = devices.__getitem__
    audio.get_default_input_device_info.return_value = devices[0]
    monkeypatch.setattr(
        vc.sr.Microphone, "get_pyaudio", lambda: SimpleNamespace(PyAudio=lambda: audio)
    )
    assert vc._pick_device_index() == expected


def test_bound_source_without_pulse_route_fails(monkeypatch):
    monkeypatch.setenv("PULSE_SOURCE", "alsa_input.front")
    audio = Mock()
    audio.get_device_count.return_value = 1
    audio.get_device_info_by_index.return_value = dict(
        name="pipewire", maxInputChannels=2, index=0
    )
    audio.get_default_input_device_info.return_value = dict(index=0)
    monkeypatch.setattr(
        vc.sr.Microphone, "get_pyaudio", lambda: SimpleNamespace(PyAudio=lambda: audio)
    )
    with pytest.raises(RuntimeError, match="(?i)(pulse|microphone)"):
        vc._pick_device_index()
