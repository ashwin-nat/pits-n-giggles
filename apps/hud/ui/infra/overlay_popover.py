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

from typing import Any, Callable, List, Optional, Tuple

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QFont, QGuiApplication, QHideEvent
from PySide6.QtWidgets import (QCheckBox, QFrame, QHBoxLayout, QLabel,
                               QSlider, QVBoxLayout, QWidget)

from lib.logger import PngLogger

from ..overlays import BaseOverlay
from ..overlays.base.overlay_settings import (Divider, Note, OverlaySetting,
                                              Slider, Toggle)

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class _SliderRow(QWidget):
    """An optional label above a slider and its value text."""

    def __init__(self, parent: QWidget, setting: Slider):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        if setting.label:
            layout.addWidget(QLabel(setting.label, self))

        row = QHBoxLayout()
        row.setSpacing(8)
        self._unit = setting.unit
        self.slider = QSlider(Qt.Orientation.Horizontal, self)
        self.slider.setRange(setting.lo, setting.hi)
        self._text = QLabel(self)
        self._text.setMinimumWidth(52)
        self._text.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.slider.valueChanged.connect(self._show_value)
        row.addWidget(self.slider, 1)
        row.addWidget(self._text)
        layout.addLayout(row)

    def set_value(self, value: int):
        """Show value without emitting valueChanged."""
        self.slider.blockSignals(True)
        self.slider.setValue(value)
        self.slider.blockSignals(False)
        self._show_value(self.slider.value())

    def _show_value(self, value: int):
        self._text.setText(f"{value}{self._unit}")


