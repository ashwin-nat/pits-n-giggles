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

from apps.lib.packet_forwarder import AsyncUDPForwarder, UDPForwarder

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
        """Set up test cases with mock data."""
        self.forward_addresses = [('localhost', 21212), ('192.168.1.1', 8080)]
        self.forwarder = AsyncUDPForwarder(self.forward_addresses)
        self.test_data = self._generateRandomData(1200)  # Generate random data of 1200 bytes

    def _generateRandomData(self, length: int) -> bytes:
        """Generate random data of a given length."""
        if not isinstance(length, int) or length <= 0:
            raise ValueError("Length must be a positive integer")
        return bytes(random.randint(0, 255) for _ in range(length))

    def test_forwarding_data(self):
        """Test that data is forwarded to all configured destinations."""
        async def async_test_forwarding():
            # Mock the send method of the transport
            with patch.object(self.forwarder.m_transport, 'send', new_callable=AsyncMock) as mock_send:
                # Call the forward method
                await self.forwarder.forward(self.test_data)

                # Check that send was called for each destination
                self.assertEqual(mock_send.call_count, len(self.forward_addresses))

                # Verify the calls were made with correct arguments
                for destination in self.forward_addresses:
                    mock_send.assert_any_call(self.test_data, destination)

        # Run the async test synchronously
        asyncio.run(async_test_forwarding())

    def test_no_forwarding_on_empty_list(self):
        """Test that no forwarding occurs when the list of addresses is empty."""
        async def async_test_no_forwarding():
            # Create an empty forwarding list
            empty_forwarder = AsyncUDPForwarder([])

            # Mock the send method of the transport
            with patch.object(empty_forwarder.m_transport, 'send', new_callable=AsyncMock) as mock_send:
                # Call the forward method
                await empty_forwarder.forward(self.test_data)

                # Ensure that send was not called
                mock_send.assert_not_called()

        # Run the async test synchronously
        asyncio.run(async_test_no_forwarding())

    def test_transport_error_handling(self):
        """Test error handling during packet forwarding."""
        async def async_test_error_handling():
            # Mock the send method to raise an exception
            with patch.object(self.forwarder.m_transport, 'send', new_callable=AsyncMock) as mock_send:
                # Configure the mock to raise an OSError
                mock_send.side_effect = OSError("Simulated network error")

                # Call forward method and ensure it doesn't raise an unhandled exception
                try:
                    await self.forwarder.forward(self.test_data)
                except Exception as e:
                    self.fail(f"Forward method raised an unexpected exception: {e}")

                # Verify send was called for each destination
                self.assertEqual(mock_send.call_count, len(self.forward_addresses))

        # Run the async test synchronously
        asyncio.run(async_test_error_handling())

    def test_multiple_forward_calls(self):
        """Test multiple consecutive forward calls."""
        async def async_test_multiple_forwards():
            # Mock the send method of the transport
            with patch.object(self.forwarder.m_transport, 'send', new_callable=AsyncMock) as mock_send:
                # Make multiple forward calls
                for _ in range(3):
                    await self.forwarder.forward(self.test_data)

                # Check that send was called correct number of times
                self.assertEqual(mock_send.call_count, len(self.forward_addresses) * 3)

        # Run the async test synchronously
        asyncio.run(async_test_multiple_forwards())
