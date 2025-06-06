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

import configparser
import os
import tkinter as tk
import traceback
from tkinter import messagebox, ttk, BooleanVar, StringVar, IntVar
from typing import Callable
from pydantic import ValidationError

from .console_interface import ConsoleInterface
from .config_io import load_config_from_ini, save_config_to_ini
from .config_schema import PngSettings

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

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
        "log_file": "png.log",
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

    def __init__(self,
                 parent: tk.Tk,
                 app: ConsoleInterface,
                 save_callback: Callable[[configparser.ConfigParser], None],
                 config_file: str,
                 settings_icon_path: str):
        """
        Initialize the SettingsWindow.

        Args:
            parent: The parent Tkinter window.
            app: The main application object.
            save_callback: A callback function to propagate saved settings.
            config_file: The path to the settings file.
            settings_icon_path: The path to the settings icon.
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
        self.window.iconbitmap(settings_icon_path)

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

        self.settings = load_config_from_ini(self.config_file)

    def save_settings(self) -> None:
        """
        Save the current settings to the configuration file.

        The settings are written to the file specified by `self.config_file`. After saving,
        the `save_callback` is called to propagate the updated settings.
        """

        try:
            data = {}
            for section, section_data in self.entry_vars.items():
                data[section] = {
                    key: var.get() for key, var in section_data.items()
                }
            new_model = PngSettings(**data)
            save_config_to_ini(new_model, self.config_file)
        except ValidationError as ve:
            messagebox.showerror("Invalid Settings", ve.json(indent=2))
            return

        # with open(self.config_file, 'w', encoding='utf-8') as f:
        #     self.settings.write(f)

        self.app.log(f"Settings saved to {self.config_file}")
        self.save_callback(self.settings)

    def create_tabs(self) -> None:
        self.entry_vars = {}

        # To populate UI, iterate through fields like:
        for section_name, section_model in self.settings:
            tab = ttk.Frame(self.notebook)
            self.notebook.add(tab, text=section_name)
            self.entry_vars.setdefault(section_name, {})

            for i, (field_name, field) in enumerate(section_model.__fields__.items()):
                label_text = field.description if field.description else field_name
                label = ttk.Label(tab, text=label_text + ":")
                label.grid(row=i, column=0, sticky="w", padx=5, pady=5)

                value = getattr(section_model, field_name)
                if isinstance(value, bool):
                    var = BooleanVar(value=value)
                    control = ttk.Checkbutton(tab, variable=var)
                elif field_name == 'packet_capture_mode':
                    var = StringVar(value=value)
                    control = ttk.Combobox(tab, textvariable=var, values=["disabled", "enabled", "auto"])
                else:
                    var = StringVar(value=str(value))
                    control = ttk.Entry(tab, textvariable=var, width=30)

                control.grid(row=i, column=1, sticky="ew", padx=5, pady=5)
                self.entry_vars[section_name][field_name] = var

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
            data = {}
            for section, section_data in self.entry_vars.items():
                data[section] = {
                    key: var.get() for key, var in section_data.items()
                }
            new_model = PngSettings(**data)
            save_config_to_ini(new_model, self.config_file)
        except ValidationError as ve:
            messagebox.showerror("Invalid Settings", ve.json(indent=2))
