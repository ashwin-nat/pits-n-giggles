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
from typing import List, Tuple, Optional

from apps.backend.state_mgmt_layer import SessionState
from apps.backend.state_mgmt_layer.intf import (PeriodicUpdateData,
                                                StreamOverlayData)
from apps.backend.telemetry_layer import F1TelemetryHandler
from lib.config import PngSettings
from lib.inter_task_communicator import AsyncInterTaskCommunicator
from lib.web_server import ClientType
from lib.ipc import IpcPublisherAsync

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
    run_ipc_server: bool,
    shutdown_event: asyncio.Event,
    telemetry_handler: F1TelemetryHandler) -> Tuple[TelemetryWebServer, IpcPublisherAsync]:
    """Initialize the UI interface layer and return then server obj for proper cleanup

    Args:
        settings (PngSettings): Png settings
        logger (logging.Logger): Logger
        session_state (SessionState): Handle to the session state
        debug_mode (bool): Debug enabled if true
        tasks (List[asyncio.Task]): List of tasks to be executed
        ver_str (str): Version string
        run_ipc_server (bool): Whether to run the IPC server
        shutdown_event (asyncio.Event): Event to signal shutdown
        telemetry_handler (F1TelemetryHandler): Telemetry handler

    Returns:
        Tuple[TelemetryWebServer, IpcPublisherAsync]: Web server and IPC publisher instances
    """

    # First, create the server instance
    web_server = TelemetryWebServer(
        settings=settings,
        ver_str=ver_str,
        logger=logger,
        session_state=session_state,
        debug_mode=debug_mode,
    )
    ipc_pub = IpcPublisherAsync(logger=logger, port=settings.Network.broker_xsub_port)

    # Register tasks associated with this web server
    tasks.append(asyncio.create_task(web_server.run(), name="Web Server Task"))
    tasks.append(asyncio.create_task(lowFreqUpdateTask(
        settings.Display.refresh_interval,
        settings.StreamOverlay.show_sample_data_at_start,
        web_server,
        session_state,
        logger,
        shutdown_event,
        ipc_pub), name="Race Table Update Task"))
    tasks.append(asyncio.create_task(frontEndMessageTask(web_server, shutdown_event),
                                     name="Front End Message Task"))
    tasks.append(asyncio.create_task(hudInteractionTask(web_server, shutdown_event), name="HUD Interaction Task"))
    if settings.HUD.enabled:
        tasks.append(asyncio.create_task(highFreqUpdateTask(session_state,
                                                       write_interval_ms=settings.Display.hud_refresh_interval,
                                                       shutdown_event=shutdown_event, ipc_pub=ipc_pub), name="HUD Update Task"))

    registerIpcTask(run_ipc_server, logger, session_state, telemetry_handler, tasks)
    return web_server, ipc_pub

async def lowFreqUpdateTask(
        update_interval_ms: int,
        stream_overlay_start_sample_data: bool,
        server: TelemetryWebServer,
        session_state: SessionState,
        logger: logging.Logger,
        shutdown_event: asyncio.Event,
        ipc_pub: IpcPublisherAsync) -> None:
    """Task to update clients with telemetry data

    Args:
        update_interval_ms (int): Update interval in milliseconds
        stream_overlay_start_sample_data (bool): Whether to show sample data in overlay until real data arrives
        server (TelemetryWebServer): The telemetry web server
        session_state (SessionState): Handle to the session state data structure
        logger (logging.Logger): Logger handle
        shutdown_event (asyncio.Event): Event to signal shutdown
        ipc_pub (IpcPublisherAsync): IPC publisher instance
    """

    await _initial_random_sleep()
    interval = update_interval_ms / 1000.0
    loop = asyncio.get_running_loop()
    next_tick = loop.time()

    while not shutdown_event.is_set():
        next_tick += interval

        race_table_data = PeriodicUpdateData(logger, session_state).toJSON()
        await ipc_pub.publish("race-table-update", race_table_data) # IPC publish is O(1) so do it always

        if server.is_any_client_interested_in_event('race-table-update'):
            await server.send_to_clients_interested_in_event(
                event='race-table-update',
                data=race_table_data
            )

        if server.is_any_client_interested_in_event('stream-overlay-update'):
            await server.send_to_clients_interested_in_event(
                event='stream-overlay-update',
                data=StreamOverlayData(session_state).toJSON(stream_overlay_start_sample_data)
            )
        # --------------

        # Deadline sleep (no drift)
        delay = next_tick - loop.time()
        if delay > 0:
            await asyncio.sleep(delay)
        else:
            # Missed deadline: yield but do not accumulate drift
            next_tick = loop.time()
            await asyncio.sleep(0)

    server.m_logger.debug("Shutting down race table update task")

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

async def hudInteractionTask(server: TelemetryWebServer, shutdown_event: asyncio.Event) -> None:
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

async def highFreqUpdateTask(
        session_state: SessionState,
        write_interval_ms: int,
        shutdown_event: asyncio.Event,
        ipc_pub: IpcPublisherAsync) -> None:
    """Task to update HUD clients with telemetry data

    Args:
        session_state (SessionState): Handle to the session state data structure
        write_interval_ms (int): Write interval in milliseconds
        shutdown_event (async.Event): Event to signal shutdown
        ipc_pub (IpcPublisherAsync): IPC publisher instance
    """
    await ipc_pub.start()
    await _initial_random_sleep()
    interval = write_interval_ms / 1000.0
    loop = asyncio.get_running_loop()
    next_tick = loop.time()

    while not shutdown_event.is_set():
        next_tick += interval

        data = StreamOverlayData(session_state).toJSON(False)
        await ipc_pub.publish("stream-overlay-update", data)

        delay = next_tick - loop.time()
        if delay > 0:
            await asyncio.sleep(delay)
        else:
            # Missed deadline — resync without sleeping
            next_tick = loop.time()
            await asyncio.sleep(0)

# -------------------------------------- UTILS -------------------------------------------------------------------------

async def _initial_random_sleep() -> None:
    """Sleep for a random amount of time to avoid bursty events"""
    await asyncio.sleep(random.uniform(0, 0.2))
