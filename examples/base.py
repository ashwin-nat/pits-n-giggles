from dataclasses import dataclass
from PySide6.QtCore import Qt, QPoint
from PySide6.QtWidgets import QWidget


@dataclass
class OverlaysConfig:
    x: int
    y: int
    width: int
    height: int


class BaseOverlay(QWidget):
    """Base class for all display-only overlays (e.g., lap timer, tyre info, etc.)."""

    def __init__(self, config: OverlaysConfig, locked: bool = False):
        super().__init__()
        self.config = config
        self.locked = locked
        self._drag_pos = None
        self._setup_window()
        self.build_ui()
        self.apply_config()

    # -------------------------------------------------------------------------
    # Setup
    # -------------------------------------------------------------------------
    def _setup_window(self):
        """Apply base window setup and initial flags."""
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground, False)
        self.update_window_flags()

    def apply_config(self):
        """Apply initial geometry from config."""
        self.setGeometry(
            self.config.x,
            self.config.y,
            self.config.width,
            self.config.height
        )

    # -------------------------------------------------------------------------
    # Window State
    # -------------------------------------------------------------------------
    def update_window_flags(self):
        """Refresh window flags based on locked state."""
        flags = Qt.WindowStaysOnTopHint | Qt.Tool

        if self.locked:
            flags |= Qt.FramelessWindowHint
            self.setWindowFlag(Qt.WindowTransparentForInput, True)
        else:
            flags |= (
                Qt.Window
                | Qt.CustomizeWindowHint
                | Qt.WindowTitleHint
                | Qt.WindowSystemMenuHint
                | Qt.WindowCloseButtonHint
                | Qt.WindowMinMaxButtonsHint
                | Qt.FramelessWindowHint
            )
            self.setWindowFlag(Qt.WindowTransparentForInput, False)

        self.setWindowFlags(flags)
        self.show()

    def set_locked_state(self, locked: bool):
        """Set locked state dynamically."""
        self.locked = locked
        self.update_window_flags()

    def get_window_info(self) -> OverlaysConfig:
        """Return current geometry as an OverlaysConfig."""
        geo = self.geometry()
        return OverlaysConfig(
            x=geo.x(),
            y=geo.y(),
            width=geo.width(),
            height=geo.height()
        )

    # -------------------------------------------------------------------------
    # Subclass hooks
    # -------------------------------------------------------------------------
    def build_ui(self):
        """Subclasses must implement this to build their layout."""
        raise NotImplementedError

    def update_data(self, data):
        """Subclasses implement to refresh their displayed data."""
        pass

    # -------------------------------------------------------------------------
    # Mouse interactions (dragging + resizing only)
    # -------------------------------------------------------------------------
    def mousePressEvent(self, event):
        if not self.locked and event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if not self.locked and event.buttons() == Qt.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
