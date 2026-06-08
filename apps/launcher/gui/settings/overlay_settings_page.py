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

from collections import defaultdict
from typing import TYPE_CHECKING, Any, List, Tuple

from pydantic import BaseModel
from pydantic.fields import FieldInfo
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QPushButton,
                               QScrollArea, QVBoxLayout, QWidget)

from .toggle_switch import ToggleSwitchWidget

if TYPE_CHECKING:
    from .settings import SettingsWindow

# -------------------------------------- CLASSES -----------------------------------------------------------------------

_HEADER_STYLE = """
    QFrame {
        background-color: #2d2d30;
        border: 1px solid #4a4a4a;
        border-radius: 4px;
    }
    QFrame:hover {
        background-color: #37373d;
        border-color: #555555;
    }
"""

_BODY_STYLE = """
    QWidget#overlayRowBody {
        background-color: #252526;
        border: 1px solid #4a4a4a;
        border-top: none;
        border-radius: 0 0 4px 4px;
    }
"""


class PlainCollapsibleRow(QWidget):
    """Collapsible row with the same header chrome as OverlayRowWidget but no toggle switch."""

    def __init__(self, title: str, icons_dict: dict, parent: QWidget = None) -> None:
        super().__init__(parent)
        self._icons_dict = icons_dict
        self._expanded = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 2, 0, 2)
        outer.setSpacing(0)

        self._header = header = QFrame()
        header.setFrameShape(QFrame.Shape.StyledPanel)
        header.setStyleSheet(_HEADER_STYLE)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 12, 8)
        header_layout.setSpacing(12)

        name_label = QLabel(title)
        name_label.setFont(QFont("Roboto", 10, QFont.Weight.Bold))
        name_label.setStyleSheet("color: #d4d4d4; background: transparent; border: none;")
        header_layout.addWidget(name_label)
        header_layout.addStretch()

        self._arrow_btn = QPushButton()
        self._arrow_btn.setFlat(True)
        self._arrow_btn.setFixedSize(28, 28)
        self._arrow_btn.setStyleSheet("QPushButton { background: transparent; border: none; }")
        self._arrow_btn.clicked.connect(self._toggle_expand)
        self._update_arrow()
        header_layout.addWidget(self._arrow_btn)

        outer.addWidget(header)

        self._body = QWidget()
        self._body.setObjectName("overlayRowBody")
        self._body.setStyleSheet(_BODY_STYLE)
        self._body_layout = QVBoxLayout(self._body)
        self._body_layout.setContentsMargins(16, 10, 20, 10)
        self._body_layout.setSpacing(8)
        self._body.setVisible(False)
        outer.addWidget(self._body)

    @property
    def content_layout(self) -> QVBoxLayout:
        return self._body_layout

    def _toggle_expand(self) -> None:
        self._expanded = not self._expanded
        self._body.setVisible(self._expanded)
        self._update_arrow()

    def _update_arrow(self) -> None:
        key = 'caret-down' if self._expanded else 'caret-right'
        self._arrow_btn.setIcon(self._icons_dict[key])


