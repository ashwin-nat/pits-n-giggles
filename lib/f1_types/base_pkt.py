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
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, Tuple

from .header import PacketHeader

# -------------------------------------- TYPES -------------------------------------------------------------------------

T_Enum = TypeVar("T_Enum", bound="F1BaseEnum")
T_SubPacket = TypeVar("T_SubPacket", bound="F1SubPacketBase")

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

    @classmethod
    def safeCast(cls: Type[T_Enum], value: Union[int, T_Enum]) -> Union[T_Enum, int]:
        """
        Safely cast a value to the enum type.

        Args:
            value (int): The value to cast.

        Returns:
            Optional[F1BaseEnum]: The cast enum value.
        """
        return cls(value) if cls.isValid(value) else value

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

    __slots__ = ("m_header",)

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
    All derived classes must use __slots__.
    """

    @abstractmethod
    def toJSON(self) -> Dict[str, Any]:
        raise NotImplementedError(f"{self.__class__.__name__} must implement toJSON()")

    def diff_fields(
        self: T_SubPacket,
        other: T_SubPacket,
        fields: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Compare two packet objects and return a dict of changed fields.

        Args:
            other: Another object of the same subclass.
            fields: Optional list of field names to check.
                    If None, defaults to this class's __slots__.

        Returns:
            Dict[str, Dict[str, Any]]: {field: {"old_value": old, "new_value": new}}
        """
        if type(self) is not type(other):
            raise TypeError(
                f"Cannot diff objects of different types: {type(self)} vs {type(other)}"
            )

        if fields is None:
            fields = self.__slots__  # type: ignore[attr-defined]

        changes: Dict[str, Dict[str, Any]] = {}
        for field in fields:
            old_val = getattr(self, field)
            new_val = getattr(other, field)
            if old_val != new_val:
                changes[field] = {"old_value": old_val, "new_value": new_val}

        return changes
