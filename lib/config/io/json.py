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

import copy
import json
import os
import shutil
from logging import Logger
from typing import Any, Dict, Iterator, Optional, Tuple

from pydantic import BaseModel, ValidationError

from ..schema.png import PngSettings
from ..schema.utils import ConflictError

# -------------------------------------- TYPES -------------------------------------------------------------------------

# A key path into the raw config dict, and whether a missing final key may drop its parent entry instead
_ResetPath = Tuple[Tuple[Any, ...], bool]

# Each pass deletes at least one value that is present, so this only bounds a schema bug
_MAX_REPAIR_PASSES = 100

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def load_config_from_json(path: str, logger: Optional[Logger] = None, fail_if_missing: bool = False,
                          read_only: bool = False) -> PngSettings:
    """
    Load and validate configuration from JSON, repairing what is invalid.

    - If file missing --> write defaults
    - If a field or dict entry is invalid --> reset only that value to its default
    - If a rule between fields fails (e.g. two equal ports) --> reset every field the rule names
    - If a section cannot be repaired, or is not an object --> reset that section
    - If new fields added --> merge them in
    - Invalid file --> backup and rewrite

    Args:
        path (str): Path to the JSON file.
        logger (Optional[Any]): Logger for debug/info logs.
        fail_if_missing (bool): Whether to fail if the config file is missing.
        read_only (bool): Repair in memory only: never write, create or back up the file. Launcher-managed
            subsystems load this way, so the launcher is the file's only writer.

    Returns:
        PngSettings: Fully validated config with missing or invalid parts repaired.

    Raises:
        FileNotFoundError: If fail_if_missing is True and the config file is missing.
    """
    if os.path.exists(path):
        raw = _load_raw_json(path, logger, read_only)
        model, repaired = _validate_with_repairs(raw, logger)
        if not read_only:
            _maybe_update_config(raw, model, path, logger, repaired)
        _log_invalid_keys(raw, model, logger)
        return model

    if fail_if_missing:
        raise FileNotFoundError(f"Config file not found: {path}")

    model = PngSettings()
    if read_only:
        if logger:
            logger.info("No config at %s, using defaults", path)
        return model

    # No config file --> create full defaults
    if logger:
        logger.info("No config at %s, writing defaults", path)
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


