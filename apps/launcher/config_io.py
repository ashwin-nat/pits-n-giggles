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

import configparser
import os

from .config_schema import (CaptureSettings, DisplaySettings,
                            ForwardingSettings, LoggingSettings,
                            NetworkSettings, PngSettings, PrivacySettings)


def configparser_to_dict(cp: configparser.ConfigParser) -> dict:
    """Convert a ConfigParser object to a dictionary

    Args:
        cp (ConfigParser): The ConfigParser object to convert.

    Returns:
        dict: A dictionary representation of the ConfigParser object.
    """
    return {s: dict(cp.items(s)) for s in cp.sections()}

def dict_to_configparser(data: dict) -> configparser.ConfigParser:
    """Convert a dictionary to a ConfigParser object

    Args:
        data (dict): The dictionary to convert.

    Returns:
        ConfigParser: A ConfigParser object representation of the dictionary.
    """
    cp = configparser.ConfigParser()
    for section, values in data.items():
        cp[section] = {k: str(v) for k, v in values.items()}
    return cp

def load_config_from_ini(path: str) -> PngSettings:
    """Load a PngSettings model from an INI file.

    Args:
        path (str): The path to the INI file.

    Returns:
        PngSettings: The loaded PngSettings model.
    """
    cp = configparser.ConfigParser()
    if os.path.exists(path):
        cp.read(path)
        raw_dict = configparser_to_dict(cp)
        return PngSettings(**raw_dict)
    else:
        # Create default model and save it to file
        model = PngSettings(
            Network=NetworkSettings(),
            Capture=CaptureSettings(),
            Display=DisplaySettings(),
            Logging=LoggingSettings(),
            Privacy=PrivacySettings(),
            Forwarding=ForwardingSettings(),
        )
        save_config_to_ini(model, path)
        return model

def save_config_to_ini(settings: PngSettings, path: str) -> None:
    """Save a PngSettings model to an INI file.

    Args:
        settings (PngSettings): The PngSettings model to save.
        path (str): The path to the INI file.
    """
    cp = dict_to_configparser(settings.dict(by_alias=True))
    with open(path, 'w', encoding='utf-8') as f:
        cp.write(f)
