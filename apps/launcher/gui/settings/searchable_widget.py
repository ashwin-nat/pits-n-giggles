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

import html
import re
from dataclasses import dataclass
from typing import Optional

from PySide6.QtWidgets import QLabel, QWidget

# -------------------------------------- CLASSES -----------------------------------------------------------------------

@dataclass
class SearchableWidget:
    """Represents a widget that can be searched in the settings dialog"""
    widget: QWidget
    description: str
    field_name: str
    label_widget: Optional[QLabel] = None  # The label widget to highlight, if any
    category_index: Optional[int] = None  # The category this widget belongs to

    def matches(self, search_text: str) -> bool:
        """Check if this widget matches the search text"""
        search_lower = search_text.lower()
        return search_lower in self.description.lower() or search_lower in self.field_name.lower()

    def matches_description(self, search_text: str) -> bool:
        """Check if search text matches the description (not just field name)"""
        return search_text.lower() in self.description.lower()

    def apply_highlight(self, search_text: str):
        """Apply highlighting to the label if search matches description"""
        if not self.label_widget:
            return

        if not search_text:
            self.label_widget.setText(self.description)
            return

        if not self.matches_description(search_text):
            self.label_widget.setText(self.description)
            return

        # HTML-escape the description to prevent injection
        escaped_description = html.escape(self.description)

        # Build regex pattern with escaped search text (case-insensitive)
        pattern = re.escape(search_text)

        def _repl(m: re.Match) -> str:
            # The matched text is already HTML-escaped
            original = m.group(0)
            return f'<span style="background-color: #e3dc09; color: #000000;">{original}</span>'

        # Apply highlighting with case-insensitive matching
        highlighted = re.sub(pattern, _repl, escaped_description, flags=re.IGNORECASE)
        self.label_widget.setText(highlighted)
