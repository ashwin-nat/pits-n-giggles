"""
MIT License

Copyright (c) 2025 Ashwin Natarajan

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

# -------------------------------------- IMPORTS -----------------------------------------------------------------------
import asyncio
import logging
from typing import List, Tuple

from lib.inter_task_communicator import AsyncInterTaskCommunicator
from lib.packet_forwarder import AsyncUDPForwarder

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def setupForwarder(forwarding_targets: List[Tuple[str, int]],
                   tasks: List[asyncio.Task],
                   shutdown_event: asyncio.Event,
                   logger: logging.Logger) -> AsyncUDPForwarder:
    """Init the forwarding task and return the forwarder so targets can be updated at runtime.

    Args:
        forwarding_targets (List[Tuple[str, int]]): Initial forwarding targets (may be empty)
        tasks (List[asyncio.Task]): List of tasks
        shutdown_event (asyncio.Event): Shutdown event
        logger (logging.Logger): Logger

    Returns:
        AsyncUDPForwarder: The forwarder instance (call update_targets() to change destinations)
    """

    udp_forwarder = AsyncUDPForwarder(forwarding_targets, logger)
    tasks.append(asyncio.create_task(udpForwardingTask(udp_forwarder, shutdown_event, logger),
                                     name="UDP Forwarder Task"))
    logger.debug("UDP Forwarder task registered. Initial targets=%s", forwarding_targets)
    return udp_forwarder

async def udpForwardingTask(udp_forwarder: AsyncUDPForwarder,
                            shutdown_event: asyncio.Event,
                            logger: logging.Logger) -> None:
    """UDP Forwarding Task

    Args:
        udp_forwarder (AsyncUDPForwarder): Forwarder instance (shared with IPC handler for hot-reload)
        shutdown_event (asyncio.Event): Shutdown event
        logger (logging.Logger): Logger
    """

    while not shutdown_event.is_set():
        if packet := await AsyncInterTaskCommunicator().receive("packet-forward"):
            await udp_forwarder.forward(packet)

    udp_forwarder.close()
    logger.debug("Shutting down UDP Forwarder task...")
