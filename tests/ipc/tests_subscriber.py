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

import asyncio
import sys
import os
from unittest.mock import MagicMock, patch
import logging
import socketio

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from .base import TestIPC

from lib.ipc import IpcSubscriber

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# ----------------------------------------------------------------------------------------------------------------------

class TestIpcSubscriber(TestIPC):

    def setUp(self):
        self.url = "http://testserver"
        self.logger = MagicMock(spec=logging.Logger)

        # Patch socketio.Client to avoid real network connections
        self.sio_patch = patch("lib.ipc.subscriber.socketio.Client")
        self.mock_sio_class = self.sio_patch.start()
        self.mock_sio = MagicMock()
        self.mock_sio_class.return_value = self.mock_sio

    def tearDown(self):
        self.sio_patch.stop()

    def test_initial_state(self):
        subscriber = IpcSubscriber(self.url, self.logger)
        self.assertFalse(subscriber._stop_event.is_set())
        self.assertFalse(subscriber._connected)
        self.assertEqual(subscriber.url, self.url)
        self.assertEqual(subscriber.logger, self.logger)
        self.assertEqual(subscriber._event_handlers, [])

    def test_on_decorator_registers_handler(self):
        subscriber = IpcSubscriber(self.url, self.logger)

        @subscriber.on("test-event")
        def handler(data):
            return data

        self.assertIn(("test-event", handler), subscriber._event_handlers)
        self.mock_sio.on.assert_any_call("test-event", handler)

    def test_on_connect_disconnect_callbacks(self):
        subscriber = IpcSubscriber(self.url, self.logger)

        connect_called = []
        disconnect_called = []

        @subscriber.on_connect
        def connect_cb():
            connect_called.append(True)

        @subscriber.on_disconnect
        def disconnect_cb():
            disconnect_called.append(True)

        # simulate connect
        subscriber._handle_connect()
        self.assertTrue(subscriber._connected)
        self.assertTrue(connect_called)

        # simulate disconnect
        subscriber._handle_disconnect()
        self.assertFalse(subscriber._connected)
        self.assertTrue(disconnect_called)

    def test_run_connects_and_sleeps(self):
        subscriber = IpcSubscriber(self.url, self.logger)

        # Patch _setup_sio to prevent overwriting self._sio
        with patch.object(subscriber, "_setup_sio", return_value=None):
            # Patch _sio.sleep to break the loop immediately
            def stop_loop(seconds):
                subscriber._stop_event.set()

            subscriber._sio.sleep.side_effect = stop_loop

            subscriber.run()
            subscriber._sio.connect.assert_called_with(
                self.url, wait=True, transports=["websocket", "polling"]
            )

    def test_stop_disconnects(self):
        subscriber = IpcSubscriber(self.url, self.logger)
        subscriber._connected = True
        subscriber._sio.disconnect = MagicMock()

        subscriber.stop()
        self.assertFalse(subscriber._connected)
        subscriber._sio.disconnect.assert_called_once()

    def test_logging(self):
        subscriber = IpcSubscriber(self.url, self.logger)
        subscriber.logger.info("test message")
        self.logger.info.assert_called_with("test message")

    def test_run_connects_and_sleeps(self):
        """Test that run() calls connect and sleeps once, then exits."""
        subscriber = IpcSubscriber(self.url, self.logger)

        # Patch _setup_sio to prevent overwriting self._sio
        with patch.object(subscriber, "_setup_sio", return_value=None):
            # Patch sleep to stop loop after one iteration
            def stop_loop(seconds):
                subscriber._stop_event.set()

            subscriber._sio.sleep.side_effect = stop_loop

            subscriber.run()

            subscriber._sio.connect.assert_called_with(
                self.url, wait=True, transports=["websocket", "polling"]
            )
