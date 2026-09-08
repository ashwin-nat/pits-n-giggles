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

# ------------------------- IMPORTS -------------------------------------------------------------------------------------

from typing import Any

# ------------------------- ERROR CLASSES ------------------------------------------------------------------------------

class InvalidPacketLengthError(Exception):
    """
    This exception type is used to indicate to the telemetry manager that there has
    been a parsing error due to receving a packet of unexpected length (possibly
    incomplete or corrupt. or more realistically a bug)
    """
    def __init__(self, message):
        super().__init__(f"Invalid packet length. {message}")

class PacketParsingError(Exception):
    """Raised when packet data is malformed or insufficient"""
    def __init__(self, message):
        super().__init__(f"Malformed packet. {message}")

class PacketCountValidationError(Exception):
    """Raised when sub-packet count validation against max count fails"""
    def __init__(self, message):
        super().__init__(f"Packet count validation error. {message}")

class UnsupportedValueError(Exception):
    """
    Raised when a packet field carries a value this codebase does not know how to handle,
    leaving the packet impossible to interpret.

    Not necessarily corruption - the game introduces new values in patches. Prefer
    F1BaseEnum.safeCast (or F1RawValueEnum) wherever an unknown value can be tolerated;
    raise this only where the packet is not meaningful without it, so that the parser
    factory drops it and logs the offending value.
    """
    def __init__(self, field: str, value: Any):
        self.m_field = field
        self.m_value = value
        super().__init__(f"Unsupported value for {field}: {value!r}")
