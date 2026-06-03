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

from .base_pkt import F1CompareableEnum


class ERSDeployMode(F1CompareableEnum): # pylint: disable=invalid-enum-extension
    """Abstract base for ERS deploy mode enums. Defines no members."""

    def __str__(self) -> str:
        return self.name.title()


class ERSDeployModePre26(ERSDeployMode):
    """ERS deployment modes for pre-2026 seasons. Mode 3 = OVERTAKE."""

    NONE = 0
    MEDIUM = 1
    HOTLAP = 2
    OVERTAKE = 3


class ERSDeployMode26(ERSDeployMode):
    """ERS deployment modes for 2026+ seasons. Mode 3 = BOOST."""

    NONE = 0
    MEDIUM = 1
    HOTLAP = 2
    BOOST = 3
