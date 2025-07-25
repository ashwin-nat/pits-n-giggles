# MIT License
#
# Copyright (c) [2024] [Ashwin Natarajan]
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
# pylint: skip-file

import asyncio
import os
import sys
import threading
from time import sleep

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests_base import F1TelemetryUnitTestsBase

from lib.inter_task_communicator import (AsyncInterTaskCommunicator,
                                           ITCMessage,
                                           TyreDeltaMessage)

# ----------------------------------------------------------------------------------------------------------------------

class TestAsyncInterTaskCommunicator(F1TelemetryUnitTestsBase):
    async def asyncSetUp(self):
        """Create a fresh communicator for each test (async version)"""
        self.communicator = AsyncInterTaskCommunicator()

    async def test_timeout_none(self):
        """Test receive with timeout=None (indefinite wait)"""
        async def wait_and_send():
            await asyncio.sleep(0.1)
            await self.communicator.send('wait_queue', "Delayed Message")

        send_task = asyncio.create_task(wait_and_send())

        message = await self.communicator.receive('wait_queue', timeout=None)
        self.assertEqual(message, "Delayed Message")
        await send_task

    async def test_timeout_zero(self):
        """Test receive with timeout=0 (non-blocking)"""
        result = await self.communicator.receive('empty_queue', timeout=0)
        self.assertIsNone(result)

    async def test_timeout_positive(self):
        """Test receive with a positive timeout and delayed message"""
        # No message initially
        result = await self.communicator.receive('timeout_queue', timeout=0.1)
        self.assertIsNone(result)

        async def delayed_send():
            await asyncio.sleep(0.05)
            await self.communicator.send('timeout_queue', "Timely Message")

        send_task = asyncio.create_task(delayed_send())

        message = await self.communicator.receive('timeout_queue', timeout=0.2)
        self.assertEqual(message, "Timely Message")
        await send_task
