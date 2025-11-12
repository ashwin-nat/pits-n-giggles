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

from PySide6.QtCore import QEasingCurve, QPropertyAnimation
from PySide6.QtWidgets import QGraphicsOpacityEffect, QStackedWidget

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class AnimatedStackedWidget(QStackedWidget):
    """QStackedWidget with fade transition animations between pages."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._animation_duration = 200  # milliseconds
        self._is_animating = False
        self._pending_index = None

    def setCurrentIndexAnimated(self, index: int):
        """Switch to a page with fade animation."""
        if self._is_animating:
            # Queue the next transition
            self._pending_index = index
            return

        if index == self.currentIndex():
            return

        self._is_animating = True
        current_widget = self.currentWidget()
        next_widget = self.widget(index)

        if current_widget is None or next_widget is None:
            self.setCurrentIndex(index)
            self._is_animating = False
            return

        # Create opacity effects if they don't exist
        if current_widget.graphicsEffect() is None:
            current_effect = QGraphicsOpacityEffect(current_widget)
            current_widget.setGraphicsEffect(current_effect)
        else:
            current_effect = current_widget.graphicsEffect()

        if next_widget.graphicsEffect() is None:
            next_effect = QGraphicsOpacityEffect(next_widget)
            next_widget.setGraphicsEffect(next_effect)
        else:
            next_effect = next_widget.graphicsEffect()

        # Set initial states
        current_effect.setOpacity(1.0)
        next_effect.setOpacity(0.0)

        # Create fade-out animation for current widget
        self._fade_out = QPropertyAnimation(current_effect, b"opacity")
        self._fade_out.setDuration(self._animation_duration)
        self._fade_out.setStartValue(1.0)
        self._fade_out.setEndValue(0.0)
        self._fade_out.setEasingCurve(QEasingCurve.OutCubic)

        # Create fade-in animation for next widget
        self._fade_in = QPropertyAnimation(next_effect, b"opacity")
        self._fade_in.setDuration(self._animation_duration)
        self._fade_in.setStartValue(0.0)
        self._fade_in.setEndValue(1.0)
        self._fade_in.setEasingCurve(QEasingCurve.InCubic)

        # Switch to next widget when fade-out is halfway done
        def switch_page():
            self.setCurrentIndex(index)
            self._fade_in.start()

        self._fade_out.finished.connect(self._on_animation_finished())
        self._fade_out.valueChanged.connect(
            lambda: switch_page() if self._fade_out.currentValue() <= 0.5 and
                                     self.currentIndex() != index else None
        )

        self._fade_out.start()

    def _on_animation_finished(self):
        """Handle animation completion."""
        self._is_animating = False

        # Process any pending transition
        if self._pending_index is not None:
            pending = self._pending_index
            self._pending_index = None
            self.setCurrentIndexAnimated(pending)
