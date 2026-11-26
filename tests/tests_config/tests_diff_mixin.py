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
# pylint: skip-file

import os
import sys
import typing
from enum import Enum
from typing import Any, Dict, Optional, Tuple

import allure
import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import BaseModel, Field

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.config import DisplaySettings, HudSettings, MfdPageId, MfdSettings, NetworkSettings, PngSettings
from lib.config.schema.diff import ConfigDiffMixin

from .tests_config_base import TestF1ConfigBase

pytestmark = allure.feature("Config diff")

# -------------------------------------- Simple test models ------------------------------------------------------------

class Mode(str, Enum):
    A = "a"
    B = "b"


class Inner(ConfigDiffMixin, BaseModel):
    x: int = 0
    y: str = "hello"


class Outer(ConfigDiffMixin, BaseModel):
    name: str = "default"
    value: int = 1
    inner: Inner = Field(default_factory=Inner)
    tags: Dict[str, int] = Field(default_factory=dict)
    position: Dict[str, int] = Field(
        default_factory=dict,
        json_schema_extra={"diff_exclude": True},
    )
    ratio: Optional[float] = None
    mode: Mode = Mode.A
    items: Dict[str, Inner] = Field(default_factory=dict)


class SectionA(ConfigDiffMixin, BaseModel):
    alpha: int = 0
    beta: str = "x"


class SectionB(ConfigDiffMixin, BaseModel):
    gamma: float = 1.0


class Root(ConfigDiffMixin, BaseModel):
    section_a: SectionA = Field(default_factory=SectionA)
    section_b: SectionB = Field(default_factory=SectionB)
    outer: Outer = Field(default_factory=Outer)

# -------------------------------------- Tests -----------------------------------------------------------------------

