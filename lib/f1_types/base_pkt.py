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

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

from typing import Dict, Any
from enum import Enum
from abc import ABC, abstractmethod

from .header import PacketHeader

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class BaseEnum(Enum):
    @classmethod
    def isValid(cls, value: int) -> bool:
        """
        Check if the given value is a valid enum value.

        Args:
            value (int): The value to validate.

        Returns:
            bool: True if valid for this enum.
        """
        if isinstance(value, cls):
            return True
        return any(value == member.value for member in cls)

class F1PacketBase:
    """
    Base class for parsed F1 telemetry packets.
    """

    def __init__(self, header: PacketHeader) -> None:
        """
        Initializes the PacketHeaderParser with the raw packet data.

        Args:
            data (bytes): Raw binary data representing the packet header.
        """

        self.m_header: PacketHeader = header

    @abstractmethod
    def __str__(self) -> str:
        """String representation

        Returns:
            str: String representation
        """
        pass

    @abstractmethod
    def toJSON(self, include_header: bool) -> Dict[str, Any]:
        """Converts the object to a dictionary suitable for JSON serialization.

        Arguments:
            include_header(bool): Whether header should be included in the dict

        Returns:
            Dict[str, Any]: A dictionary representing the JSON-compatible data.
        """
        pass

class F1SubPacketBase:
    """
    Base class for parsed nested F1 telemetry packets.
    """

    def __init__(self) -> None:
        """
        Initializes the PacketHeaderParser with the raw packet data.

        Args:
            data (bytes): Raw binary data representing the packet header.
        """
        return

    @abstractmethod
    def __str__(self) -> str:
        """String representation

        Returns:
            str: String representation
        """
        pass

    @abstractmethod
    def toJSON(self, include_header: bool) -> Dict[str, Any]:
        """Converts the object to a dictionary suitable for JSON serialization.

        Arguments:
            include_header(bool): Whether header should be included in the dict

        Returns:
            Dict[str, Any]: A dictionary representing the JSON-compatible data.
        """
        pass
