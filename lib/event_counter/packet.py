# MIT License
#
# Copyright (c) [2026] [Ashwin Natarajan]
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

from dataclasses import dataclass
from typing import ClassVar

from .base import Stat

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------


@dataclass(slots=True)
class PacketStat(Stat):
    """Packet throughput counter with cumulative payload size.

    Tracks:
        - `count`: number of packets observed.
        - `bytes`: total payload bytes across observed packets.
    """

    TYPE: ClassVar[str] = "__PACKET__"
    bytes: int = 0

    def increment_with_size(self, size: int) -> None:
        """Record one packet and add its payload size to total bytes."""
        self.count += 1
        self.bytes += size

    def to_dict(self) -> dict:
        """Serialize this packet stat to a JSON-friendly dictionary."""
        return {
            "type": self.TYPE,
            "count": self.count,
            "bytes": self.bytes,
        }
