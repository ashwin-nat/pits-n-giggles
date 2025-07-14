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

import datetime
import sys
import threading
import tkinter as tk
import webbrowser
from tkinter import ttk
from typing import Callable, Dict

from PIL import Image, ImageTk

from lib.config import PngSettings, load_config_from_ini
from lib.version import is_update_available

from .app_managers import BackendAppMgr, PngAppMgrBase, SaveViewerAppMgr
from .console_interface import ConsoleInterface
from .logger import get_rotating_logger
from .settings import SettingsWindow
from .styles import COLOUR_SCHEME

# -------------------------------------- CLASS  DEFINITIONS ------------------------------------------------------------

class PngLauncher(ConsoleInterface):
    def __init__(self, root: tk.Tk, ver_str: str, logo_path: str, settings_icon_path: str, debug_mode: bool):
        """Initialize the main application window

        Args:
            root (tk.Tk): The main Tkinter window
            ver_str (str): Version string
            logo_path (str): Path to the application logo
            settings_icon_path (str): Path to the settings icon
            debug_mode (bool): Flag to enable debug mode
        """

        self.root = root
        self.version = ver_str if ver_str != 'dev' else ''
        self.app_name = "Pits n' Giggles"
        self.config_file = "png_config.ini"
        self.logo_path = logo_path
        self.settings_icon_path = settings_icon_path
        self.debug_mode = debug_mode

        # Init logger before anything else
        self.setup_logger()

        # Apply theme to root window
        self.root.configure(bg=COLOUR_SCHEME["background"])

        # Initialize sub-apps dict
        self.subapps: Dict[str, PngAppMgrBase] = {}

        # Configure the main window
        root.title(f"{self.app_name} {self.version}")
        root.geometry("1280x720")

        # Create custom style
        self.create_custom_style()

        # Create main frames
        self.header_frame = ttk.Frame(root, padding="10", style="Racing.TFrame")
        self.header_frame.pack(fill=tk.X)

        self.subapps_frame = ttk.LabelFrame(root, text="Pits n' Giggles subsystems",
                                            padding="10", style="Racing.TLabelframe")
        self.subapps_frame.pack(fill=tk.X, padx=10, pady=5)

        self.console_frame = ttk.Frame(root, padding="10", style="Racing.TFrame")
        self.console_frame.pack(fill=tk.BOTH, expand=True)

        # Initialisations
        self.load_settings()
        self.setup_header()
        self.setup_console()
        self.setup_subapps()

        self.stdout_original = sys.stdout
        sys.stdout = self

        # Check for updates in parallel (no-op in dev mode)
        if self.version:
            threading.Thread(target=self.check_for_updates_background, daemon=True).start()

        # Initial log message
        self.log(f"Pits n' Giggles started. Version: {self.version}")

    def create_custom_style(self):
        """Create custom styles for the application"""
        style = ttk.Style()

        # Configure the theme
        style.theme_use("clam")

        # Configure frame styles
        style.configure("Racing.TFrame", background=COLOUR_SCHEME["background"])
        style.configure("Racing.TLabelframe", background=COLOUR_SCHEME["background"],
                       foreground=COLOUR_SCHEME["foreground"])
        style.configure("Racing.TLabelframe.Label", background=COLOUR_SCHEME["background"],
                       foreground=COLOUR_SCHEME["accent1"], font=("Arial", 10, "bold"))

        # Configure button styles
        style.configure("Racing.TButton", background=COLOUR_SCHEME["accent2"],
                       foreground=COLOUR_SCHEME["foreground"])
        style.map("Racing.TButton",
            background=[("active", COLOUR_SCHEME["accent1"])],
            foreground=[("active", COLOUR_SCHEME["background"])])
        style.map("Racing.TButton",
                background=[
                    ("active", COLOUR_SCHEME["accent1"]),
                    ("disabled", COLOUR_SCHEME["disabled_bg"])  # or any color you prefer
                ],
                foreground=[
                    ("active", COLOUR_SCHEME["background"]),
                    ("disabled", COLOUR_SCHEME["disabled_text"])  # define this in your scheme
                ])

        # Configure label styles
        style.configure("Racing.TLabel", background=COLOUR_SCHEME["background"],
                       foreground=COLOUR_SCHEME["foreground"])
        style.configure("Header.TLabel", background=COLOUR_SCHEME["background"],
                       foreground=COLOUR_SCHEME["accent1"], font=("Arial", 14, "bold"))
        style.configure("Version.TLabel", background=COLOUR_SCHEME["background"],
                       foreground=COLOUR_SCHEME["foreground"], font=("Arial", 10))

        # Configure status styles
        style.configure("Running.TLabel", background=COLOUR_SCHEME["running"])
        style.configure("Stopped.TLabel", background=COLOUR_SCHEME["stopped"])
        style.configure("Warning.TLabel", background=COLOUR_SCHEME["warning"])

        style.configure("UpdateAvailable.TButton",
            background="#4592BB",
            foreground=COLOUR_SCHEME["foreground"])

        style.map("UpdateAvailable.TButton",
            background=[("active", "#2E6A8A")],
            foreground=[("active", COLOUR_SCHEME["background"])])

    def load_settings(self):
        """Load application settings"""
        self.settings = load_config_from_ini(self.config_file, self.m_logger)

    def setup_subapps(self):
        """Set up the hard-coded sub-apps"""
        self.subapps = {
            # Backend app reads port from config file
            "server": BackendAppMgr(
                console_app=self,
                port_str=str(self.settings.Network.server_port),
                args=["--config-file", self.config_file, "--debug", "--replay-server"] \
                    if self.debug_mode else ["--config-file", self.config_file ],
                proto=self.settings.HTTPS.proto
            ),
            # SaveViewer app reads port from args
            "save_viewer": SaveViewerAppMgr(
                console_app=self,
                port_str=str(self.settings.Network.save_viewer_port),
            ),
        }

        # Create UI for each subapp
        for i, (_, subapp) in enumerate(self.subapps.items()):
            frame = ttk.Frame(self.subapps_frame, style="Racing.TFrame")
            frame.grid(row=0, column=i, padx=15, pady=5)

            # Add controls for this subapp
            label = ttk.Label(frame, text=f"{subapp.display_name}:", style="Racing.TLabel")
            label.grid(row=0, column=0, padx=5, pady=5)

            status_label = ttk.Label(frame, textvariable=subapp.status_var, width=10, style="Stopped.TLabel")
            status_label.grid(row=0, column=1, padx=5, pady=5)

            # Configure status label colors based on status
            self._update_status_style(subapp.status_var, status_label)

            subapp.status_var.trace_add("write", lambda *args, sv=subapp.status_var, lbl=status_label:
                                        self._update_status_style(sv, lbl))

            # Dynamically create buttons from subapp and add them to the frame
            for idx, button in enumerate(subapp.get_buttons(frame)):  # Pass the frame here
                button.grid(row=0, column=2 + idx, padx=5, pady=5)
        # Launch the sub-apps that should start by default
        for subapp in self.subapps.values():
            if subapp.start_by_default:
                subapp.start()

    def _update_status_style(self, status_var: tk.StringVar, label: ttk.Label) -> None:
        """
        Update the style of the label based on the status value.

        This function changes the style of the provided label depending on the
        value of the given status variable. It adjusts the style to:
        - "Running.TLabel" for "Running"
        - "Stopped.TLabel" for "Stopped"
        - "Warning.TLabel" for other status values.

        Args:
            status_var (tk.StringVar): The variable holding the status value.
            label (ttk.Label): The label whose style will be updated.
        """
        status = status_var.get()
        if status == "Running":
            label.configure(style="Running.TLabel")
        elif status == "Stopped":
            label.configure(style="Stopped.TLabel")
        else:
            label.configure(style="Warning.TLabel")

    def setup_header(self):
        # App info section with racing theme
        info_frame = ttk.Frame(self.header_frame, style="Racing.TFrame")
        info_frame.pack(side=tk.LEFT)

        # Load the image using PIL/Pillow
        pil_image = Image.open(self.logo_path)
        target_height = 30
        width, height = pil_image.size
        new_width = int(width * (target_height / height))
        pil_image = pil_image.resize((new_width, target_height), Image.Resampling.LANCZOS)
        self.logo_image = ImageTk.PhotoImage(pil_image)

        logo_label = tk.Label(info_frame, image=self.logo_image, bg=COLOUR_SCHEME["background"])
        logo_label.pack(side=tk.LEFT, padx=(0, 10))

        app_label = ttk.Label(info_frame, text=f"{self.app_name}", style="Header.TLabel")
        app_label.pack(side=tk.LEFT)

        if self.version:
            version_label = ttk.Label(info_frame, text=f"v{self.version}", style="Version.TLabel")
            version_label.pack(side=tk.LEFT, padx=(5, 0))

        # Buttons section
        buttons_frame = ttk.Frame(self.header_frame, style="Racing.TFrame")
        buttons_frame.pack(side=tk.RIGHT)

        self._add_header_button(buttons_frame, "Settings", self.open_settings)
        self._add_header_button(buttons_frame, "Clear Log", self.clear_log)

        # External links
        self._add_header_button(buttons_frame, "Tips n' Tricks", lambda: webbrowser.open("https://pitsngiggles.com/blog"))
        self._add_header_button(buttons_frame, "Discord", lambda: webbrowser.open("https://discord.gg/qQsSEHhW2V"))
        self.update_button = self._add_header_button(
            buttons_frame, "Updates", lambda: webbrowser.open("https://pitsngiggles.com/releases")
        )

    def _add_header_button(self, parent, text: str, command: Callable) -> ttk.Button:
        btn = ttk.Button(parent, text=text, command=command, style="Racing.TButton")
        btn.pack(side=tk.LEFT, padx=(0, 10))
        return btn

    def setup_console(self):
        # Create a text widget for the console with racing theme
        self.console = tk.Text(self.console_frame, wrap=tk.WORD,
                             bg=COLOUR_SCHEME["console_bg"],
                             fg=COLOUR_SCHEME["console_fg"],
                             insertbackground=COLOUR_SCHEME["console_fg"],
                             font=("Consolas", 10))
        self.console.pack(fill=tk.BOTH, expand=True)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.console, orient=tk.VERTICAL, command=self.console.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.console.config(yscrollcommand=scrollbar.set)

        # Make text read-only
        self.console.configure(state=tk.DISABLED)

    def setup_logger(self):
        """Set up the logger for the application"""
        self.m_logger = get_rotating_logger()

    def log(self, message: str, is_child_message: bool=False):
        """Add a message to the console with timestamp. Also write to file
        Args:
            message (str): The message to log
            is_child_message (bool): Whether the message is from a child process
        """
        if is_child_message:
            formatted_message = message
            self.m_logger.info(message.rstrip(), extra={"with_timestamp": False}, stacklevel=2)
        else:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            formatted_message = f"[{timestamp}] {message}\n"
            self.m_logger.info(message.rstrip(), extra={"with_timestamp": True}, stacklevel=2)

        self.console.configure(state=tk.NORMAL)
        self.console.insert(tk.END, formatted_message)
        self.console.see(tk.END)  # Auto-scroll to the end
        self.console.configure(state=tk.DISABLED)

    def clear_log(self):
        """Clear the console log"""
        self.console.configure(state=tk.NORMAL)
        self.console.delete(1.0, tk.END)
        self.console.configure(state=tk.DISABLED)
        self.log("Log cleared")

    def open_settings(self):
        """Open the settings window"""
        self.log("Opening settings window")
        SettingsWindow(
            parent=self.root,
            app=self,
            settings=self.settings,
            save_callback=self.settings_change_callback,
            config_file=self.config_file,
            settings_icon_path=self.settings_icon_path
        )

    def settings_change_callback(self, new_settings: PngSettings) -> None:
        """Callback function to save settings from the settings window"""

        self.log("Settings changed, restarting apps...")

        # Save the new settings
        self.settings = new_settings

        # Propagate settings to sub-apps and restart them
        for _, subapp in self.subapps.items():
            # Check if the subapp needs to be restarted
            if subapp.on_settings_change(new_settings):
                subapp.restart()

    def write(self, text):
        """Handle print statements by redirecting to our log"""
        if text.strip():  # Only process non-empty strings
            self.log(text.rstrip())

    def flush(self):
        """Required for stdout redirection"""
        return

    def on_closing(self):
        """Stop all running sub-apps and restore stdout before closing"""
        for _, subapp in self.subapps.items():
            if subapp.is_running:
                self.log(f"Stopping {subapp.display_name}...")
                subapp.stop()

        sys.stdout = self.stdout_original
        self.root.destroy()

    def check_for_updates_background(self) -> None:
        """Background thread to check if an update is available"""
        try:
            if is_update_available(self.version):
                self.root.after(0, self.mark_update_button_available)
        except Exception as e: # pylint: disable=broad-exception-caught
            self.log(f"[Update Check] Failed: {e}")

    def mark_update_button_available(self) -> None:
        """Highlight the update button to indicate an update is available"""
        self.update_button.configure(style="UpdateAvailable.TButton")
        self.update_button.configure(text="Update Available!")