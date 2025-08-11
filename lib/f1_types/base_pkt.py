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

from abc import abstractmethod
from enum import Enum
from functools import total_ordering
from typing import Any, Dict, Optional

from .header import PacketHeader

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class F1BaseEnum(Enum):
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

    def __str__(self):
        """Return the string representation of this object

        Returns:
            str: string representation
        """

        return self.name

@total_ordering
class F1CompareableEnum(F1BaseEnum):
    """
    Base class for Enums that require comparison support.

    Inherits from F1BaseEnum and adds ordering operators
    based on the underlying integer values.

    Note:
        Only use this class for Enums where ordering of values makes sense.
    """

    def __eq__(self, other: Any) -> bool:
        """
        Check equality with another enum of the same type.

        Args:
            other (Any): The object to compare.

        Returns:
            bool: True if values are equal.
        """
        if isinstance(other, self.__class__):
            return self.value == other.value
        return NotImplemented

    def __lt__(self, other: Any) -> bool:
        """
        Check if this enum's value is less than another's.

        Args:
            other (Any): The object to compare.

        Returns:
            bool: True if this value is less than the other.
        """
        if isinstance(other, self.__class__):
            return self.value < other.value
        return NotImplemented

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
    def toJSON(self, include_header: Optional[bool] = False) -> Dict[str, Any]:
        """Converts the object to a dictionary suitable for JSON serialization.

        Arguments:
            include_header(bool): Whether header should be included in the dict. Default: False

        Returns:
            Dict[str, Any]: A dictionary representing the JSON-compatible data.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement toJSON()")

class F1SubPacketBase:
    """
    Base class for parsed nested F1 telemetry packets.
    """

    @abstractmethod
    def toJSON(self) -> Dict[str, Any]:
        """Converts the object to a dictionary suitable for JSON serialization.

        Returns:
            Dict[str, Any]: A dictionary representing the JSON-compatible data.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement toJSON()")
