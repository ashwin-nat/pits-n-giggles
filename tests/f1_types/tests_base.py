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

from lib.f1_types import F1PacketBase, PacketHeader, F1PacketType
from lib.f1_types.base_pkt import F1BaseEnum, F1CompareableEnum, F1SubPacketBase
from .tests_parser_base import F1TypesTest


# --- Helper classes for testing ---

class Color(F1BaseEnum):
    RED = 1
    GREEN = 2
    BLUE = 3

class Severity(F1CompareableEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3

class PacketWithoutToJSON(F1PacketBase):
    def __init__(self, header):
        super().__init__(header)

class SubPacketWithoutToJSON(F1SubPacketBase):
    def __init__(self, _data: int):
        pass

class DummyDiffPacket(F1SubPacketBase):
    __slots__ = ("a", "b")

    def __init__(self, a, b):
        self.a = a
        self.b = b

    def toJSON(self):
        return {"a": self.a, "b": self.b}

class OtherPacket(F1SubPacketBase):
    __slots__ = ("x",)

    def __init__(self, x):
        self.x = x

    def toJSON(self):
        return {"x": self.x}

# --- Test cases ---

class TestF1BaseEnum(F1TypesTest):
    def test_from_value_valid(self):
        self.assertEqual(Color(1), Color.RED)
        self.assertEqual(Color(3), Color.BLUE)

    def test_from_value_invalid(self):
        self.assertFalse(Color.isValid(99))

class TestF1CompareableEnum(F1TypesTest):
    def test_comparison(self):
        self.assertTrue(Severity.LOW < Severity.MEDIUM)
        self.assertTrue(Severity.HIGH > Severity.MEDIUM)
        self.assertTrue(Severity.LOW <= Severity.LOW)
        self.assertTrue(Severity.HIGH >= Severity.HIGH)
        self.assertFalse(Severity.MEDIUM == Severity.HIGH)
        self.assertTrue(Severity.MEDIUM != Severity.HIGH)

    def test_invalid_comparison(self):
        with self.assertRaises(TypeError):
            _ = Severity.LOW < "not-an-enum"

class TestF1PacketBase(F1TypesTest):
    def setUp(self):
        self.m_header = self.getRandomHeader(packet_type=F1PacketType.MOTION, game_year=25, num_players=22)

    def test_header_assignment(self):
        packet = PacketWithoutToJSON(self.m_header)
        self.assertEqual(packet.m_header, self.m_header)

    def test_not_implemented(self):
        packet = PacketWithoutToJSON(self.m_header)
        with self.assertRaises(NotImplementedError):
            packet.toJSON()

class TestF1SubPacketBase(F1TypesTest):
    def test_not_implemented(self):
        packet = SubPacketWithoutToJSON(1)
        with self.assertRaises(NotImplementedError):
            packet.toJSON()

    def test_diff_no_changes(self):
        p1 = DummyDiffPacket(1, 2)
        p2 = DummyDiffPacket(1, 2)
        changes = p1.diff_fields(p2)
        self.assertEqual(changes, {})

    def test_diff_with_changes(self):
        p1 = DummyDiffPacket(1, 2)
        p2 = DummyDiffPacket(1, 3)
        changes = p1.diff_fields(p2)
        self.assertEqual(changes, {"b": {"old_value": 2, "new_value": 3}})

    def test_diff_with_field_subset(self):
        p1 = DummyDiffPacket(1, 2)
        p2 = DummyDiffPacket(9, 3)
        changes = p1.diff_fields(p2, ["b"])
        self.assertEqual(changes, {"b": {"old_value": 2, "new_value": 3}})

    def test_diff_type_mismatch(self):
        p1 = DummyDiffPacket(1, 2)
        p2 = OtherPacket(5)
        with self.assertRaises(TypeError):
            p1.diff_fields(p2)
