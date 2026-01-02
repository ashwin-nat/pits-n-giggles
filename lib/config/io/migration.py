# MIT License
#
# Copyright (c) [2025] [Ashwin Natarajan]
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

import json
import os
from logging import Logger
from typing import Dict, Optional

from ..schema import OverlayPosition, PngSettings
from .ini import load_config_from_ini
from .json import load_config_from_json, save_config_to_json

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def load_config_migrated(
    ini_path: str,
    json_path: str,
    logger: Optional[Logger] = None
) -> PngSettings:
    """
    Load application configuration using the new JSON-based format,
    migrating automatically from legacy INI if necessary.

    Migration rules:

    - If JSON exists --> load JSON.
    - Else if INI exists --> load INI (auto-fills defaults), then save JSON.
    - Else --> create default settings and save JSON.

    Args:
        ini_path (str): Path to existing legacy INI config.
        json_path (str): Path to new JSON config.
        logger (Optional[Logger]): Optional logger.

    Returns:
        PngSettings: Fully validated settings.
    """

    # ---------------------------------------------------
    # 1. JSON exists --> load it directly
    # ---------------------------------------------------
    if os.path.exists(json_path):
        if logger:
            logger.debug("Loading configuration from JSON: %s", json_path)
        return load_config_from_json(json_path, logger=logger)

    # ---------------------------------------------------
    # 2. JSON missing but old INI exists --> migrate
    # ---------------------------------------------------
    if os.path.exists(ini_path):
        if logger:
            logger.info("Migrating configuration from INI --> JSON")
            logger.debug("Loading legacy INI config from %s", ini_path)

        ini_settings = load_config_from_ini(ini_path, logger=logger, should_write=False)

        # Normalize and ensure defaults for missing values
        model = PngSettings(**ini_settings.model_dump())

        if logger:
            logger.debug("Writing migrated configuration to JSON: %s", json_path)

        save_config_to_json(model, json_path)
        return model

    # ---------------------------------------------------
    # 3. Neither config exists --> create fresh defaults
    # ---------------------------------------------------
    if logger:
        logger.info("No config found. Creating new JSON config with defaults.")

    model = PngSettings()
    save_config_to_json(model, json_path)
    return model

def maybe_migrate_legacy_hud_layout(
    settings: PngSettings,
    json_config_path: str,
    legacy_layout_path: str,
    logger: Optional[Logger] = None,
) -> PngSettings:
    """Migrate legacy png_overlays.json into HUD.layout (one-time)."""

    if not os.path.exists(legacy_layout_path):
        return settings

    if logger:
        logger.info("Legacy png_overlays.json found; attempting HUD layout migration")

    new_settings = settings

    try:
        legacy_layout = _read_legacy_layout(legacy_layout_path)

        default_layout = dict(settings.HUD.layout)
        merged_layout = _merge_legacy_layout(
            default_layout,
            legacy_layout,
            logger,
        )

        new_settings = settings.model_copy(deep=True)
        new_settings.HUD.layout = merged_layout

        save_config_to_json(new_settings, json_config_path)

        if logger:
            logger.info("HUD layout successfully migrated from legacy file")

    except Exception as e:  # pylint: disable=broad-exception-caught
        if logger:
            logger.error(
                "Failed to migrate legacy HUD layout; reverting to defaults: %s",
                e,
            )

    finally:
        # Always delete legacy file
        try:
            os.remove(legacy_layout_path)
            if logger:
                logger.debug("Deleted legacy png_overlays.json")
        except Exception as e:  # pylint: disable=broad-exception-caught
            if logger:
                logger.warning("Failed to delete legacy png_overlays.json: %s",e,)

    return new_settings

def _read_legacy_layout(
    legacy_layout_path: str,
) -> Dict[str, OverlayPosition]:
    """Read and parse legacy png_overlays.json.

    Raises:
        Exception on any parse or validation failure.
    """
    with open(legacy_layout_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    if not isinstance(raw, dict):
        raise ValueError("Legacy layout root is not a dict")

    layout: Dict[str, OverlayPosition] = {}

    for overlay_id, data in raw.items():
        if not isinstance(data, dict):
            raise ValueError(f"Invalid layout entry for overlay '{overlay_id}'")

        layout[overlay_id] = OverlayPosition.fromJSON(data)

    if not layout:
        raise ValueError("Legacy layout contained no valid overlays")

    return layout

def _merge_legacy_layout(
    default_layout: Dict[str, OverlayPosition],
    legacy_layout: Dict[str, OverlayPosition],
    logger: Optional[Logger],
) -> Dict[str, OverlayPosition]:
    """Merge legacy layout into defaults (legacy overrides, defaults fill gaps)."""
    merged = dict(default_layout)

    for overlay_id, pos in legacy_layout.items():
        if overlay_id not in merged:
            if logger:
                logger.debug(
                    "Ignoring legacy layout for unknown overlay '%s'",
                    overlay_id,
                )
            continue

        merged[overlay_id] = pos

    return merged
