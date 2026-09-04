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
import pytest

from lib.f1_types.base_pkt import (F1BaseEnum, F1CompareableEnum,
                                   F1RawValueEnum, F1SubPacketBase)
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

class Shape(F1RawValueEnum):
    """Stand-in for any enum whose source keeps inventing values we don't declare."""
    CIRCLE = 1
    SQUARE = 2
    UNKNOWN = 255

    def __str__(self):
        # Dict lookup keyed by member: exercises hashing/equality of the pseudo-members
        return {
            Shape.CIRCLE: "Circle",
            Shape.SQUARE: "Square",
            Shape.UNKNOWN: "Unknown",
        }[self]

    def has_corners(self):
        # Membership check that deliberately lumps unknowns in with one known value
        return self in [Shape.SQUARE, Shape.UNKNOWN]

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

    def test_hashable(self):
        # Since overriding __eq__ disables the builtin __hash__ method,
        # this tc ensures that the explict __hash__ definition works and doesn't break
        mapping = {
            Severity.LOW: "low",
            Severity.MEDIUM: "medium",
            Severity.HIGH: "high",
        }

        self.assertEqual(mapping[Severity.LOW], "low")
        self.assertEqual(mapping[Severity.MEDIUM], "medium")
        self.assertEqual(mapping[Severity.HIGH], "high")

class TestF1RawValueEnum:
    """Undeclared values must be indistinguishable from UNKNOWN, while still
    carrying the incoming raw value."""

    # --- sanity: declared members are untouched ---

    @pytest.mark.parametrize("value, expected", [(1, Shape.CIRCLE), (2, Shape.SQUARE),
                                                 (255, Shape.UNKNOWN)])
    def test_declared_values_still_resolve(self, value, expected):
        assert Shape(value) is expected

    def test_declared_member_is_not_unknown(self):
        assert not Shape.CIRCLE.is_unknown()
        assert Shape.CIRCLE.raw_value == 1

    def test_sentinel_itself_is_not_flagged_unknown(self):
        # UNKNOWN is a declared member, so it reports its own value and no raw payload
        assert not Shape.UNKNOWN.is_unknown()
        assert Shape.UNKNOWN.raw_value == 255

    def test_pseudo_members_are_not_enumerated(self):
        Shape(50)
        assert list(Shape) == [Shape.CIRCLE, Shape.SQUARE, Shape.UNKNOWN]

    def test_non_int_still_raises(self):
        with pytest.raises(ValueError):
            Shape("nope")

    def test_bool_is_not_captured_as_a_raw_value(self):
        # True collides with CIRCLE's value and is resolved by the stdlib before
        # _missing_ runs; False reaches _missing_ and is rejected rather than
        # being recorded as a raw value
        assert Shape(True) is Shape.CIRCLE
        with pytest.raises(ValueError):
            Shape(False)

    # --- equality: no functional change from plain safeCast-to-UNKNOWN ---

    def test_two_different_unknowns_are_equal(self):
        assert Shape(50) == Shape(60)

    @pytest.mark.parametrize("value", [4, 50, 60, 254])
    def test_unknown_equals_the_sentinel(self, value):
        assert Shape(value) == Shape.UNKNOWN

    def test_unknown_not_equal_to_declared_member(self):
        assert Shape(50) != Shape.CIRCLE

    def test_unknowns_hash_like_the_sentinel(self):
        assert hash(Shape(50)) == hash(Shape(60)) == hash(Shape.UNKNOWN)

    def test_unknowns_collapse_in_a_set(self):
        assert {Shape(50), Shape(60), Shape.UNKNOWN} == {Shape.UNKNOWN}

    def test_unknown_works_as_a_dict_key(self):
        # __str__ does a dict lookup keyed by member, so this must resolve
        assert {Shape.UNKNOWN: "unknown"}[Shape(50)] == "unknown"

    def test_unknown_matches_in_membership_checks(self):
        # Guards the `self in [...]` pattern used to group unknowns with a known value
        assert Shape(50).has_corners()

    def test_str_matches_the_sentinel(self):
        assert str(Shape(50)) == str(Shape.UNKNOWN) == "Unknown"

    def test_value_matches_the_sentinel(self):
        assert Shape(50).value == Shape.UNKNOWN.value

    def test_comparison_with_foreign_type(self):
        assert Shape(50) != "not-an-enum"
        assert Shape.CIRCLE != 1

    # --- the payload: the whole point of the exercise ---

    @pytest.mark.parametrize("value", [4, 50, 60, 254])
    def test_raw_value_is_preserved(self, value):
        assert Shape(value).raw_value == value

    def test_unknowns_are_flagged(self):
        assert Shape(50).is_unknown()

    def test_equal_unknowns_keep_distinct_raw_values(self):
        x, y = Shape(50), Shape(60)
        assert x == y
        assert x.raw_value != y.raw_value

    def test_same_raw_value_is_cached(self):
        assert Shape(50) is Shape(50)

    def test_safe_cast_preserves_raw_value(self):
        # safeCast is the path callers actually use
        assert Shape.safeCast(50, Shape.UNKNOWN).raw_value == 50
