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
from typing import Any, Awaitable, Callable, List, Tuple

from apps.core.state_mgmt_layer import SessionState
from apps.core.state_mgmt_layer.intf import (PeriodicUpdateData,
                                                RaceInfoData,
                                                StreamOverlayData)
from apps.core.telemetry_layer import F1TelemetryHandler
from lib.config import PngSettings
from lib.inter_task_communicator import AsyncInterTaskCommunicator
from lib.ipc import IpcDealerAsync, IpcPublisherAsync, PngAppId

from .ipc import registerIpcTask
from .request_handlers import handleDriverInfoRequest

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def _initDealer(
    settings: PngSettings,
    logger: logging.Logger,
    session_state: SessionState) -> IpcDealerAsync:
    dealer = IpcDealerAsync(
        host="127.0.0.1",
        port=settings.Network.broker_router_port,
        identity=str(PngAppId.BACKEND),
        logger=logger,
    )

    @dealer.route("driver-info-request")
    async def _handle_driver_info_request(data: dict, sender: str) -> dict:
        logger.debug("Received driver info request via router: %s from %s", data, sender)
        result = handleDriverInfoRequest(session_state, data.get("index"))
        if result.ok:
            return {"ok": True, "data": result.data}
        return {"ok": False, "error": result.detail, "data": None}

    @dealer.route("race-info-request")
    async def _handle_race_info_request(data: dict, sender: str) -> dict:
        logger.debug("Received race info request via router from %s", sender)
        return {"ok": True, "data": RaceInfoData(session_state).toJSON()}

    return dealer

def initUiIntfLayer(
    settings: PngSettings,
    logger: logging.Logger,
    session_state: SessionState,
    tasks: List[asyncio.Task],
    run_ipc_server: bool,
    shutdown_event: asyncio.Event,
    telemetry_handler: F1TelemetryHandler) -> Tuple[IpcPublisherAsync, IpcDealerAsync]:
    """Initialize the UI interface layer.

    Args:
        settings (PngSettings): Png settings
        logger (logging.Logger): Logger
        session_state (SessionState): Handle to the session state
        tasks (List[asyncio.Task]): List of tasks to be executed
        run_ipc_server (bool): Whether to run the IPC server
        shutdown_event (asyncio.Event): Event to signal shutdown
        telemetry_handler (F1TelemetryHandler): Telemetry handler

    Returns:
        Tuple[IpcPublisherAsync, IpcDealerAsync]: IPC publisher and dealer instances
    """

    ipc_pub = IpcPublisherAsync(logger=logger, port=settings.Network.broker_xsub_port)
    tasks.append(ipc_pub.get_task())

    dealer = _initDealer(settings, logger, session_state)
    tasks.append(asyncio.create_task(dealer.start(), name="Backend Dealer Recv"))

    tasks.append(asyncio.create_task(
        _periodic_task(
            settings.Display.local_telemetry_interval_ms,
            shutdown_event,
            logger,
            lowFreqLocalUpdateTask,
            session_state,
            ipc_pub), name="Low Frequency Local Update Task"
        ))
    tasks.append(asyncio.create_task(
        _periodic_task(
            settings.Display.hud_refresh_interval,
            shutdown_event,
            logger,
            highFreqLocalUpdateTask,
            session_state,
            ipc_pub), name="High Frequency Local Update Task"))

    tasks.append(asyncio.create_task(frontEndMessageTask(ipc_pub, shutdown_event),
                                     name="Front End Message Task"))
    tasks.append(asyncio.create_task(hudInteractionTask(dealer, shutdown_event),
                                     name="HUD Interaction Task"))

    registerIpcTask(run_ipc_server, logger, session_state, telemetry_handler, ipc_pub, dealer, tasks)
    return ipc_pub, dealer

async def lowFreqLocalUpdateTask(
        session_state: SessionState,
        ipc_pub: IpcPublisherAsync) -> None:
    """Low frequency local update task to publish periodic data

    Args:
        session_state (SessionState): The session state
        ipc_pub (IpcPublisherAsync): The IPC publisher
    """

    race_table_data = PeriodicUpdateData(session_state).toJSON()
    await ipc_pub.publish("race-table-update", race_table_data) # IPC publish is O(1) so do it always

async def highFreqLocalUpdateTask(
    session_state: SessionState,
    ipc_pub: IpcPublisherAsync) -> None:
    """High frequency local update task to publish stream overlay data

    Args:
        session_state (SessionState): The session state
        ipc_pub (IpcPublisherAsync): The IPC publisher
    """

    data = StreamOverlayData(session_state, export_hud_data=True).toJSON(False)
    await ipc_pub.publish("stream-overlay-update", data)

async def frontEndMessageTask(
    ipc_pub: IpcPublisherAsync,
    shutdown_event: asyncio.Event) -> None:
    """Task to forward frontend-update messages to the broker.

    Args:
        ipc_pub (IpcPublisherAsync): The IPC publisher (broker)
        shutdown_event (asyncio.Event): Event to signal shutdown
    """

    while not shutdown_event.is_set():
        if message := await AsyncInterTaskCommunicator().receive("frontend-update"):
            await ipc_pub.publish("frontend-update", message.toJSON())

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

# -------------------------------------- UTILS -------------------------------------------------------------------------

async def _initial_random_sleep() -> None:
    """Sleep for a random amount of time to avoid bursty events"""
    await asyncio.sleep(random.uniform(0, 0.2))

async def _periodic_task(
    interval_ms: int,
    shutdown_event: asyncio.Event,
    logger: logging.Logger,
    task_coro: Callable[..., Awaitable[Any]],
    *args,
    **kwargs) -> None:
    """Utility to run a periodic task with deadline scheduling

    Args:
    interval_ms (int): Interval in milliseconds
    shutdown_event (asyncio.Event): Event to signal shutdown
    logger (logging.Logger): Logger
    task_coro: Coroutine function to run periodically
    *args: Positional arguments to pass to task_coro
    **kwargs: Keyword arguments to pass to task_coro
    """
    await _initial_random_sleep() # Stagger start times
    interval = interval_ms / 1000.0
    loop = asyncio.get_running_loop()
    next_tick = loop.time()

    task = asyncio.current_task()
    task_name = task.get_name() if task else "<unknown>"

    logger.debug("%s: Starting periodic task", task_name)

    while not shutdown_event.is_set():
        next_tick += interval
        try:
            await task_coro(*args, **kwargs)
        except Exception as e: # pylint: disable=broad-except
            logger.exception("%s: Error running periodic task %s", task_name, e)

        delay = next_tick - loop.time()

        if delay > 0:
            await asyncio.sleep(delay)
        else:
            # Missed deadline — resync without sleeping
            next_tick = loop.time()
            await asyncio.sleep(0)

    logger.debug("%s: Shutting down periodic task", task_name)
