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
import random
import sys
from unittest.mock import AsyncMock, MagicMock, patch

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests_base import F1TelemetryUnitTestsBase

from lib.packet_forwarder import AsyncUDPForwarder

# ----------------------------------------------------------------------------------------------------------------------

class TestAsyncUDPForwarder(F1TelemetryUnitTestsBase):
    def setUp(self):
        self.forward_addresses = [('127.0.0.1', 21212), ('192.168.1.1', 8080)]
        self.test_data = self._generateRandomData(1200)

    def _generateRandomData(self, length: int) -> bytes:
        return bytes(random.randint(0, 255) for _ in range(length))

    def test_forwarding_data(self):
        async def async_test():
            with patch("lib.packet_forwarder.AsyncUDPTransport.send", new_callable=AsyncMock) as mock_send:
                forwarder = AsyncUDPForwarder(self.forward_addresses)
                await forwarder.forward(self.test_data)

                # Allow scheduled tasks to run
                await asyncio.sleep(0.01)

                self.assertEqual(mock_send.call_count, len(self.forward_addresses))
                for addr in self.forward_addresses:
                    mock_send.assert_any_call(self.test_data, addr)

        asyncio.run(async_test())

    def test_no_forwarding_on_empty_list(self):
        async def async_test():
            with patch("lib.packet_forwarder.AsyncUDPTransport.send", new_callable=AsyncMock) as mock_send:
                forwarder = AsyncUDPForwarder([])
                await forwarder.forward(self.test_data)

                await asyncio.sleep(0.01)
                mock_send.assert_not_called()

        asyncio.run(async_test())

    def test_transport_error_handling(self):
        async def async_test():
            with patch("lib.packet_forwarder.AsyncUDPTransport.send", new_callable=AsyncMock) as mock_send:
                mock_send.side_effect = OSError("Simulated error")
                forwarder = AsyncUDPForwarder(self.forward_addresses)

                # Should not raise despite exception
                try:
                    await forwarder.forward(self.test_data)
                    await asyncio.sleep(0.01)
                except Exception as e:
                    self.fail(f"Unexpected exception: {e}")

                self.assertEqual(mock_send.call_count, len(self.forward_addresses))

        asyncio.run(async_test())

    def test_multiple_forward_calls(self):
        async def async_test():
            with patch("lib.packet_forwarder.AsyncUDPTransport.send", new_callable=AsyncMock) as mock_send:
                forwarder = AsyncUDPForwarder(self.forward_addresses)

                for _ in range(3):
                    await forwarder.forward(self.test_data)

                await asyncio.sleep(0.05)  # Give time for all tasks

                self.assertEqual(mock_send.call_count, len(self.forward_addresses) * 3)

        asyncio.run(async_test())

    def test_partial_forward_failure(self):
        async def async_test():
            with patch("lib.packet_forwarder.AsyncUDPTransport.send", new_callable=AsyncMock) as mock_send:
                # Simulate failure for the second address only
                async def side_effect(data, addr):
                    if addr == self.forward_addresses[1]:
                        raise OSError("Simulated error for one address")
                    await asyncio.sleep(0)

                mock_send.side_effect = side_effect

                forwarder = AsyncUDPForwarder(self.forward_addresses)

                try:
                    await forwarder.forward(self.test_data)
                    await asyncio.sleep(0.01)
                except Exception as e:
                    self.fail(f"Unexpected exception: {e}")

                self.assertEqual(mock_send.call_count, len(self.forward_addresses))
                mock_send.assert_any_call(self.test_data, self.forward_addresses[0])
                mock_send.assert_any_call(self.test_data, self.forward_addresses[1])

        asyncio.run(async_test())

# ----------------------------------------------------------------------------------------------------------------------