def _load_raw_json(path: str, logger: Optional[Logger], read_only: bool = False) -> Dict[str, Any]:
    """Read JSON safely and provide empty dict on catastrophic failure, backing the file up unless read_only."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if not isinstance(raw, dict):
            raise ValueError(f"top level is {type(raw).__name__}, expected an object")
        return raw
    except Exception as e: # pylint: disable=broad-exception-caught
        if logger:
            logger.error("Could not parse JSON config: %s", e)
        if not read_only:
            _backup_invalid_file(path, logger)
        return {}


def _validate_with_repairs(raw: Dict[str, Any], logger: Optional[Logger]) -> Tuple[PngSettings, bool]:
    """
    Validate every section, then the cross-section rules, resetting invalid values until the config is valid.
    Returns the settings and whether anything was reset.
    """
    data = copy.deepcopy(raw)
    repaired = False

    for _ in range(_MAX_REPAIR_PASSES):
        sections: Dict[str, BaseModel] = {}
        for section_name in PngSettings.model_fields:
            sections[section_name], section_repaired = _validate_section(data, section_name, logger)
            repaired |= section_repaired

        try:
            return PngSettings(**sections), repaired
        except ValidationError as e:
            # Sanity guard, unreached while every cross-section rule raises ConflictError naming its fields
            if not _reset(data, _reset_paths(e), logger):
                if logger:
                    logger.debug("%s", e)
                break
            repaired = True

    if logger:
        logger.error("Could not repair the config across sections, using defaults for all of it.")
    return PngSettings(), True


def _validate_section(data: Dict[str, Any], section_name: str, logger: Optional[Logger]) -> Tuple[BaseModel, bool]:
    """
    Validate one section of data in place, resetting invalid values in it. Falls back to the section's defaults
    if the section is not an object or cannot be repaired. Returns the section and whether anything was reset.
    """
    model_field = PngSettings.model_fields[section_name]
    section_data = data.setdefault(section_name, {})
    repaired = False

    if isinstance(section_data, dict):
        for _ in range(_MAX_REPAIR_PASSES):
            try:
                return model_field.annotation.model_validate(section_data), repaired
            except ValidationError as e:
                # Sanity guard, unreached while every rule raises ConflictError naming its fields
                if not _reset(section_data, _reset_paths(e), logger, prefix=section_name):
                    if logger:
                        logger.debug("%s", e)
                    break
                repaired = True
            except Exception as e: # pylint: disable=broad-exception-caught
                # A validator raised something other than ValueError, so no field to point at: reset the section
                if logger:
                    logger.error("Unexpected %s validating section [%s]: %s", type(e).__name__, section_name, e)
                break

    if logger:
        logger.warning("Invalid config in section [%s], using defaults.", section_name)
    data[section_name] = {}
    return model_field.default_factory(), True


def _reset_paths(error: ValidationError) -> Iterator[_ResetPath]:
    """The raw-data paths to reset for each error: the fields a ConflictError names, else the error's own loc."""
    for err in error.errors():
        loc = tuple(err["loc"])
        exc = err.get("ctx", {}).get("error")
        if isinstance(exc, ConflictError):
            for field in exc.fields:
                yield loc + tuple(field.split(".")), False
        else:
            # A missing required field cannot be deleted; drop the dict entry that holds it instead
            yield loc, err["type"] == "missing"


def _reset(data: Dict[str, Any], paths: Iterator[_ResetPath], logger: Optional[Logger], prefix: str = "") -> bool:
    """Delete each path that is present from data, so its default applies. Returns whether anything was deleted."""
    deleted = False
    for path, parent_if_missing in paths:
        if path and not _has_path(data, path) and parent_if_missing:
            path = path[:-1]
        if not path or not _has_path(data, path):
            continue

        parent = _get_path(data, path[:-1])
        if logger:
            name = ".".join(str(part) for part in (prefix, *path) if part != "")
            logger.warning("Invalid config value at [%s] (%r), using its default.", name, parent[path[-1]])
        del parent[path[-1]]
        deleted = True
    return deleted


def _has_path(data: Any, path: Tuple[Any, ...]) -> bool:
    node = data
    for key in path:
        if not isinstance(node, dict) or key not in node:
            return False
        node = node[key]
    return True


def _get_path(data: Dict[str, Any], path: Tuple[Any, ...]) -> Any:
    node = data
    for key in path:
        node = node[key]
    return node


def _log_invalid_keys(raw: Dict[str, Any], model: PngSettings, logger: Optional[Logger]) -> None:
    if not logger:
        return

    model_dict = model.model_dump()

    for section, items in raw.items():
        if section not in model_dict:
            logger.debug("Ignored unknown section [%s]", section)
            continue

        if isinstance(items, dict):
            for key in items.keys():
                if key not in model_dict[section]:
                    logger.debug("Ignored unknown key [%s].[%s]", section, key)


def _maybe_update_config(
    raw: Dict[str, Any],
    model: PngSettings,
    path: str,
    logger: Optional[Logger],
    repaired: bool,
) -> None:
    """
    Rewrite the file if anything was repaired, new fields appeared, or the on-disk content differs. A repaired
    file is backed up first.
    """
    if repaired or raw != model.model_dump():
        if repaired:
            _backup_invalid_file(path, logger)
        save_config_to_json(model, path)


def _backup_invalid_file(path: str, logger: Optional[Logger]):
    backup = f"{path}.invalid"
    shutil.move(path, backup)
    if logger:
        logger.info("Backed up invalid JSON config to %s", backup)
