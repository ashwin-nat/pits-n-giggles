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

from lib.packet_forwarder import AsyncUDPForwarder
from lib.subsystem import AddTask

# Waking up periodically to recheck shutdown_event, rather than blocking on queue.get()
# indefinitely, is what lets this task exit cleanly - there is no unblock signal to fall back on
# now that the ITC singleton is gone.
_QUEUE_POLL_TIMEOUT_SEC = 0.2

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def setupForwarder(forwarding_targets: List[Tuple[str, int]],
                   packet_forward_queue: asyncio.Queue,
                   add_task: AddTask,
                   shutdown_event: asyncio.Event,
                   logger: logging.Logger) -> AsyncUDPForwarder:
    """Init the forwarding task and return the forwarder so targets can be updated at runtime.

    Args:
        forwarding_targets (List[Tuple[str, int]]): Initial forwarding targets (may be empty)
        packet_forward_queue (asyncio.Queue): Queue the telemetry handler pushes raw packets to
        add_task (AddTask): The subsystem's add_task, which registers rather than starts
        shutdown_event (asyncio.Event): Shutdown event
        logger (logging.Logger): Logger

    Returns:
        AsyncUDPForwarder: The forwarder instance (call update_targets() to change destinations)
    """

    udp_forwarder = AsyncUDPForwarder(forwarding_targets, logger)
    add_task(udpForwardingTask(packet_forward_queue, udp_forwarder, shutdown_event, logger),
             name="UDP Forwarder Task")
    logger.debug("UDP Forwarder task registered. Initial targets=%s", forwarding_targets)
    return udp_forwarder

async def udpForwardingTask(packet_forward_queue: asyncio.Queue,
                            udp_forwarder: AsyncUDPForwarder,
                            shutdown_event: asyncio.Event,
                            logger: logging.Logger) -> None:
    """UDP Forwarding Task

    Args:
        packet_forward_queue (asyncio.Queue): Queue the telemetry handler pushes raw packets to
        udp_forwarder (AsyncUDPForwarder): Forwarder instance (shared with IPC handler for hot-reload)
        shutdown_event (asyncio.Event): Shutdown event
        logger (logging.Logger): Logger
    """

    while not shutdown_event.is_set():
        try:
            packet = await asyncio.wait_for(packet_forward_queue.get(), timeout=_QUEUE_POLL_TIMEOUT_SEC)
        except asyncio.TimeoutError:
            continue
        await udp_forwarder.forward(packet)

    udp_forwarder.close()
    logger.debug("Shutting down UDP Forwarder task...")