class OverlayRowWidget(QWidget):
    """A row representing one overlay group: header with toggle + collapsible settings body."""

    def __init__(self,
                 group_name: str,
                 category_name: str,
                 enable_field: Tuple[str, Any, FieldInfo],
                 config_fields: List[Tuple[str, Any, FieldInfo]],
                 settings_window: "SettingsWindow") -> None:
        super().__init__(settings_window)
        self._settings_window = settings_window
        self._expanded = False
        self._has_config = bool(config_fields)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 2, 0, 2)
        outer.setSpacing(0)

        # ---- Header ----
        self._header = header = QFrame()
        header.setFrameShape(QFrame.Shape.StyledPanel)
        header.setStyleSheet(_HEADER_STYLE)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 12, 8)
        header_layout.setSpacing(12)

        name_label = QLabel(group_name)
        name_label.setFont(QFont("Roboto", 10, QFont.Weight.Bold))
        name_label.setStyleSheet("color: #d4d4d4; background: transparent; border: none;")
        name_label.setTextFormat(Qt.TextFormat.RichText)
        header_layout.addWidget(name_label)
        header_layout.addStretch()

        # Toggle switch wired to the enable field
        en_field_name, en_field_value, en_field_info = enable_field
        en_field_path = f"{category_name}.{en_field_name}"

        toggle = ToggleSwitchWidget(checked=bool(en_field_value))
        toggle.toggled.connect(
            lambda checked, p=en_field_path: settings_window._on_field_changed(p, checked)
        )
        settings_window.field_widgets[en_field_path] = toggle
        header_layout.addWidget(toggle)

        # Expand/collapse button — only shown when there are config fields
        self._arrow_btn = QPushButton()
        self._arrow_btn.setFlat(True)
        self._arrow_btn.setFixedSize(28, 28)
        self._arrow_btn.setStyleSheet("QPushButton { background: transparent; border: none; }")
        self._arrow_btn.clicked.connect(self._toggle_expand)
        self._update_arrow()
        header_layout.addWidget(self._arrow_btn)

        if not self._has_config:
            self._arrow_btn.setVisible(False)

        outer.addWidget(header)

        # Register the header as searchable for the enable field description
        settings_window._register_searchable(
            header,
            en_field_info.description or group_name,
            en_field_name,
        )

        # ---- Body (config fields) ----
        self._body = QWidget()
        self._body.setObjectName("overlayRowBody")
        self._body.setStyleSheet(_BODY_STYLE)
        body_layout = QVBoxLayout(self._body)
        body_layout.setContentsMargins(16, 10, 20, 10)
        body_layout.setSpacing(8)

        for cf_name, cf_value, cf_info in config_fields:
            cf_path = f"{category_name}.{cf_name}"
            settings_window._render_field(cf_name, cf_value, cf_path, cf_info, body_layout)

        self._body.setVisible(False)
        outer.addWidget(self._body)

    def _toggle_expand(self) -> None:
        self._expanded = not self._expanded
        self._body.setVisible(self._expanded)
        self._update_arrow()

    def _update_arrow(self) -> None:
        key = 'caret-down' if self._expanded else 'caret-right'
        self._arrow_btn.setIcon(self._settings_window.icons_dict[key])


class OverlaySettingsPage(QScrollArea):
    """Specialized settings page for the HUD category.

    Renders ungrouped HUD fields in a collapsed 'General' section and
    each overlay group as an OverlayRowWidget with a toggle + expandable body.
    """

    def __init__(self,
                 category_name: str,
                 category_model: BaseModel,
                 settings_window: "SettingsWindow") -> None:
        super().__init__(settings_window)
        self._settings_window = settings_window
        self._category_name = category_name
        self._category_model = category_model

        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setStyleSheet("QScrollBar:vertical { width: 12px; }")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(10, 10, 20, 10)
        layout.setSpacing(8)

        # Category title
        field_info = settings_window._get_field_info_from_path(category_name)
        title_label = QLabel(field_info.description)
        title_label.setFont(QFont("Roboto", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #d4d4d4; background-color: transparent;")
        layout.addWidget(title_label)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #3e3e3e;")
        layout.addWidget(separator)

        # Partition fields
        ungrouped: List[Tuple[str, Any, FieldInfo]] = []
        grouped: dict = defaultdict(list)
        group_order: List[str] = []

        for fn, fi in type(category_model).model_fields.items():
            if not settings_window._is_field_visible(fi):
                continue
            fv = getattr(category_model, fn)
            ui_cfg = (fi.json_schema_extra or {}).get("ui", {})
            gname = ui_cfg.get("group")
            if gname:
                if gname not in grouped:
                    group_order.append(gname)
                grouped[gname].append((fn, fv, fi))
            else:
                ungrouped.append((fn, fv, fi))

        # General section (ungrouped fields)
        if ungrouped:
            general = PlainCollapsibleRow("General", settings_window.icons_dict, self)
            for fn, fv, fi in ungrouped:
                fp = f"{category_name}.{fn}"
                settings_window._render_field(fn, fv, fp, fi, general.content_layout)
            layout.addWidget(general)

        # Overlay rows
        for gname in group_order:
            fields = grouped[gname]

            enable_field = None
            config_fields: List[Tuple[str, Any, FieldInfo]] = []
            for fn, fv, fi in fields:
                ui_cfg = (fi.json_schema_extra or {}).get("ui", {})
                if ui_cfg.get("overlay_enable"):
                    enable_field = (fn, fv, fi)
                else:
                    config_fields.append((fn, fv, fi))

            if enable_field:
                row = OverlayRowWidget(
                    group_name=gname,
                    category_name=category_name,
                    enable_field=enable_field,
                    config_fields=config_fields,
                    settings_window=settings_window,
                )
                layout.addWidget(row)
            else:
                # Group with no enable field — render as a plain collapsible
                if config_fields:
                    grp = PlainCollapsibleRow(gname, settings_window.icons_dict, self)
                    for fn, fv, fi in config_fields:
                        fp = f"{category_name}.{fn}"
                        settings_window._render_field(fn, fv, fp, fi, grp.content_layout)
                    layout.addWidget(grp)

        layout.addStretch()
        self.setWidget(content)
