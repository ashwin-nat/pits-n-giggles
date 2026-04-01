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
from typing import Dict

from pydantic import BaseModel, Field

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.config.schema.diff import ConfigDiffMixin

from .tests_config_base import TestF1ConfigBase

# -------------------------------------- Simple test models ------------------------------------------------------------

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


class SectionA(ConfigDiffMixin, BaseModel):
    alpha: int = 0
    beta: str = "x"


class SectionB(ConfigDiffMixin, BaseModel):
    gamma: float = 1.0


class Root(ConfigDiffMixin, BaseModel):
    section_a: SectionA = Field(default_factory=SectionA)
    section_b: SectionB = Field(default_factory=SectionB)

# -------------------------------------- Tests -----------------------------------------------------------------------

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
