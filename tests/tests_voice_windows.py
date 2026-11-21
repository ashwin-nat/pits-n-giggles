"""Windows/frozen-build regressions: model lookup and Piper playback without pw-play."""

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from apps.voice import paths, tts


def test_voice_home_defaults_to_repo_root(monkeypatch):
    monkeypatch.delenv("PNG_VOICE_HOME", raising=False)
    monkeypatch.delattr(sys, "frozen", raising=False)
    assert paths.voice_home() == Path(paths.__file__).resolve().parents[2]


def test_voice_home_uses_executable_folder_when_frozen(monkeypatch, tmp_path):
    monkeypatch.delenv("PNG_VOICE_HOME", raising=False)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(tmp_path / "pits_n_giggles.exe"))
    assert paths.voice_home() == tmp_path.resolve()
    assert paths.models_dir("piper") == tmp_path.resolve() / "models" / "piper"


def test_voice_home_env_override_wins(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setenv("PNG_VOICE_HOME", str(tmp_path))
    assert paths.models_dir("whisper") == tmp_path.resolve() / "models" / "whisper"


def _speaker_without_pcm_player(monkeypatch):
    monkeypatch.setattr(tts.shutil, "which", lambda _name: None)
    speaker = tts.Speaker()
    chunk = SimpleNamespace(sample_rate=22050, audio_int16_bytes=b"\x00\x01" * 64)
    speaker._piper = Mock(synthesize=Mock(return_value=[chunk, chunk]))
    return speaker


def test_piper_plays_through_pyaudio_without_pcm_player(monkeypatch):
    stream = Mock()
    audio = Mock(open=Mock(return_value=stream))
    fake = SimpleNamespace(paInt16=8, PyAudio=Mock(return_value=audio))
    monkeypatch.setitem(sys.modules, "pyaudio", fake)
    speaker = _speaker_without_pcm_player(monkeypatch)
    fallback = Mock()
    monkeypatch.setattr(speaker, "_say_fallback", fallback)

    speaker.say("Box this lap.")

    audio.open.assert_called_once_with(format=8, channels=1, rate=22050, output=True)
    assert stream.write.call_count == 2
    stream.close.assert_called_once()
    audio.terminate.assert_called_once()
    fallback.assert_not_called()


def test_pyaudio_failure_falls_back_to_system_voice(monkeypatch):
    audio = Mock(open=Mock(side_effect=OSError("no output device")))
    fake = SimpleNamespace(paInt16=8, PyAudio=Mock(return_value=audio))
    monkeypatch.setitem(sys.modules, "pyaudio", fake)
    speaker = _speaker_without_pcm_player(monkeypatch)
    fallback = Mock()
    monkeypatch.setattr(speaker, "_say_fallback", fallback)

    speaker.say("Box this lap.")

    fallback.assert_called_once_with("Box this lap.")
    audio.terminate.assert_called_once()


def _fake_audio(monkeypatch, devices, default_input=None, default_api=0):
    from apps.voice import voice_controller as vc

    audio = Mock()
    audio.get_device_count.return_value = len(devices)
    audio.get_device_info_by_index.side_effect = devices.__getitem__
    if default_input is None:
        audio.get_default_input_device_info.side_effect = OSError("No Default Input Device")
    else:
        audio.get_default_input_device_info.return_value = devices[default_input]
    audio.get_default_host_api_info.return_value = {"index": default_api}
    monkeypatch.setattr(
        vc.sr.Microphone, "get_pyaudio", lambda: SimpleNamespace(PyAudio=lambda: audio)
    )
    monkeypatch.delenv("PULSE_SOURCE", raising=False)
    return vc, audio


# What PyAudio reported on the user's Windows PC (trimmed), across two host APIs.
WINDOWS_INPUTS = [
    dict(name="Microsoft Sound Mapper - Input", maxInputChannels=2, hostApi=0, index=0),
    dict(name="Stereo Mix (Realtek HD Audio Stereo input)", maxInputChannels=2, hostApi=0, index=1),
    dict(name="Microphone (Realtek HD Audio Mic input)", maxInputChannels=2, hostApi=0, index=2),
    dict(name="Headset (Galaxy Buds+ (24A2))", maxInputChannels=1, hostApi=0, index=3),
    dict(name="Headset (Jabra Evolve2 85)", maxInputChannels=1, hostApi=0, index=4),
    dict(name="Speakers (Realtek HD Audio)", maxInputChannels=0, hostApi=0, index=5),
    dict(name="Headset (@System32\\drivers\\bthhfenum.sys,#2;%1 Hands-Free%0\r\n;(Jabra Evolve2 85))",
         maxInputChannels=1, hostApi=3, index=6),
]


def test_windows_mic_selected_by_name_without_default(monkeypatch):
    vc, audio = _fake_audio(monkeypatch, WINDOWS_INPUTS)
    assert vc._pick_device_index(None, "jabra") == 4
    audio.terminate.assert_called_once()


def test_name_match_prefers_default_host_api(monkeypatch):
    vc, _ = _fake_audio(monkeypatch, WINDOWS_INPUTS, default_api=3)
    assert vc._pick_device_index(None, "Jabra") == 6


def test_name_match_is_case_insensitive_and_trimmed(monkeypatch):
    vc, _ = _fake_audio(monkeypatch, WINDOWS_INPUTS)
    assert vc._pick_device_index(None, "  GALAXY buds ") == 3


def test_missing_named_mic_falls_back_to_default(monkeypatch):
    vc, _ = _fake_audio(monkeypatch, WINDOWS_INPUTS, default_input=2)
    assert vc._pick_device_index(None, "rode") == 2


def test_stereo_mix_is_never_picked(monkeypatch):
    devices = [WINDOWS_INPUTS[1], dict(WINDOWS_INPUTS[2], index=1)]
    vc, _ = _fake_audio(monkeypatch, devices)
    assert vc._pick_device_index(None, "stereo") == 1
    assert vc._pick_device_index() == 1


def test_explicit_index_still_wins_over_name(monkeypatch):
    vc, _ = _fake_audio(monkeypatch, WINDOWS_INPUTS)
    assert vc._pick_device_index(2, "jabra") == 2


# ---- Windows: candidates are test-opened, WDM-KS last -------------------------------------

HOST_APIS = {0: "MME", 1: "Windows DirectSound", 2: "Windows WASAPI", 3: "Windows WDM-KS"}


def _windows_audio(monkeypatch, devices, opens, default_input=None):
    """``opens`` = set of device indexes whose open() succeeds."""
    vc, audio = _fake_audio(monkeypatch, devices, default_input=default_input)
    monkeypatch.setattr(vc.sys, "platform", "win32")
    audio.get_host_api_info_by_index.side_effect = lambda i: {"name": HOST_APIS[i]}

    def fake_open(**kwargs):
        if kwargs["input_device_index"] in opens:
            return Mock()
        raise OSError(-9999, "Unanticipated host error")

    audio.open.side_effect = fake_open
    return vc, audio


# The user's PC as seen from the restricted account: only WDM-KS, which fails.
WDMKS_JABRA = dict(name="Headset (@System32\\drivers\\bthhfenum.sys,#2;%1 Hands-Free%0\r\n;(Jabra Evolve2 85))",
                   maxInputChannels=1, hostApi=3, index=0, defaultSampleRate=8000.0)
MME_JABRA = dict(name="Headset (Jabra Evolve2 85)", maxInputChannels=1, hostApi=0, index=1,
                 defaultSampleRate=16000.0)
MME_REALTEK = dict(name="Microphone (Realtek HD Audio Mic input)", maxInputChannels=2, hostApi=0,
                   index=2, defaultSampleRate=44100.0)


def test_windows_skips_jabra_entry_that_fails_to_open(monkeypatch, capsys):
    vc, _ = _windows_audio(monkeypatch, [WDMKS_JABRA, MME_JABRA, MME_REALTEK], opens={1, 2})
    assert vc._pick_device_index(None, "jabra") == 1
    assert "Using microphone: Headset (Jabra Evolve2 85) (MME)" in capsys.readouterr().out


def test_windows_tries_mme_before_wdmks(monkeypatch):
    vc, audio = _windows_audio(monkeypatch, [WDMKS_JABRA, MME_JABRA], opens={0, 1})
    assert vc._pick_device_index(None, "jabra") == 1
    first = audio.open.call_args_list[0].kwargs
    assert first["input_device_index"] == 1 and first["rate"] == 16000


def test_windows_falls_back_to_another_input_when_named_fails(monkeypatch, capsys):
    vc, _ = _windows_audio(monkeypatch, [WDMKS_JABRA, MME_REALTEK | {"index": 1}], opens={1})
    assert vc._pick_device_index(None, "jabra") == 1
    assert "Realtek" in capsys.readouterr().out


def test_windows_no_openable_input_raises_clear_error(monkeypatch):
    vc, audio = _windows_audio(monkeypatch, [WDMKS_JABRA], opens=set())
    with pytest.raises(RuntimeError, match="could be opened"):
        vc._pick_device_index(None, "jabra")
    audio.terminate.assert_called_once()


def test_listen_session_reports_unopened_microphone(monkeypatch, capsys):
    from apps.voice import voice_controller as vc

    controller = vc.VoiceController.__new__(vc.VoiceController)
    mic = Mock()
    mic.__enter__ = Mock(return_value=SimpleNamespace(stream=None))
    mic.__exit__ = Mock()
    controller._mic = mic
    assert controller._listen_session() is False
    assert "Microphone could not be opened" in capsys.readouterr().out
    mic.__exit__.assert_not_called()


def _retry_controller(monkeypatch, outcomes):
    """Controller whose _listen_session yields ``outcomes`` in turn (exceptions raised)."""
    import threading

    from apps.voice import voice_controller as vc

    controller = vc.VoiceController.__new__(vc.VoiceController)
    controller._running = threading.Event()
    controller._running.set()
    sessions = iter(outcomes)

    def session():
        result = next(sessions)
        if isinstance(result, Exception):
            raise result
        return result

    controller._listen_session = session
    controller._open_microphone = Mock()
    sleeps = []
    monkeypatch.setattr(vc.time, "sleep", sleeps.append)
    return controller, sleeps


def test_dropped_bluetooth_stream_is_reopened(monkeypatch, capsys):
    controller, sleeps = _retry_controller(
        monkeypatch, [OSError(-9999, "Unanticipated host error"), True]
    )
    controller._listen_loop()
    assert controller._open_microphone.call_count == 1
    assert sleeps == [2.0]
    assert "reopening in 2s" in capsys.readouterr().out


def test_microphone_retries_give_up_with_message(monkeypatch, capsys):
    from apps.voice import voice_controller as vc

    limit = vc.VoiceController.MIC_RETRY_LIMIT
    controller, sleeps = _retry_controller(
        monkeypatch, [OSError(-9999, "host error")] * (limit + 1)
    )
    controller._listen_loop()
    assert len(sleeps) == limit
    assert max(sleeps) <= 10.0
    assert "voice input stopped" in capsys.readouterr().out


def test_stop_during_retry_exits_quietly(monkeypatch):
    controller, sleeps = _retry_controller(monkeypatch, [False])
    controller._running.clear()
    controller._listen_loop()
    assert sleeps == []
