"""Voice controller for the Pits n' Giggles AI race engineer.

Pipeline::

    Jabra mic -> speech-to-text -> wake word -> grounded race engineer
    -> neural TTS -> Jabra earpiece

Plus an optional TelemetryWatcher that makes the engineer speak up on its own
(tyre wear, fuel deficit, safety car, weather change).

Settings live in ``png_voice.json`` at the repo root (see engineer.DEFAULT_CONFIG).
"""

import logging
import os

import re
import shutil
import subprocess
import threading
import time
from typing import Callable, Optional
from uuid import uuid4

from apps.voice.contracts import Answer, RadioWork, RequestContext
from apps.voice.radio_queue import RadioQueue
from apps.voice.session_tracker import SessionProgressTracker

import speech_recognition as sr

from apps.voice.engineer import load_config, make_engineer
from apps.voice.tts import Speaker
from apps.voice.race_control_announcer import RaceControlAnnouncer
from apps.voice.watcher import TelemetryWatcher

LOGGER = logging.getLogger(__name__)

FOLLOWUP_WINDOW_SEC = 8.0  # after a bare wake word, next phrase is the question


def select_headset_mic(name_contains: str = "jabra") -> None:
    """Make the Bluetooth/USB headset the PipeWire default input.

    PyAudio only sees ALSA names, so we route the ALSA "default"/"pulse" device to
    the headset by setting the default source. Switches a Bluetooth headset into
    HSP/HFP (mic-enabled) mode if it is currently in A2DP (playback only).
    """
    if not shutil.which("pactl"):
        return

    def _pactl(*args: str) -> str:
        return subprocess.run(
            ["pactl", *args], capture_output=True, text=True, check=False
        ).stdout

    def _find_source() -> Optional[str]:
        for line in _pactl("list", "short", "sources").splitlines():
            parts = line.split()
            if (
                len(parts) > 1
                and "monitor" not in parts[1].lower()
                and (name_contains and name_contains in parts[1].lower())
            ):
                return parts[1]
        return None

    source = _find_source()
    if source is None:
        for line in _pactl("list", "short", "cards").splitlines():
            parts = line.split()
            if (
                len(parts) > 1
                and parts[1].startswith("bluez_card")
                and name_contains
                and name_contains in parts[1].lower()
            ):
                for profile in ("headset-head-unit-msbc", "headset-head-unit"):
                    subprocess.run(
                        ["pactl", "set-card-profile", parts[1], profile],
                        capture_output=True,
                        check=False,
                    )
                    time.sleep(1.5)
                    source = _find_source()
                    if source:
                        break
    if source:
        _pactl("set-default-source", source)
        os.environ["PULSE_SOURCE"] = source
        LOGGER.info("Voice input: %s", source)
        print(f"[Voice] Using microphone: {source}")
    else:
        sources = [
            parts[1]
            for line in _pactl("list", "short", "sources").splitlines()
            if len(parts := line.split()) > 1 and "monitor" not in parts[1].lower()
        ]
        default = _pactl("get-default-source").strip()
        if default in sources:
            os.environ["PULSE_SOURCE"] = default
            return
        # Do not silently switch to somebody else's Bluetooth headset.
        source = next((s for s in sources if not s.startswith("bluez_input")), None)
        if source is None:
            raise RuntimeError(
                "No usable microphone input. Connect the configured headset or select "
                "a real default input in your system audio settings "
                "(not an output monitor)."
            )
        _pactl("set-default-source", source)
        # WirePlumber can retain a monitor as default despite set-default-source.
        # Bind this process explicitly instead of trusting that global setting.
        os.environ["PULSE_SOURCE"] = source
        LOGGER.info("Voice input: %s", source)


def _pick_device_index(requested: Optional[int] = None) -> int:
    """Inspect input metadata without opening a microphone stream."""
    audio = sr.Microphone.get_pyaudio().PyAudio()
    try:
        devices = [
            audio.get_device_info_by_index(i) for i in range(audio.get_device_count())
        ]
        usable = [
            i
            for i, device in enumerate(devices)
            if device.get("maxInputChannels", 0) > 0
            and "monitor" not in device["name"].lower()
        ]
        if requested is not None:
            if requested in usable:
                return requested
            raise RuntimeError(
                "Configured microphone is not a usable input; select a real microphone."
            )
        bound_source = os.environ.get("PULSE_SOURCE")
        if bound_source:
            for wanted in (bound_source, "pulse"):
                for index in usable:
                    if devices[index]["name"] == wanted:
                        return index
            raise RuntimeError(
                "Cannot route the microphone source through PulseAudio; "
                "install its ALSA plugin or select a matching input device."
            )
        try:
            default = int(audio.get_default_input_device_info()["index"])
        except (OSError, ValueError, KeyError):
            default = None
        for wanted in ("pipewire", "pulse", "default"):
            for index in usable:
                if devices[index]["name"].lower() == wanted:
                    return index
        if default in usable:
            return default
        if usable:
            return usable[0]
        raise RuntimeError(
            "No microphone input available; connect a microphone "
            "and select it in audio settings."
        )
    finally:
        audio.terminate()


