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

import os
from typing import Optional
from logging import Logger

from .ini import load_config_from_ini
from .json import load_config_from_json, save_config_to_json
from ..schema import PngSettings

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