class OverlayPopover(QWidget):
    """Popup that renders an overlay's popover_settings() and applies every change live.

    Usage: `popover.open_for(overlay, global_pos)`; `refresh(overlay)` after the overlay changes from elsewhere.
    Clicking outside closes it (Qt.Popup).
    """

    _STYLE = """
        QWidget#OverlayPopoverInner {
            background-color: rgba(32, 32, 32, 255);
            border: 1px solid #E10600;
            border-radius: 8px;
        }
        QLabel, QCheckBox {
            color: white;
            font-family: "Formula1";
            font-size: 14px;
            background: transparent;
        }
        QLabel#OverlayPopoverTitle {
            font-size: 16px;
        }
        QLabel#OverlayPopoverNote {
            color: #F5B400;
            font-size: 12px;
        }
        QFrame#OverlayPopoverDivider {
            background-color: rgba(255, 255, 255, 40);
            border: none;
        }
        QCheckBox::indicator {
            width: 14px;
            height: 14px;
            border: 1px solid #8a8a8a;
            border-radius: 3px;
            background-color: #1e1e1e;
        }
        QCheckBox::indicator:checked {
            border: 1px solid #E10600;
            background-color: #E10600;
        }
        QCheckBox:disabled, QLabel:disabled {
            color: rgba(255, 255, 255, 110);
        }
        QSlider::groove:horizontal {
            border: 1px solid #3e3e3e;
            height: 6px;
            background-color: #1e1e1e;
            border-radius: 3px;
        }
        QSlider::handle:horizontal {
            background-color: #E10600;
            border: 1px solid #E10600;
            width: 16px;
            margin: -6px 0;
            border-radius: 8px;
        }
        QSlider::handle:horizontal:disabled {
            background-color: #5a5a5a;
            border: 1px solid #5a5a5a;
        }
    """

    def __init__(self, logger: PngLogger):
        super().__init__(None, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(280)
        self._logger = logger
        self._overlay: Optional[BaseOverlay] = None
        self._rendered: List[Tuple[OverlaySetting, QWidget]] = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self._inner = QWidget(self)
        self._inner.setObjectName("OverlayPopoverInner")
        outer.addWidget(self._inner)

        self._layout = QVBoxLayout(self._inner)
        self._layout.setContentsMargins(14, 12, 14, 14)
        self._layout.setSpacing(10)
        self._title = QLabel(self._inner)
        self._title.setObjectName("OverlayPopoverTitle")
        self._title.setFont(QFont("Formula1"))
        self._layout.addWidget(self._title)

        self.setStyleSheet(self._STYLE)

    def open_for(self, overlay: BaseOverlay, global_pos: QPoint):
        """Render overlay's settings and show the popover at global_pos, kept on that screen."""
        self._logger.debug("%s | Opening overlay popover at (%d, %d)",
                           overlay.OVERLAY_ID, global_pos.x(), global_pos.y())
        self._overlay = overlay
        self._title.setText(overlay.OVERLAY_ID.display_name)
        self._render(overlay.popover_settings())
        self.move(self._clamped_pos(global_pos))
        self.show()

    def refresh(self, overlay: BaseOverlay):
        """Re-read every value if open on overlay, so it never shows state changed elsewhere."""
        if self.isVisible() and overlay is self._overlay:
            self._sync()

    def hideEvent(self, event: QHideEvent):
        """Log the close: an outside click, or the lock."""
        self._logger.debug("%s | Overlay popover closed", self._overlay.OVERLAY_ID)
        super().hideEvent(event)

    # ---------------------------------------------------------
    def _render(self, settings: List[OverlaySetting]):
        for _setting, widget in self._rendered:
            self._layout.removeWidget(widget)
            widget.hide()  # deleteLater() waits for the event loop; until then it would still paint and take input
            widget.deleteLater()
        self._rendered = [(setting, self._make_widget(setting)) for setting in settings]
        for _setting, widget in self._rendered:
            self._layout.addWidget(widget)
        self._sync()

    def _make_widget(self, setting: OverlaySetting) -> QWidget:
        if isinstance(setting, Toggle):
            box = QCheckBox(setting.label, self._inner)
            box.toggled.connect(lambda on: self._apply(setting.on_change, on))
            return box
        if isinstance(setting, Slider):
            row = _SliderRow(self._inner, setting)
            row.slider.valueChanged.connect(lambda v: self._apply(setting.on_change, v))
            return row
        if isinstance(setting, Note):
            note = QLabel(self._inner)
            note.setObjectName("OverlayPopoverNote")
            note.setWordWrap(True)
            # Fixed width now and fixed height per text in _sync(), measured with the stylesheet font: a wrapped
            # label's height otherwise depends on a width Qt only settles later, so the first resize comes out short
            note.ensurePolished()
            margins = self._layout.contentsMargins()
            note.setFixedWidth(self.width() - margins.left() - margins.right())
            return note
        assert isinstance(setting, Divider), f"Unknown overlay setting {setting!r}"
        line = QFrame(self._inner)
        line.setObjectName("OverlayPopoverDivider")
        line.setFixedHeight(1)
        return line

    def _apply(self, on_change: Callable[[Any], None], value: Any):
        on_change(value)
        self._sync()

    def _sync(self):
        """Re-read every setting into its widget: values, enabled state, note visibility."""
        for setting, widget in self._rendered:
            if isinstance(setting, Toggle):
                widget.blockSignals(True)
                widget.setChecked(setting.value())
                widget.blockSignals(False)
            elif isinstance(setting, Slider):
                widget.set_value(setting.value())
                widget.setEnabled(setting.enabled())
            elif isinstance(setting, Note):
                widget.setText(setting.text())
                widget.setFixedHeight(widget.heightForWidth(widget.width()))
                widget.setVisible(setting.visible())
        # Activate now: the minimum height a shown note set only drops on the next (deferred) layout pass
        self._layout.activate()
        self.layout().activate()
        self.adjustSize()
        if self.isVisible():
            # A note appearing grows it downwards, possibly past the screen edge
            self.move(self._clamped_pos(self.pos()))

    def _clamped_pos(self, global_pos: QPoint) -> QPoint:
        screen = QGuiApplication.screenAt(global_pos) or QGuiApplication.primaryScreen()
        area: QRect = screen.availableGeometry()
        x = min(max(global_pos.x(), area.left()), area.right() - self.width())
        y = min(max(global_pos.y(), area.top()), area.bottom() - self.height())
        return QPoint(x, y)
