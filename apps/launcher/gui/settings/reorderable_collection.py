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

from typing import Any, Dict, List, Tuple

from pydantic.fields import FieldInfo

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class ReorderableCollection:
    """Helper class to encapsulate reorderable collection metadata"""

    def __init__(self, field_info: FieldInfo):
        ui_config = (field_info.json_schema_extra or {}).get("ui", {})
        self.is_reorderable = ui_config.get("reorderable_collection", False)
        self.enabled_field = ui_config.get("item_enabled_field", "enabled")
        self.position_field = ui_config.get("item_position_field", "position")

    def get_enabled(self, item: Any) -> bool:
        """Get enabled state from an item"""
        return getattr(item, self.enabled_field, True)

    def set_enabled(self, item: Any, value: bool):
        """Set enabled state on an item"""
        if hasattr(item, self.enabled_field):
            setattr(item, self.enabled_field, value)

    def get_position(self, item: Any) -> int:
        """Get position from an item"""
        return getattr(item, self.position_field, 0)

    def set_position(self, item: Any, value: int):
        """Set position on an item"""
        if hasattr(item, self.position_field):
            setattr(item, self.position_field, value)

    def get_sorted_all_items(self, items_dict: Dict[str, Any]) -> List[Tuple[str, Any]]:
        """Get sorted list of all items (enabled and disabled)."""
        return sorted(items_dict.items(), key=lambda x: self.get_position(x[1]))
