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

import apps.backend.state_mgmt_layer as TelWebAPI
from lib.inter_task_communicator import AsyncInterTaskCommunicator
from lib.web_server import ClientType

from .ipc import registerIpcTask
from .telemetry_web_server import TelemetryWebServer

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def initUiIntfLayer(
    port: int,
    logger: logging.Logger,
    client_update_interval_ms: int,
    debug_mode: bool,
    stream_overlay_start_sample_data: bool,
    stream_overlay_update_interval_ms: int,
    tasks: List[asyncio.Task],
    ver_str: str,
    cert_path: Optional[str],
    key_path: Optional[str],
    ipc_port: Optional[int],
    shutdown_event: asyncio.Event,
    disable_browser_autoload: bool) -> TelemetryWebServer:
    """Initialize the UI interface layer and return then server obj for proper cleanup

    Args:
        port (int): Port number
        logger (logging.Logger): Logger
        client_update_interval_ms (int): How often the client will be updated with new info
        debug_mode (bool): Debug enabled if true
        stream_overlay_start_sample_data (bool): Whether to show sample data in overlay until real data arrives
        stream_overlay_update_interval_ms (int): How often the stream overlay will be updated
        tasks (List[asyncio.Task]): List of tasks to be executed
        ver_str (str): Version string
        cert_path (Optional[str]): Path to the certificate file
        key_path (Optional[str]): Path to the key file
        ipc_port (Optional[int]): IPC port
        shutdown_event (asyncio.Event): Event to signal shutdown
        disable_browser_autoload (bool): Whether to disable browser autoload

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
        disable_browser_autoload=disable_browser_autoload
    )

    # Register tasks associated with this web server
    tasks.append(asyncio.create_task(web_server.run(), name="Web Server Task"))
    tasks.append(asyncio.create_task(raceTableClientUpdateTask(client_update_interval_ms, web_server, shutdown_event),
                                     name="Race Table Update Task"))
    tasks.append(asyncio.create_task(streamOverlayUpdateTask(stream_overlay_update_interval_ms,
                                                             stream_overlay_start_sample_data, web_server,
                                                             shutdown_event),
                                     name="Stream Overlay Update Task"))
    tasks.append(asyncio.create_task(frontEndMessageTask(web_server, shutdown_event),
                                     name="Front End Message Task"))

    registerIpcTask(ipc_port, logger, tasks)
    return web_server

async def raceTableClientUpdateTask(
        update_interval_ms: int,
        server: TelemetryWebServer,
        shutdown_event: asyncio.Event) -> None:
    """Task to update clients with telemetry data

    Args:
        update_interval_ms (int): Update interval in milliseconds
        server (TelemetryWebServer): The telemetry web server
        shutdown_event (asyncio.Event): Event to signal shutdown
    """

    sleep_duration = update_interval_ms / 1000
    while not shutdown_event.is_set():
        if not server.is_client_of_type_connected(ClientType.RACE_TABLE):
            await server.send_to_clients_of_type(
                event='race-table-update',
                data=TelWebAPI.RaceInfoUpdate().toJSON(),
                client_type=ClientType.RACE_TABLE)
        await asyncio.sleep(sleep_duration)

    server.m_logger.debug("Shutting down race table update task")

async def streamOverlayUpdateTask(
    update_interval_ms: int,
    stream_overlay_start_sample_data: bool,
    server: TelemetryWebServer,
    shutdown_event: asyncio.Event) -> None:
    """Task to update clients with player telemetry overlay data
    Args:
        update_interval_ms (int): Update interval in milliseconds
        stream_overlay_start_sample_data (bool): Whether to show sample data in overlay until real data arrives
        server (TelemetryWebServer): The telemetry web server
        shutdown_event (asyncio.Event): Event to signal shutdown
    """

    sleep_duration = update_interval_ms / 1000
    while not shutdown_event.is_set():
        if not server.is_client_of_type_connected(ClientType.PLAYER_STREAM_OVERLAY):
            await server.send_to_clients_of_type(
                event='player-overlay-update',
                data=TelWebAPI.PlayerTelemetryOverlayUpdate().toJSON(stream_overlay_start_sample_data),
                client_type=ClientType.PLAYER_STREAM_OVERLAY)
        await asyncio.sleep(sleep_duration)

    server.m_logger.debug("Shutting down stream overlay update task")

async def frontEndMessageTask(server: TelemetryWebServer, shutdown_event: asyncio.Event) -> None:
    """Task to update clients with telemetry data

    Args:
        server (TelemetryWebServer): The telemetry web server
        shutdown_event (asyncio.Event): Event to signal shutdown
    """

    while not shutdown_event.is_set():
        if message := await AsyncInterTaskCommunicator().receive("frontend-update"):
            await server.send_to_clients_of_type(
                event='frontend-update',
                data=message.toJSON(),
                client_type=ClientType.RACE_TABLE)

    server.m_logger.debug("Shutting down front end message task")
