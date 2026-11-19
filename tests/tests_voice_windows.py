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
