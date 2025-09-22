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
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar, Union

from .errors import PacketCountValidationError, PacketParsingError
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
        try:
            cls(value)
            return True
        except (ValueError, TypeError):
            return False

    @classmethod
    def safeCast(cls: Type[T_Enum], value: Union[int, T_Enum]) -> Union[T_Enum, int]:
        """
        Safely cast a value to the enum type.

        Args:
            value (int): The value to cast.

        Returns:
            Optional[F1BaseEnum]: The cast enum value.
        """
        try:
            return cls(value)
        except ValueError:
            return value

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
    All derived classes must use __slots__.
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
            fields = self.__slots__ # pylint: disable=no-member

        changes: Dict[str, Dict[str, Any]] = {}
        for field in fields:
            old_val = getattr(self, field)
            new_val = getattr(other, field)
            if old_val != new_val:
                changes[field] = {"old_value": old_val, "new_value": new_val}

        return changes

    @classmethod
    def parse_array(
        cls: type[T_SubPacket],
        data: bytes,
        offset: int,
        item_len: int,
        count: int,
        max_count: int,
        **item_kwargs: Any
    ) -> Tuple[List[T_SubPacket], int]:
        """
        Parse a fixed number of sub-packets of this subclass from the data.

        Args:
            data (bytes): The raw data buffer.
            offset (int): The starting offset in the data.
            item_len (int): The length in bytes of each item.
            count (int): The number of items to parse.
            max_count (int): The maximum allowed items.
            **item_kwargs: Extra args passed to the subclass constructor.

        Returns:
            tuple[list[T_SubPacket], int]: A list of parsed sub-packets and the updated offset.
        """
        if count == 0:
            return [], offset

        total_raw_len = max_count * item_len
        raw = data[offset : offset + total_raw_len]
        expected_len = count * item_len

        if count > max_count:
            raise PacketCountValidationError(
                f"Too many {cls.__name__} items: {count} > {max_count}"
            )
        if total_raw_len < expected_len:
            raise PacketParsingError(
                f"Insufficient {cls.__name__} data: "
                f"expected {expected_len} bytes, got {total_raw_len} for {count} items"
            )

        items = [
            cls(raw[i : i + item_len], **item_kwargs)
            for i in range(0, expected_len, item_len)
        ]
        return items, offset + total_raw_len
