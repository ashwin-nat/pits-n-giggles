# MIT License
#
# Copyright (c) [2026] [Ashwin Natarajan]
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
from typing import List, Tuple

from lib.config import CaptureSettings, PngSettings
from lib.ipc import IpcClientSync

from ..base_mgr import PngAppMgrBase

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

class BackendSettingsChangeBase(PngAppMgrBase):
    """The settings-change half of BackendAppMgr: decides what a settings change means for the
    backend - which fields can be pushed to the running child over IPC, and which need a restart -
    and sends the live config change commands. Never instantiated on its own; BackendAppMgr
    supplies the identity fields and the lifecycle/UI half."""

    ABSTRACT = True

    def on_settings_change(self, new_settings: PngSettings) -> bool:
        """Handle changes in settings for the backend application

        :param new_settings: New settings

        :return: True if the app needs to be restarted
        """

        # Update UDP action codes if required
        if udp_action_codes_diff := self.curr_settings.diff(new_settings, {
            "Network": [
                "udp_tyre_delta_action_code",
                "udp_custom_action_code",
            ],
            "HUD": [
                "toggle_overlays_udp_action_code",
                "lap_timer_toggle_udp_action_code",
                "timing_tower_toggle_udp_action_code",
                "mfd_toggle_udp_action_code",
                "cycle_mfd_udp_action_code",
                "prev_mfd_page_udp_action_code",
                "input_overlay_toggle_udp_action_code",
                "track_radar_overlay_toggle_udp_action_code",
                "mfd_interaction_udp_action_code",
                "hud_overlay_toggle_udp_action_code",
                "circuit_info_toggle_udp_action_code",
                "pu_toggle_udp_action_code",
            ],
        }):
            for fields_in_category in udp_action_codes_diff.values():
                for field, diff in fields_in_category.items():
                    new_value = diff["new_value"]
                    self.send_udp_action_code_change(field, new_value)
        else:
            self.debug_log(f"{self.DISPLAY_NAME} UDP action codes NO CHANGE")

        # Update forwarding targets if changed - no restart needed
        if self.curr_settings.diff(new_settings, {"Forwarding": []}):
            self.send_forwarding_config_change(new_settings.Forwarding.forwarding_targets)
        else:
            self.debug_log(f"{self.DISPLAY_NAME} Forwarding targets NO CHANGE")

        # Update hot swappable capture settings if changed - no restart needed
        if capture_diff := self.curr_settings.diff(new_settings, {
            # Capture fields the backend can apply without a restart. Add a field here only after wiring it
            # into F1TelemetryHandler.updateCaptureSettings or SessionState.updateCaptureSettings - anything
            # else belongs in the restart required list below.
            "Capture": [
                "post_race_data_autosave",
                "post_quali_data_autosave",
                "post_fp_data_autosave",
                "post_tt_data_autosave",
                "save_race_ctrl_msg",
                "just_in_case_autosave",
            ],
        }):
            self.debug_log(f"{self.DISPLAY_NAME} Capture settings change: {json.dumps(capture_diff, indent=2)}")
            self.send_capture_config_change(new_settings.Capture)
        else:
            self.debug_log(f"{self.DISPLAY_NAME} Capture settings NO CHANGE")

        if restart_required_fields_diff := self.curr_settings.diff(new_settings, {
            "Network": [
                "telemetry_port",
                "wdt_interval_sec",
                "broker_xsub_port",
                "broker_router_port",
                "enable_pkt_ordering",
            ],
            "Capture" : [
                "session_dir",
            ],
            "Display" : [
                "local_telemetry_rate",
            ],
            "Logging" : [],
            "Privacy" : [],
            "StreamOverlay" : [],
            "TimeLossInPitsF1": [],
            "TimeLossInPitsF2": [],
            "Prediction": [],
            "HUD": [
                "menu_silence_threshold_sec",
            ],
        }):
            self.debug_log(f"{self.DISPLAY_NAME} Restart required fields change: "
                           f"{json.dumps(restart_required_fields_diff, indent=2)}")
        else:
            self.debug_log(f"{self.DISPLAY_NAME} Restart required fields NO CHANGE")

        # Restart if diff is not empty
        return bool(restart_required_fields_diff)

    def send_udp_action_code_change(self, action_code_field: str, value: int) -> None:
        """Send a UDP action code change command to the backend."""
        self.debug_log(f"Sending UDP action code change for {action_code_field} to backend...")
        ipc_client = IpcClientSync(self.ipc_port)
        rsp = ipc_client.request("udp-action-code-change", {"action_code_field": action_code_field, "value": value})
        if not rsp or rsp.get("status") != "success":
            self.error_log(f"Failed to change UDP action code: {rsp}")

    def send_forwarding_config_change(self, targets: List[Tuple[str, int]]) -> None:
        """Send updated forwarding targets to the backend without restarting it."""
        self.debug_log(f"Sending forwarding config change to backend. Targets: {targets}")
        ipc_client = IpcClientSync(self.ipc_port)
        rsp = ipc_client.request("forwarding-config-change", {"targets": [{"host": h, "port": p} for h, p in targets]})
        if not rsp or rsp.get("status") != "success":
            self.error_log(f"Failed to update forwarding config: {rsp}")
        else:
            self.debug_log(f"Forwarding config change response: {rsp}")

    def send_capture_config_change(self, capture_settings: CaptureSettings) -> None:
        """Send updated capture settings to the backend without restarting it.

        The whole section is sent; the backend picks out the fields it can apply live.
        """
        self.debug_log("Sending capture config change to backend...")
        self._send_simple_config_change("capture-config-change",
                                        {"capture": capture_settings.model_dump(mode="json")})

    def _send_simple_config_change(self, command: str, value: dict) -> None:
        """Send a simple config change command to the backend without restarting it."""
        ipc_client = IpcClientSync(self.ipc_port)
        rsp = ipc_client.request(command, value)
        if not rsp or rsp.get("status") != "success":
            self.error_log(f"Failed to update {command}: {rsp}")
        else:
            self.debug_log(f"{command} change response: {rsp}")
