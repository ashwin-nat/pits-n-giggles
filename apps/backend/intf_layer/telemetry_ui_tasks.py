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
import random
from typing import List, Optional

from apps.backend.state_mgmt_layer import SessionState
from apps.backend.state_mgmt_layer.intf import (PeriodicUpdateData,
                                                StreamOverlayData)
from lib.config import PngSettings
from lib.inter_task_communicator import AsyncInterTaskCommunicator
from lib.web_server import ClientType

from .ipc import registerIpcTask
from .telemetry_web_server import TelemetryWebServer

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def initUiIntfLayer(
    settings: PngSettings,
    logger: logging.Logger,
    session_state: SessionState,
    debug_mode: bool,
    tasks: List[asyncio.Task],
    ver_str: str,
    ipc_port: Optional[int],
    shutdown_event: asyncio.Event) -> TelemetryWebServer:
    """Initialize the UI interface layer and return then server obj for proper cleanup

    Args:
        settings (PngSettings): Png settings
        logger (logging.Logger): Logger
        session_state (SessionState): Handle to the session state
        debug_mode (bool): Debug enabled if true
        tasks (List[asyncio.Task]): List of tasks to be executed
        ver_str (str): Version string
        ipc_port (Optional[int]): IPC port
        shutdown_event (asyncio.Event): Event to signal shutdown

    Returns:
        TelemetryWebServer: The initialized web server
    """

    # First, create the server instance
    web_server = TelemetryWebServer(
        settings=settings,
        ver_str=ver_str,
        logger=logger,
        session_state=session_state,
        debug_mode=debug_mode,
    )

    # Register tasks associated with this web server
    tasks.append(asyncio.create_task(web_server.run(), name="Web Server Task"))
    tasks.append(asyncio.create_task(raceTableClientUpdateTask(settings.Display.refresh_interval, web_server,
                                                               session_state,
                                                               logger,
                                                               shutdown_event),
                                     name="Race Table Update Task"))
    tasks.append(asyncio.create_task(streamOverlayUpdateTask(settings.Display.refresh_interval,
                                                             settings.StreamOverlay.show_sample_data_at_start,
                                                             web_server, session_state, shutdown_event),
                                     name="Stream Overlay Update Task"))
    tasks.append(asyncio.create_task(frontEndMessageTask(web_server, shutdown_event),
                                     name="Front End Message Task"))
    tasks.append(asyncio.create_task(hudNotifierTask(web_server, shutdown_event), name="HUD Notifier Task"))

    registerIpcTask(ipc_port, logger, session_state, tasks)
    return web_server

async def raceTableClientUpdateTask(
        update_interval_ms: int,
        server: TelemetryWebServer,
        session_state: SessionState,
        logger: logging.Logger,
        shutdown_event: asyncio.Event) -> None:
    """Task to update clients with telemetry data

    Args:
        update_interval_ms (int): Update interval in milliseconds
        server (TelemetryWebServer): The telemetry web server
        session_state (SessionState): Handle to the session state data structure
        logger (logging.Logger): Logger handle
        shutdown_event (asyncio.Event): Event to signal shutdown
    """

    await _initial_random_sleep()
    sleep_duration = update_interval_ms / 1000
    while not shutdown_event.is_set():
        if server.is_any_client_interested_in_event('race-table-update'):
            await server.send_to_clients_interested_in_event(
                event='race-table-update',
                data=PeriodicUpdateData(logger, session_state).toJSON()
            )
        await asyncio.sleep(sleep_duration)

    server.m_logger.debug("Shutting down race table update task")

async def streamOverlayUpdateTask(
    update_interval_ms: int,
    stream_overlay_start_sample_data: bool,
    server: TelemetryWebServer,
    session_state: SessionState,
    shutdown_event: asyncio.Event) -> None:
    """Task to update clients with player telemetry overlay data
    Args:
        update_interval_ms (int): Update interval in milliseconds
        stream_overlay_start_sample_data (bool): Whether to show sample data in overlay until real data arrives
        server (TelemetryWebServer): The telemetry web server
        session_state (SessionState): Handle to the session state data structure
        shutdown_event (asyncio.Event): Event to signal shutdown
    """

    await _initial_random_sleep()
    sleep_duration = update_interval_ms / 1000
    while not shutdown_event.is_set():
        if server.is_any_client_interested_in_event('stream-overlay-update'):
            await server.send_to_clients_interested_in_event(
                event='stream-overlay-update',
                data=StreamOverlayData(session_state).toJSON(stream_overlay_start_sample_data))
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

async def hudNotifierTask(server: TelemetryWebServer, shutdown_event: asyncio.Event) -> None:
    """Task to update HUD clients with telemetry data

    Args:
        server (TelemetryWebServer): The telemetry web server
        shutdown_event (asyncio.Event): Event to signal shutdown
    """

    while not shutdown_event.is_set():
        if message := await AsyncInterTaskCommunicator().receive("hud-notifier"):
            await server.send_to_clients_interested_in_event(
                event=str(message.m_message_type),
                data=message.toJSON())

    server.m_logger.debug("Shutting down HUD notifier task")

# -------------------------------------- UTILS -------------------------------------------------------------------------

async def _initial_random_sleep() -> None:
    """Sleep for a random amount of time to avoid bursty events"""
    await asyncio.sleep(random.uniform(0, 0.2))
