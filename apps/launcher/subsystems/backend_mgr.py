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
import webbrowser
from dataclasses import replace
from typing import TYPE_CHECKING, List

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMenu, QPushButton, QToolButton, QWidget

from lib.config import PngSettings
from lib.error_status import (PNG_ERROR_CODE_HTTP_PORT_IN_USE,
                              PNG_ERROR_CODE_UDP_TELEMETRY_PORT_IN_USE)
from lib.ipc import IpcClientSync

from .base_mgr import ExitReason, PngAppMgrBase, PngAppMgrConfig

if TYPE_CHECKING:
    from apps.launcher.gui import PngLauncherWindow

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class BackendAppMgr(PngAppMgrBase):
    """Implementation of PngApp for backend services"""

    buttons_update_signal = Signal()

    MODULE_PATH = "apps.backend"
    DISPLAY_NAME = "Core"
    SHORT_NAME = "CORE"

    def __init__(self,
                 common_cfg: PngAppMgrConfig,
                 replay_server: bool):
        """Initialize the backend manager
        :param common_cfg: Common configuration for the backend app manager
        :param replay_server: Whether to run the replay server
        """

        extra_args = []
        extra_args.append("--run-ipc-server")
        if common_cfg.debug_mode:
            extra_args.append("--debug")
        if replay_server:
            extra_args.append("--replay-server")
        final_args = [*common_cfg.args, *extra_args]
        self.port = common_cfg.settings.Network.server_port
        self.proto = common_cfg.settings.HTTPS.proto
        self.additional_servers = common_cfg.settings.Network.additional_servers

        config = replace(common_cfg,
                         args=final_args,
                         post_start_cb=self.post_start,
                         post_stop_cb=self.post_stop
        )

        super().__init__(
            config=config,
        )
        self.register_exit_reason(PNG_ERROR_CODE_HTTP_PORT_IN_USE, ExitReason(
            code=PNG_ERROR_CODE_HTTP_PORT_IN_USE,
            status="HTTP Port Conflict",
            title="HTTP port in use",
            message="The HTTP port is already in use by another process. Please close the other process and try again or change the port.",
            can_restart=False,
            settings_field='Network -> "Pits n\' Giggles HTTP Server Port"'
        ))
        self.register_exit_reason(PNG_ERROR_CODE_UDP_TELEMETRY_PORT_IN_USE, ExitReason(
            code=PNG_ERROR_CODE_UDP_TELEMETRY_PORT_IN_USE,
            status="UDP Port Conflict",
            title="UDP port in use",
            message="The UDP port is already in use by another process. Please close the other process and try again or change the port.",
            can_restart=False,
            settings_field='Network -> "F1 UDP Telemetry Port"'
        ))
        self.buttons_update_signal.connect(self._update_dashboard_overlay_buttons)

    def get_buttons(self) -> List[QPushButton]:
        """Return a list of button objects directly
        :return: List of button objects
        """

        self.start_stop_button = self.build_button(self.get_icon("start"), self.start_stop_callback, "Start")
        self.manual_save_button = self.build_button(self.get_icon("save"), self.manual_save, "Manual Save")

        if self.additional_servers:
            # Split-button for Dashboard
            self.open_dashboard_button = self._build_split_button(
                self.get_icon("dashboard"), "Open Dashboard",
                self.open_dashboard, self._build_port_menu(is_overlay=False)
            )
            # Split-button for Stream Overlay
            self.open_obs_overlay_button = self._build_split_button(
                self.get_icon("twitch"), "Open Stream Overlay",
                self.open_obs_overlay, self._build_port_menu(is_overlay=True)
            )
        else:
            self.open_dashboard_button = self.build_button(self.get_icon("dashboard"), self.open_dashboard,
                                                           "Open Dashboard")
            self.open_obs_overlay_button = self.build_button(self.get_icon("twitch"), self.open_obs_overlay,
                                                             "Open Stream Overlay")

        buttons = [
            self.start_stop_button,
            self.open_dashboard_button,
            self.open_obs_overlay_button,
            self.manual_save_button,
        ]

        return buttons

    def _build_split_button(self, icon, tooltip, default_action, menu):
        """Build a composite split-button: icon button + dropdown arrow button."""
        container = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Main icon button — left side of the split, no right border-radius
        main_btn = QPushButton()
        main_btn.setIcon(icon)
        main_btn.setToolTip(tooltip)
        main_btn.setFixedSize(32, 32)
        main_btn.setStyleSheet("""
            QPushButton {
                background-color: #3e3e3e;
                border: 1px solid #4e4e4e;
                border-top-left-radius: 6px;
                border-bottom-left-radius: 6px;
                border-top-right-radius: 0px;
                border-bottom-right-radius: 0px;
                border-right: none;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #0e639c;
                border: 1px solid #1177bb;
                border-right: none;
            }
            QPushButton:pressed { background-color: #0d5689; }
            QPushButton:disabled {
                background-color: #2d2d2d;
                border-color: #2d2d2d;
                opacity: 0.4;
            }
        """)
        main_btn.clicked.connect(default_action)
        layout.addWidget(main_btn)

        # Arrow button — right side of the split, no left border-radius
        arrow_btn = QPushButton("\u25BC")
        arrow_btn.setFixedSize(18, 32)
        arrow_btn.setToolTip(f"{tooltip} (select port)")
        arrow_btn.setStyleSheet("""
            QPushButton {
                font-size: 8px;
                padding: 0px;
                background-color: #3e3e3e;
                border: 1px solid #4e4e4e;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
                border-top-left-radius: 0px;
                border-bottom-left-radius: 0px;
                border-left: none;
                color: #d4d4d4;
            }
            QPushButton:hover {
                background-color: #0e639c;
                border: 1px solid #1177bb;
                border-left: none;
            }
            QPushButton:pressed { background-color: #0d5689; }
            QPushButton:disabled {
                background-color: #2d2d2d;
                border-color: #2d2d2d;
                opacity: 0.4;
            }
            QPushButton::menu-indicator { image: none; width: 0px; }
        """)
        arrow_btn.setMenu(menu)
        layout.addWidget(arrow_btn)

        container.setLayout(layout)
        container.setFixedSize(50, 32)

        # Expose references so the rest of the code can enable/disable and swap icons
        container.main_btn = main_btn
        container.arrow_btn = arrow_btn
        container._menu = menu
        container.setEnabled = lambda enabled: (main_btn.setEnabled(enabled), arrow_btn.setEnabled(enabled))
        container.setIcon = main_btn.setIcon
        container.setToolTip = main_btn.setToolTip
        container.icon = main_btn.icon

        return container

    def _build_port_menu(self, is_overlay: bool) -> QMenu:
        """Build a dropdown menu listing all ports (primary + additional)."""
        menu = QMenu()
        path = "/player-stream-overlay" if is_overlay else ""

        primary_action = menu.addAction(f":{self.port}  (Primary)")
        primary_action.triggered.connect(
            lambda: self._open_url(f'{self.proto}://localhost:{self.port}{path}')
        )

        for server in self.additional_servers:
            label = server.label or ""
            display = f":{server.port}  {label}".strip()
            action = menu.addAction(display)
            p = server.port
            action.triggered.connect(
                lambda checked=False, port=p: self._open_url(
                    f'{self.proto}://localhost:{port}{path}'
                )
            )

        menu.addSeparator()
        open_all = menu.addAction("Open All")
        open_all.triggered.connect(lambda: self._open_all_ports(path))

        return menu

    def _open_all_ports(self, path: str = ""):
        """Open all configured ports in the browser."""
        self._open_url(f'{self.proto}://localhost:{self.port}{path}')
        for server in self.additional_servers:
            self._open_url(f'{self.proto}://localhost:{server.port}{path}')

    def _update_dashboard_overlay_buttons(self):
        """Rebuild dashboard/overlay buttons after additional_servers changed."""
        old_is_split = hasattr(self.open_dashboard_button, 'main_btn')
        new_needs_split = bool(self.additional_servers)

        if old_is_split and new_needs_split:
            # Same button type — just rebuild the menus
            self.open_dashboard_button.arrow_btn.setMenu(self._build_port_menu(is_overlay=False))
            self.open_obs_overlay_button.arrow_btn.setMenu(self._build_port_menu(is_overlay=True))
            return

        if not old_is_split and not new_needs_split:
            return

        # Button type changed — swap widgets in the layout
        was_dashboard_enabled = self.open_dashboard_button.isEnabled()
        was_overlay_enabled = self.open_obs_overlay_button.isEnabled()

        if new_needs_split:
            new_dashboard = self._build_split_button(
                self.get_icon("dashboard"), "Open Dashboard",
                self.open_dashboard, self._build_port_menu(is_overlay=False)
            )
            new_overlay = self._build_split_button(
                self.get_icon("twitch"), "Open Stream Overlay",
                self.open_obs_overlay, self._build_port_menu(is_overlay=True)
            )
        else:
            new_dashboard = self.build_button(
                self.get_icon("dashboard"), self.open_dashboard, "Open Dashboard"
            )
            new_overlay = self.build_button(
                self.get_icon("twitch"), self.open_obs_overlay, "Open Stream Overlay"
            )

        self._swap_button_in_layout(self.open_dashboard_button, new_dashboard)
        self._swap_button_in_layout(self.open_obs_overlay_button, new_overlay)

        self.open_dashboard_button = new_dashboard
        self.open_obs_overlay_button = new_overlay

        self.set_button_state(self.open_dashboard_button, was_dashboard_enabled)
        self.set_button_state(self.open_obs_overlay_button, was_overlay_enabled)

    def _swap_button_in_layout(self, old_button, new_button):
        """Replace a button widget in its parent layout."""
        if isinstance(new_button, QPushButton):
            new_button.setFixedSize(32, 32)
        parent = old_button.parentWidget()
        if parent and parent.layout():
            parent.layout().replaceWidget(old_button, new_button)
        old_button.setParent(None)
        old_button.deleteLater()

    @staticmethod
    def _open_url(url: str):
        """Open a URL in the default browser, with WSL2 fallback."""
        import subprocess, sys
        if sys.platform == 'linux':
            for cmd in (['wslview', url], ['cmd.exe', '/c', 'start', '', url]):
                try:
                    subprocess.Popen(
                        cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    return
                except FileNotFoundError:
                    continue
        webbrowser.open(url, new=2)

    def open_dashboard(self):
        """Open the dashboard viewer in a web browser."""
        self._open_url(f'{self.proto}://localhost:{self.port}')

    def open_obs_overlay(self):
        """Open the OBS overlay page in a web browser."""
        self._open_url(f'{self.proto}://localhost:{self.port}/player-stream-overlay')

    def on_settings_change(self, new_settings: PngSettings) -> bool:
        """Handle changes in settings for the backend application

        :param new_settings: New settings

        :return: True if the app needs to be restarted
        """

        # Update the port number
        self.port = new_settings.Network.server_port
        self.proto = new_settings.HTTPS.proto
        old_additional_servers = self.additional_servers
        self.additional_servers = new_settings.Network.additional_servers

        # Rebuild dashboard/overlay buttons if multi-port config changed
        if old_additional_servers != self.additional_servers:
            self.buttons_update_signal.emit()

        # Update UDP action codes if required
        if udp_action_codes_diff := self.curr_settings.diff(new_settings, {
            "Network": [
                "udp_tyre_delta_action_code",
                "udp_custom_action_code",
                "enable_pkt_ordering",
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
            ],
        }):
            for fields_in_category in udp_action_codes_diff.values():
                for field, diff in fields_in_category.items():
                    new_value = diff["new_value"]
                    self.send_udp_action_code_change(field, new_value)
        else:
            self.debug_log(f"{self.DISPLAY_NAME} UDP action codes NO CHANGE")

        if restart_required_fields_diff := self.curr_settings.diff(new_settings, {
            "Network": [
                "telemetry_port",
                "server_port",
                "wdt_interval_sec",
                "broker_xsub_port",
                "enable_pkt_ordering",
                "additional_servers",
            ],
            "Capture" : [],
            "Display" : [
                "refresh_interval",
            ],
            "Logging" : [],
            "Privacy" : [],
            "Forwarding" : [],
            "StreamOverlay" : [],
            "TimeLossInPitsF1": [],
            "TimeLossInPitsF2": [],
        }):
            self.debug_log(f"{self.DISPLAY_NAME} Restart required fields change: "
                           f"{json.dumps(restart_required_fields_diff, indent=2, default=str)}")
        else:
            self.debug_log(f"{self.DISPLAY_NAME} Restart required fields NO CHANGE")

        # Restart if diff is not empty
        return bool(restart_required_fields_diff)

    def post_start(self):
        """Update buttons after app start"""
        self.set_button_icon(self.start_stop_button, self.get_icon("stop"))
        self.set_button_tooltip(self.start_stop_button, "Stop")
        self.set_button_state(self.start_stop_button, True)
        self.set_button_state(self.start_stop_button, True)
        self.set_button_state(self.open_dashboard_button, True)
        self.set_button_state(self.open_obs_overlay_button, True)
        self.set_button_state(self.manual_save_button, True)

    def post_stop(self):
        """Update buttons after app stop"""
        self.set_button_icon(self.start_stop_button, self.get_icon("start"))
        self.set_button_tooltip(self.start_stop_button, "Start")
        self.set_button_state(self.start_stop_button, True)
        self.set_button_state(self.open_dashboard_button, False)
        self.set_button_state(self.open_obs_overlay_button, False)
        self.set_button_state(self.manual_save_button, False)

    def manual_save(self):
        """Send a manual save command to the backend."""
        self.debug_log("Sending manual save command to backend...")
        ipc_client = IpcClientSync(self.ipc_port)
        rsp = ipc_client.request("manual-save", {})

        status = rsp["status"]
        message = rsp.get("message")

        if status == "success":
            self.info_log(f"Manual save success. Path {message}")
            self.show_success("Manual Save Success", f"The session has been saved successfully at:\n{message}")

        else:
            error = rsp.get("error", "Unknown error")
            message = rsp.get("message", "")
            self.info_log(f"Error in manual save: error={error} message={message}")

            error_details = "\n".join(filter(None, [error, message]))
            self.show_error("Manual Save Error", error_details)

    def send_udp_action_code_change(self, action_code_field: str, value: int):
        """Send a UDP action code change command to the backend."""
        self.debug_log(f"Sending UDP action code change for {action_code_field} to backend...")
        ipc_client = IpcClientSync(self.ipc_port)
        rsp = ipc_client.request("udp-action-code-change", {"action_code_field": action_code_field, "value": value})
        if not rsp or rsp.get("status") != "success":
            self.error_log(f"Failed to change UDP action code: {rsp}")
        else:
            self.debug_log(f"Change UDP action code response: {rsp}")

    def start_stop_callback(self):
        """Start or stop the backend application."""
        # disable the button. enable in post_start/post_stop
        self.set_button_state(self.start_stop_button, False)
        self.set_button_state(self.manual_save_button, False)
        self.set_button_state(self.open_dashboard_button, False)
        self.set_button_state(self.open_obs_overlay_button, False)
        try:
            # Call the start_stop method
            self.start_stop("Stop button pressed")
        except Exception as e: # pylint: disable=broad-exception-caught
            # Log the error or handle it as needed
            self.debug_log(f"{self.DISPLAY_NAME}:Error during start/stop: {e}")
            # If no exception, it will be handled in post_start/post_stop
            self.set_button_state(self.start_stop_button, True)
