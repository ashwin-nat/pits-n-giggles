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
from configparser import ConfigParser
from typing import Any

from .config_schema import PngSettings

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------


def load_config_from_ini(path: str) -> PngSettings:
    """Load and validate configuration from INI file.

    Args:
        path (str): Path to INI file.

    Returns:
        PngSettings: Parsed and validated configuration.
    """
    cp = ConfigParser()
    raw = {}

    if os.path.exists(path):
        cp.read(path)
        raw = {section: dict(cp.items(section)) for section in cp.sections()}

        # Pydantic v2: parse raw dict with coercion, nested models, validation
        model = PngSettings.model_validate(raw)

        # Save updated config if the loaded raw data differs from fully parsed+serialized model
        if raw != _stringify_dict(model.model_dump()):
            save_config_to_ini(model, path)
    else:
        model = PngSettings()
        save_config_to_ini(model, path)

    return model

def save_config_to_ini(settings: PngSettings, path: str) -> None:
    """Save PngSettings model to INI file.

    Args:
        settings (PngSettings): Parsed and validated configuration.
        path (str): Path to INI file.
    """
    cp = ConfigParser()
    cp.read_dict(settings.model_dump(by_alias=True))
    with open(path, 'w', encoding='utf-8') as f:
        cp.write(f)

def _stringify_dict(d: Any) -> Any:
    """
    Recursively converts all values in a nested dictionary to strings.

    Args:
        d (Any): The input data structure, typically a dictionary or a nested dictionary.

    Returns:
        Any: A new data structure with the same keys as `d`, but all leaf values converted to strings.
             Non-dict inputs are converted to strings directly.

    Example:
        >>> stringify_dict({'a': 1, 'b': {'c': True}})
        {'a': '1', 'b': {'c': 'True'}}
    """
    if isinstance(d, dict):
        # Recursively apply to each key-value pair
        return {k: _stringify_dict(v) for k, v in d.items()}
    # Base case: convert non-dict leaf value to string
    return str(d)