@allure.story("Examples")
class TestConfigDiffMixin(TestF1ConfigBase):
    """Tests for ConfigDiffMixin recursive diffing"""

    # ---- Case 3: full recursive diff ----

    def test_identical_models_produce_empty_diff(self):
        """identical models produce empty diff"""
        a = Outer()
        b = Outer()
        self.assertEqual(a.diff(b), {})

    def test_primitive_field_changed(self):
        """changed primitive field appears in diff"""
        a = Outer(name="old", value=1)
        b = Outer(name="new", value=1)
        result = a.diff(b)
        self.assertIn("name", result)
        self.assertEqual(result["name"]["old_value"], "old")
        self.assertEqual(result["name"]["new_value"], "new")
        self.assertNotIn("value", result)

    def test_nested_submodel_field_changed(self):
        """changed nested submodel field appears under its key"""
        a = Outer(inner=Inner(x=1, y="hi"))
        b = Outer(inner=Inner(x=2, y="hi"))
        result = a.diff(b)
        self.assertIn("inner", result)
        self.assertIn("x", result["inner"])
        self.assertEqual(result["inner"]["x"]["old_value"], 1)
        self.assertEqual(result["inner"]["x"]["new_value"], 2)
        self.assertNotIn("y", result["inner"])

    def test_nested_submodel_unchanged_not_in_diff(self):
        """unchanged nested submodel is absent from diff"""
        a = Outer(name="changed", inner=Inner(x=5))
        b = Outer(name="different", inner=Inner(x=5))
        result = a.diff(b)
        self.assertNotIn("inner", result)

    def test_dict_field_key_value_changed(self):
        """changed value in a dict field appears in diff"""
        a = Outer(tags={"lap": 1, "sector": 2})
        b = Outer(tags={"lap": 9, "sector": 2})
        result = a.diff(b)
        self.assertIn("tags", result)
        self.assertIn("lap", result["tags"])
        self.assertEqual(result["tags"]["lap"]["old_value"], 1)
        self.assertEqual(result["tags"]["lap"]["new_value"], 9)
        self.assertNotIn("sector", result["tags"])

    def test_dict_field_key_added(self):
        """new key in a dict field shows up in diff with old_value=None"""
        a = Outer(tags={})
        b = Outer(tags={"new_key": 42})
        result = a.diff(b)
        self.assertIn("tags", result)
        self.assertIn("new_key", result["tags"])
        self.assertIsNone(result["tags"]["new_key"]["old_value"])
        self.assertEqual(result["tags"]["new_key"]["new_value"], 42)

    def test_dict_field_key_removed(self):
        """removed key in a dict field shows up in diff with new_value=None"""
        a = Outer(tags={"gone": 7})
        b = Outer(tags={})
        result = a.diff(b)
        self.assertIn("tags", result)
        self.assertIn("gone", result["tags"])
        self.assertEqual(result["tags"]["gone"]["old_value"], 7)
        self.assertIsNone(result["tags"]["gone"]["new_value"])

    def test_dict_field_unchanged_not_in_diff(self):
        """unchanged dict field is absent from diff"""
        a = Outer(tags={"k": 1}, name="x")
        b = Outer(tags={"k": 1}, name="y")
        result = a.diff(b)
        self.assertNotIn("tags", result)

    # ---- diff_exclude annotation ----

    def test_diff_exclude_field_ignored(self):
        """field annotated with diff_exclude is not included in diff"""
        a = Outer(position={"x": 0, "y": 0})
        b = Outer(position={"x": 999, "y": 999})
        result = a.diff(b)
        self.assertNotIn("position", result)

    def test_diff_exclude_does_not_suppress_other_fields(self):
        """diff_exclude on one field does not suppress unrelated changed fields"""
        a = Outer(name="old", position={"x": 0})
        b = Outer(name="new", position={"x": 999})
        result = a.diff(b)
        self.assertIn("name", result)
        self.assertNotIn("position", result)

    # ---- has_changed ----

    def test_has_changed_true_when_different(self):
        """has_changed returns True when models differ"""
        a = Outer(value=1)
        b = Outer(value=2)
        self.assertTrue(a.has_changed(b))

    def test_has_changed_false_when_identical(self):
        """has_changed returns False when models are identical"""
        a = Outer()
        b = Outer()
        self.assertFalse(a.has_changed(b))

    # ---- Case 2: flat field list ----

    def test_diff_with_field_list_only_checks_listed_fields(self):
        """diff with field list only checks specified fields"""
        a = Outer(name="old", value=10)
        b = Outer(name="new", value=99)
        # Only watch "name"
        result = a.diff(b, ["name"])
        self.assertIn("name", result)
        self.assertNotIn("value", result)

    def test_diff_with_field_list_empty_when_listed_field_unchanged(self):
        """diff with field list is empty when the listed field is unchanged"""
        a = Outer(name="same", value=10)
        b = Outer(name="same", value=99)
        result = a.diff(b, ["name"])
        self.assertEqual(result, {})

    # ---- Case 1: section dict ----

    def test_diff_with_section_dict_targets_subsection(self):
        """diff with section dict only diffs named subsection"""
        a = Root(section_a=SectionA(alpha=1), section_b=SectionB(gamma=2.0))
        b = Root(section_a=SectionA(alpha=9), section_b=SectionB(gamma=9.0))
        # Only watch section_a
        result = a.diff(b, {"section_a": []})
        self.assertIn("section_a", result)
        self.assertNotIn("section_b", result)
        self.assertIn("alpha", result["section_a"])

    def test_diff_with_section_dict_empty_when_subsection_unchanged(self):
        """diff with section dict is empty when subsection is unchanged"""
        a = Root(section_a=SectionA(alpha=5), section_b=SectionB(gamma=9.0))
        b = Root(section_a=SectionA(alpha=5), section_b=SectionB(gamma=3.0))
        result = a.diff(b, {"section_a": []})
        self.assertEqual(result, {})

    def test_diff_with_section_dict_specific_subfields(self):
        """diff with section dict and specific subfields only checks those fields"""
        a = Root(section_a=SectionA(alpha=1, beta="x"))
        b = Root(section_a=SectionA(alpha=9, beta="z"))
        # Only watch beta within section_a
        result = a.diff(b, {"section_a": ["beta"]})
        self.assertIn("section_a", result)
        self.assertIn("beta", result["section_a"])
        self.assertNotIn("alpha", result["section_a"])

# -------------------------------------- PngSettings examples --------------------------------------------------------

def _hud_with_weather_page_disabled() -> HudSettings:
    pages = dict(PngSettings().HUD.mfd_settings.pages)
    pages[MfdPageId.WEATHER_FORECAST] = pages[MfdPageId.WEATHER_FORECAST].model_copy(update={"enabled": False})
    return HudSettings(mfd_settings=MfdSettings(pages=pages))


