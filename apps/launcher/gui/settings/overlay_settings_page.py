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

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, List, Optional, Tuple

from pydantic import BaseModel
from pydantic.fields import FieldInfo
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon, QPixmap
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QPushButton,
                               QScrollArea, QVBoxLayout, QWidget)

from .collapsible_group import HeaderCollapsibleGroup
from .toggle_switch import ToggleSwitchWidget

if TYPE_CHECKING:
    from .settings import SettingsWindow

# -------------------------------------- HELPERS -----------------------------------------------------------------------

def _resolve_asset_path(relative: str) -> Optional[Path]:
    if hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)
    else:
        # Walk up from this file (apps/launcher/gui/settings/) to the project root
        base = Path(__file__).resolve().parents[4]
    p = base / relative
    return p if p.exists() else None


# -------------------------------------- CLASSES -----------------------------------------------------------------------

class _PreviewPopup(QWidget):
    """Frameless popup showing a full-size preview image. Dismisses on any click."""

    def __init__(self, abs_path: Path, invoker: QWidget, close_icon: QIcon) -> None:
        pixmap = QPixmap(str(abs_path))
        if pixmap.isNull():
            raise ValueError(f"Preview image not found or invalid: {abs_path}")

        super().__init__(invoker.window(), Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("background-color: #1e1e1e; border: 1px solid #555555;")

        screen_geo = invoker.screen().availableGeometry()
        max_w = int(screen_geo.width() * 0.8)
        max_h = int(screen_geo.height() * 0.8)
        if pixmap.width() > max_w or pixmap.height() > max_h:
            pixmap = pixmap.scaled(max_w, max_h,
                                   Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)
        top_bar.addStretch()
        close_btn = QPushButton()
        close_btn.setIcon(close_icon)
        close_btn.setFlat(True)
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("QPushButton { background: transparent; border: none; }"
                                "QPushButton:hover { background-color: #3e3e3e; border-radius: 4px; }")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.close)
        top_bar.addWidget(close_btn)
        layout.addLayout(top_bar)

        img_label = QLabel()
        img_label.setPixmap(pixmap)
        layout.addWidget(img_label)

        self.adjustSize()
        center = screen_geo.center()
        self.move(center.x() - self.width() // 2, center.y() - self.height() // 2)

    def mousePressEvent(self, event) -> None:
        self.close()
        event.accept()


class _PreviewIconLabel(QLabel):
    """20x20 icon label that opens a full-size preview popup on click."""

    def __init__(self, abs_path: Optional[Path], icon_pixmap: QPixmap, close_icon: QIcon) -> None:
        super().__init__()
        self._abs_path = abs_path
        self._close_icon = close_icon
        self.setFixedSize(20, 20)
        self.setPixmap(icon_pixmap)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("background: transparent; border: none;")
        self.setToolTip("Preview")

    def mousePressEvent(self, event) -> None:
        if self._abs_path is not None:
            try:
                _PreviewPopup(self._abs_path, self, self._close_icon).show()
            except ValueError:
                pass
        event.accept()


def _make_preview_icon_label(preview_image: str, icon_pixmap: QPixmap, close_icon: QIcon) -> _PreviewIconLabel:
    return _PreviewIconLabel(_resolve_asset_path(preview_image), icon_pixmap, close_icon)


def _make_overlay_header_extra(
    category_name: str,
    enable_field: Tuple[str, Any, FieldInfo],
    settings_window: "SettingsWindow",
) -> QWidget:
    """Build the right-side header widget containing an optional preview icon and enable toggle."""
    en_field_name, en_field_value, en_field_info = enable_field
    en_field_path = f"{category_name}.{en_field_name}"

    container = QWidget()
    container.setStyleSheet("background: transparent;")
    layout = QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(8)

    preview_path = (en_field_info.json_schema_extra or {}).get("ui", {}).get("preview_image")
    if preview_path:
        icon_pixmap = settings_window.icons_dict.get("overlay-preview", QIcon()).pixmap(20, 20)
        close_icon = settings_window.icons_dict.get("close", QIcon())
        layout.addWidget(_make_preview_icon_label(preview_path, icon_pixmap, close_icon))

    toggle = ToggleSwitchWidget(checked=bool(en_field_value))
    toggle.toggled.connect(
        lambda checked, p=en_field_path: settings_window._on_field_changed(p, checked)
    )
    settings_window.field_widgets[en_field_path] = toggle
    layout.addWidget(toggle)

    return container


class OverlaySettingsPage(QScrollArea):
    """Specialized settings page for the HUD category.

    Renders ungrouped HUD fields in a collapsed 'General' section and
    each overlay group as a collapsible row with a toggle and expandable body.
    """

    def __init__(self,
                 category_name: str,
                 category_model: BaseModel,
                 settings_window: "SettingsWindow") -> None:
        super().__init__(settings_window)
        self._settings_window = settings_window

        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setStyleSheet("QScrollBar:vertical { width: 12px; }")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(10, 10, 20, 10)
        layout.setSpacing(8)

        field_info = settings_window._get_field_info_from_path(category_name)
        title_label = QLabel(field_info.description or category_name)
        title_label.setFont(QFont("Roboto", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #d4d4d4; background-color: transparent;")
        layout.addWidget(title_label)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #3e3e3e;")
        layout.addWidget(separator)

        ungrouped: List[Tuple[str, Any, FieldInfo]] = []
        grouped: dict = {}
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
                    grouped[gname] = []
                grouped[gname].append((fn, fv, fi))
            else:
                ungrouped.append((fn, fv, fi))

        if ungrouped:
            general = HeaderCollapsibleGroup("General", settings_window.icons_dict, parent=self)
            general.set_collapsed(True)
            for fn, fv, fi in ungrouped:
                fp = f"{category_name}.{fn}"
                settings_window._render_field(fn, fv, fp, fi, general.content_layout)
            layout.addWidget(general)

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
                header_extra = _make_overlay_header_extra(category_name, enable_field, settings_window)
                group = HeaderCollapsibleGroup(gname, settings_window.icons_dict,
                                               header_extra=header_extra, parent=self)
                group.set_collapsed(True)
                settings_window._register_searchable(
                    group,
                    enable_field[2].description or gname,
                    enable_field[0],
                )
                for cf_name, cf_value, cf_info in config_fields:
                    cf_path = f"{category_name}.{cf_name}"
                    settings_window._render_field(cf_name, cf_value, cf_path, cf_info, group.content_layout)
                layout.addWidget(group)
            elif config_fields:
                group = HeaderCollapsibleGroup(gname, settings_window.icons_dict, parent=self)
                group.set_collapsed(True)
                for fn, fv, fi in config_fields:
                    fp = f"{category_name}.{fn}"
                    settings_window._render_field(fn, fv, fp, fi, group.content_layout)
                layout.addWidget(group)

        layout.addStretch()
        self.setWidget(content)
