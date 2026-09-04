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

import pytest

from lib.periodic_task import periodic_task

# -------------------------------------- FIXTURES -----------------------------------------------------------------------

@pytest.fixture
def logger():
    log = logging.getLogger("tests_periodic_task")
    log.addHandler(logging.NullHandler())
    return log

# -------------------------------------- TESTS --------------------------------------------------------------------------

async def test_runs_task_coro_repeatedly_until_shutdown(logger):
    shutdown_event = asyncio.Event()
    calls = []

    async def tick():
        calls.append(len(calls))
        if len(calls) >= 3:
            shutdown_event.set()

    await periodic_task(10, shutdown_event, logger, tick)

    assert calls == [0, 1, 2]

async def test_passes_through_args_and_kwargs(logger):
    shutdown_event = asyncio.Event()
    received = []

    async def tick(a, b, kw=None):
        received.append((a, b, kw))
        shutdown_event.set()

    await periodic_task(10, shutdown_event, logger, tick, 1, 2, kw="x")

    assert received == [(1, 2, "x")]

async def test_shutdown_event_already_set_runs_zero_iterations(logger):
    shutdown_event = asyncio.Event()
    shutdown_event.set()
    calls = []

    async def tick():
        calls.append(1)

    await periodic_task(10, shutdown_event, logger, tick)

    assert calls == []

async def test_exception_in_task_coro_is_swallowed_and_loop_continues(logger):
    shutdown_event = asyncio.Event()
    calls = []

    async def tick():
        calls.append(len(calls))
        if len(calls) == 1:
            raise RuntimeError("boom")
        if len(calls) >= 2:
            shutdown_event.set()

    await periodic_task(10, shutdown_event, logger, tick)

    assert calls == [0, 1]

async def test_missed_deadline_resyncs_without_sleeping(logger):
    """If task_coro overruns the interval, the loop must resync rather than pile up sleeps."""
    shutdown_event = asyncio.Event()
    calls = []

    async def tick():
        calls.append(len(calls))
        # Sleep far longer than the interval so every tick misses its deadline.
        await asyncio.sleep(0.02)
        if len(calls) >= 3:
            shutdown_event.set()

    await asyncio.wait_for(
        periodic_task(1, shutdown_event, logger, tick),
        timeout=2.0,
    )

    assert calls == [0, 1, 2]