@allure.story("PngSettings examples")
@allure.title("One changed field shows as one leaf under its section")
def test_png_settings_leaf_diff():
    """Diffs default PngSettings against a copy with Network.telemetry_port changed.

    Expected: the diff holds that one leaf with its old and new value, under its section.
    """
    old = PngSettings()
    new = PngSettings(Network=NetworkSettings(telemetry_port=20778))

    assert old.diff(new) == {"Network": {"telemetry_port": {"old_value": 20777, "new_value": 20778}}}


@allure.story("PngSettings examples")
@allure.title("Several changed fields in one section show as sibling leaves")
def test_png_settings_multi_leaf_diff():
    """Diffs default PngSettings against a copy with two Network fields changed.

    Expected: both leaves sit under Network, and no other field or section appears.
    """
    old = PngSettings()
    new = PngSettings(Network=NetworkSettings(telemetry_port=20778, enable_pkt_ordering=True))

    assert old.diff(new) == {"Network": {
        "telemetry_port": {"old_value": 20777, "new_value": 20778},
        "enable_pkt_ordering": {"old_value": False, "new_value": True},
    }}


@allure.story("PngSettings examples")
@allure.title("A change inside a nested container shows at its full path")
def test_png_settings_single_container_diff():
    """Diffs default PngSettings against a copy with the weather MFD page disabled, a field of one entry in the
    HUD.mfd_settings.pages dict.

    Expected: the diff nests HUD > mfd_settings > pages > weather_forecast > enabled, and holds nothing else.
    """
    old = PngSettings()
    new = PngSettings(HUD=_hud_with_weather_page_disabled())

    assert old.diff(new) == {"HUD": {"mfd_settings": {"pages": {
        MfdPageId.WEATHER_FORECAST: {"enabled": {"old_value": True, "new_value": False}},
    }}}}


@allure.story("PngSettings examples")
@allure.title("Changes across several sections each show under their own section")
def test_png_settings_multi_container_diff():
    """Diffs default PngSettings against a copy with changes in Network, Display and inside HUD's MFD pages.

    Expected: one entry per changed section, each holding only its own changes, and has_changed is True.
    """
    old = PngSettings()
    new = PngSettings(Network=NetworkSettings(telemetry_port=20778), Display=DisplaySettings(refresh_interval=300),
                      HUD=_hud_with_weather_page_disabled())

    assert old.diff(new) == {
        "Network": {"telemetry_port": {"old_value": 20777, "new_value": 20778}},
        "Display": {"refresh_interval": {"old_value": 200, "new_value": 300}},
        "HUD": {"mfd_settings": {"pages": {
            MfdPageId.WEATHER_FORECAST: {"enabled": {"old_value": True, "new_value": False}},
        }}},
    }
    assert old.has_changed(new)

# -------------------------------------- Property strategies ---------------------------------------------------------

# Small value sets, so two independent draws often share fields, dict keys and dict values
_KEYS = st.sampled_from(["k1", "k2", "k3"])
_SMALL_INT = st.integers(0, 2)
_WORD = st.sampled_from(["a", "b"])

_INNERS = st.builds(Inner, x=_SMALL_INT, y=_WORD)
# position (diff_exclude) stays at its default: the properties do not cover exclusion, which is being dropped
_OUTERS = st.builds(
    Outer, name=_WORD, value=_SMALL_INT, inner=_INNERS, tags=st.dictionaries(_KEYS, _SMALL_INT),
    ratio=st.none() | st.sampled_from([0.5, 1.5]), mode=st.sampled_from(Mode),
    items=st.dictionaries(_KEYS, _INNERS))
_ROOTS = st.builds(Root, section_a=st.builds(SectionA, alpha=_SMALL_INT, beta=_WORD),
                   section_b=st.builds(SectionB, gamma=st.sampled_from([1.0, 2.0])), outer=_OUTERS)
_PAIRS = st.tuples(_ROOTS, _ROOTS)

# -------------------------------------- Property helpers ------------------------------------------------------------

def _is_leaf(entry: Any) -> bool:
    return isinstance(entry, dict) and set(entry) == {"old_value", "new_value"}


def _swap(diff: Dict[str, Any]) -> Dict[str, Any]:
    return {key: ({"old_value": entry["new_value"], "new_value": entry["old_value"]} if _is_leaf(entry)
                  else _swap(entry))
            for key, entry in diff.items()}


