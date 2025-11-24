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
import sys
import threading
from typing import TYPE_CHECKING, Any, Dict, List

from PySide6.QtWidgets import QPushButton

from lib.button_debouncer import ButtonDebouncer
from lib.config import PngSettings, HudSettings, save_config_to_json
from lib.ipc import IpcParent

from ..base_mgr import PngAppMgrBase

from PySide6.QtWidgets import QWidget, QVBoxLayout, QSlider, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from .scale_popup import ScalePopup, SliderItem

if TYPE_CHECKING:
    from apps.launcher.gui import PngLauncherWindow


# -------------------------------------- CLASSES -----------------------------------------------------------------------

class HudAppMgr(PngAppMgrBase):
    """Implementation of PngApp for save viewer"""
    def __init__(self,
                 window: "PngLauncherWindow",
                 settings: PngSettings,
                 args: list[str],
                 debug_mode: bool,
                 integration_test_mode: bool,
                 coverage_enabled: bool):
        """Initialize the save viewer manager
        :param console_app: Reference to a console interface for logging
        :param settings: Settings object
        :param args: Command line arguments to pass to the save viewer subsystem
        :param debug_mode: Whether to run the save viewer in debug mode
        :param integration_test_mode: Whether to run the save viewer in integration test mode
        """
        self.port = settings.Network.save_viewer_port
        self.supported = (sys.platform == "win32") # Only supported on Windows
        self.enabled = settings.HUD.enabled
        self.integration_test_mode = integration_test_mode
        self.integration_test_interval = 2.0
        self.args = args + ["--debug"] if debug_mode else (args or [])
        self.locked = True # HUD starts locked by default
        self.debouncer = ButtonDebouncer(debounce_time=1.5)
        self.integration_test_thread = None
        self.integration_test_stop_event = threading.Event()
        super().__init__(
            http_port_conflict_settings_field='N/A',
            udp_port_conflict_settings_field="N/A",
            module_path="apps.hud",
            display_name="HUD",
            short_name="HUD",
            start_by_default=(self.supported and self.enabled),
            window=window,
            settings=settings,
            args=self.args,
            debug_mode=debug_mode,
            coverage_enabled=coverage_enabled,
            post_start_cb=self.post_start,
            post_stop_cb=self.post_stop,
        )
        if not self.enabled:
            self._update_status("Disabled")
        elif not self.supported:
            self._update_status("Unsupported")

        self.scale_popup = ScalePopup(self.window)
        self.scale_popup.hide()

    def get_buttons(self) -> List[QPushButton]:
        """Return a list of button objects directly
        :return: List of button objects
        """

        self.start_stop_button = self.build_button(self.get_icon("start"), self.start_stop_callback, "Start")
        self.hide_show_button = self.build_button(self.get_icon("show-hide"), self.hide_show_callback, "Hide/Show")
        self.lock_button = self.build_button(self.get_icon("unlock"), self.lock_callback, "Unlock Overlays")
        self.reset_button = self.build_button(self.get_icon("reset"), self.reset_callback, "Reset Overlays")
        self.next_page_button = self.build_button(self.get_icon("next-page"), self.next_page_callback, "Next MFD Page")
        self.scale_button = self.build_button(self.get_icon("aspect-ratio"), self.scale_callback, "Scale Overlays")

        if not self.enabled:
            self.set_button_state(self.start_stop_button, False)
            self.set_button_state(self.hide_show_button, False)
            self.set_button_state(self.lock_button, False)
            self.set_button_state(self.reset_button, False)
            self.set_button_state(self.next_page_button, False)
            self.set_button_state(self.scale_button, False)

        return [
            self.start_stop_button,
            self.hide_show_button,
            self.lock_button,
            self.reset_button,
            self.next_page_button,
            self.scale_button,
        ]

    def hide_show_callback(self):
        """Open the dashboard viewer in a web browser."""
        self.info_log("Sending hide/show command to HUD...")
        rsp = IpcParent(self.ipc_port).request(
            command="toggle-overlays-visibility", args={}
        )
        self.info_log(str(rsp))

    def lock_callback(self):
        """Lock or unlock the HUD from receiving data."""
        if not self.debouncer.onButtonPress("lock_button"):
            self.debug_log("Lock button press debounced.")
            return

        self.debug_log("Toggling HUD lock state...")
        self.set_button_state(self.lock_button, False)
        rsp = IpcParent(self.ipc_port).request(command="lock-widgets", args={
            "old-value": self.locked,
            "new-value": not self.locked,
        })
        self.locked = not self.locked
        self.info_log(str(rsp))

        self.set_button_state(self.lock_button, True)
        status = rsp.get("status", None)
        if status is not None:
            self.set_lock_button_icon()
        else:
            self.error_log("Failed to toggle lock state.")

    def reset_callback(self):
        """Open the dashboard viewer in a web browser."""
        self.info_log("Sending reset command to HUD...")
        rsp = IpcParent(self.ipc_port).request(command="reset-overlays", args={})
        self.info_log(str(rsp))

    def next_page_callback(self):
        """Open the dashboard viewer in a web browser."""
        self.info_log("Sending next page command to HUD...")
        rsp = IpcParent(self.ipc_port).request(
            command="next-page", args={}
        )
        self.info_log(str(rsp))

    def start(self, reason: str):
        """Check for enabled flag before starting"""
        self.debug_log(f"Starting {self.display_name}... Reason: {reason}")
        if not self.enabled:
            self.debug_log(f"{self.display_name} is not enabled.")
            self._update_status("Disabled")
            return

        # Run the standard start
        super().start(reason)

    def post_start(self):
        """Update buttons after app start"""
        self.set_button_state(self.hide_show_button, True)
        self.set_button_state(self.start_stop_button, True)
        self.set_button_icon(self.start_stop_button, self.get_icon("stop"))
        self.set_button_tooltip(self.start_stop_button, "Stop")
        self.set_button_state(self.lock_button, True)
        self.set_button_state(self.reset_button, True)
        self.set_button_state(self.next_page_button, True)
        self.set_button_state(self.scale_button, True)

        # Start integration test thread if in integration test mode
        if self.integration_test_mode:
            self._start_integration_test_thread()

    def post_stop(self):
        """Update buttons after app stop"""
        # Stop integration test thread if running
        if self.integration_test_mode:
            self._stop_integration_test_thread()

        self.set_button_state(self.hide_show_button, False)
        self.set_button_state(self.start_stop_button, True)
        self.set_button_icon(self.start_stop_button, self.get_icon("start"))
        self.set_button_tooltip(self.start_stop_button, "Start")
        self.set_button_state(self.lock_button, False)
        self.set_button_state(self.reset_button, False)
        self.set_button_state(self.next_page_button, False)
        self.set_button_state(self.scale_button, False)

    def start_stop_callback(self):
        """Start or stop the backend application."""
        # disable the button. enable in post_start/post_stop
        self.set_button_state(self.hide_show_button, False)
        self.set_button_state(self.start_stop_button, False)
        self.set_button_state(self.lock_button, False)
        self.set_button_state(self.reset_button, False)
        self.set_button_state(self.next_page_button, False)
        self.set_button_state(self.scale_button, False)
        try:
            # Call the start_stop method
            self.start_stop("Button pressed")
        except Exception as e: # pylint: disable=broad-exception-caught
            # Log the error or handle it as needed
            self.debug_log(f"{self.display_name}:Error during start/stop: {e}")
            # If no exception, it will be handled in post_start/post_stop
            self.set_button_state(self.hide_show_button, True)
            self.set_button_state(self.start_stop_button, True)
            self.set_button_state(self.lock_button, True)
            self.set_button_state(self.reset_button, True)
            self.set_button_state(self.next_page_button, True)
            self.set_button_state(self.scale_button, True)

    def set_lock_button_icon(self):
        """Set the icon and tooltip for the lock button based on state"""
        if self.locked:
            self.set_button_icon(self.lock_button, self.get_icon("unlock"))
            self.set_button_tooltip(self.lock_button, "Unlock Overlays")
        else:
            self.set_button_icon(self.lock_button, self.get_icon("lock"))
            self.set_button_tooltip(self.lock_button, "Lock Overlays")

    def process_enabled_change(self):
        """
        Process the enabled state change and update the GUI accordingly.

        If the application is enabled, start the backend application,
        enable the start/stop button, update the lock button text and
        enable the ping button. If the application is disabled, stop
        the backend application, disable the start/stop button and
        disable the ping and lock buttons.
        """

        if self.enabled:
            self.start("Enabling HUD")
            self.set_button_state(self.lock_button, True)
            self.set_lock_button_icon()
            self.set_button_state(self.hide_show_button, True)
        else:
            self.stop("Disabling HUD")
            self.set_button_state(self.start_stop_button, False)
            self.set_button_state(self.hide_show_button, False)
            self.set_button_state(self.lock_button, False)

    def _send_overlays_opacity_change(self, new_settings: PngSettings) -> None:
        """Send overlays opacity change to HUD app

        Args:
            new_settings (PngSettings): New settings
        """
        self.debug_log("Sending set-overlays-opacity command to HUD...")
        rsp = IpcParent(self.ipc_port).request(command="set-overlays-opacity", args={
            "opacity": new_settings.HUD.overlays_opacity,
        })
        if not rsp or rsp.get("status") != "success":
            self.error_log(f"Failed to set overlays opacity: {rsp}")
        else:
            self.debug_log(f"Set overlays opacity response: {rsp}")

    def _start_integration_test_thread(self):
        """Start the integration test thread"""
        self.integration_test_stop_event.clear()
        self.integration_test_thread = threading.Thread(
            target=self._integration_test_worker,
            daemon=True
        )
        self.integration_test_thread.start()
        self.info_log(
            f"Integration test thread started with interval {self.integration_test_interval}s"
        )

    def _stop_integration_test_thread(self):
        """Stop the integration test thread"""
        if self.integration_test_thread and self.integration_test_thread.is_alive():
            self.info_log("Stopping integration test thread...")
            self.integration_test_stop_event.set()
            self.integration_test_thread.join(timeout=5.0)
            self.info_log("Integration test thread stopped")

    def _integration_test_worker(self):
        """Worker thread that periodically calls next_page_callback"""
        while (not self.integration_test_stop_event.is_set()) and \
            (not self.integration_test_stop_event.wait(timeout=self.integration_test_interval)):
            self.next_page_callback()

    def on_settings_change(self, new_settings: PngSettings) -> bool:
        """Handle changes in settings for the backend application

        :param new_settings: New settings

        :return: True if the app needs to be restarted
        """

        # Enabling/disabling overlays requires subsystem restart
        if settings_requiring_restart := self.curr_settings.diff(new_settings, {
            "HUD": [
                "enabled",
                "show_lap_timer",
                "show_timing_tower",
                "timing_tower_max_rows",
                "show_mfd",
                "mfd_settings",
            ],
        }):
            self.debug_log(f"HUD settings changed. Restarting app. Diff: {json.dumps(
                settings_requiring_restart, indent=2)}")
            self.enabled = new_settings.HUD.enabled
            return True

        if self.curr_settings.diff(new_settings, {
            "HUD": [
                "overlays_opacity",
            ],
        }):
            self._send_overlays_opacity_change(new_settings)

        if diff := self.curr_settings.diff(new_settings, {
            "HUD": [
                "lap_timer_ui_scale",
                "timing_tower_ui_scale",
                "mfd_ui_scale",
            ],
        }):

            # TODO: figure out how to display status message in a message box, indicating that user will need to resize
            self.debug_log(f"UI scale changed. Diff: {json.dumps(diff, indent=2)}")
            key_to_oid: Dict[str, str] = {
                "lap_timer_ui_scale": "lap_timer",
                "timing_tower_ui_scale": "timing_tower",
                "mfd_ui_scale": "mfd",
            }
            for key, data in diff["HUD"].items():
                oid = key_to_oid[key]
                self._send_ui_scale_change_cmd(oid, data)

        return False

    def _send_ui_scale_change_cmd(self, oid: str, data: Dict[str, Any]) -> None:
        """Send UI scale change command to HUD app

        Args:
            oid (str): Overlay ID
            data (Dict[str, Any]): UI scale data
        """
        self.debug_log(f"Sending set-ui-scale command to HUD with oid {oid} and data {data}")
        rsp = IpcParent(self.ipc_port).request(command="set-ui-scale", args={
            "oid": oid,
            "scale_factor": data["new_value"]
        })
        if not rsp or rsp.get("status") != "success":
            self.error_log(f"Failed to set {oid} UI scale: {rsp}")
        else:
            self.debug_log(f"Set {oid} UI scale response: {rsp}")

    def scale_callback(self):
        self.debug_log("Scale button pressed")

        # Toggle
        if self.scale_popup.isVisible():
            self.scale_popup.hide()
            return

        hud_settings = self.curr_settings.HUD

        # Build items (NO per-slider callback)
        items = [
            SliderItem(
                key="lap_timer",
                label="Lap Timer Scale",
                min=HudSettings.model_fields["lap_timer_ui_scale"].json_schema_extra["ui"]["min_ui"],
                max=HudSettings.model_fields["lap_timer_ui_scale"].json_schema_extra["ui"]["max_ui"],
                value=int(hud_settings.lap_timer_ui_scale * 100),
            ),
            SliderItem(
                key="timing_tower",
                label="Timing Tower Scale",
                min=HudSettings.model_fields["timing_tower_ui_scale"].json_schema_extra["ui"]["min_ui"],
                max=HudSettings.model_fields["timing_tower_ui_scale"].json_schema_extra["ui"]["max_ui"],
                value=int(hud_settings.timing_tower_ui_scale * 100),
            ),
            SliderItem(
                key="mfd",
                label="MFD Scale",
                min=HudSettings.model_fields["mfd_ui_scale"].json_schema_extra["ui"]["min_ui"],
                max=HudSettings.model_fields["mfd_ui_scale"].json_schema_extra["ui"]["max_ui"],
                value=int(hud_settings.mfd_ui_scale * 100),
            ),
        ]

        # Rebuild popup UI
        self.scale_popup.set_items(items)
        self.scale_popup.set_confirm_callback(self._scale_popup_on_confirm)

        # Position below button
        btn = self.scale_button
        gpos = btn.mapToGlobal(btn.rect().bottomLeft())
        self.scale_popup.move(gpos)

        self.scale_popup.show()

    def _scale_popup_on_confirm(self, values: dict[str, int]):
        """Scale confirm callback. No guarantee that values have been changed"""

        new_settings = self.curr_settings.model_copy(deep=True)
        new_settings.HUD.timing_tower_ui_scale = values["timing_tower"] / 100.0
        new_settings.HUD.lap_timer_ui_scale = values["lap_timer"] / 100.0
        new_settings.HUD.mfd_ui_scale = values["mfd"] / 100.0

        diff = self.curr_settings.diff(new_settings, {
            "HUD": [
                "lap_timer_ui_scale",
                "timing_tower_ui_scale",
                "mfd_ui_scale",
            ],
        })
        self.debug_log(f"Scale confirm callback with values: {values}. Diff: {diff}. Bool={bool(diff)}")
        if diff:
            key_to_oid: Dict[str, str] = {
                "lap_timer_ui_scale": "lap_timer",
                "timing_tower_ui_scale": "timing_tower",
                "mfd_ui_scale": "mfd",
            }
            for key, data in diff["HUD"].items():
                oid = key_to_oid[key]
                self._send_ui_scale_change_cmd(oid, data)

            # Update current settings and save to disk
            self.curr_settings = new_settings
            try:
                save_config_to_json(new_settings, self.window.config_file_new)
            except Exception as e: # pylint: disable=broad-exception-caught
                self.error_log(f"Failed to save settings to {self.window.config_file_new}: {e}")

            self.debug_log("Settings saved successfully")
