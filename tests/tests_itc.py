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

from lib.inter_thread_communicator import (AsyncInterTaskCommunicator,
                                           ITCMessage,
                                           TyreDeltaMessage)

# ----------------------------------------------------------------------------------------------------------------------

class TestAsyncInterThreadCommunicator(F1TelemetryUnitTestsBase):
    def setUp(self):
        """Create a fresh communicator for each test"""
        self.communicator = AsyncInterTaskCommunicator()

    async def async_test_timeout_none(self):
        """Test receive with timeout=None (indefinite wait)"""
        # This test will timeout if the receive doesn't work correctly
        async def wait_and_send():
            await asyncio.sleep(0.1)
            await self.communicator.send('wait_queue', "Delayed Message")

        # Start a task to send a message after a short delay
        send_task = asyncio.create_task(wait_and_send())

        # Receive should wait indefinitely
        message = await self.communicator.receive('wait_queue', timeout=None)

        # Verify message
        self.assertEqual(message, "Delayed Message")

        # Ensure send task completed
        await send_task

    def test_timeout_none(self):
        """Wrapper to run async test synchronously"""
        asyncio.run(self.async_test_timeout_none())

    async def async_test_timeout_zero(self):
        """Test receive with timeout=0 (non-blocking)"""
        result = await self.communicator.receive('empty_queue', timeout=0)
        self.assertIsNone(result)

    def test_timeout_zero(self):
        """Wrapper to run async test synchronously"""
        asyncio.run(self.async_test_timeout_zero())

    async def async_test_timeout_positive(self):
        """Test receive with a positive timeout"""
        # No message initially
        result = await self.communicator.receive('timeout_queue', timeout=0.1)
        self.assertIsNone(result)

        # Send a message after a delay
        async def delayed_send():
            await asyncio.sleep(0.05)
            await self.communicator.send('timeout_queue', "Timely Message")

        # Start delayed send
        send_task = asyncio.create_task(delayed_send())

        # Receive with longer timeout should get the message
        message = await self.communicator.receive('timeout_queue', timeout=0.2)
        self.assertEqual(message, "Timely Message")

        # Ensure send task completed
        await send_task

    def test_timeout_positive(self):
        """Wrapper to run async test synchronously"""
        asyncio.run(self.async_test_timeout_positive())