def _apply(value: Any, diff: Dict[str, Any], item_type: Any = None) -> Any:
    """value with diff's new values written in. In a dict field, a None new value marks a removed key, and
    added model values arrive serialized, so they are rebuilt as item_type."""
    if isinstance(value, BaseModel):
        updates = {}
        for name, entry in diff.items():
            args = typing.get_args(type(value).model_fields[name].annotation)
            updates[name] = entry["new_value"] if _is_leaf(entry) else \
                _apply(getattr(value, name), entry, args[1] if len(args) == 2 else None)
        return value.model_copy(update=updates)
    out = dict(value)
    for key, entry in diff.items():
        if not _is_leaf(entry):
            out[key] = _apply(out[key], entry)
        elif entry["new_value"] is None:
            del out[key]
        else:
            new = entry["new_value"]
            out[key] = item_type.model_validate(new) if isinstance(new, dict) and item_type else new
    return out

# -------------------------------------- Properties ------------------------------------------------------------------

@allure.story("Properties")
@allure.title("A diff with itself, or with a deep copy, is empty")
@given(pair=_PAIRS)
def test_diff_with_self_is_empty(pair: Tuple[Root, Root]) -> None:
    """Diffs a generated model with itself and with a deep copy.

    Expected: both diffs are empty and has_changed is False.
    """
    a, _ = pair
    assert a.diff(a) == {}
    assert a.diff(a.model_copy(deep=True)) == {}
    assert not a.has_changed(a)


@allure.story("Properties")
@allure.title("A diff is empty exactly when the two models are equal")
@given(pair=_PAIRS)
def test_diff_empty_iff_equal(pair: Tuple[Root, Root]) -> None:
    """Diffs two generated models drawn from small value sets, so they often share fields.

    Expected: has_changed is True exactly when the two models' data differs.
    """
    a, b = pair
    assert a.has_changed(b) == (a.model_dump() != b.model_dump())


@allure.story("Properties")
@allure.title("Swapping the two sides of a diff swaps every old and new value")
@given(pair=_PAIRS)
def test_diff_is_symmetric(pair: Tuple[Root, Root]) -> None:
    """Diffs two generated models both ways.

    Expected: b.diff(a) is a.diff(b) with old_value and new_value swapped at every leaf.
    """
    a, b = pair
    assert b.diff(a) == _swap(a.diff(b))


@allure.story("Properties")
@allure.title("Applying a diff to its old side gives its new side")
@given(pair=_PAIRS)
def test_diff_applied_gives_new_side(pair: Tuple[Root, Root]) -> None:
    """Writes every new value of a.diff(b) into a, removing dict keys whose new value is None.

    Expected: the result equals b, so the diff lists every change and only changes.
    """
    a, b = pair
    assert _apply(a, a.diff(b)).model_dump() == b.model_dump()


@allure.story("Properties")
@allure.title("A diff over chosen sections is the full diff narrowed to those sections")
@given(pair=_PAIRS, data=st.data())
def test_section_diff_is_narrowed_full_diff(pair: Tuple[Root, Root], data: st.DataObject) -> None:
    """Diffs two generated models over a random subset of sections ({"section_a": [], ...}).

    Expected: the result is the full diff with only those sections kept.
    """
    a, b = pair
    sections = data.draw(st.sets(st.sampled_from(list(Root.model_fields))), label="sections")
    full = a.diff(b)
    assert a.diff(b, {s: [] for s in sections}) == {s: full[s] for s in sections if s in full}


@allure.story("Properties")
@allure.title("A diff over chosen fields of a section is the full diff narrowed to those fields")
@given(pair=_PAIRS, data=st.data())
def test_field_diff_is_narrowed_full_diff(pair: Tuple[Root, Root], data: st.DataObject) -> None:
    """Diffs one section of two generated models over a random non-empty subset of its fields
    ({"outer": ["name", ...]}), the form subsystem managers use to watch settings. Dict-typed fields are left out:
    a field list compares a dict whole rather than key by key (plan, phase 4).

    Expected: the result is the full diff of that section with only those fields kept.
    """
    a, b = pair
    section = data.draw(st.sampled_from(list(Root.model_fields)), label="section")
    names = [name for name, field in type(getattr(a, section)).model_fields.items()
             if typing.get_origin(field.annotation) is not dict]
    fields = data.draw(st.lists(st.sampled_from(names), min_size=1, unique=True), label="fields")
    full = a.diff(b).get(section, {})
    expected = {f: full[f] for f in fields if f in full}
    assert a.diff(b, {section: fields}) == ({section: expected} if expected else {})
