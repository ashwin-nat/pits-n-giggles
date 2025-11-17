"""
Example Subsystem Implementations
Shows how to create concrete subsystem managers
"""

from typing import List, Dict, Any
from .subsystem_manager import SubsystemManager
from PySide6.QtWidgets import QMainWindow


class ServerSubsystem(SubsystemManager):
    """Example: HTTP Server subsystem"""

    def __init__(self, console: QMainWindow, start_by_default: bool = True):
        super().__init__(
            module_path="my_app.server",  # Your actual module path
            display_name="Server",
            console=console,
            start_by_default=start_by_default,
            args=["--port", "4768"],  # Example args
            http_port_conflict_field="server.http_port",
            debug_mode=False
        )

        # Subsystem-specific state
        self.port = 4768
        self.connected_clients = 0

    def get_buttons(self) -> List[Dict[str, Any]]:
        """Define buttons for the server panel"""
        buttons = []

        if self.is_running:
            buttons.append({
                'text': 'Stop',
                'command': self.stop,
                'primary': False
            })
            buttons.append({
                'text': 'Restart',
                'command': self.restart,
                'primary': False
            })
            buttons.append({
                'text': 'Dashboard',
                'command': self.open_dashboard,
                'primary': False
            })
            buttons.append({
                'text': 'Stream Overlay',
                'command': self.open_stream_overlay,
                'primary': False
            })
        else:
            buttons.append({
                'text': 'Start',
                'command': self.start,
                'primary': True
            })

        return buttons

    def open_dashboard(self):
        """Open the web dashboard"""
        import webbrowser
        webbrowser.open(f"http://localhost:{self.port}")
        self._log_info("Opening dashboard in browser...")

    def open_stream_overlay(self):
        """Open the stream overlay"""
        import webbrowser
        webbrowser.open(f"http://localhost:{self.port}/overlay")
        self._log_info("Opening stream overlay in browser...")


class HUDSubsystem(SubsystemManager):
    """Example: HUD overlay subsystem"""

    def __init__(self, console: QMainWindow, start_by_default: bool = True):
        super().__init__(
            console=console,
            module_path="my_app.hud",
            display_name="HUD",
            start_by_default=start_by_default,
            args=[],
            debug_mode=False
        )

        self.current_page = 1
        self.total_pages = 5

    def get_buttons(self) -> List[Dict[str, Any]]:
        """Define buttons for the HUD panel"""
        buttons = []

        if self.is_running:
            buttons.append({
                'text': 'Stop',
                'command': self.stop,
                'primary': False
            })
            buttons.append({
                'text': 'Hide/Show',
                'command': self.toggle_visibility,
                'primary': False
            })
            buttons.append({
                'text': 'Unlock',
                'command': self.unlock_position,
                'primary': False
            })
            buttons.append({
                'text': 'Reset',
                'command': self.reset_position,
                'primary': False
            })
            buttons.append({
                'text': 'Next Page',
                'command': self.next_page,
                'primary': False
            })
        else:
            buttons.append({
                'text': 'Start',
                'command': self.start,
                'primary': True
            })

        return buttons

    def toggle_visibility(self):
        """Toggle HUD visibility"""
        self._log_info("Toggling HUD visibility...")
        # In real implementation, send IPC command to HUD

    def unlock_position(self):
        """Unlock HUD for repositioning"""
        self._log_info("Unlocking HUD position...")
        # In real implementation, send IPC command

    def reset_position(self):
        """Reset HUD to default position"""
        self._log_info("Resetting HUD position...")
        # In real implementation, send IPC command

    def next_page(self):
        """Cycle to next HUD page"""
        self.current_page = (self.current_page % self.total_pages) + 1
        self._log_info(f"Switching to HUD page {self.current_page}...")
        # In real implementation, send IPC command


class DashboardSubsystem(SubsystemManager):
    """Example: Save viewer/analyzer subsystem"""

    def __init__(self, console: QMainWindow, start_by_default: bool = True):
        super().__init__(
            console=console,
            module_path="my_app.dashboard",
            display_name="Save Viewer",
            start_by_default=start_by_default,
            args=["--port", "8080"],
            http_port_conflict_field="dashboard.http_port",
            debug_mode=False
        )

        self.port = 8080
        self.last_save_file = None

    def get_buttons(self) -> List[Dict[str, Any]]:
        """Define buttons for the save viewer panel"""
        buttons = []

        if self.is_running:
            buttons.append({
                'text': 'Stop',
                'command': self.stop,
                'primary': False
            })
            buttons.append({
                'text': 'Open File',
                'command': self.open_file_dialog,
                'primary': False
            })
            buttons.append({
                'text': 'Dashboard',
                'command': self.open_dashboard,
                'primary': False
            })
        else:
            buttons.append({
                'text': 'Start',
                'command': self.start,
                'primary': True
            })

        return buttons

    def open_file_dialog(self):
        """Open file picker for save files"""
        from PySide6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            None,
            "Open Save File",
            "",
            "Save Files (*.sav);;All Files (*.*)"
        )

        if file_path:
            self.last_save_file = file_path
            self._log_info(f"Loading save file: {file_path}")
            # In real implementation, send file path to dashboard via IPC

    def open_dashboard(self):
        """Open the dashboard in browser"""
        import webbrowser
        webbrowser.open(f"http://localhost:{self.port}")
        self._log_info("Opening dashboard in browser...")


# Additional example: Manual save subsystem
class ManualSaveSubsystem(SubsystemManager):
    """Example: Manual save trigger subsystem"""

    def __init__(self, start_by_default: bool = False):
        super().__init__(
            module_path="my_app.manual_save",
            display_name="Manual Save",
            start_by_default=start_by_default,
            args=[],
            debug_mode=False
        )

    def get_buttons(self) -> List[Dict[str, Any]]:
        """Define buttons for manual save panel"""
        buttons = []

        if self.is_running:
            buttons.append({
                'text': 'Stop',
                'command': self.stop,
                'primary': False
            })
            buttons.append({
                'text': 'Trigger Save',
                'command': self.trigger_save,
                'primary': True
            })
        else:
            buttons.append({
                'text': 'Start',
                'command': self.start,
                'primary': True
            })

        return buttons

    def trigger_save(self):
        """Manually trigger a save"""
        self._log_info("Triggering manual save...")
        # In real implementation, send IPC command to save module