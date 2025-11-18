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

from typing import Any, Dict, Iterable, List, Optional, Union

# -------------------------------------- CLASS  DEFINITIONS ------------------------------------------------------------

class ConfigDiffMixin:
    """Provides recursive diffing and change detection for Pydantic config models."""

    def diff(self,
             other: "ConfigDiffMixin",
             fields: Optional[Union[Dict[str, List[str]], List[str]]] = None
             ) -> Dict[str, Any]:
        """
        Return a nested dict showing changed fields and their old/new values.

        - If fields is a dict, you can specify sub-sections.
          Empty lists inside it (e.g. {"Capture": []}) mean "compare all fields in that section".
        - If fields is None, {}, or [], compares everything recursively.
        """
        result: Dict[str, Any] = {}

        # --- Case 1: Nested dict like {"Network": [...], "Capture": []}
        if isinstance(fields, dict):
            for section, subfields in fields.items():
                self_section = getattr(self, section, None)
                other_section = getattr(other, section, None)
                if self_section is None or other_section is None:
                    continue

                # Empty list → full recursive diff for that section
                if not subfields:
                    section_diff = self_section.diff(other_section)
                else:
                    section_diff = self_section.diff(other_section, subfields) \
                        if hasattr(self_section, "diff") \
                        else self._basic_diff(self_section, other_section, subfields)

                if section_diff:
                    result[section] = section_diff
            return result

        # --- Case 2: Flat list of fields
        if isinstance(fields, list) and fields:
            return self._basic_diff(self, other, fields)

        # --- Case 3: Compare everything recursively (fields is None, empty, etc.)
        result = {}
        for name, value in getattr(self, "__dict__", {}).items():
            other_value = getattr(other, name, None)
            if isinstance(value, ConfigDiffMixin) and isinstance(other_value, ConfigDiffMixin):
                subdiff = value.diff(other_value)
                if subdiff:
                    result[name] = subdiff
            elif value != other_value:
                    result[name] = {"old_value": value, "new_value": other_value}
        return result

    def _basic_diff(self, self_obj: Any, other_obj: Any, fields: Iterable[str]) -> Dict[str, Any]:
        """Compare plain attributes and return a dict of changed fields with old/new values."""
        changes = {}
        for f in fields:
            old_val = getattr(self_obj, f, None)
            new_val = getattr(other_obj, f, None)
            if old_val != new_val:
                changes[f] = {"old_value": old_val, "new_value": new_val}
        return changes

    def has_changed(self,
                    other: "ConfigDiffMixin",
                    fields: Optional[Union[Dict[str, List[str]], List[str]]] = None
                    ) -> bool:
        """Return True if any watched field (or any field if none specified) differs."""
        return bool(self.diff(other, fields))