class TestAsyncUDPForwarderUpdateTargets(F1TelemetryUnitTestsBase):
    """Tests for runtime target updates via update_targets()."""

    def setUp(self):
        self.addr_a = ('127.0.0.1', 21212)
        self.addr_b = ('127.0.0.1', 21213)
        self.addr_c = ('127.0.0.1', 21214)
        self.test_data = bytes(range(64))

    def test_update_targets_add_to_empty(self):
        """Forwarder starts empty; adding a target makes it forward."""
        async def async_test():
            with patch("lib.packet_forwarder.AsyncUDPTransport.send", new_callable=AsyncMock) as mock_send:
                forwarder = AsyncUDPForwarder([])
                await forwarder.forward(self.test_data)
                mock_send.assert_not_called()

                forwarder.update_targets([self.addr_a])
                await forwarder.forward(self.test_data)
                mock_send.assert_called_once_with(self.test_data, self.addr_a)

        asyncio.run(async_test())

    def test_update_targets_add_to_existing(self):
        """Adding a second target results in both being forwarded to."""
        async def async_test():
            with patch("lib.packet_forwarder.AsyncUDPTransport.send", new_callable=AsyncMock) as mock_send:
                forwarder = AsyncUDPForwarder([self.addr_a])
                forwarder.update_targets([self.addr_a, self.addr_b])
                await forwarder.forward(self.test_data)
                self.assertEqual(mock_send.call_count, 2)
                mock_send.assert_any_call(self.test_data, self.addr_a)
                mock_send.assert_any_call(self.test_data, self.addr_b)

        asyncio.run(async_test())

    def test_update_targets_remove_target(self):
        """Removing a target stops forwarding to it."""
        async def async_test():
            with patch("lib.packet_forwarder.AsyncUDPTransport.send", new_callable=AsyncMock) as mock_send:
                forwarder = AsyncUDPForwarder([self.addr_a, self.addr_b])
                forwarder.update_targets([self.addr_a])
                await forwarder.forward(self.test_data)
                mock_send.assert_called_once_with(self.test_data, self.addr_a)

        asyncio.run(async_test())

    def test_update_targets_replace_all(self):
        """Replacing all targets forwards only to the new set."""
        async def async_test():
            with patch("lib.packet_forwarder.AsyncUDPTransport.send", new_callable=AsyncMock) as mock_send:
                forwarder = AsyncUDPForwarder([self.addr_a])
                forwarder.update_targets([self.addr_b, self.addr_c])
                await forwarder.forward(self.test_data)
                self.assertEqual(mock_send.call_count, 2)
                mock_send.assert_any_call(self.test_data, self.addr_b)
                mock_send.assert_any_call(self.test_data, self.addr_c)

        asyncio.run(async_test())

    def test_update_targets_empty_list_disables_forwarding(self):
        """Setting an empty target list stops all forwarding."""
        async def async_test():
            with patch("lib.packet_forwarder.AsyncUDPTransport.send", new_callable=AsyncMock) as mock_send:
                forwarder = AsyncUDPForwarder([self.addr_a])
                forwarder.update_targets([])
                await forwarder.forward(self.test_data)
                mock_send.assert_not_called()

        asyncio.run(async_test())

    def test_update_targets_unchanged_targets_reuse_socket(self):
        """Targets that remain across an update keep their socket object."""
        async def async_test():
            with patch("lib.packet_forwarder.socket.socket") as mock_sock_cls:
                mock_sock = MagicMock()
                mock_sock.connect = MagicMock()
                mock_sock.setblocking = MagicMock()
                mock_sock_cls.return_value = mock_sock

                forwarder = AsyncUDPForwarder([self.addr_a])
                socket_after_init = forwarder.m_transport.m_sockets[self.addr_a]

                # Update: keep addr_a, add addr_b
                forwarder.update_targets([self.addr_a, self.addr_b])
                socket_after_update = forwarder.m_transport.m_sockets[self.addr_a]

                self.assertIs(socket_after_init, socket_after_update,
                              "Unchanged target should reuse its existing socket")

        asyncio.run(async_test())