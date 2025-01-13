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

import os
import sys
import random
import io
from unittest.mock import patch
from unittest.mock import patch, MagicMock

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.packet_forwarder import UDPForwarder
from tests_base import F1TelemetryUnitTestsBase

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
