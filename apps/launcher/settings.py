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
import re
import tkinter as tk
from tkinter import BooleanVar, StringVar, messagebox, ttk, filedialog
from typing import Callable, get_args, get_origin, Union

from pydantic import ValidationError

from lib.config import FilePathStr, PngSettings, save_config_to_ini

from .console_interface import ConsoleInterface

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

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
                 settings: PngSettings,
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
        self.settings = settings

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

    def create_tabs(self) -> None:
        """
        Create tabs for each section of the settings using the schema model.

        - Boolean fields get checkboxes.
        - FilePathStr fields get an entry box with a 'Browse...' button.
        - Other fields get standard entry boxes.
        """
        self.entry_vars = {}

        for section_name, field in type(self.settings).model_fields.items():
            # Only for this particular section, the user is expected to configure by editing the ini file
            if section_name in {"TimeLossInPitsF1", "TimeLossInPitsF2"}:
                continue
            section_model = getattr(self.settings, section_name)
            section_name_formatted = self._pascal_to_title(section_name)
            tab = ttk.Frame(self.notebook)
            self.notebook.add(tab, text=section_name_formatted)
            self.entry_vars.setdefault(section_name, {})

            # Configure grid columns - make sure we have 4 columns (including 2 for buttons)
            tab.columnconfigure(0, weight=0)  # Labels column
            tab.columnconfigure(1, weight=1)  # Entry fields column
            tab.columnconfigure(2, weight=0)  # Button column (e.g., Save)
            tab.columnconfigure(3, weight=0)  # Button column (e.g., Clear)

            model_fields = type(section_model).model_fields
            for i, (field_name, field) in enumerate(model_fields.items()):
                label_text = field.description or field_name
                label = ttk.Label(tab, text=f"{label_text}:")
                label.grid(row=i, column=0, sticky="w", padx=5, pady=5)

                value = getattr(section_model, field_name)
                annotation = field.annotation
                origin = get_origin(annotation)
                args = get_args(annotation)
                is_file_path = (
                    annotation is FilePathStr or
                    origin is FilePathStr or
                    (origin is Union and FilePathStr in args)
                )

                if isinstance(value, bool):
                    var = BooleanVar(value=value)
                    control = ttk.Checkbutton(tab, variable=var)
                    control.grid(row=i, column=1, sticky="w", padx=5, pady=5)

                elif is_file_path:
                    var = StringVar(value=str(value))

                    # Entry field
                    entry = ttk.Entry(tab, textvariable=var)
                    entry.grid(row=i, column=1, sticky="ew", padx=(5, 2), pady=5)

                    # Browse button
                    browse_btn = ttk.Button(
                        tab,
                        text="Browse...",
                        command=lambda v=var: self._browse_file(v)
                    )
                    browse_btn.grid(row=i, column=2, sticky="w", padx=(2, 2), pady=5)

                    # Clear button
                    clear_btn = ttk.Button(
                        tab,
                        text="Clear",
                        command=lambda v=var: v.set("")
                    )
                    clear_btn.grid(row=i, column=3, sticky="w", padx=(0, 5), pady=5)

                else:
                    var = StringVar(value=str(value))
                    control = ttk.Entry(tab, textvariable=var, width=30)
                    control.grid(row=i, column=1, sticky="ew", padx=5, pady=5)

                # ⬇️ Hoisted line (common to all branches)
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

        This method:
        - Collects user inputs from the UI
        - Strips trailing spaces from all string values
        - Validates the data by building a new PngSettings model
        - Compares it to the existing model to detect changes
        - Saves the config to the INI file if changed
        - Calls a callback if provided
        - Displays errors in a user-friendly format if validation fails
        """
        data = {}

        # Gather input values from each tab and field
        for section, section_data in self.entry_vars.items():
            data[section] = {}
            for key, var in section_data.items():
                val = var.get()
                # Strip whitespace from strings only
                if isinstance(val, str):
                    val = val.strip()
                data[section][key] = val

        try:
            # Build new model to validate and capture changes
            new_model = PngSettings(**data)
        except ValidationError as ve:
            # Show all validation issues nicely
            error_messages = []
            for err in ve.errors():
                loc = " > ".join(str(x) for x in err["loc"])
                msg = err["msg"]
                error_messages.append(f"{loc}: {msg}")
            messagebox.showerror("Invalid Settings", "\n".join(error_messages))
            return

        # If settings haven't changed, skip saving and callback
        if new_model == self.settings:
            return

        self.settings = new_model

        # Save new settings to config file
        save_config_to_ini(new_model, self.config_file)
        self.app.debug_log(f"Settings saved to {self.config_file}")

        # Run any registered save callback
        if self.save_callback:
            self.save_callback(new_model)

        # Show a success message
        messagebox.showinfo("Settings Saved", "Settings saved successfully.")

    def _pascal_to_title(self, name: str) -> str:
        """
        Convert PascalCase or ALLCAPS section names to a title format.

        Examples:
            'LoggingSettings' → 'Logging Settings'
            'StreamOverlay'   → 'Stream Overlay'
            'HTTPS'           → 'HTTPS'
        """
        if name.isupper():
            return name  # Leave acronyms like HTTPS, UDP unchanged

        # Insert space before capital letters that are followed by lowercase letters
        return re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', name)

    def _browse_file(self, var: StringVar) -> None:
        """
        Open a file dialog and set the selected path into the given StringVar.

        Args:
            var (StringVar): The variable to update with the selected file path.
        """
        if file_path := filedialog.askopenfilename():
            var.set(file_path)
