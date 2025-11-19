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
import shutil
from logging import Logger
from typing import Any, Dict, Optional, Set, Tuple

from pydantic import ValidationError

from ..schema import PngSettings

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def load_config_from_json(path: str, logger: Optional[Logger] = None) -> PngSettings:
    """
    Load and validate configuration from JSON.

    Behavior matches the INI version:

    - If file missing --> write defaults
    - If section invalid --> restore only that section
    - If new fields added --> merge them in
    - Invalid file --> backup and rewrite

    Args:
        path (str): Path to the JSON file.
        logger (Optional[Any]): Logger for debug/info logs.

    Returns:
        PngSettings: Fully validated config with missing or invalid parts repaired.
    """
    if os.path.exists(path):
        raw = _load_raw_json(path, logger)
        validated, restored, updated = _validate_sections(raw, logger)
        model = PngSettings(**validated)
        _maybe_update_config(raw, model, path, logger, updated, restored)
        _log_invalid_keys(raw, model, logger, restored)
        return model

    # No config file --> create full defaults
    model = PngSettings()
    save_config_to_json(model, path)
    return model


def save_config_to_json(settings: PngSettings, path: str) -> None:
    """Write settings to JSON.

    Args:
        settings (PngSettings): Parsed and validated configuration to write.
        path (str): Path to the JSON file.
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(settings.model_dump(by_alias=True), f, indent=4)


def _load_raw_json(path: str, logger: Optional[Logger]) -> Dict[str, Any]:
    """Read JSON safely and provide empty dict on catastrophic failure."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f) or {}
    except Exception as e:
        if logger:
            logger.error("Could not parse JSON config: %s", e)
        _backup_invalid_file(path, logger)
        return {}


def _validate_sections(
    raw: Dict[str, Any],
    logger: Optional[Logger],
) -> Tuple[Dict[str, Any], Set[str], bool]:
    """
    Validate each top-level section against equivalent Pydantic section model.
    """
    validated: Dict[str, Any] = {}
    restored: Set[str] = set()
    updated = False

    for field_name, model_field in PngSettings.model_fields.items():
        section_model_cls = model_field.annotation
        section_data = raw.get(field_name, {})

        try:
            section_model = section_model_cls.model_validate(section_data)
        except ValidationError as e:
            # Replace only this section
            section_model = model_field.default_factory()
            restored.add(field_name)
            updated = True

            if logger:
                logger.warning("Invalid config in section [%s], using defaults.", field_name)
                logger.debug("%s", e)

        validated[field_name] = section_model

    return validated, restored, updated


def _log_invalid_keys(
    raw: Dict[str, Any],
    defaults: PngSettings,
    logger: Optional[Logger],
    restored_sections: Set[str],
) -> None:
    if not logger:
        return

    default_dict = defaults.model_dump()

    for section, items in raw.items():
        if section not in default_dict:
            logger.debug("Ignored unknown section [%s]", section)
            continue

        if section not in restored_sections:
            valid_keys = {k.lower(): k for k in default_dict[section].keys()}

            for key in items.keys():
                if key.lower() not in valid_keys:
                    logger.debug("Ignored unknown key [%s].[%s]", section, key)


def _maybe_update_config(
    raw: Dict[str, Any],
    model: PngSettings,
    path: str,
    logger: Optional[Logger],
    updated: bool,
    restored_sections: Set[str],
) -> None:
    """
    Same semantics as the INI version:
    - If invalid sections restored
    - Or if new fields appear
    - Or mismatches exist
    --> rewrite
    """
    model_dict = model.model_dump()

    if updated or raw != model_dict:
        if restored_sections:
            _backup_invalid_file(path, logger)
        save_config_to_json(model, path)


def _backup_invalid_file(path: str, logger: Optional[Logger]):
    backup = path + ".invalid"
    shutil.move(path, backup)
    if logger:
        logger.info("Backed up invalid JSON config to %s", backup)
