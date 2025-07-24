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

from lib.packet_forwarder import AsyncUDPForwarder, UDPForwarder

# ----------------------------------------------------------------------------------------------------------------------

class TestUDPForwarder(F1TelemetryUnitTestsBase):

    def setUp(self):
        """Set up test cases with mock data and suppress stdout/stderr."""
        self.forward_addresses = [('localhost', 21212), ('192.168.1.1', 8080)]
        self.forwarder = UDPForwarder(self.forward_addresses)
        self.test_data = self._generateRandomData(1200)  # Generate random data of 1200 bytes

    def _generateRandomData(self, length: int) -> bytes:
        """Generate random data of a given length."""
        # Ensure length is a positive integer and string.ascii_letters and string.digits are correctly used
        if not isinstance(length, int) or length <= 0:
            raise ValueError("Length must be a positive integer")

        # Generate random data
        return bytes(random.randint(0, 255) for _ in range(length))

    @patch('socket.socket')  # Patch socket to mock its behavior
    def test_forwarding_data(self, mock_socket):
        """Test that data is forwarded to all configured destinations."""
        # Create a mock socket instance
        mock_sendto = MagicMock()
        mock_socket.return_value = MagicMock(sendto=mock_sendto)

        # Call the forward method with random data
        self.forwarder.forward(self.test_data)

        # Ensure sendto was called for each destination
        for destination in self.forward_addresses:
            mock_sendto.assert_any_call(self.test_data, destination)

        # Check if sendto was called the correct number of times (one for each destination)
        self.assertEqual(mock_sendto.call_count, len(self.forward_addresses))

    @patch('socket.socket')
    def test_no_forwarding_on_empty_list(self, mock_socket):
        """Test that no forwarding occurs when the list of addresses is empty."""
        # Create an empty forwarding list
        empty_forwarder = UDPForwarder([])

        # Call the forward method (should not attempt to forward anything)
        empty_forwarder.forward(self.test_data)

        # Ensure that socket.sendto is not called
        mock_socket.return_value.sendto.assert_not_called()

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
                def side_effect(data, addr):
                    if addr == self.forward_addresses[1]:
                        raise OSError("Simulated error for one address")
                    return asyncio.Future()  # default mock async response

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