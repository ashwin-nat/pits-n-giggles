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

import asyncio

from apps.backend.app_ctx import AppCtx
from apps.backend.state_mgmt_layer import SessionState
from lib.error_status import PngTelemetryPortInUseError, is_port_in_use_error

from .telemetry_forwarder import setupForwarder
from .telemetry_handler import F1TelemetryHandler, setupTelemetryTask

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def initTelemetryLayer(
        ctx: AppCtx,
        replay_server: bool,
        session_state: SessionState) -> F1TelemetryHandler:
    """Initialize the telemetry layer

    Args:
        ctx (AppCtx): Backend app context (logger, settings, subsystem). The subsystem's
            add_task registers the telemetry/forwarder tasks, and fire_and_forget dispatches
            frontend/HUD notifications and the dealer routes.
        replay_server (bool): Whether to enable the TCP replay debug server.
        session_state (SessionState): Handle to the session state

    Returns:
        F1TelemetryHandler: Telemetry handler
    """

    # Kept as a plain queue rather than fire_and_forget - per-packet forwarding at telemetry
    # rate would otherwise spawn a task per packet.
    packet_forward_queue: asyncio.Queue = asyncio.Queue()

    try:
        handler = setupTelemetryTask(
            ctx=ctx,
            replay_server=replay_server,
            session_state=session_state,
            packet_forward_queue=packet_forward_queue,
        )
    except OSError as e:
        ctx.logger.error("setupTelemetryTask failed with error %s", e)
        if is_port_in_use_error(e.errno):
            raise PngTelemetryPortInUseError() from e
        raise  # Re-raise if it's a different OSError

    udp_forwarder = setupForwarder(
        forwarding_targets=ctx.settings.Forwarding.forwarding_targets,
        packet_forward_queue=packet_forward_queue,
        add_task=ctx.subsystem.add_task,
        shutdown_event=ctx.subsystem.shutdown_event,
        logger=ctx.logger
    )
    handler.set_udp_forwarder(udp_forwarder)
    return handler
