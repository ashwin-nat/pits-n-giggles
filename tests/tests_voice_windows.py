"""Windows/frozen-build regressions: model lookup and Piper playback without pw-play."""

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

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
