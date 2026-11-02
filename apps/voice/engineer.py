"""Local evidence-first and optional Gemini race-engineer backends.

The local backend renders supported facts from validated telemetry and only uses
Ollama to select eligible reviewed advice cards. The optional cloud backend keeps
the legacy Gemini/MCP tool-calling behavior. The local backend owns an asyncio
loop in a background thread so the controller can call it from its worker thread.
"""

import asyncio
import concurrent.futures
import json
import logging
import os
import threading
from pathlib import Path
import time
from typing import Any, Dict, Iterator, Optional

from apps.voice.contracts import Answer, Intent, RequestContext
from apps.voice.session_tracker import SessionProgressTracker

LOGGER = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).resolve().parents[2] / "png_voice.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "backend": "local",  # "local" (offline) or "cloud" (Gemini)
    "ollama_url": "http://127.0.0.1:11434",
    "ollama_model": "llama3.1:8b",
    "whisper_model": "small.en",
    "piper_voice": "en_GB-alan-medium",
    "gemini_api_key": "",
    "model": "gemini-2.5-flash",
    "wake_words": ["radio", "engineer"],
    "require_wake_word": True,
    "tts_voice": "en-GB-RyanNeural",
    "mic_name_contains": "jabra",
    "mcp_url": "http://127.0.0.1:4770/mcp",
    "proactive": True,
    "proactive_poll_sec": 5,
    "race_control_announce": True,
    "race_control_url": "http://127.0.0.1:4768/race-info",
    "race_control_poll_sec": 2,
}

SYSTEM_PROMPT = """\
You are the driver's race engineer on team radio during an F1 game session.
The driver is racing and listening through a headset, so:
- Answer in ONE or TWO short spoken sentences. Be terse and calm, like real F1
  radio.
- ALWAYS fetch live data with the tools before answering anything about the session.
  "Me / my / I" means the player: use the get_player_* tools or get_player_driver_info.
  Use get_drivers_list to resolve other drivers by name, get_race_table for gaps
  and positions.
- Never invent numbers. If data is unavailable or disconnected, say so briefly.
- Speak numbers naturally for text-to-speech: lap times like "one thirty-two
  point four", gaps like "plus one point two seconds", percentages rounded
  ("rears at sixty percent").
  Tool times are in milliseconds; convert them. No markdown, lists, or symbols.
- Give a recommendation when it helps (e.g. "box in two laps", "lift and coast").
- Tyre wear above 80 percent risks a puncture: warn the driver.
"""


