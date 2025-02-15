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

import threading
from time import sleep
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests_base import F1TelemetryUnitTestsBase
from lib.inter_thread_communicator import InterThreadCommunicator, ITCMessage, TyreDeltaMessage
# ----------------------------------------------------------------------------------------------------------------------

class TestInterThreadCommunicator(F1TelemetryUnitTestsBase):
    def setUp(self):
        """Initialize a fresh InterThreadCommunicator instance before each test."""
        self.itc = InterThreadCommunicator()
        self.queue_name = "test_queue"

    def test_singleton_behavior(self):
        """Ensure only one instance of InterThreadCommunicator exists."""
        another_instance = InterThreadCommunicator()
        self.assertIs(self.itc, another_instance)

    def test_send_and_receive_message(self):
        """Test sending and receiving a message from the queue."""
        message = ITCMessage(ITCMessage.MessageType.CUSTOM_MARKER, "Test Message")
        self.itc.send(self.queue_name, message)
        received_message = self.itc.receive(self.queue_name)
        self.assertEqual(received_message, message)

    def test_receive_with_timeout(self):
        """Test that receiving with a timeout returns None if no message is available."""
        received_message = self.itc.receive(self.queue_name, timeout_sec=1)
        self.assertIsNone(received_message)

    def test_receive_wait_indefinite(self):
        """Test blocking receive from the queue."""
        message = ITCMessage(ITCMessage.MessageType.TYRE_DELTA_NOTIFICATION, "Blocking Test")

        def send_message_later():
            sleep(1)
            self.itc.send(self.queue_name, message)

        threading.Thread(target=send_message_later).start()
        received_message = self.itc.receiveWaitIndefinite(self.queue_name)
        self.assertEqual(received_message, message)

    def test_json_serialization(self):
        """Test JSON serialization of ITCMessage and TyreDeltaMessage."""
        tyre_msg = TyreDeltaMessage(TyreDeltaMessage.TyreType.SLICK, TyreDeltaMessage.TyreType.WET, 1.23)
        itc_msg = ITCMessage(ITCMessage.MessageType.TYRE_DELTA_NOTIFICATION, tyre_msg)
        json_output = itc_msg.toJSON()
        expected_json = {
            "message-type": "tyre-delta",
            "message": {
                "curr-tyre-type": "slick",
                "other-tyre-type": "wet",
                "tyre-delta": 1.23
            }
        }
        self.assertEqual(json_output, expected_json)

    def test_queue_isolation_between_threads(self):
        """Ensure that messages sent to different queues do not interfere."""
        queue_1, queue_2 = "queue1", "queue2"
        message_1 = ITCMessage(ITCMessage.MessageType.UDP_PACKET_FORWARD, "Data 1")
        message_2 = ITCMessage(ITCMessage.MessageType.CUSTOM_MARKER, "Data 2")

        self.itc.send(queue_1, message_1)
        self.itc.send(queue_2, message_2)

        self.assertEqual(self.itc.receive(queue_1), message_1)
        self.assertEqual(self.itc.receive(queue_2), message_2)

    def test_queue_empty_exception_handling(self):
        """Ensure receive handles empty queue properly."""
        received = self.itc.receive(self.queue_name)
        self.assertIsNone(received)
