"""Standalone, local-only voice engineer for the user's audio session."""

import argparse
import asyncio
import ipaddress
import json
import logging
import signal
import threading
from pathlib import Path
from urllib.parse import urlsplit

import requests

from apps.voice.engineer import load_config
from apps.voice.voice_controller import VoiceController

LOGGER = logging.getLogger(__name__)


def validate_local_config(config: dict) -> None:
    """Reject cloud backends and non-loopback model/telemetry endpoints."""
    if config.get("backend", "local") != "local":
        raise ValueError("The voice service requires backend=local")
    for name in ("ollama_url", "mcp_url"):
        endpoint = urlsplit(config.get(name, ""))
        host = endpoint.hostname
        try:
            loopback = host == "localhost" or ipaddress.ip_address(host).is_loopback
        except ValueError:
            loopback = False
        if (
            endpoint.scheme not in ("http", "https")
            or not loopback
            or endpoint.username is not None
            or endpoint.password is not None
        ):
            raise ValueError(
                f"{name} must be a loopback HTTP endpoint without credentials"
            )


def check_dependencies() -> dict:
    """Load existing models and probe local services without opening a microphone."""
    config = load_config()
    validate_local_config(config)
    response = requests.get(config["ollama_url"].rstrip("/") + "/api/tags", timeout=10)
    response.raise_for_status()
    installed = {model["name"] for model in response.json().get("models", [])}
    if config["ollama_model"] not in installed:
        raise RuntimeError("Configured local Ollama model is not installed")

    # Import lazily so --help and lifecycle tests never load model runtimes.
    from fastmcp import Client  # pylint: disable=import-outside-toplevel
    from piper import PiperVoice  # pylint: disable=import-outside-toplevel

    from apps.voice.stt import WhisperSTT  # pylint: disable=import-outside-toplevel

    async def check_mcp():
        async with Client(config["mcp_url"]) as client:
            return len(await client.list_tools())

    tools = asyncio.run(check_mcp())
    if not tools:
        raise RuntimeError("Local MCP server did not provide telemetry tools")
    stt = WhisperSTT(config["whisper_model"], threads=4)
    model_path = (
        Path(__file__).resolve().parents[2]
        / "models"
        / "piper"
        / f"{config['piper_voice']}.onnx"
    )
    voice = PiperVoice.load(str(model_path))
    audio_bytes = sum(
        len(chunk.audio_int16_bytes) for chunk in voice.synthesize("Radio check.")
    )
    if not audio_bytes:
        raise RuntimeError("Local Piper model generated no speech audio")
    del stt
    return {
        "ok": True,
        "backend": "local",
        "device": "cpu",
        "whisper": config["whisper_model"],
        "piper": config["piper_voice"],
        "ollama": config["ollama_model"],
        "mcp_tools": tools,
        "microphone_opened": False,
    }


def run(stop: threading.Event) -> None:
    """Supervise the voice workers; fail so systemd can recover dead listeners."""
    validate_local_config(load_config())
    controller = VoiceController()
    try:
        if controller.engineer is None:
            raise RuntimeError(
                "Local race engineer unavailable; check Ollama and its model"
            )
        controller.start()
        LOGGER.info(
            "Voice listening locally; say the configured wake word to ask a question"
        )
        while not stop.wait(0.5):
            if not controller.is_alive:
                raise RuntimeError(
                    "Voice listener or question worker stopped unexpectedly"
                )
    finally:
        controller.stop()


def main(argv=None) -> int:
    """Run the audio-session service or a microphone-free dependency check."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check local dependencies without microphone capture",
    )
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(name)s: %(message)s"
    )
    stop = threading.Event()
    previous = {}
    try:
        if args.check:
            print(json.dumps(check_dependencies()))
            return 0
        for number in (signal.SIGINT, signal.SIGTERM):
            previous[number] = signal.signal(number, lambda _number, _frame: stop.set())
        run(stop)
        return 0
    except Exception:  # pylint: disable=broad-exception-caught
        LOGGER.exception("Voice service failed")
        return 1
    finally:
        for number, handler in previous.items():
            signal.signal(number, handler)