def load_config() -> Dict[str, Any]:
    """Load png_voice.json merged over defaults."""
    cfg = dict(DEFAULT_CONFIG)
    try:
        cfg.update(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
    except FileNotFoundError:
        pass
    except Exception as exc:  # pylint: disable=broad-except
        LOGGER.error("Bad %s: %s", CONFIG_PATH, exc)
    return cfg


class RaceEngineer:
    """LLM + MCP tool-calling agent. Thread-safe synchronous ``ask()``."""

    MAX_TURNS_BEFORE_RESET = 20

    def __init__(self, cfg: Optional[Dict[str, Any]] = None) -> None:
        self.cfg = cfg or load_config()
        api_key = (
            self.cfg.get("gemini_api_key")
            or os.environ.get("GEMINI_API_KEY")
            or os.environ.get("GOOGLE_API_KEY")
        )
        if not api_key:
            raise RuntimeError(
                "No Gemini API key: set GEMINI_API_KEY or "
                "gemini_api_key in png_voice.json"
            )

        from google import genai  # pylint: disable=import-outside-toplevel

        self._genai_client = genai.Client(api_key=api_key)

        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._loop.run_forever, daemon=True, name="RaceEngineerLoop"
        )
        self._thread.start()
        self._mcp = None
        self._chat = None
        self._turns = 0
        self._ask_lock = threading.Lock()

    # ------------------------------------------------------------------ public
    def ask_stream(self, question: str) -> Iterator[str]:
        """Cloud answers are short; yield the whole reply as one chunk."""
        yield self.ask(question)

    def ask(self, question: str, timeout: float = 30.0) -> str:
        """Ask the engineer a question; returns the spoken-style answer."""
        with self._ask_lock:
            fut = asyncio.run_coroutine_threadsafe(self._ask(question), self._loop)
            try:
                return fut.result(timeout=timeout)
            except Exception as exc:  # pylint: disable=broad-except
                LOGGER.error("Engineer error: %s", exc)
                self._reset()
                return "Sorry, lost the data link. Say again."

    def close(self) -> None:
        """Shut down the MCP connection and loop."""

        async def _close():
            if self._mcp is not None:
                try:
                    await self._mcp.__aexit__(None, None, None)
                except Exception:  # pylint: disable=broad-except
                    pass

        asyncio.run_coroutine_threadsafe(_close(), self._loop).result(timeout=5)
        self._loop.call_soon_threadsafe(self._loop.stop)

    def cancel_request(self, request_id: str) -> None:
        """Cloud mode remains legacy and cannot cancel an in-flight request."""

    def reset_session(self, session_uid: int | None, generation: int) -> None:
        """Cloud mode has no local evidence state to reset."""

    # ---------------------------------------------------------------- internal
    async def _ensure_ready(self) -> None:
        if self._mcp is None:
            from fastmcp import Client  # pylint: disable=import-outside-toplevel

            client = Client(self.cfg["mcp_url"])
            await client.__aenter__()
            self._mcp = client
            LOGGER.info("Engineer connected to MCP at %s", self.cfg["mcp_url"])
        if self._chat is None or self._turns >= self.MAX_TURNS_BEFORE_RESET:
            from google.genai import types  # pylint: disable=import-outside-toplevel

            self._chat = self._genai_client.aio.chats.create(
                model=self.cfg["model"],
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    tools=[self._mcp.session],  # Gemini calls MCP tools automatically
                    temperature=0.4,
                    thinking_config=types.ThinkingConfig(
                        thinking_budget=0
                    ),  # low latency
                ),
            )
            self._turns = 0

    async def _ask(self, question: str) -> str:
        await self._ensure_ready()
        rsp = await self._chat.send_message(question)
        self._turns += 1
        return (rsp.text or "").strip() or "No data on that right now."

    def _reset(self) -> None:
        """Drop the chat + MCP connection so the next ask reconnects cleanly."""

        async def _drop():
            if self._mcp is not None:
                try:
                    await self._mcp.__aexit__(None, None, None)
                except Exception:  # pylint: disable=broad-except
                    pass
            self._mcp = None
            self._chat = None

        try:
            asyncio.run_coroutine_threadsafe(_drop(), self._loop).result(timeout=5)
        except Exception:  # pylint: disable=broad-except
            self._mcp = None
            self._chat = None


# =============================================================================
# Local evidence-first engineer
# =============================================================================


