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
import logging
import os
from typing import Dict, Optional

import webview

from lib.button_debouncer import ButtonDebouncer
from lib.child_proc_mgmt import notify_parent_init_complete
from lib.config import PngSettings
from lib.file_path import resolve_user_file

from .config import OverlaysConfig
from .infra import WindowManager

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

_DEFAULT_OVERLAYS_CONFIG: Dict[str, OverlaysConfig] = {
    'lapTimer': OverlaysConfig(
        x=10,
        y=300,
        width=280,
        height=380,
    ),
    'timingTower': OverlaysConfig(
        x=10,
        y=55,
        width=450,
        height=270,
    ),
}

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class OverlaysMgr:
    def __init__(self,
                 logger: logging.Logger,
                 settings: PngSettings,
                 config_file: Optional[str] = 'png_overlays.json',
                 debug: bool = False):
        """Construct a new OverlaysMgr object. Ctor will init config files and windows

        Args:
            logger (logging.Logger): Logger object
            settings (PngSettings): App Settings
            config_file (str, optional): Path to config file. Defaults to 'png_overlays.json'.
            debug (bool, optional): Debug mode. Defaults to False.
        """
        self.logger = logger
        self.config_file = resolve_user_file(config_file)
        self.debouncer = ButtonDebouncer(debounce_time=1.0)
        self.debug_mode = debug
        self._init_config()

        assert settings.HUD.enabled, "HUD must be enabled to run overlays manager"
        self.window_manager = WindowManager(logger)

        if settings.HUD.show_lap_timer:
            window_id = 'lapTimer'
            self._init_window_by_id(window_id)
            self.logger.debug(f"Created window '{window_id}'")
        else:
            self.logger.debug("Lap timer overlay is disabled")

        if settings.HUD.show_timing_tower:
            window_id = 'timingTower'
            self._init_window_by_id(window_id)
            self.logger.debug(f"Created window '{window_id}'")
        else:
            self.logger.debug("Timing tower overlay is disabled")

    def run(self):
        """Start the overlays manager"""
        webview.start(notify_parent_init_complete, debug=self.debug_mode)

    def on_locked_state_change(self, args: Dict[str, bool]):
        """Handle locked state change"""
        self.window_manager.set_locked_state_all(args)
        locked_value = args.get('new-value')
        if not locked_value:
            return

        changed = False
        for window_id, window_params in self.config.items():
            curr_params = self.window_manager.get_window_info(window_id)
            if curr_params != window_params:
                self.logger.debug(f"Updating config for window '{window_id}' to {curr_params}")
                self.config[window_id] = curr_params
                changed = True

        if changed:
            self._save_config()

    def race_table_update(self, data):
        """Handle race table update"""
        self.window_manager.broadcast_data(data)

    def toggle_overlays_visibility(self):
        """Toggle overlays visibility"""
        if self.debouncer.onButtonPress("toggle_overlays_visibility"):
            self.logger.debug("Toggling overlays visibility")
            self.window_manager.toggle_visibility_all()
        else:
            self.logger.debug("Not toggling overlays visibility. Reason: debounce")

    def stop(self):
        """Stop the overlays manager"""
        self.window_manager.stop()

    def _get_html_path_for_window(self, window_id: str) -> str:
        """Constructs the absolute path to the HTML file for a given window ID."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        html_file_path = os.path.join(base_dir, "..", "overlays", window_id, f"{window_id}.html")
        return html_file_path

    def _init_config(self):
        """"Load config file if it exists. Else, use default config."""
        should_write = False
        config = self._load_config()
        if not config:
            self.config = _DEFAULT_OVERLAYS_CONFIG
            self.logger.debug("Using default config")
            should_write = True
        else:
            # Check if any keys are missing from default config and add them with default values
            for key, value in _DEFAULT_OVERLAYS_CONFIG.items():
                if key not in config:
                    config[key] = value
                    self.logger.debug(f"Missing overlay config key. Added {key} to config")
                    should_write = True

            self.config = config
            json_str = json.dumps({k: v.toJSON() for k, v in self.config.items()}, indent=2)
            self.logger.debug(f"Final loaded config: \n{json_str}")
        if should_write:
            pass

    def _save_config(self):
        """"Save config file"""
        json_str = json.dumps({k: v.toJSON() for k, v in self.config.items()}, indent=2)
        self.logger.debug(f"Saving config to {self.config_file}. Config: \n{json_str}")
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump({k: v.toJSON() for k, v in self.config.items()}, f, indent=4)

    def _load_config(self) -> Optional[Dict[str, OverlaysConfig]]:
        """"Load config file if it exists. Else, return None"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    try:
                        parsed_contents = json.load(f)
                        return {
                            window_name: OverlaysConfig.fromJSON(params)
                            for window_name, params in parsed_contents.items()
                        }
                    except Exception as e: # pylint: disable=broad-exception-caught
                        self.logger.error(f"Failed to load config file: {e}. Falling back to default config")
            except Exception as e: # pylint: disable=broad-exception-caught
                self.logger.error(f"Failed to load config file: {e}. Falling back to default config")

        return None

    def _init_window_by_id(self, window_id: str) -> None:
        """Initialize a window by its ID"""
        window_config = self.config.get(window_id)
        assert window_config, f"Window '{window_id}' not found in config"
        self.window_manager.create_window(
            window_id=window_id,
            html_path=self._get_html_path_for_window(window_id),
            params=window_config)
        self.logger.info(f"Created window '{window_id}'")
