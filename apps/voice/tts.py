"""Text-to-speech for the AI race engineer.

Local Piper PCM prefers PipeWire's ``pw-play``; ``paplay`` is the PulseAudio
fallback. Where neither exists (Windows, macOS) Piper audio is played in-process
through PyAudio, which the microphone path already depends on. Explicit cloud
mode can use Edge TTS and ``ffplay``. ``pyttsx3`` is the final offline fallback.
"""

import asyncio
import logging
import os
import shutil
import subprocess
import tempfile
import threading

from apps.voice.paths import models_dir

LOGGER = logging.getLogger(__name__)


class Speaker:
    """Thread-safe speaker. ``speaking`` is set while audio is playing so the
    microphone loop can ignore the engineer's own voice."""

    def __init__(
        self,
        voice: str = "en-GB-RyanNeural",
        piper_voice: str = "",
        *,
        offline: bool = True,
    ) -> None:
        self.voice = voice
        self.offline = offline
        self.speaking = threading.Event()
        self._lock = threading.Lock()
        self._player = shutil.which("ffplay")
        self._fallback = None
        self._piper = None
        self._pw_play = shutil.which("pw-play")
        self._pcm_player = self._pw_play
        self._pcm_format = "s16"
        if self._pcm_player is None:
            self._pcm_player = shutil.which("paplay")
            self._pcm_format = "s16le"
        if piper_voice:
            self._load_piper(piper_voice)

    def _load_piper(self, name: str) -> None:
        path = models_dir("piper") / f"{name}.onnx"
        try:
            from piper import PiperVoice  # pylint: disable=import-outside-toplevel

            self._piper = PiperVoice.load(str(path))
            LOGGER.info("Piper voice loaded: %s", name)
        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.warning("Piper unavailable (%s): %s", path, exc)

    def say(self, text: str) -> None:
        """Speak ``text`` (blocking). Serialised so callouts never overlap answers."""
        if not text:
            return
        with self._lock:
            self.speaking.set()
            try:
                if not self._say_piper(text):
                    if self.offline or not self._say_edge(text):
                        self._say_fallback(text)
            finally:
                self.speaking.clear()

    def _say_piper(self, text: str) -> bool:
        if self._piper is None:
            return False
        if not self._pcm_player:
            return self._say_piper_pyaudio(text)
        try:
            proc = None
            n_bytes, rate = 0, 22050
            for chunk in self._piper.synthesize(text):
                if proc is None:
                    rate = chunk.sample_rate
                    command = [
                        self._pcm_player,
                        "--raw",
                        f"--rate={rate}",
                        f"--format={self._pcm_format}",
                        "--channels=1",
                    ]
                    if self._pcm_player == self._pw_play:
                        command.append("-")
                    proc = subprocess.Popen(command, stdin=subprocess.PIPE)
                proc.stdin.write(chunk.audio_int16_bytes)
                n_bytes += len(chunk.audio_int16_bytes)
            if proc is not None:
                proc.stdin.close()
                try:
                    return_code = proc.wait(timeout=n_bytes / (2 * rate) + 3)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
                    LOGGER.warning(
                        "Audio output stuck (Bluetooth link?) - reconnect the headset"
                    )
                    print("[Voice] Audio output stuck - try reconnecting the headset")
                    return False
                if return_code != 0:
                    LOGGER.warning("Audio player exited with status %s", return_code)
                    return False
            return proc is not None
        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.warning("Piper failed: %s", exc)
            return False

    def _say_piper_pyaudio(self, text: str) -> bool:
        """Play Piper PCM in-process when no command-line PCM player is installed."""
        try:
            import pyaudio  # pylint: disable=import-outside-toplevel
        except ImportError:
            return False
        audio = stream = None
        try:
            for chunk in self._piper.synthesize(text):
                if stream is None:
                    audio = pyaudio.PyAudio()
                    stream = audio.open(
                        format=pyaudio.paInt16,
                        channels=1,
                        rate=chunk.sample_rate,
                        output=True,
                    )
                stream.write(chunk.audio_int16_bytes)
            return stream is not None
        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.warning("Piper playback via PyAudio failed: %s", exc)
            return False
        finally:
            if stream is not None:
                try:
                    stream.stop_stream()
                    stream.close()
                except Exception:  # pylint: disable=broad-except
                    pass
            if audio is not None:
                audio.terminate()

    def _say_edge(self, text: str) -> bool:
        if not self._player:
            return False
        try:
            import edge_tts  # pylint: disable=import-outside-toplevel
        except ImportError:
            return False
        fd, path = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)
        try:
            asyncio.run(edge_tts.Communicate(text, self.voice, rate="+10%").save(path))
            subprocess.run(
                [self._player, "-nodisp", "-autoexit", "-loglevel", "quiet", path],
                check=False,
            )
            return True
        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.warning("edge-tts failed (%s), using fallback voice", exc)
            return False
        finally:
            try:
                os.remove(path)
            except OSError:
                pass

    def _say_fallback(self, text: str) -> None:
        try:
            if self._fallback is None:
                import pyttsx3  # pylint: disable=import-outside-toplevel

                self._fallback = pyttsx3.init()
            self._fallback.say(text)
            self._fallback.runAndWait()
        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.error("No TTS available: %s", exc)
            print(f"[Engineer] {text}")