class LocalEngineer:
    """Local fact answers with an optional exact-reviewed-card selector."""

    def __init__(
        self,
        cfg: Optional[Dict[str, Any]] = None,
        *,
        tracker: SessionProgressTracker,
        telemetry_adapter=None,
        epoch_clock=time.time,
        mono_clock=time.monotonic,
    ) -> None:
        self.cfg = cfg or load_config()
        self._url = self.cfg["ollama_url"].rstrip("/") + "/api/generate"
        self._model = self.cfg["ollama_model"]
        self.tracker = tracker
        self._adapter = telemetry_adapter
        self._epoch = epoch_clock
        self._mono = mono_clock
        self._mcp = None
        self._closed = False
        self._request_lock = threading.Lock()
        self._requests: dict[str, dict[str, Any]] = {}
        self._generation = tracker.current_generation()
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._loop.run_forever, daemon=True, name="LocalEngineerLoop"
        )
        self._thread.start()
        LOGGER.info("Local engineer ready; Ollama fallback is lazy (%s)", self._model)

    @staticmethod
    def _refusal(text="Live telemetry is unavailable; I can't verify that right now."):
        return Answer(text, "insufficient", None, (), ())

    def _request_current(self, request):
        if (
            self._closed
            or request.cancelled()
            or request.generation != self.tracker.current_generation()
            or self._mono() >= request.deadline_mono
        ):
            return False
        with self._request_lock:
            state = self._requests.get(request.request_id)
            return state is None or not state["cancelled"]

    async def _ensure_adapter(self):
        if self._adapter is not None:
            return self._adapter
        from fastmcp import Client  # pylint: disable=import-outside-toplevel
        from apps.voice.telemetry import TelemetryAdapter

        self._mcp = Client(self.cfg["mcp_url"])
        await self._mcp.__aenter__()
        self._adapter = TelemetryAdapter(
            self._mcp,
            self.tracker,
            epoch_clock=self._epoch,
            mono_clock=self._mono,
        )
        return self._adapter

    async def _ask_request(self, question, request, request_state):
        with self._request_lock:
            if (
                request_state["cancelled"]
                or request.cancelled()
                or request.generation != self.tracker.current_generation()
            ):
                return None
            request_state["task"] = asyncio.current_task()
        request_start = self._mono()
        LOGGER.info(
            "voice engineer request_start id=%s generation=%s mono=%.6f",
            request.request_id,
            request.generation,
            request_start,
        )
        try:
            from apps.voice.direct_answers import answer_direct, classify

            intent = classify(question)
            if intent.topic not in (
                "tyres",
                "weather",
                "fuel",
                "gaps",
                "pit",
                "complex",
            ):
                return self._refusal("I don't have a verified answer for that.")
            if not self._request_current(request):
                return None
            adapter = await self._ensure_adapter()
            collected_intent = Intent("pit") if intent.topic == "complex" else intent
            telemetry_start = self._mono()
            LOGGER.info(
                "voice telemetry_start id=%s generation=%s topic=%s mono=%.6f",
                request.request_id,
                request.generation,
                collected_intent.topic,
                telemetry_start,
            )
            evidence = await adapter.collect(
                collected_intent, min(request.deadline_mono, self._mono() + 2.0)
            )
            LOGGER.info(
                "voice telemetry_complete id=%s generation=%s topic=%s "
                "mono=%.6f duration=%.3f available=%s reason=%r",
                request.request_id,
                request.generation,
                collected_intent.topic,
                self._mono(),
                self._mono() - telemetry_start,
                evidence.reason is None,
                evidence.reason,
            )
            if not self._request_current(request):
                return None
            if evidence.reason is not None:
                return self._refusal()
            if intent.topic != "complex":
                answer = answer_direct(intent, evidence)
                LOGGER.info(
                    "voice engineer_first_text id=%s generation=%s route=direct "
                    "mono=%.6f duration=%.3f",
                    request.request_id,
                    request.generation,
                    self._mono(),
                    self._mono() - request_start,
                )
                return answer if answer is not None else self._refusal()
            return await self._complex_answer(question, evidence, request)
        except asyncio.CancelledError:
            return None
        except Exception:
            LOGGER.exception("Local engineer request failed")
            return self._refusal()

    async def _complex_answer(self, question, evidence, request):
        from dataclasses import replace

        from apps.voice.knowledge import (
            build_context,
            retrieve_cards,
            validate_fallback,
        )

        if not self._request_current(request):
            return None
        cards = retrieve_cards(Intent("complex"), question, game_season=None)
        complex_evidence = replace(evidence, topic="complex")
        context = build_context(question, complex_evidence, cards)
        if context is None:
            return self._refusal("Insufficient verified data to answer that safely.")
        try:
            selected = await self._select_card(context, request)
        except asyncio.CancelledError:
            return None
        except Exception:
            LOGGER.warning("Local selector unavailable", exc_info=True)
            return self._refusal("Insufficient verified data to answer that safely.")
        if not self._request_current(request):
            return None
        answer = validate_fallback(selected, cards)
        if answer.kind == "insufficient":
            return answer
        return replace(answer, evidence=evidence)

    async def _select_card(self, context, request):
        """Run one absolutely bounded Ollama request and return its raw ID output."""
        import aiohttp  # pylint: disable=import-outside-toplevel

        remaining = min(8.0, request.deadline_mono - self._mono())
        if remaining <= 0:
            raise TimeoutError("Selector deadline exceeded")
        loop = asyncio.get_running_loop()
        deadline = loop.time() + remaining
        payload = {
            "model": self._model,
            "prompt": context,
            "stream": False,
            "keep_alive": "2h",
            "options": {"temperature": 0, "num_predict": 8, "num_ctx": 4096},
        }
        selector_start = self._mono()
        status = "error"
        LOGGER.info(
            "voice selector_start id=%s generation=%s mono=%.6f budget=%.3f",
            request.request_id,
            request.generation,
            selector_start,
            remaining,
        )
        try:
            async with asyncio.timeout_at(deadline):
                async with aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=None)
                ) as session:
                    async with session.post(self._url, json=payload) as response:
                        response.raise_for_status()
                        body = await response.json()
                        result = body.get("response")
                        status = "complete"
                        return result if type(result) is str else ""
        except asyncio.CancelledError:
            status = "cancelled"
            raise
        except TimeoutError:
            status = "timeout"
            raise
        finally:
            LOGGER.info(
                "voice selector_complete id=%s generation=%s status=%s "
                "mono=%.6f duration=%.3f",
                request.request_id,
                request.generation,
                status,
                self._mono(),
                self._mono() - selector_start,
            )

    def ask_stream(
        self, question: str, *, request: RequestContext | None = None
    ) -> Iterator[Answer]:
        """Yield one direct or reviewed-card answer; cancellation stays silent."""
        if request is None:
            now = self._mono()
            request = RequestContext(
                f"internal-{id(question)}-{now}",
                self.tracker.current_generation(),
                now + 10.0,
                lambda: False,
            )
        if self._closed or not self._request_current(request):
            return
        state = {"cancelled": False, "task": None}
        with self._request_lock:
            if request.request_id in self._requests:
                return
            self._requests[request.request_id] = state
        future = asyncio.run_coroutine_threadsafe(
            self._ask_request(question, request, state), self._loop
        )
        try:
            timeout = max(0.0, request.deadline_mono - self._mono()) + 0.25
            answer = future.result(timeout=timeout)
            if answer is not None and self._request_current(request):
                yield answer
        except (concurrent.futures.CancelledError, concurrent.futures.TimeoutError):
            future.cancel()
        finally:
            with self._request_lock:
                self._requests.pop(request.request_id, None)

    def ask(self, question: str) -> str:
        """Backward-compatible convenience API."""
        return " ".join(answer.text for answer in self.ask_stream(question))

    def cancel_request(self, request_id: str) -> None:
        """Mark and cancel a registered request without blocking its caller."""
        with self._request_lock:
            state = self._requests.get(request_id)
            if state is None or state["cancelled"]:
                return
            state["cancelled"] = True
            task = state["task"]
        if task is not None and not self._loop.is_closed():
            self._loop.call_soon_threadsafe(task.cancel)

    def reset_session(self, session_uid: int | None, generation: int) -> None:
        """Invalidate all current requests without waiting for inference."""
        with self._request_lock:
            self._generation = generation
            tasks = []
            for state in self._requests.values():
                state["cancelled"] = True
                if state["task"] is not None:
                    tasks.append(state["task"])
        for task in tasks:
            if not self._loop.is_closed():
                self._loop.call_soon_threadsafe(task.cancel)

    def revalidate_answer(self, answer: Answer, *, request: RequestContext):
        """Perform invalidation-only evidence revalidation immediately pre-speech."""
        from dataclasses import replace

        if not self._request_current(request):
            return None
        evidence = answer.evidence
        if evidence is None:
            return answer if answer.kind == "insufficient" else None
        if (
            evidence.reason is not None
            or evidence.generation != request.generation
            or self._mono()
            >= min(evidence.expires_mono, evidence.progress_valid_until_mono)
        ):
            return self._refusal()

        cleanup_complete = threading.Event()

        async def revalidate():
            task = asyncio.current_task()
            with self._request_lock:
                state = self._requests.get(request.request_id)
                if state is None or state["cancelled"]:
                    return None
                state["task"] = task
            try:
                adapter = await self._ensure_adapter()
                return await adapter.revalidate(
                    evidence, deadline_mono=request.deadline_mono
                )
            finally:
                with self._request_lock:
                    state = self._requests.get(request.request_id)
                    if state is not None and state["task"] is task:
                        state["task"] = None
                cleanup_complete.set()

        future = asyncio.run_coroutine_threadsafe(revalidate(), self._loop)
        try:
            checked = future.result(
                timeout=max(0.0, request.deadline_mono - self._mono()) + 0.1
            )
        except (concurrent.futures.CancelledError, concurrent.futures.TimeoutError):
            future.cancel()
            cleanup_complete.wait(timeout=0.25)
            return None if not self._request_current(request) else self._refusal()
        except Exception:
            LOGGER.warning("Answer revalidation failed", exc_info=True)
            return self._refusal()
        if checked is None:
            return None
        if not self._request_current(request):
            return None
        if (
            checked.reason is not None
            or checked.generation != request.generation
            or self._mono()
            >= min(checked.expires_mono, checked.progress_valid_until_mono)
        ):
            return self._refusal()
        return replace(answer, evidence=checked)

    def close(self) -> None:
        """Release MCP and the private loop after the question worker has stopped."""
        if self._closed:
            return
        self.reset_session(None, self.tracker.current_generation() + 1)

        async def _close():
            if self._mcp is not None:
                await self._mcp.__aexit__(None, None, None)
                self._mcp = None

        try:
            asyncio.run_coroutine_threadsafe(_close(), self._loop).result(timeout=5)
        finally:
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._thread.join(timeout=5)
            if not self._thread.is_alive():
                self._loop.close()
                self._closed = True


def make_engineer(
    cfg: Optional[Dict[str, Any]] = None,
    *,
    tracker: SessionProgressTracker,
):
    """Create the configured engineer with the controller's shared tracker."""
    cfg = cfg or load_config()
    if cfg.get("backend", "local") == "cloud":
        return RaceEngineer(cfg)
    return LocalEngineer(cfg, tracker=tracker)
