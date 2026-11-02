"""Offline speech-to-text using faster-whisper on CPU."""

import logging
from pathlib import Path

import numpy as np

LOGGER = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).resolve().parents[2] / "models" / "whisper"

F1_PROMPT = (
    "Radio, engineer. Box box. Tyres, softs, mediums, hards, inters, wets. "
    "Fuel, ERS, DRS, gap, undercut, overcut, pit window, safety car, VSC, lap time, sector."
)


class WhisperSTT:
    """Transcribe ``speech_recognition.AudioData`` locally."""

    def __init__(self, model: str = "small.en", threads: int = 8) -> None:
        from faster_whisper import (
            WhisperModel,
        )  # pylint: disable=import-outside-toplevel

        self.model = WhisperModel(
            model,
            device="cpu",
            compute_type="int8",
            cpu_threads=threads,
            download_root=str(MODELS_DIR),
        )
        LOGGER.info("Whisper %s loaded", model)

    def transcribe(self, audio) -> str:
        raw = audio.get_raw_data(convert_rate=16000, convert_width=2)
        pcm = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        segments, _ = self.model.transcribe(
            pcm,
            language="en",
            beam_size=1,
            vad_filter=True,
            initial_prompt=F1_PROMPT,
            condition_on_previous_text=False,
        )
        return " ".join(s.text.strip() for s in segments).strip()
