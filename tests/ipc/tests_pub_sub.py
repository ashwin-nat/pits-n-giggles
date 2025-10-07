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
# pylint: skip-file

import threading
import asyncio
import time
import sys
import os
import zmq

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests_base import F1TelemetryUnitTestsBase

from lib.ipc import PublisherAsync, SubscriberSync

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# ----------------------------------------------------------------------------------------------------------------------

class TestPubSub(F1TelemetryUnitTestsBase):

    async def test_basic_pub_sub(self):
        port = 5556
        publisher = PublisherAsync(port=port)
        subscriber = SubscriberSync(port=port)

        received_messages = []
        def subscriber_callback(data):
            received_messages.append(data)

        # Run publisher in a separate task
        publisher_task = asyncio.create_task(publisher.run())
        await asyncio.sleep(0.1) # Give publisher a moment to bind

        # Run subscriber in a separate thread
        subscriber_thread = threading.Thread(target=subscriber.run, args=(subscriber_callback,))
        subscriber_thread.daemon = True
        subscriber_thread.start()
        await asyncio.sleep(0.1) # Give subscriber a moment to connect

        # Publish some messages
        test_data_1 = {"key": "value1", "number": 1}
        test_data_2 = {"key": "value2", "number": 2}

        await publisher.publish(test_data_1)
        await asyncio.sleep(0.1)
        await publisher.publish(test_data_2)
        await asyncio.sleep(0.1)

        # Close publisher and subscriber
        await publisher.close()
        # Signal the subscriber to stop and then close it
        subscriber.close()
        subscriber_thread.join(timeout=1) # Wait for the subscriber thread to finish

        self.assertEqual(len(received_messages), 2)
        self.assertEqual(received_messages[0], test_data_1)
        self.assertEqual(received_messages[1], test_data_2)

        # Clean up the publisher task
        publisher_task.cancel()
        try:
            await publisher_task
        except asyncio.CancelledError:
            pass