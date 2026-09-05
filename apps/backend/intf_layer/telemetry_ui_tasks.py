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

from apps.backend.state_mgmt_layer import SessionState
from apps.backend.state_mgmt_layer.intf import (PeriodicUpdateData,
                                                StreamOverlayData)
from lib.inter_task_communicator import AsyncInterTaskCommunicator
from lib.ipc import IpcDealerAsync, IpcPublisherAsync, PngAppId

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

async def lowFreqLocalUpdateTask(
        session_state: SessionState,
        ipc_pub: IpcPublisherAsync) -> None:
    """Low frequency local update task to publish periodic data

    Args:
        session_state (SessionState): The session state
        ipc_pub (IpcPublisherAsync): The IPC publisher
    """

    race_table_data = PeriodicUpdateData(session_state, send_position_data=True).toJSON()
    await ipc_pub.publish("race-table-update", race_table_data) # IPC publish is O(1) so do it always

async def highFreqLocalUpdateTask(
    session_state: SessionState,
    ipc_pub: IpcPublisherAsync,
    stream_overlay_start_sample_data: bool) -> None:
    """High frequency local update task to publish stream overlay data

    Args:
        session_state (SessionState): The session state
        ipc_pub (IpcPublisherAsync): The IPC publisher
        stream_overlay_start_sample_data (bool): Whether to show sample data at start
    """

    data = StreamOverlayData(session_state, export_hud_data=True, export_pu_data=True).toJSON(
        stream_overlay_start_sample_data)
    await ipc_pub.publish("stream-overlay-update", data)

async def frontEndMessageTask(
    dealer: IpcDealerAsync,
    shutdown_event: asyncio.Event) -> None:
    """Task to forward aperiodic frontend messages (toasts, markers, etc.) to apps/web via the
    router/dealer channel.

    Args:
        dealer (IpcDealerAsync): The ZeroMQ DEALER async client
        shutdown_event (asyncio.Event): Event to signal shutdown
    """

    while not shutdown_event.is_set():
        if message := await AsyncInterTaskCommunicator().receive("frontend-update"):
            await dealer.fire(str(PngAppId.WEB), "frontend-update", message.toJSON())

async def hudInteractionTask(
    dealer: IpcDealerAsync,
    shutdown_event: asyncio.Event) -> None:
    """Task to forward HUD button-press notifications via ZeroMQ DEALER.

    Args:
        dealer (IpcDealerAsync): The ZeroMQ DEALER async client
        shutdown_event (asyncio.Event): Event to signal shutdown
    """

    while not shutdown_event.is_set():
        if message := await AsyncInterTaskCommunicator().receive("hud-notifier"):
            await dealer.fire(str(PngAppId.HUD), str(message.m_message_type), message.toJSON())
