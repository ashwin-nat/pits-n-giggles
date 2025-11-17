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
from tkinter import (BooleanVar, DoubleVar, IntVar, StringVar, filedialog, Variable,
                     messagebox, ttk)
from typing import Any, Callable, Dict, Optional, Union, get_args, get_origin

from pydantic import ValidationError, BaseModel

from lib.config import FilePathStr, PngSettings, save_config_to_ini

from .console_interface import ConsoleInterface

# -------------------------------------- TYPES -------------------------------------------------------------------------

WidgetCreator = Callable[[ttk.Frame, int, str, Any, Any, Dict[str, Any], str],
                         Variable]

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

        Uses `ui_meta` at the class level to determine section visibility and label.
        Uses field-level `json_schema_extra` to select the input control type.
        Widget creation is handled via a dispatch table based on ui_type.
        """
        self.entry_vars: Dict[str, Dict[str, Variable]] = {}

        for section_name, section_field in type(self.settings).model_fields.items():
            section_class: BaseModel = section_field.annotation
            ui_meta: Dict[str, Any] = section_class.ui_meta

            # Skip invisible or unsupported sections
            if not ui_meta["visible"]:
                self.app.debug_log(f"Skipping invisible settings section: {section_name}")
                continue

            section_instance = self.settings.__dict__[section_name]
            section_label: str = self._pascal_to_title(section_name)

            # --- Create tab ---
            tab: ttk.Frame = ttk.Frame(self.notebook)
            self.notebook.add(tab, text=section_label)
            self.entry_vars.setdefault(section_name, {})

            # --- Grid configuration ---
            tab.columnconfigure(0, weight=0)  # Label column
            tab.columnconfigure(1, weight=1)  # Input column
            tab.columnconfigure(2, weight=0)  # Browse/Clear buttons
            tab.columnconfigure(3, weight=0)

            # --- Populate fields ---
            for i, (field_name, field_info) in enumerate(section_class.model_fields.items()):
                label_text: str = field_info.description
                ttk.Label(tab, text=f"{label_text}:").grid(row=i, column=0, sticky="w", padx=5, pady=5)

                value: Any = section_instance.__dict__[field_name]
                field_meta: Dict[str, Any] = field_info.json_schema_extra
                ui_meta: Dict[str, Any] = field_meta["ui"]
                ui_type: str = ui_meta.get("type")

                # Create widget using dispatch table
                var: Variable = self._create_widget(
                    tab, i, field_name, field_info, value, ui_meta, ui_type, section_name
                )

                # Store reference for later save/apply
                self.entry_vars[section_name][field_name] = var

    def _create_widget(
        self,
        tab: ttk.Frame,
        row: int,
        field_name: str,
        field_info: Any,
        value: Any,
        ui_meta: Dict[str, Any],
        ui_type: str,
        section_name: str
    ) -> Union[BooleanVar, IntVar, DoubleVar, StringVar]:
        """
        Create a widget based on ui_type using a dispatch table.

        Args:
            tab: The parent frame/tab to place the widget in
            row: Grid row number for widget placement
            field_name: Name of the field being created
            field_info: Pydantic field info object containing metadata
            value: Current value of the field
            ui_meta: UI metadata dictionary from json_schema_extra
            ui_type: Type of UI widget to create (e.g., 'check_box', 'slider')
            section_name: Name of the settings section

        Returns:
            Variable object (BooleanVar, IntVar, DoubleVar, or StringVar) bound to the widget
        """

        # Dispatch table mapping ui_type to creator methods
        widget_creators: Dict[str, WidgetCreator] = {
            "check_box": self._create_checkbox,
            "slider": self._create_slider,
            "hostport_entry": self._create_hostport_entry,
            "file_path": self._create_file_path,
        }

        # Check if it's a file path field (for backward compatibility)
        annotation = field_info.annotation
        origin = get_origin(annotation)
        args = get_args(annotation)
        is_file_path: bool = (
            annotation is FilePathStr or
            origin is FilePathStr or
            (origin is Union and FilePathStr in args)
        )

        # Determine creator
        if ui_type in widget_creators:
            creator: Callable = widget_creators[ui_type]
        elif is_file_path:
            creator = self._create_file_path
        else:
            creator = self._create_text_entry

        # Call the appropriate creator
        return creator(tab, row, field_name, field_info, value, ui_meta, section_name)

    def _create_checkbox(
        self,
        tab: ttk.Frame,
        row: int,
        field_name: str,
        _field_info: Any,
        value: bool,
        _ui_meta: Dict[str, Any],
        section_name: str
    ) -> BooleanVar:
        """
        Create a checkbox widget.

        Args:
            tab: The parent frame/tab to place the widget in
            row: Grid row number for widget placement
            field_name: Name of the field being created
            value: Current boolean value of the field
            section_name: Name of the settings section

        Returns:
            BooleanVar bound to the checkbox widget
        """
        var: BooleanVar = BooleanVar(value=value)
        widget: ttk.Checkbutton = ttk.Checkbutton(tab, variable=var)
        widget.grid(row=row, column=1, sticky="w", padx=5, pady=5)
        self.app.debug_log(f"Created checkbox for {section_name}.{field_name}")
        return var

    def _create_slider(
        self,
        tab: ttk.Frame,
        row: int,
        field_name: str,
        field_info: Any,
        value: Union[int, float],
        ui_meta: Dict[str, Any],
        section_name: str
    ) -> Union[IntVar, DoubleVar]:
        """
        Create a slider widget with value label.

        Args:
            tab: The parent frame/tab to place the widget in
            row: Grid row number for widget placement
            field_name: Name of the field being created
            field_info: Pydantic field info object containing metadata
            value: Current numeric value of the field
            ui_meta: UI metadata dictionary containing 'min' and 'max' keys
            section_name: Name of the settings section

        Returns:
            IntVar or DoubleVar bound to the slider widget
        """
        minv: Union[int, float] = ui_meta["min"]
        maxv: Union[int, float] = ui_meta["max"]

        is_int_field: bool = field_info.annotation in (int, Optional[int])
        var: Union[IntVar, DoubleVar] = IntVar(value=int(value)) if is_int_field else DoubleVar(value=float(value))

        scale: ttk.Scale = ttk.Scale(tab, from_=minv, to=maxv, orient="horizontal", variable=var)
        scale.grid(row=row, column=1, sticky="ew", padx=5, pady=5)

        # Precompute label width from the max value length
        max_text: str = f"{maxv:.0f}" if is_int_field else f"{maxv:.2f}"
        fmt: str = "{:.0f}" if is_int_field else "{:.2f}"
        value_label: ttk.Label = ttk.Label(tab, text=fmt.format(value), width=len(max_text), anchor="e")
        value_label.grid(row=row, column=2, sticky="e", padx=(5, 10), pady=5)

        def _update_label(*_: Any) -> None:
            """Update the label text when slider value changes."""
            value_label.config(text=fmt.format(var.get()))

        var.trace_add("write", _update_label)

        self.app.debug_log(f"Created slider for {section_name}.{field_name}")
        return var

    def _create_hostport_entry(
        self,
        tab: ttk.Frame,
        row: int,
        field_name: str,
        _field_info: Any,
        value: str,
        _ui_meta: Dict[str, Any],
        section_name: str
    ) -> StringVar:
        """
        Create a host:port entry widget.

        Args:
            tab: The parent frame/tab to place the widget in
            row: Grid row number for widget placement
            field_name: Name of the field being created
            value: Current string value of the field
            section_name: Name of the settings section

        Returns:
            StringVar bound to the entry widget
        """
        var: StringVar = StringVar(value=value)
        entry: ttk.Entry = ttk.Entry(tab, textvariable=var)
        entry.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        self.app.debug_log(f"Created hostport entry for {section_name}.{field_name}")
        return var

    def _create_file_path(
        self,
        tab: ttk.Frame,
        row: int,
        field_name: str,
        _field_info: Any,
        value: str,
        _ui_meta: Dict[str, Any],
        section_name: str
    ) -> StringVar:
        """
        Create a file path entry with Browse and Clear buttons.

        Args:
            tab: The parent frame/tab to place the widget in
            row: Grid row number for widget placement
            field_name: Name of the field being created
            value: Current file path value
            section_name: Name of the settings section

        Returns:
            StringVar bound to the entry widget
        """
        var: StringVar = StringVar(value=value)

        entry: ttk.Entry = ttk.Entry(tab, textvariable=var)
        entry.grid(row=row, column=1, sticky="ew", padx=(5, 2), pady=5)

        browse_btn: ttk.Button = ttk.Button(
            tab, text="Browse...", command=lambda v=var: self._browse_file(v)
        )
        browse_btn.grid(row=row, column=2, sticky="w", padx=(2, 2), pady=5)

        clear_btn: ttk.Button = ttk.Button(tab, text="Clear", command=lambda v=var: v.set(""))
        clear_btn.grid(row=row, column=3, sticky="w", padx=(0, 5), pady=5)

        self.app.debug_log(f"Created file path entry for {section_name}.{field_name}")
        return var

    def _create_text_entry(
        self,
        tab: ttk.Frame,
        row: int,
        field_name: str,
        _field_info: Any,
        value: Any,
        _ui_meta: Dict[str, Any],
        section_name: str
    ) -> StringVar:
        """
        Create a standard text entry widget.

        Args:
            tab: The parent frame/tab to place the widget in
            row: Grid row number for widget placement
            field_name: Name of the field being created
            value: Current value of the field (will be converted to string)
            section_name: Name of the settings section

        Returns:
            StringVar bound to the entry widget
        """
        var: StringVar = StringVar(value=str(value))
        entry: ttk.Entry = ttk.Entry(tab, textvariable=var, width=30)
        entry.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        self.app.debug_log(f"Created text entry for {section_name}.{field_name}")
        return var

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
