# MIT License
#
# Copyright (c) [2024] [Ashwin Natarajan]
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

import configparser
import os
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable
from .console_interface import ConsoleInterface

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

# Define racing theme colors
COLOR_THEME = {
    "background": "#1E1E1E",       # Dark background
    "foreground": "#E0E0E0",       # Light text
    "accent1": "#FF2800",          # Racing red
    "accent2": "#303030",          # Dark gray
    "console_bg": "#000000",       # Console black
    "console_fg": "#00FF00",       # Terminal green
    "running": "#00CC00",          # Green for running status
    "stopped": "#FF2800",          # Red for stopped status
    "warning": "#FFA500"           # Orange for warnings
}

# Default settings - everything is a string in this layer
DEFAULT_SETTINGS = {
    "Network": {
        "telemetry_port": "20777",
        "server_port": "4768",
        "save_viewer_port": "4769",
        "udp_custom_action_code": "12",
        "udp_tyre_delta_action_code": "11"
    },
    "Capture": {
        "post_race_data_autosave": "True"
    },
    "Display": {
        "refresh_interval": "200",
        "disable_browser_autoload": "False"
    },
    "Logging": {
        "log_file": "png_launcher.log", # TODO - use proper value
        "log_file_size": "1000000"
    },
    "Privacy": {
        "process_car_setup": "False"
    },
    "Forwarding": {
        "target_1": "",
        "target_2": "",
        "target_3": "",
    }
}

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

class SettingsWindow:
    """
    A window for managing application settings.

    This class creates a settings window where the user can view and edit various
    configuration options for the application. Settings are saved to a configuration file.
    """

    def __init__(self, parent: tk.Tk, app: ConsoleInterface, save_callback: Callable[[configparser.ConfigParser], None], config_file: str = "app_settings.ini"):
        """
        Initialize the SettingsWindow.

        Args:
            parent: The parent Tkinter window.
            app: The main application object.
            save_callback: A callback function to propagate saved settings.
            config_file: The path to the settings file (defaults to "app_settings.ini").
        """
        self.parent = parent
        self.app = app
        self.save_callback = save_callback
        self.config_file = config_file
        self.settings = configparser.ConfigParser()

        # Load or create settings
        self.load_settings()

        # Create settings window
        self.window = tk.Toplevel(parent)
        self.window.title("Application Settings")
        self.window.geometry("600x500")
        self.window.transient(parent)
        self.window.grab_set()

        # Apply theme
        self.window.configure(bg=COLOR_THEME["background"])

        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create tabs for each section
        self.create_tabs()

        # Create save/cancel buttons
        self.create_buttons()

    def load_settings(self) -> None:
        """
        Load settings from a configuration file or create new ones with defaults.

        This method reads the settings file if it exists, or creates default settings
        if no settings file is found. It ensures all sections and keys exist.
        """
        if os.path.exists(self.config_file):
            self.settings.read(self.config_file)

        # Ensure all sections and keys exist
        for section, options in DEFAULT_SETTINGS.items():
            if not self.settings.has_section(section):
                self.settings.add_section(section)

            for key, value in options.items():
                if not self.settings.has_option(section, key):
                    self.settings.set(section, key, value)

    def save_settings(self) -> None:
        """
        Save the current settings to the configuration file.

        The settings are written to the file specified by `self.config_file`. After saving,
        the `save_callback` is called to propagate the updated settings.
        """
        with open(self.config_file, 'w') as f:
            self.settings.write(f)

        self.app.log(f"Settings saved to {self.config_file}")
        self.save_callback(self.settings)

    def create_tabs(self) -> None:
        """
        Create tabs for each settings section and populate them with input fields.

        This method creates a tab for each section in the settings file and populates
        it with appropriate input widgets (entry, checkbox, combobox, etc.) based on
        the type of each setting.
        """
        self.entry_vars = {}

        for section in self.settings.sections():
            tab = ttk.Frame(self.notebook, padding=10)
            self.notebook.add(tab, text=section)

            # Create a frame for this section with a scrollbar
            canvas = tk.Canvas(tab, bg=COLOR_THEME["background"])
            scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)

            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )

            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            # Add settings fields
            for i, (key, value) in enumerate(self.settings[section].items()):
                # Create a label and entry for each setting
                label = ttk.Label(scrollable_frame, text=key.replace('_', ' ').title() + ":")
                label.grid(row=i, column=0, sticky="w", padx=5, pady=5)

                # Use different controls based on value type
                if value.lower() in ['true', 'false']:
                    # Boolean - use checkbox
                    var = tk.BooleanVar(value=value.lower() == 'true')
                    control = ttk.Checkbutton(scrollable_frame, variable=var)
                elif key == 'packet_capture_mode':
                    # Enumeration - use combobox
                    var = tk.StringVar(value=value)
                    control = ttk.Combobox(scrollable_frame, textvariable=var,
                                          values=["disabled", "enabled", "auto"])
                    control.set(value)
                else:
                    # Text entry for everything else
                    var = tk.StringVar(value=value)
                    control = ttk.Entry(scrollable_frame, textvariable=var, width=30)

                control.grid(row=i, column=1, sticky="ew", padx=5, pady=5)

                # Store the variable for later retrieval
                if section not in self.entry_vars:
                    self.entry_vars[section] = {}
                self.entry_vars[section][key] = var

    def create_buttons(self) -> None:
        """
        Create the save and cancel buttons at the bottom of the settings window.

        This method creates the buttons and places them in a frame at the bottom of the window.
        The save button will trigger saving the settings, and the cancel button will close
        the settings window without saving.
        """
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        save_button = ttk.Button(button_frame, text="Save", command=self.on_save)
        save_button.pack(side=tk.RIGHT, padx=5)

        cancel_button = ttk.Button(button_frame, text="Cancel", command=self.window.destroy)
        cancel_button.pack(side=tk.RIGHT, padx=5)

    def on_save(self) -> None:
        """
        Save the settings from the UI to the configuration file.

        This method retrieves the current values from the user input fields, updates
        the settings object, and then calls `save_settings()` to persist the changes.
        It will also close the settings window after saving.
        """
        try:
            for section, options in self.entry_vars.items():
                for key, var in options.items():
                    # Convert boolean to string
                    value = str(var.get()) if isinstance(var, tk.BooleanVar) else var.get()
                    self.settings.set(section, key, value)

            self.save_settings()
            self.window.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")
