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

def setupForwarder(forwarding_targets: List[Tuple[str, int]], tasks: List[asyncio.Task], logger: logging.Logger) -> None:
    """Init the forwarding thread, if targets are defined

    Args:
        forwarding_targets (List[Tuple[str, int]]): Forwarding Targets list
        tasks (List[asyncio.Task]): List of tasks
        logger (logging.Logger): Logger
    """

    # Register the task only if targets are defined
    if forwarding_targets:
        tasks.append(asyncio.create_task(udpForwardingTask(forwarding_targets, logger), name="UDP Forwarder Task"))
    else:
        logger.debug("No forwarding targets defined. Not registering task.")

async def udpForwardingTask(forwarding_targets: List[Tuple[str, int]], logger: logging.Logger) -> None:
    """UDP Forwarding Task

    Args:
        forwarding_targets (List[Tuple[str, int]]): Forwarding Targets list
        logger (logging.Logger): Logger
    """

    udp_forwarder = AsyncUDPForwarder(forwarding_targets, logger)
    logger.info(f"Initialised forwarder. Targets={forwarding_targets}")
    while True:
        packet = await AsyncInterTaskCommunicator().receive("packet-forward")
        assert packet is not None
        await udp_forwarder.forward(packet)
