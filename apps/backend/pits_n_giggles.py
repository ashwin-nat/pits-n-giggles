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

import argparse
import asyncio
from typing import Any, Dict, List, Optional, override

from apps.backend.intf_layer import (frontEndMessageTask,
                                     highFreqLocalUpdateTask,
                                     hudInteractionTask,
                                     lowFreqLocalUpdateTask)
from apps.backend.intf_layer.ipc import (handleCaptureConfigChange,
                                         handleForwardingConfigChange,
                                         handleManualSave,
                                         handleUdpActionCodeChange)
from apps.backend.intf_layer.request_handlers import handleDriverInfoRequest
from apps.backend.state_mgmt_layer import (SessionState,
                                           initStateManagementLayer)
from apps.backend.state_mgmt_layer.intf import RaceInfoData
from apps.backend.telemetry_layer import F1TelemetryHandler, initTelemetryLayer
from lib.inter_task_communicator import AsyncInterTaskCommunicator
from lib.ipc import PngAppId
from lib.subsystem import AsyncSubsystem, PubSubRole

# -------------------------------------- CLASS  DEFINITIONS ------------------------------------------------------------

class BackendSubsystem(AsyncSubsystem):
    """The dumb core - receives telemetry from the game, analyses it, and publishes the result.

    Has no HTTP server of its own: it publishes over pub/sub and answers pull requests over the
    router/dealer channel, and apps/web owns all browser-facing serving.
    """

    NAME = "backend"
    DESCRIPTION = "Realtime Telemetry Server"

    APP_ID = PngAppId.BACKEND
    PUBSUB = PubSubRole.PUBLISHER
    DEALER = True

    def __init__(self) -> None:
        """Construct the subsystem. Nothing is started until main() runs."""

        super().__init__()
        self.session_state: Optional[SessionState] = None
        self.telemetry_handler: Optional[F1TelemetryHandler] = None

    @override
    def add_args(self, parser: argparse.ArgumentParser) -> None:
        """Add the backend's own CLI flags.

        Args:
            parser (argparse.ArgumentParser): Parser to extend
        """

        parser.add_argument('--replay-server', action='store_true',
                            help="Enable the TCP replay debug server")

    @override
    async def setup(self) -> None:
        """Build the three backend layers and wire them to the IPC surfaces."""

        self.logger.info(
            "Starting F1 telemetry backend. NOTE: The tables will be empty until the red lights appear "
            "on the screen before the race start - that is when the game starts sending telemetry data")

        # The state and telemetry layers still take a task list rather than the registry. They
        # create the tasks; the registry adopts them so they are gathered and logged with the rest.
        layer_tasks: List[asyncio.Task] = []

        self.session_state = initStateManagementLayer(
            logger=self.logger,
            settings=self.settings,
            ver_str=self.version,
            tasks=layer_tasks,
            shutdown_event=self.shutdown_event)

        self.telemetry_handler = initTelemetryLayer(
            settings=self.settings,
            replay_server=self.args.replay_server,
            logger=self.logger,
            ver_str=self.version,
            shutdown_event=self.shutdown_event,
            session_state=self.session_state,
            tasks=layer_tasks)

        for task in layer_tasks:
            self.adopt_task(task)

        self._register_dealer_routes()
        self._register_mgmt_routes()
        self._register_publish_tasks()

    def _register_dealer_routes(self) -> None:
        """Answer the pull requests apps/web bridges from the browser."""

        @self.dealer.route("driver-info-request")
        async def _driver_info_request(data: dict, sender: str) -> dict:
            self.logger.debug("Received driver info request via router: %s from %s", data, sender)
            result = handleDriverInfoRequest(self.session_state, data.get("index"))
            if result.ok:
                return {"ok": True, "data": result.data}
            return {"ok": False, "error": result.detail, "error_code": result.error.name, "data": None}

        @self.dealer.route("race-info-request")
        async def _race_info_request(_data: dict, sender: str) -> dict:
            self.logger.debug("Received race info request via router from %s", sender)
            return RaceInfoData(self.session_state).toJSON()

    def _register_mgmt_routes(self) -> None:
        """Commands the launcher sends when the user changes settings or asks for a save."""

        @self.mgmt.on("manual-save")
        async def _manual_save(_args: dict) -> dict:
            return await handleManualSave(logger=self.logger, session_state=self.session_state)

        @self.mgmt.on("udp-action-code-change")
        async def _udp_action_code_change(args: dict) -> dict:
            return await handleUdpActionCodeChange(args, self.logger, self.telemetry_handler)

        @self.mgmt.on("forwarding-config-change")
        async def _forwarding_config_change(args: dict) -> dict:
            return await handleForwardingConfigChange(args, self.logger, self.telemetry_handler)

        @self.mgmt.on("capture-config-change")
        async def _capture_config_change(args: dict) -> dict:
            return await handleCaptureConfigChange(
                args, self.logger, self.telemetry_handler, self.session_state)

    def _register_publish_tasks(self) -> None:
        """The periodic publishes, plus the two event-driven forwarders."""

        self.add_periodic(
            self.settings.Display.local_telemetry_interval_ms,
            lowFreqLocalUpdateTask,
            self.session_state,
            self.publisher,
            name="Low Frequency Local Update Task")

        self.add_periodic(
            self.settings.Display.hud_refresh_interval,
            highFreqLocalUpdateTask,
            self.session_state,
            self.publisher,
            self.settings.StreamOverlay.show_sample_data_at_start,
            name="High Frequency Local Update Task")

        self.add_task(frontEndMessageTask(self.dealer, self.shutdown_event),
                      name="Front End Message Task")
        self.add_task(hudInteractionTask(self.dealer, self.shutdown_event),
                      name="HUD Interaction Task")

    @override
    def collect_stats(self) -> Dict[str, Any]:
        """Return ingress (telemetry in) and egress (IPC out) stats.

        Returns:
            Dict[str, Any]: Stats body
        """

        return {
            "ingress": self.telemetry_handler.getStats(),
            "egress": {
                "ipc_pub": self.publisher.get_stats(),
                "dealer": self.dealer.get_stats(),
            },
        }

    @override
    async def on_shutdown(self, reason: str) -> None:
        """Release the ITC receivers and stop the telemetry handler.

        The base closes the publisher and dealer once this returns.

        Args:
            reason (str): Why the shutdown was requested
        """

        self.logger.debug("Shutting down the backend. Reason: %s", reason)
        # Releases the frontend-update, hud-notifier, packet-forward and external-api-update
        # receivers from their await, so their tasks can see the shutdown event and exit.
        await AsyncInterTaskCommunicator().unblock_receivers()
        await self.telemetry_handler.stop()

# -------------------------------------- ENTRY POINT -------------------------------------------------------------------

def entry_point():
    """Entry point"""

    BackendSubsystem.main()
