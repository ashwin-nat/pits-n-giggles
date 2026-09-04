# MIT License
#
# Copyright (c) [2026] [Ashwin Natarajan]
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
from typing import Any, Awaitable, Callable

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

async def _initial_random_sleep() -> None:
    """Sleep for a random amount of time to avoid bursty events"""
    await asyncio.sleep(random.uniform(0, 0.2))

async def periodic_task(
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
