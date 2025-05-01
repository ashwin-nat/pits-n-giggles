
# MIT License
#
# Copyright (c) [2024] [Ashwin Natarajan]
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
import logging
from dataclasses import dataclass, fields
from pathlib import Path
from typing import List, Tuple

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

@dataclass
class Config:
    """The data class containing the app config
    """
    telemetry_port: int
    server_port: int
    udp_custom_action_code: int
    udp_tyre_delta_action_code: int
    post_race_data_autosave: bool
    refresh_interval: int
    disable_browser_autoload: bool
    process_car_setup: bool
    forwarding_targets: List[Tuple[str, int]]
    stream_overlay_start_sample_data: bool

    def __repr__(self) -> str:
        """Return the string representation, formatted one key-value pair per line

        Returns:
            str: string representation
        """
        return "\n".join(f"{field.name}: {getattr(self, field.name)}" for field in fields(self))

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

_default_config = {
    'Network': {
        'telemetry_port': 20777,  # Integer
        'server_port': 5000,      # Integer
        'udp_custom_action_code': None,  # None (optional, not set by default)
        'udp_tyre_delta_action_code' : None,
    },
    'Capture': {
        'post_race_data_autosave': True,  # Boolean
    },
    'Display': {
        'refresh_interval': 200,  # Integer
        'disable_browser_autoload': False,  # Boolean
    },
    'Privacy': {
        'process_car_setup': True, # Boolean
    },
    'Forwarding': {
        'target1': '',
        'target2': '',
        'target3': '',
    },
    'Stream Overlay' : {
        'show_sample_data_at_start' : False, # Boolean
    }
}

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def load_config(config_file: str = "config.ini", logger: logging.Logger = None) -> Config:
    """Load settings from an INI file or create it if missing, and add new keys.

    Args:
        config_file (str, optional): Path to the config file. Defaults to "config.ini".
        logger (logging.Logger, optional): Logger instance. Defaults to None.

    Returns:
        Config: The config data object
    """

    def get_value_int(section: str, key: str) -> int:
        """Fetch integer value from INI or use default from _default_config.

        Args:
            section (str): Section name
            key (str): Key name

        Returns:
            int: Value as int for the given key under the given section
        """

        default_value = _default_config.get(section, {}).get(key, None)
        value = config.get(section, key, fallback=default_value)

        # Handle case where value is empty string or None
        return default_value if value == '' or value is None else int(value)

    def get_value_bool(section, key):
        """Fetch boolean value from INI or use default from _default_config.

        Args:
            section (str): Section name
            key (str): Key name

        Returns:
            int: Value as bool for the given key under the given section
        """

        default_value = _default_config.get(section, {}).get(key, False)
        value = config.get(section, key, fallback=str(default_value))

        # Handle case where value is empty string or None
        if value == '' or value is None:
            return default_value

        # Try converting to boolean
        return config.getboolean(section, key, fallback=default_value)

    def get_forwarding_targets() -> List[Tuple[str, int]]:
        """Parse the forwarding targets and return its list

        Raises:
            ValueError: _description_

        Returns:
            List[Tuple[str, int]]: _description_
        """

        section = config.items('Forwarding')
        ret_list = []

        for key, value in section:
            # Keys must begin with target
            if not key.startswith('target'):
                if logger:
                    logger.debug(f"config key {key} under Forwarding does not start with 'target'. Skipping")
                continue
            # empty values are valid, just skip
            if not value.rstrip():
                if logger:
                    logger.debug(f"Skipping key {key} because empty value")
                continue
            # Try to split the string at the colon
            try:
                ip_addr, port_str = value.rstrip().split(":", 1)  # Split only at the first colon
            except ValueError as exc:
                raise ValueError(
                    f"Forwarding target {key} is invalid. Must be of format ip_addr:port or hostname:port"
                ) from exc
            try:
                port = int(port_str)
            except ValueError as exc:
                raise ValueError(f"Forwarding target {key} has invalid port.") from exc

            ret_list.append((ip_addr, port))

        return ret_list

    config_path = Path(config_file)
    config = configparser.ConfigParser()

    # Check if the config file exists; if not, create an empty file
    if not config_path.exists():
        if logger:
            logger.debug(f"Config file {config_file} not found. Creating an empty config file.")
        config_path.touch()  # Creates an empty file

    # Read the configuration from the file
    config.read(config_file)

    # Populate missing sections and keys with default values from _default_config
    should_write = False
    for section, options in _default_config.items():
        if section not in config:
            config.add_section(section)
        for key, default_value in options.items():
            if key not in config[section]:
                # Convert non-string values to string before writing them into the config
                config[section][key] = str(default_value) if default_value is not None else ''
                if logger:
                    logger.debug(f"Missing config key {section}:{key}. Using default value: {str(default_value)}")
                should_write = True

    # Save the updated config back to the file
    if should_write:
        with open(config_file, 'w', encoding='utf-8') as f:
            config.write(f)

    # Create and return the Config object with values from INI file
    return Config(
        telemetry_port=get_value_int("Network", "telemetry_port"),
        server_port=get_value_int("Network", "server_port"),
        udp_custom_action_code=get_value_int("Network", "udp_custom_action_code"),
        udp_tyre_delta_action_code=get_value_int("Network", "udp_tyre_delta_action_code"),

        post_race_data_autosave=get_value_bool("Capture", "post_race_data_autosave"),

        refresh_interval=get_value_int("Display", "refresh_interval"),
        disable_browser_autoload=get_value_bool("Display", "disable_browser_autoload"),

        process_car_setup=get_value_bool("Privacy", "process_car_setup"),

        forwarding_targets=get_forwarding_targets(),

        stream_overlay_start_sample_data=get_value_bool("Stream Overlay", "show_sample_data_at_start"),
    )
