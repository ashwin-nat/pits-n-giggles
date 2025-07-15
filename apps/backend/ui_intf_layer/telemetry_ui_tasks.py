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
import logging
from typing import List, Optional

import msgpack
import socketio

import apps.backend.state_mgmt_layer as TelWebAPI
from lib.inter_task_communicator import AsyncInterTaskCommunicator

from .telemetry_web_server import TelemetryWebServer

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def initUiIntfLayer(
    port: int,
    logger: logging.Logger,
    client_update_interval_ms: int,
    debug_mode: bool,
    stream_overlay_start_sample_data: bool,
    tasks: List[asyncio.Task],
    ver_str: str,
    cert_path: Optional[str],
    key_path: Optional[str]) -> TelemetryWebServer:
    """Initialize the UI interface layer and return then server obj for proper cleanup

    Args:
        port (int): Port number
        logger (logging.Logger): Logger
        client_update_interval_ms (int): How often the client will be updated with new info
        debug_mode (bool): Debug enabled if true
        stream_overlay_start_sample_data (bool): Whether to show sample data in overlay until real data arrives
        tasks (List[asyncio.Task]): List of tasks to be executed
        ver_str (str): Version string
        cert_path (Optional[str]): Path to the certificate file
        key_path (Optional[str]): Path to the key file

    Returns:
        TelemetryWebServer: The initialized web server
    """

    # First, create the server instance
    web_server = TelemetryWebServer(
        port=port,
        ver_str=ver_str,
        logger=logger,
        cert_path=cert_path,
        key_path=key_path,
        debug_mode=debug_mode,
    )

    # Register tasks associated with this server
    tasks.append(asyncio.create_task(web_server.run(), name="Web Server Task"))
    tasks.append(asyncio.create_task(raceTableClientUpdateTask(client_update_interval_ms, web_server.m_sio),
                                     name="Race Table Update Task"))
    tasks.append(asyncio.create_task(streamOverlayUpdateTask(60, stream_overlay_start_sample_data, web_server.m_sio),
                                     name="Stream Overlay Update Task"))
    tasks.append(asyncio.create_task(frontEndMessageTask(web_server.m_sio),
                                     name="Front End Message Task"))
    return web_server

async def raceTableClientUpdateTask(update_interval_ms: int, sio: socketio.AsyncServer) -> None:
    """Task to update clients with telemetry data

    Args:
        update_interval_ms (int): Update interval in milliseconds
        sio (socketio.AsyncServer): The socketio server instance
    """

    sleep_duration = update_interval_ms / 1000
    while True:
        if not _isRoomEmpty(sio, "race-table"):
            packed = msgpack.packb(TelWebAPI.RaceInfoUpdate().toJSON(), use_bin_type=True)
            await sio.emit('race-table-update', packed, room="race-table")
        await asyncio.sleep(sleep_duration)

async def streamOverlayUpdateTask(
    update_interval_ms: int,
    stream_overlay_start_sample_data: bool,
    sio: socketio.AsyncServer) -> None:
    """Task to update clients with player telemetry overlay data
    Args:
        update_interval_ms (int): Update interval in milliseconds
        stream_overlay_start_sample_data (bool): Whether to show sample data in overlay until real data arrives
        sio (socketio.AsyncServer): The socketio server instance
    """

    sleep_duration = update_interval_ms / 1000
    while True:
        if not _isRoomEmpty(sio, "player-stream-overlay"):
            packed = msgpack.packb(
                TelWebAPI.PlayerTelemetryOverlayUpdate().toJSON(stream_overlay_start_sample_data), use_bin_type=True)
            await sio.emit(
                'player-overlay-update',
                packed,
                room="player-stream-overlay"
            )
        await asyncio.sleep(sleep_duration)

async def frontEndMessageTask(sio: socketio.AsyncServer) -> None:
    """Task to update clients with telemetry data

    Args:
        sio (socketio.AsyncServer): The socketio server instance
    """

    while True:
        if message := await AsyncInterTaskCommunicator().receive("frontend-update"):
            packed = msgpack.packb(message.toJSON(), use_bin_type=True)
            await sio.emit('frontend-update', packed, room="race-table")

def _isRoomEmpty(sio: socketio.AsyncServer, room_name: str, namespace: Optional[str] = '/') -> bool:
    """Check if a room is empty

    Args:
        sio (socketio.AsyncServer): The socketio server instance
        room_name (str): The room name
        namespace (Optional[str], optional): The namespace. Defaults to '/'

    Returns:
        bool: True if the room is empty, False otherwise
    """
    participants = list(sio.manager.get_participants(namespace, room_name))
    return not participants
