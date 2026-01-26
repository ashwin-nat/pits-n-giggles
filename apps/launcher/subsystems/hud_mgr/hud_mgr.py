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
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple

from pydantic import ValidationError
from PySide6.QtWidgets import QPushButton

from lib.button_debouncer import ButtonDebouncer
from lib.config import (INPUT_TELEMETRY_OVERLAY_ID, LAP_TIMER_OVERLAY_ID,
                        MFD_OVERLAY_ID, TIMING_TOWER_OVERLAY_ID,
                        TRACK_MAP_OVERLAY_ID, TRACK_RADAR_OVERLAY_ID,
                        HudSettings, OverlayPosition, PngSettings)
from lib.ipc import IpcClientSync

from ..base_mgr import PngAppMgrBase
from .popup import OverlaysAdjustPopup, SliderItem

if TYPE_CHECKING:
    from apps.launcher.gui import PngLauncherWindow


# -------------------------------------- BUTTON CONFIGURATION ----------------------------------------------------------

@dataclass
class ButtonConfig:
    """Configuration for a button"""
    name: str
    icon: str
    callback: Callable
    tooltip: str
    enabled_when_stopped: bool = False


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
        self.debouncer = ButtonDebouncer(debounce_time=0.5)
        self.integration_test_thread = None
        self.integration_test_stop_event = threading.Event()

        # Button registry
        self.buttons: Dict[str, QPushButton] = {}

        super().__init__(
            module_path="apps.hud",
            display_name="HUD",
            short_name="HUD",
            start_by_default=(self.supported and self.enabled),
            should_display=True,
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

        self.overlays_adj_popup = OverlaysAdjustPopup(self.window)
        self.overlays_adj_popup.hide()

    def _get_button_configs(self) -> List[ButtonConfig]:
        """Define button configurations

        Returns:
            List of button configurations in display order
        """
        return [
            ButtonConfig(
                name="start_stop",
                icon="start",
                callback=self.start_stop_callback,
                tooltip="Start",
                enabled_when_stopped=True
            ),
            ButtonConfig(
                name="hide_show",
                icon="show-hide",
                callback=self.hide_show_callback,
                tooltip="Hide/Show"
            ),
            ButtonConfig(
                name="next_page",
                icon="next-page",
                callback=self.next_page_callback,
                tooltip="Next MFD Page"
            ),
            ButtonConfig(
                name="reset",
                icon="reset",
                callback=self.reset_callback,
                tooltip="Reset Overlays Positions"
            ),
            ButtonConfig(
                name="lock",
                icon="unlock",
                callback=self.lock_callback,
                tooltip="Edit Overlays"
            ),
            ButtonConfig(
                name="mfd_interact",
                icon="mfd-interact",
                callback=self.mfd_interact_callback,
                tooltip="MFD Interact"
            )
        ]

    def get_buttons(self) -> List[QPushButton]:
        """Return a list of button objects directly
        :return: List of button objects
        """
        button_list = []
        for config in self._get_button_configs():
            btn = self.build_button(
                self.get_icon(config.icon),
                config.callback,
                config.tooltip
            )
            self.buttons[config.name] = btn

            # Set initial state based on enabled flag
            if not self.enabled:
                self.set_button_state(btn, False)

            button_list.append(btn)

        return button_list

    def _update_all_button_states(self, running: bool):
        """Update all button states based on running state

        Args:
            running: Whether the HUD is currently running
        """
        configs = {cfg.name: cfg for cfg in self._get_button_configs()}

        for name, btn in self.buttons.items():
            config = configs.get(name)
            if not config:
                continue

            # Enable button if running OR if it's enabled when stopped
            should_enable = running or config.enabled_when_stopped
            self.set_button_state(btn, should_enable)

    def hide_show_callback(self):
        """Open the dashboard viewer in a web browser."""
        self.info_log("Sending hide/show command to HUD...")
        rsp = IpcClientSync(self.ipc_port).request(
            command="toggle-overlays-visibility", args={}
        )
        self.info_log(str(rsp))

    def lock_callback(self):
        """Lock or unlock the HUD from receiving data."""
        if not self.debouncer.onButtonPress("lock_button"):
            self.debug_log("Lock button press debounced.")
            return

        self.debug_log("Toggling HUD lock state...")
        self.set_button_state(self.buttons["lock"], False)

        requested_state = not self.locked
        success, rsp = self._request_lock_state_change(
            old_value=self.locked,
            new_value=requested_state,
        )

        self.locked = requested_state
        self.set_button_state(self.buttons["lock"], True)

        if success:
            # Update lock button icon and tooltip based on new state
            if self.locked:
                self.set_button_icon(self.buttons["lock"], self.get_icon("unlock"))
                self.set_button_tooltip(self.buttons["lock"], "Edit Overlays")
            else:
                self.set_button_icon(self.buttons["lock"], self.get_icon("lock"))
                self.set_button_tooltip(self.buttons["lock"], "Lock Overlays")

            if self.locked:
                try:
                    self._save_layout_if_changed(rsp)
                except Exception as e:  # pylint: disable=broad-except
                    self.error_log(f"Failed to persist HUD layout: {e}")

        else:
            self.error_log("Failed to toggle lock state.")

        if self.locked:
            self.overlays_adj_popup.hide()
        else:
            self.show_scale_popup()

    def reset_callback(self):
        """Reset HUD overlays to default layout."""
        self.info_log("Sending reset overlays command to HUD...")

        default_layout_json = HudSettings.get_default_layout_json()
        try:
            rsp = IpcClientSync(self.ipc_port).request(
                command="set-overlays-layout",
                args={
                    "layout": default_layout_json,
                },
            )
        except Exception as e: # pylint: disable=broad-except
            self.error_log(f"IPC request failed while resetting overlays: {e}")
            return

        status = rsp.get("status")
        if status != "success":
            self.error_log(f"Failed to reset HUD overlays: {rsp.get("error", "unknown error")}")
            return

        # IPC success - write defaults
        try:
            self._save_new_layout_to_disk(
                new_layout=HudSettings.get_default_layout_dict()
            )
            self.info_log("HUD overlays reset to defaults and saved successfully.")
        except Exception as e:  # pylint: disable=broad-except
            self.error_log(f"Failed to persist default HUD layout: {e}")

    def next_page_callback(self):
        """Cycle to the next page of the HUD."""
        self.info_log("Sending next page command to HUD...")
        rsp = IpcClientSync(self.ipc_port).request(
            command="next-page", args={}
        )
        self.info_log(str(rsp))

    def mfd_interact_callback(self):
        """Interact with the MFD."""
        self.info_log("Sending MFD interact command to HUD...")
        rsp = IpcClientSync(self.ipc_port).request(
            command="mfd-interact", args={}
        )
        self.info_log(str(rsp))

    def start(self, reason: str):
        """Check for enabled flag before starting"""
        self.debug_log(f"Starting {self.display_name}... Reason: {reason}")
        if not self.enabled:
            self.debug_log(f"{self.display_name} is not enabled.")
            self._update_status("Disabled")
            return

        if not self.supported:
            self.debug_log(f"{self.display_name} is not supported.")
            self._update_status("Unsupported")
            return

        # Run the standard start
        super().start(reason)

    def post_start(self):
        """Update buttons after app start"""
        self._update_all_button_states(running=True)

        # Update start/stop button to show stop state
        self.set_button_icon(self.buttons["start_stop"], self.get_icon("stop"))
        self.set_button_tooltip(self.buttons["start_stop"], "Stop")

        # Start integration test thread if in integration test mode
        if self.integration_test_mode:
            self._start_integration_test_thread()

    def post_stop(self):
        """Update buttons after app stop"""
        # Stop integration test thread if running
        if self.integration_test_mode:
            self._stop_integration_test_thread()

        self._update_all_button_states(running=False)

        # Update start/stop button to show start state
        self.set_button_icon(self.buttons["start_stop"], self.get_icon("start"))
        self.set_button_tooltip(self.buttons["start_stop"], "Start")

    def start_stop_callback(self):
        """Start or stop the HUD subsystem."""
        # Disable all buttons during transition
        self._update_all_button_states(running=False)

        try:
            self.start_stop("Button pressed")
        except Exception as e: # pylint: disable=broad-exception-caught
            self.debug_log(f"{self.display_name}:Error during start/stop: {e}")
            # Re-enable buttons on error
            self._update_all_button_states(running=True)

    def process_enabled_change(self):
        """
        Process the enabled state change and update the GUI accordingly.

        If the application is enabled, start the HUD subsystem,
        enable the start/stop button, update the lock button text and
        enable the ping button. If the application is disabled, stop
        the HUD subsystem, disable the start/stop button and
        disable the ping and lock buttons.
        """
        if self.enabled:
            self.start("Enabling HUD")
        else:
            self.stop("Disabling HUD")
            self._update_all_button_states(running=False)

    def _send_overlays_opacity_change(self, opacity: int) -> None:
        """Send overlays opacity change to HUD app

        Args:
            opacity (int): New overlays opacity
        """
        self.debug_log("Sending set-overlays-opacity command to HUD...")
        rsp = IpcClientSync(self.ipc_port).request(command="set-overlays-opacity", args={
            "opacity": opacity,
        })
        if not rsp or rsp.get("status") != "success":
            self.error_log(f"Failed to set overlays opacity: {rsp}")
        else:
            self.debug_log(f"Set overlays opacity response: {rsp}")

    def _send_track_radar_idle_opacity_change(self, opacity: int) -> None:
        """Send track radar idle opacity change to HUD app

        Args:
            opacity (int): New track radar idle opacity
        """
        self.debug_log("Sending set-track-radar-idle-opacity command to HUD...")
        rsp = IpcClientSync(self.ipc_port).request(command="set-track-radar-idle-opacity", args={
            "opacity": opacity,
        })
        if not rsp or rsp.get("status") != "success":
            self.error_log(f"Failed to set track radar idle opacity: {rsp}")
        else:
            self.debug_log(f"Set track radar idle opacity response: {rsp}")

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
        """Handle changes in settings for the HUD subsystem

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
                "timing_tower_col_options",
                "show_mfd",
                "show_track_radar_overlay",
                "mfd_settings",
                "use_windowed_overlays",
            ],
            "Network": [
                "broker_xpub_port",
            ],
            "Display" : [
                "refresh_interval",
                "realtime_overlay_fps",
                "use_gpu_acceleration",
            ]
        }):
            self.debug_log(f"HUD settings changed. Restarting app. Diff: {json.dumps(
                settings_requiring_restart, indent=2)}")
            self.enabled = new_settings.HUD.enabled
            return True

        return False

    def _send_ui_scale_change_cmd(self, oid: str, data: Dict[str, Any]) -> None:
        """Send UI scale change command to HUD app

        Args:
            oid (str): Overlay ID
            data (Dict[str, Any]): UI scale data
        """
        self.debug_log(f"Sending set-ui-scale command to HUD with oid {oid} and data {data}")
        rsp = IpcClientSync(self.ipc_port).request(command="set-ui-scale", args={
            "oid": oid,
            "scale_factor": data["new_value"]
        })
        if not rsp or rsp.get("status") != "success":
            self.error_log(f"Failed to set {oid} UI scale: {rsp}")
        else:
            self.debug_log(f"Set {oid} UI scale response: {rsp}")

    def show_scale_popup(self):
        """Show the scale popup"""
        hud_settings = self.curr_settings.HUD

        # pylint: disable=unsubscriptable-object
        self.overlays_adj_popup.set_items([
            SliderItem(
                key=LAP_TIMER_OVERLAY_ID,
                label="Lap Timer Scale",
                min=HudSettings.model_fields["lap_timer_ui_scale"].json_schema_extra["ui"]["min_ui"],
                max=HudSettings.model_fields["lap_timer_ui_scale"].json_schema_extra["ui"]["max_ui"],
                value=int(hud_settings.lap_timer_ui_scale * 100),
            ),
            SliderItem(
                key=TIMING_TOWER_OVERLAY_ID,
                label="Timing Tower Scale",
                min=HudSettings.model_fields["timing_tower_ui_scale"].json_schema_extra["ui"]["min_ui"],
                max=HudSettings.model_fields["timing_tower_ui_scale"].json_schema_extra["ui"]["max_ui"],
                value=int(hud_settings.timing_tower_ui_scale * 100),
            ),
            SliderItem(
                key=MFD_OVERLAY_ID,
                label="MFD Scale",
                min=HudSettings.model_fields["mfd_ui_scale"].json_schema_extra["ui"]["min_ui"],
                max=HudSettings.model_fields["mfd_ui_scale"].json_schema_extra["ui"]["max_ui"],
                value=int(hud_settings.mfd_ui_scale * 100),
            ),
            # SliderItem(
            #     key=TRACK_MAP_OVERLAY_ID,
            #     label="Track Map Scale",
            #     min=HudSettings.model_fields["track_map_ui_scale"].json_schema_extra["ui"]["min_ui"],
            #     max=HudSettings.model_fields["track_map_ui_scale"].json_schema_extra["ui"]["max_ui"],
            #     value=int(hud_settings.track_map_ui_scale * 100),
            # ),
            SliderItem(
                key=INPUT_TELEMETRY_OVERLAY_ID,
                label="Input Telemetry Scale",
                min=HudSettings.model_fields["input_overlay_ui_scale"].json_schema_extra["ui"]["min_ui"],
                max=HudSettings.model_fields["input_overlay_ui_scale"].json_schema_extra["ui"]["max_ui"],
                value=int(hud_settings.input_overlay_ui_scale * 100),
            ),
            SliderItem(
                key=TRACK_RADAR_OVERLAY_ID,
                label="Track Radar Scale",
                min=HudSettings.model_fields["track_radar_overlay_ui_scale"].json_schema_extra["ui"]["min_ui"],
                max=HudSettings.model_fields["track_radar_overlay_ui_scale"].json_schema_extra["ui"]["max_ui"],
                value=int(hud_settings.track_radar_overlay_ui_scale * 100),
            ),

            # Opacity at the bottom
            SliderItem(
                key="overlays_opacity",
                label="Overlays Opacity",
                min=HudSettings.model_fields["overlays_opacity"].json_schema_extra["ui"]["min"],
                max=HudSettings.model_fields["overlays_opacity"].json_schema_extra["ui"]["max"],
                value=hud_settings.overlays_opacity,
            ),

            SliderItem(
                key="track_radar_idle_opacity",
                label="Track Radar Idle Opacity",
                min=HudSettings.model_fields["track_radar_idle_opacity"].json_schema_extra["ui"]["min"],
                max=HudSettings.model_fields["track_radar_idle_opacity"].json_schema_extra["ui"]["max"],
                value=hud_settings.track_radar_idle_opacity
            )
        ])
        self.overlays_adj_popup.set_confirm_callback(self._overlays_adj_popup_on_confirm)

        # Position below button
        btn = self.buttons["lock"]
        gpos = btn.mapToGlobal(btn.rect().bottomLeft())
        self.overlays_adj_popup.move(gpos)
        self.overlays_adj_popup.show()

    def _overlays_adj_popup_on_confirm(self, values: dict[str, int]):
        """
        Confirm callback for the overlays adjust popup.

        Applies slider values, forces Pydantic re-validation (including cross-field
        constraints), sends IPC updates, and persists settings on success.
        """

        # ---- Build candidate settings (ALLOW invalid intermediate state here) ----
        new_settings = self.curr_settings.model_copy(deep=True)
        new_settings.HUD.lap_timer_ui_scale = values[LAP_TIMER_OVERLAY_ID] / 100.0
        new_settings.HUD.timing_tower_ui_scale = values[TIMING_TOWER_OVERLAY_ID] / 100.0
        new_settings.HUD.mfd_ui_scale = values[MFD_OVERLAY_ID] / 100.0
        # new_settings.HUD.track_map_ui_scale = values[TRACK_MAP_OVERLAY_ID] / 100.0
        new_settings.HUD.input_overlay_ui_scale = values[INPUT_TELEMETRY_OVERLAY_ID] / 100.0
        new_settings.HUD.track_radar_overlay_ui_scale = values[TRACK_RADAR_OVERLAY_ID] / 100.0

        new_settings.HUD.overlays_opacity = values["overlays_opacity"]
        new_settings.HUD.track_radar_idle_opacity = values["track_radar_idle_opacity"]

        # ---- FORCE VALIDATION (this is the important bit) ----
        try:
            validated_settings = type(new_settings).model_validate(
                new_settings.model_dump()
            )
        except ValidationError as e:
            self.error_log("Invalid HUD settings from slider popup:")
            self.error_log(str(e))
            error_text = e.errors()[0]["msg"]
            self.error_log(error_text)

            self.show_error("Invalid HUD Settings", error_text)

            # Optional: show user feedback later (QMessageBox / toast / inline)
            return

        # ---- Compute diffs AFTER validation ----
        hud_diff = self.curr_settings.HUD.diff(
            validated_settings.HUD,
            [
                "lap_timer_ui_scale",
                "timing_tower_ui_scale",
                "mfd_ui_scale",
                "track_map_ui_scale",
                "input_overlay_ui_scale",
                "track_radar_overlay_ui_scale",
            ],
        )

        global_opacity_changed = (
            self.curr_settings.HUD.overlays_opacity
            != validated_settings.HUD.overlays_opacity
        )

        track_radar_idle_opacity_changed = (
            self.curr_settings.HUD.track_radar_idle_opacity
            != validated_settings.HUD.track_radar_idle_opacity
        )

        # ---- Apply runtime effects ----
        if global_opacity_changed:
            self._send_overlays_opacity_change(
                validated_settings.HUD.overlays_opacity
            )

        if track_radar_idle_opacity_changed:
            self._send_track_radar_idle_opacity_change(
                validated_settings.HUD.track_radar_idle_opacity
            )

        if hud_diff:
            key_to_oid = {
                "lap_timer_ui_scale": LAP_TIMER_OVERLAY_ID,
                "timing_tower_ui_scale": TIMING_TOWER_OVERLAY_ID,
                "mfd_ui_scale": MFD_OVERLAY_ID,
                "track_map_ui_scale": TRACK_MAP_OVERLAY_ID,
                "input_overlay_ui_scale": INPUT_TELEMETRY_OVERLAY_ID,
                "track_radar_overlay_ui_scale": TRACK_RADAR_OVERLAY_ID,
            }

            for key, data in hud_diff.items():
                oid = key_to_oid[key]
                self._send_ui_scale_change_cmd(oid, data)

        # ---- Persist only VALIDATED settings ----
        if hud_diff or global_opacity_changed or track_radar_idle_opacity_changed:
            self.window.update_settings(validated_settings)
            self.window.save_settings_to_disk(validated_settings)


    def _request_lock_state_change(self, old_value: bool, new_value: bool) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Send lock-widgets IPC request and validate response.

        Returns:
            (success, response)
        """
        try:
            rsp = IpcClientSync(self.ipc_port).request(
                command="lock-widgets",
                args={
                    "old-value": old_value,
                    "new-value": new_value,
                },
            )
        except Exception as e: # pylint: disable=broad-except
            self.error_log(f"IPC request failed: {e}")
            return False, None

        status = rsp.get("status")
        if status != "success":
            self.error_log(f"Lock-widgets IPC failed: {rsp.get("error", "unknown error")}")
            return False, rsp

        return True, rsp

    def _save_layout_if_changed(self, rsp: dict[str, Any]) -> None:
        """Save the layout if it has changed."""
        layout: Optional[Dict[str, Dict[str, int]]] = rsp.get("layout")
        if not layout:
            self.error_log(f"HUD layout not found in lock-widgets response: {json.dumps(rsp, indent=2)}")
            return

        should_write = False
        parsed_layout_dict = HudSettings.get_layout_dict_from_json(layout)
        for oid, overlay_layout in parsed_layout_dict.items():
            curr_cfg = self.curr_settings.HUD.layout.get(oid)
            if not curr_cfg:
                self.error_log(f"HUD layout for overlay {oid} not found in current settings. Aborting save.")
                return

            if curr_cfg.has_changed(overlay_layout):
                self.debug_log(f"Overlay {oid} layout has changed from {curr_cfg} to {overlay_layout}. "
                               "Saving to disk...")
                should_write = True

        if should_write:
            self._save_new_layout_to_disk(new_layout=parsed_layout_dict)
        else:
            self.debug_log("HUD layout has not changed. Not saving to disk...")

    def _save_new_layout_to_disk(self, new_layout: Dict[str, OverlayPosition]) -> None:
        """Save the new layout to disk and propagate the new settings to all subsystems"""
        new_settings = self.curr_settings.model_copy(deep=True)
        new_settings.HUD.layout = new_layout
        self.window.update_settings(new_settings)
        self.window.save_settings_to_disk(new_settings)
