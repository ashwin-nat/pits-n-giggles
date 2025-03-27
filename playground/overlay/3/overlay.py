import sys
import pyautogui
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor

class RacingHUD(QMainWindow):
    def __init__(self, bordered=False):
        super().__init__()

        # Set up window flags based on bordered parameter
        self.bordered = bordered
        self.update_window_flags()

        # Create central widget and layout
        central_widget = QWidget()
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Speed label
        self.speed_label = QLabel("Speed: 0 km/h")
        self.speed_label.setStyleSheet("""
            color: white;
            font-size: 24px;
            font-weight: bold;
            background-color: rgba(0, 0, 0, 100);
            padding: 10px;
            border-radius: 10px;
        """)
        layout.addWidget(self.speed_label)

        # Lap label
        self.lap_label = QLabel("Lap: 0/5")
        self.lap_label.setStyleSheet("""
            color: white;
            font-size: 20px;
            background-color: rgba(0, 0, 0, 100);
            padding: 10px;
            border-radius: 10px;
        """)
        layout.addWidget(self.lap_label)

        # Timer for updating HUD data
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_hud_data)
        self.update_timer.start(1000)  # Update every second

        # Position the HUD
        screen = pyautogui.size()
        self.setGeometry(
            screen.width - 250,  # Right side of screen
            50,  # 50 pixels from top
            200,  # Width
            150   # Height
        )

    def update_window_flags(self):
        """Update window flags based on bordered mode"""
        if self.bordered:
            # Resizable window with title bar
            self.setWindowFlags(
                Qt.Window |
                Qt.WindowStaysOnTopHint
            )
            self.setAttribute(Qt.WA_TranslucentBackground, False)

            # Add some styling for bordered mode
            self.setStyleSheet("""
                QMainWindow {
                    background-color: rgba(0, 0, 0, 150);
                    border: 2px solid white;
                }
            """)
        else:
            # Frameless, transparent overlay
            self.setWindowFlags(
                Qt.WindowStaysOnTopHint |
                Qt.FramelessWindowHint |
                Qt.Tool
            )
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setStyleSheet("")

    def toggle_border_mode(self):
        """Toggle between bordered and borderless modes"""
        self.bordered = not self.bordered
        self.update_window_flags()
        self.show()  # Reshow to apply new flags

    def update_hud_data(self):
        # Placeholder for game data retrieval
        import random

        # Simulate racing data
        current_speed = random.randint(50, 250)
        current_lap = random.randint(1, 5)

        self.speed_label.setText(f"Speed: {current_speed} km/h")
        self.lap_label.setText(f"Lap: {current_lap}/5")

    def keyPressEvent(self, event):
        """Add a hotkey to toggle border mode (F12 in this example)"""
        if event.key() == Qt.Key_F12:
            self.toggle_border_mode()

def main():
    app = QApplication(sys.argv)

    # Create HUD in borderless mode by default
    hud = RacingHUD(bordered=True)
    hud.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()