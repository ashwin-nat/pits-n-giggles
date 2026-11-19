"""Where the voice assistant keeps its config file and local models.

From source this is the repository root. In a PyInstaller build the package lives in a
temporary extraction folder, so the models and ``png_voice.json`` are looked up next
to the executable instead. ``PNG_VOICE_HOME`` overrides both.
"""

import os
import sys
from pathlib import Path


def voice_home() -> Path:
    """Return the folder that holds ``png_voice.json`` and ``models/``."""
    override = os.environ.get("PNG_VOICE_HOME")
    if override:
        return Path(override).expanduser().resolve()
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def models_dir(kind: str) -> Path:
    """Return ``<voice home>/models/<kind>``, e.g. ``models_dir("piper")``."""
    return voice_home() / "models" / kind
