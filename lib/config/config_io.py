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
import shutil
from configparser import ConfigParser
from logging import Logger
from typing import Any, Optional, Dict, Set, Tuple

from pydantic import ValidationError

from .config_schema import PngSettings

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def load_config_from_ini(path: str, logger: Optional[Logger] = None) -> PngSettings:
    """
    Load and validate configuration from INI file.

    - If the config file is missing: write full defaults to disk.
    - If any section is invalid: only that section is replaced with defaults.
    - If new fields/sections were introduced: add them and update the file.

    Args:
        path (str): Path to the INI file.
        logger (Optional[Any]): Logger for debug/info logs.

    Returns:
        PngSettings: Fully validated config with missing or invalid parts repaired.
    """
    if os.path.exists(path):
        raw = _load_raw_ini(path)
        validated, restored, updated = _validate_sections(raw, logger)
        model = PngSettings(**validated)
        _maybe_update_config(raw, model, path, logger, updated, restored)
        _log_invalid_keys(raw, model, logger)
        return model

    # No config file found → create one with defaults
    model = PngSettings()
    save_config_to_ini(model, path)
    return model

def save_config_to_ini(settings: PngSettings, path: str) -> None:
    """
    Save PngSettings model to INI file.

    Args:
        settings (PngSettings): Parsed and validated configuration to write.
        path (str): Path to the INI file.
    """
    cp = ConfigParser()
    stringified = _stringify_dict(settings.model_dump(by_alias=True))
    cp.read_dict(stringified)
    with open(path, 'w', encoding='utf-8') as f:
        cp.write(f)

def _stringify_dict(d: Any) -> Any:
    """
    Recursively convert all values in a nested dict to strings.

    Args:
        d (Any): A nested dictionary or primitive.

    Returns:
        Any: The same structure with all leaf values as strings.
    """
    if isinstance(d, dict):
        return {k: _stringify_dict(v) for k, v in d.items()}
    return "" if d is None else str(d)

def _backup_invalid_file(path: str, logger: Optional[Logger]) -> None:
    """
    Back up the invalid configuration file.

    Args:
        path (str): Path to the original INI file.
        logger (Optional[Any]): Logger for optional logging.
    """
    backup_path = path + ".invalid"
    shutil.move(path, backup_path)
    if logger:
        logger.info("Backed up invalid config to %s", backup_path)

def _log_invalid_keys(raw: dict[str, dict[str, str]], defaults: PngSettings, logger: Optional[Logger]) -> None:
    """
    Log keys with invalid or unrecognized values and show fallbacks.

    Args:
        raw (dict[str, dict[str, str]]): The raw config dict parsed from INI.
        defaults (PngSettings): The default settings model.
        logger (Optional[Any]): Logger for debug output.
    """
    if not logger:
        return

    default_dict = defaults.model_dump()

    for section, items in raw.items():
        if section not in default_dict:
            logger.debug("Ignored unknown section [%s]", section)
            continue

        for key, value in items.items():
            if key not in default_dict[section]:
                logger.debug("Ignored unknown key [%s].[%s] = %r", section, key, value)
            else:
                default_value = default_dict[section][key]
                logger.debug("Fallback: [%s].[%s] = %r -> default = %r", section, key, value, default_value)

def _load_raw_ini(path: str) -> Dict[str, Dict[str, str]]:
    """Parse INI file into a nested dictionary."""
    cp = ConfigParser()
    cp.read(path)
    return {section: dict(cp.items(section)) for section in cp.sections()}

def _validate_sections(
    raw: Dict[str, Dict[str, str]],
    logger: Optional[Logger],
) -> Tuple[Dict[str, Any], Set[str], bool]:
    """
    Validate each section against its corresponding pydantic submodel.

    Returns:
        - Dict[str, Any]: validated section models
        - Set[str]: names of sections that were invalid and restored to defaults
        - bool: whether the config was updated due to invalid or missing fields
    """
    validated: Dict[str, Any] = {}
    restored: Set[str] = set()
    updated: bool = False

    for field_name, model_field in PngSettings.model_fields.items():
        section_model_cls = model_field.annotation
        section_data = raw.get(field_name, {})

        try:
            section_model = section_model_cls.model_validate(section_data)
        except ValidationError as e:
            section_model = model_field.default_factory()
            restored.add(field_name)
            updated = True
            if logger:
                logger.warning("Invalid config in section [%s], using defaults.", field_name)
                logger.debug("%s", e)

        validated[field_name] = section_model

    return validated, restored, updated

def _maybe_update_config(
    raw: Dict[str, Dict[str, str]],
    model: PngSettings,
    path: str,
    logger: Optional[Logger],
    updated: bool,
    restored_sections: Set[str],
) -> None:
    """
    Rewrite the config file if changes were made or defaults were applied.
    """
    if updated or raw != _stringify_dict(model.model_dump()):
        if restored_sections:
            _backup_invalid_file(path, logger)
        save_config_to_ini(model, path)