class VoiceController:
    """Continuous listener that routes wake-word questions to the AI engineer."""

    def __init__(
        self,
        on_text: Optional[Callable[[str], None]] = None,
        device_index: Optional[int] = None,
        tts_enabled: bool = True,
        *,
        mono_clock=time.monotonic,
    ) -> None:
        self._mono = mono_clock
        self.tracker = SessionProgressTracker()
        self._scheduler_lock = threading.Lock()
        self._active = None
        self._busy_pending = False
        self._wake_worker = threading.Event()
        self._work = RadioQueue()
        self._generation = self.tracker.current_generation()
        self.cfg = load_config()
        self._on_text = on_text
        self._tts_enabled = tts_enabled
        self.wake_words = [w.lower() for w in self.cfg["wake_words"]]
        self.require_wake = bool(self.cfg["require_wake_word"])

        select_headset_mic(self.cfg["mic_name_contains"].lower())
        self._recognizer = sr.Recognizer()
        self._recognizer.pause_threshold = 0.6  # snappier end-of-phrase
        self._recognizer.dynamic_energy_threshold = True
        idx = _pick_device_index(device_index)
        self._mic = sr.Microphone(device_index=idx)

        self.local = self.cfg.get("backend", "local") != "cloud"
        self.stt = None
        if self.local:
            try:
                from apps.voice.stt import (
                    WhisperSTT,
                )  # pylint: disable=import-outside-toplevel

                self.stt = WhisperSTT(self.cfg["whisper_model"])
            except Exception as exc:  # pylint: disable=broad-except
                raise RuntimeError(
                    "Local Whisper STT unavailable; install the local model "
                    "before starting voice."
                ) from exc

        self.speaker = Speaker(
            self.cfg["tts_voice"],
            piper_voice=self.cfg["piper_voice"] if self.local else "",
            offline=self.local,
        )
        self.engineer = None
        try:
            self.engineer = make_engineer(self.cfg, tracker=self.tracker)
            mode = (
                f"offline ({self.cfg['ollama_model']})"
                if self.local
                else "cloud (Gemini)"
            )
            print(f"[Voice] Engineer: {mode}")
        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.error("Race engineer unavailable: %s", exc)
            print(f"[Voice] Race engineer unavailable: {exc}")

        self.watcher: Optional[TelemetryWatcher] = None
        if self.engineer:
            self.watcher = TelemetryWatcher(
                self.cfg["mcp_url"],
                self._callout,
                poll_sec=float(self.cfg["proactive_poll_sec"]),
                tracker=self.tracker,
                proactive=bool(self.cfg.get("proactive")),
                on_session=self.reset_session,
                mono_clock=self._mono,
            )

        self.race_control: Optional[RaceControlAnnouncer] = None
        if self.cfg.get("race_control_announce"):
            self.race_control = RaceControlAnnouncer(
                self._speak,
                self.cfg["race_control_url"],
                poll_sec=float(self.cfg["race_control_poll_sec"]),
            )

        self._running = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._worker_thread: Optional[threading.Thread] = None
        self._engineer_closed = False

        self._awaiting_until = 0.0

    # ------------------------------------------------------------------ public
    @property
    def is_alive(self) -> bool:
        """Readiness requires both the listener and question worker to be running."""
        return bool(
            self._running.is_set()
            and self._thread
            and self._thread.is_alive()
            and self._worker_thread
            and self._worker_thread.is_alive()
        )

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._running.set()
        self._thread = threading.Thread(
            target=self._listen_loop, daemon=True, name="VoiceListen"
        )
        self._thread.start()
        self._worker_thread = threading.Thread(
            target=self._work_loop, daemon=True, name="VoiceWork"
        )
        self._worker_thread.start()
        wake = f'"{self.wake_words[0]}, ..."' if self.require_wake else "anything"
        print(f"[Voice] Race engineer ready - say {wake}")
        if self.engineer:
            self._submit_control("greeting", "Radio check. Engineer ready.")

    def stop(self) -> None:
        self._running.clear()
        self._cancel_active()
        self._wake_worker.set()
        if self.watcher:
            self.watcher.stop()
        if self.race_control:
            self.race_control.stop()
        for thread in (self._thread, self._worker_thread):
            if thread and thread is not threading.current_thread():
                thread.join(timeout=5)
        if any(
            thread and thread.is_alive()
            for thread in (self._thread, self._worker_thread)
        ):
            LOGGER.warning(
                "Voice shutdown timed out; engineer left open until workers stop"
            )
            return
        if self.engineer and not self._engineer_closed:
            self.engineer.close()
            self._engineer_closed = True

    # ---------------------------------------------------------------- internal
    def _speak(self, text: str) -> None:
        print(f"[Engineer] {text}")
        if self._tts_enabled:
            self.speaker.say(text)

    def _callout(self, work: RadioWork) -> None:
        if self._work.submit(work, now_mono=self._mono()):
            self._wake_worker.set()

    def _submit_control(self, kind, text):
        now = self._mono()
        work = RadioWork(
            uuid4().hex, kind, text, self.tracker.current_generation(), now, now + 2
        )
        if self._work.submit(work, now_mono=now):
            self._wake_worker.set()

    def _cancel_active(self):
        with self._scheduler_lock:
            active = self._active
            if active:
                active[1].set()
        if active and self.engineer:
            self.engineer.cancel_request(active[0])

    def reset_session(self, session_uid, generation):
        """Nonblocking generation handoff; never acquire an inference/speech lock."""
        with self._scheduler_lock:
            if generation <= self._generation:
                return
            self._generation = generation
            self._work.reset(generation)
            self._busy_pending = False
            active = self._active
            if active:
                active[1].set()
        if self.engineer:
            if active:
                self.engineer.cancel_request(active[0])
            self.engineer.reset_session(session_uid, generation)
        self._wake_worker.set()

    def submit_question(self, question: str, *, captured_mono=None) -> bool:
        now = self._mono()
        captured = now if captured_mono is None else captured_mono
        work = RadioWork(
            uuid4().hex,
            "question",
            question,
            self.tracker.current_generation(),
            captured,
            captured + 10,
        )
        with self._scheduler_lock:
            admitted = self._work.submit(work, now_mono=now)
            active = self._active if admitted else None
            if active:
                active[1].set()
            if not admitted and now < work.expires_mono:
                self._busy_pending = True
        # The public engineer cancellation API must itself be nonblocking.
        if active and self.engineer:
            self.engineer.cancel_request(active[0])
        self._wake_worker.set()
        LOGGER.info(
            "radio enqueue id=%s generation=%s admitted=%s endpoint_mono=%.6f "
            "enqueue_mono=%.6f",
            work.id,
            work.generation,
            admitted,
            captured,
            now,
        )
        return admitted

    def _extract_question(self, text: str) -> Optional[str]:
        """Return the question if the phrase is addressed to the engineer."""
        lowered = text.lower().strip()
        if time.time() < self._awaiting_until:
            self._awaiting_until = 0.0
            return text
        if not self.require_wake:
            return text
        for wake in self.wake_words:
            m = re.match(
                rf"^(?:hey |ok |okay )?{re.escape(wake)}\b[\s,.!?]*(.*)$", lowered
            )
            if m:
                return m.group(1).strip()  # may be "" => bare wake word
        return None

    def _listen_loop(self) -> None:
        with self._mic as source:
            self._recognizer.adjust_for_ambient_noise(source, duration=1.0)
            while self._running.is_set():
                if self.speaker.speaking.is_set():
                    time.sleep(0.1)  # don't transcribe our own voice
                    continue
                try:
                    listen_start = self._mono()
                    audio = self._recognizer.listen(
                        source, timeout=1, phrase_time_limit=10
                    )
                    captured = self._mono()
                    LOGGER.info(
                        "radio endpoint_detection_complete_mono=%.6f "
                        "capture_listen_duration=%.3f",
                        captured,
                        captured - listen_start,
                    )
                except sr.WaitTimeoutError:
                    continue
                if self.speaker.speaking.is_set():
                    continue
                try:
                    t0 = self._mono()
                    if self.stt is not None:
                        text = self.stt.transcribe(audio)
                    elif not self.local:
                        text = self._recognizer.recognize_google(audio)
                    else:
                        raise RuntimeError(
                            "Local STT is unavailable; cloud fallback is disabled"
                        )
                    if not text:
                        continue
                    LOGGER.info(
                        "radio endpoint_mono=%.6f stt_start_mono=%.6f "
                        "stt_end_mono=%.6f stt_duration=%.3f",
                        captured,
                        t0,
                        self._mono(),
                        self._mono() - t0,
                    )
                except sr.UnknownValueError:
                    continue
                except sr.RequestError as exc:
                    LOGGER.error("Speech service error: %s", exc)
                    time.sleep(1)
                    continue
                print(f"[Voice] heard: {text}")
                if self._on_text:
                    self._on_text(text)
                question = self._extract_question(text)
                if question is None:
                    continue
                if not question:
                    self._awaiting_until = time.time() + FOLLOWUP_WINDOW_SEC
                    self._submit_control("ack", "Go ahead.")
                else:
                    self.submit_question(question, captured_mono=captured)

    def _current(self, work, cancelled):
        return (
            not cancelled.is_set()
            and work.generation == self.tracker.current_generation()
            and self._mono() < work.expires_mono
        )

    def _deliver(self, answer, work, request, cancelled):
        if not isinstance(answer, Answer) or not self._current(work, cancelled):
            return
        checked = self.engineer.revalidate_answer(answer, request=request)
        if not isinstance(checked, Answer) or not self._current(work, cancelled):
            return
        ev = checked.evidence
        if ev is not None and (
            ev.reason is not None
            or ev.generation != work.generation
            or self._mono() >= min(ev.expires_mono, ev.progress_valid_until_mono)
        ):
            return
        start = self._mono()
        LOGGER.info(
            "radio speak_invocation id=%s generation=%s route=%s "
            "reason=%s mono=%.6f",
            work.id,
            work.generation,
            checked.kind,
            ev.reason if ev else None,
            start,
        )
        # Speaker.say is blocking/nonpreemptible. Cancellation prevents subsequent
        # chunks, not the one short sentence already being played.
        self._speak(checked.text)
        LOGGER.info(
            "radio speak_return id=%s mono=%.6f "
            "speaker_call_duration=%.3f physical_first_audio=unmeasured",
            work.id,
            self._mono(),
            self._mono() - start,
        )

    def process_next(self) -> bool:
        """Process one item on the sole speech worker, with no queue lock over I/O."""
        with self._scheduler_lock:
            work = self._work.take(now_mono=self._mono())
            busy = self._busy_pending
            self._busy_pending = False
            if work is None:
                return False
            cancelled = threading.Event()
            self._active = (work.id, cancelled)
        request = RequestContext(
            work.id, work.generation, work.expires_mono, cancelled.is_set
        )
        started = self._mono()
        LOGGER.info(
            "radio dequeue id=%s generation=%s mono=%.6f queue_wait=%.3f",
            work.id,
            work.generation,
            started,
            started - work.created_mono,
        )
        try:
            if not self._current(work, cancelled):
                return True
            if busy:
                self._speak("Radio busy. Please repeat the extra question.")
            if not self._current(work, cancelled):
                return True
            if work.kind in ("ack", "greeting"):
                if self._current(work, cancelled):
                    self._speak(work.text)
            elif self.engineer is None:
                if self._current(work, cancelled):
                    self._speak("Engineer offline.")
            elif work.kind == "callout":
                answer = self.watcher.refresh_callout(work) if self.watcher else None
                self._deliver(answer, work, request, cancelled)
            elif self.local:
                first = True
                for answer in self.engineer.ask_stream(work.text, request=request):
                    if not self._current(work, cancelled):
                        break
                    if first and isinstance(answer, Answer):
                        LOGGER.info(
                            "radio first_text id=%s mono=%.6f "
                            "dequeue_to_first_text=%.3f",
                            work.id,
                            self._mono(),
                            self._mono() - started,
                        )
                        first = False
                    self._deliver(answer, work, request, cancelled)
            else:
                # Optional legacy cloud mode is explicit; never local authority.
                for text in self.engineer.ask_stream(work.text):
                    if not self._current(work, cancelled):
                        break
                    if isinstance(text, str):
                        self._speak(text)
        except Exception:
            LOGGER.exception(
                "Radio work failed id=%s generation=%s", work.id, work.generation
            )
        finally:
            with self._scheduler_lock:
                if self._active and self._active[0] == work.id:
                    self._active = None
        return True

    def _work_loop(self) -> None:
        if self.watcher:
            self.watcher.start()
        if self.race_control:
            self.race_control.start()
        while self._running.is_set():
            self._wake_worker.clear()
            if not self.process_next():
                self._wake_worker.wait(0.1)
