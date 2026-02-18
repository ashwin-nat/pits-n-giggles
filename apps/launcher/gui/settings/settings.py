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

import json
from collections import defaultdict
from typing import (TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple,
                    Union, get_args, get_origin)

from pydantic import BaseModel, ValidationError
from pydantic.fields import FieldInfo
from PySide6.QtCore import (QEasingCurve, QParallelAnimationGroup, QPoint,
                            QPropertyAnimation, Qt)
from PySide6.QtGui import QCloseEvent, QFont, QIcon
from PySide6.QtWidgets import (QButtonGroup, QCheckBox, QDialog, QFrame,
                               QGroupBox, QHBoxLayout, QLabel, QLineEdit,
                               QListWidget, QMessageBox, QPushButton,
                               QRadioButton, QScrollArea, QSlider,
                               QStackedWidget, QVBoxLayout, QWidget)

from lib.config import PngSettings

from .collapsible_group import CollapsibleGroup
from .reorderable_collection import ReorderableCollection
from .searchable_widget import SearchableWidget

if TYPE_CHECKING:
    from ..main_window import PngLauncherWindow

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class SettingsWindow(QDialog):
    """Dynamic settings window that builds UI from PngSettings schema"""

    def __init__(self,
                 parent_window: "PngLauncherWindow",
                 settings: PngSettings,
                 icons_dict: Dict[str, QIcon],
                 on_settings_change: Optional[Callable[[PngSettings], None]] = None):
        """Initialize the settings window

        Args:
            parent_window: The parent window
            settings: The current settings
            on_settings_change: A callback function to handle settings changes
        """
        super().__init__(parent_window)
        self.parent_window = parent_window
        self.original_settings = settings
        self.working_settings = settings.model_copy(deep=True)
        self.on_settings_change = on_settings_change
        self.icons_dict = icons_dict

        # Track widgets for validation and updates
        self.field_widgets: Dict[str, Any] = {}

        # Track all searchable widgets (containers and group boxes) for search filtering
        self.searchable_widgets: List[SearchableWidget] = []

        # Track category names for search filtering
        self.category_names: List[str] = []  # Original category names
        self.category_field_names: List[str] = []  # Model field names, parallel to category_names

        # Track collapsible group header widgets keyed by group title, per category
        # { category_index: { group_title: collapsible_container_widget } }
        self.collapsible_groups: Dict[int, Dict[str, QWidget]] = {}

        # Track collapsible group header widgets keyed by group title, per category
        # { category_index: { group_title: collapsible_container_widget } }
        self.collapsible_groups: Dict[int, Dict[str, QWidget]] = {}

        self.setup_ui()

    def setup_ui(self):
        """Setup the settings dialog UI"""
        self.setWindowTitle("Settings")
        self.setMinimumSize(1000, 700)

        # Apply dark theme
        self.setStyleSheet("""
            QDialog {
                background-color: #252526;
                color: #d4d4d4;
            }
            QListWidget {
                background-color: #1e1e1e;
                border: 1px solid #3e3e3e;
                border-radius: 4px;
                color: #d4d4d4;
                outline: none;
                padding: 4px;
            }
            QListWidget::item {
                padding: 10px;
                border-radius: 4px;
                margin: 2px 0px;
            }
            QListWidget::item:selected {
                background-color: #0e639c;
            }
            QListWidget::item:hover {
                background-color: #3e3e3e;
            }
            QWidget {
                border: none;
            }
            QGroupBox {
                border: 1px solid #3e3e3e;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 12px;
                background-color: #2d2d2d;
                color: #d4d4d4;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                color: #d4d4d4;
            }
            QCheckBox {
                color: #d4d4d4;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #3e3e3e;
                border-radius: 3px;
                background-color: #1e1e1e;
            }
            QCheckBox::indicator:checked {
                background-color: #0e639c;
                border-color: #0e639c;
            }
            QCheckBox::indicator:hover {
                border-color: #0e639c;
            }
            QLineEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3e3e3e;
                border-radius: 4px;
                padding: 6px;
            }
            QLineEdit:focus {
                border-color: #0e639c;
            }
            QSlider::groove:horizontal {
                border: 1px solid #3e3e3e;
                height: 6px;
                background-color: #1e1e1e;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background-color: #0e639c;
                border: 1px solid #0e639c;
                width: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background-color: #1177bb;
            }
            QLabel {
                color: #d4d4d4;
            }
            QPushButton {
                background-color: #3e3e3e;
                color: #d4d4d4;
                border: 1px solid #4e4e4e;
                border-radius: 4px;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background-color: #0e639c;
                border-color: #1177bb;
            }
            QPushButton:pressed {
                background-color: #0d5689;
            }
            QScrollArea {
                border: none;
                background-color: #1e1e1e;
            }
            QRadioButton {
                color: #d4d4d4;
                spacing: 8px;
            }

            /* Unchecked */
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 1px solid #6a6a6a;
                background-color: #1e1e1e;
            }

            /* Checked */
            QRadioButton::indicator:checked {
                border: 1px solid #0e639c;
                background-color: #0e639c;
            }

        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Search bar
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        search_label.setFixedWidth(60)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search settings by description...")
        self.search_input.textChanged.connect(self._on_search_changed)

        # Clear button for search
        clear_search_btn = QPushButton("Clear")
        clear_search_btn.setMaximumWidth(60)
        clear_search_btn.clicked.connect(self.search_input.clear)

        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(clear_search_btn)
        main_layout.addLayout(search_layout)

        # Content area with list and stacked widget
        content_layout = QHBoxLayout()

        # Category list on the left
        self.category_list = QListWidget()
        self.category_list.setMaximumWidth(200)
        self.category_list.setFont(QFont("Formula1"))
        self.category_list.currentRowChanged.connect(self.on_category_changed)

        # Stacked widget for category content on the right
        self.stacked_widget = QStackedWidget()

        # Build categories
        for category_index, (category_name, category_model) in enumerate(self.working_settings):
            if not self._is_visible(category_model):
                continue

            # Get the field info to access the description
            field_info = self._get_field_info_from_path(category_name)
            display_name = field_info.description

            self.category_list.addItem(display_name)
            self.category_names.append(display_name)
            self.category_field_names.append(category_name)

            # Track the starting index for this category's widgets
            widgets_start_index = len(self.searchable_widgets)

            category_widget = self._build_category_content(category_name, category_model)
            self.stacked_widget.addWidget(category_widget)

            # Set category_index on all widgets added during category building
            widgets_end_index = len(self.searchable_widgets)
            for sw in self.searchable_widgets[widgets_start_index:widgets_end_index]:
                sw.category_index = category_index

        content_layout.addWidget(self.category_list)
        content_layout.addWidget(self.stacked_widget, stretch=1)

        main_layout.addLayout(content_layout)

        # Button bar
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        revert_btn = QPushButton("Revert Changes")
        revert_btn.clicked.connect(self.on_revert)
        button_layout.addWidget(revert_btn)

        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self.on_reset)
        button_layout.addWidget(reset_btn)

        reset_section_btn = QPushButton("Reset Section to Defaults")
        reset_section_btn.clicked.connect(self.on_reset_section)
        button_layout.addWidget(reset_section_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.on_save)
        button_layout.addWidget(save_btn)

        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

        # Select first category
        if self.category_list.count() > 0:
            self.category_list.setCurrentRow(0)

    def on_category_changed(self, index: int):
        """Handle category selection change"""
        if index >= 0:
            self.stacked_widget.setCurrentIndex(index)

    def _register_searchable(
        self,
        widget: QWidget,
        description: str,
        field_name: str,
        label_widget: Optional[QLabel] = None,
    ) -> None:
        """Register a widget as searchable

        Args:
            widget: The widget to make searchable
            description: The description text to search against
            field_name: The field name to search against
            label_widget: Optional label widget to apply highlighting to
        """
        self.searchable_widgets.append(
            SearchableWidget(
                widget=widget,
                description=description,
                field_name=field_name,
                label_widget=label_widget,
            )
        )

    def _create_collapsible_group(self, title: str) -> CollapsibleGroup:
        return CollapsibleGroup(title, self.icons_dict, self)

    def _build_category_content(self, category_name: str, category_model: BaseModel) -> QScrollArea:
        """Build content for a settings category, grouping fields that carry a 'group' UI key
        into collapsible sections. Fields without a group are rendered at the top level as before."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        # Category title
        field_info = self._get_field_info_from_path(category_name)
        title_text = field_info.description
        title_label = QLabel(title_text)
        title_label.setFont(QFont("Roboto", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #d4d4d4; background-color: transparent;")
        layout.addWidget(title_label)

        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #3e3e3e;")
        layout.addWidget(separator)

        # Partition fields into ungrouped (rendered inline) and grouped (rendered in collapsible boxes).
        # Insertion order of group names is preserved so groups appear in the order their first field
        # is encountered, which matches the field declaration order in the model.
        ungrouped: List[Tuple[str, Any, FieldInfo]] = []
        grouped: Dict[str, List[Tuple[str, Any, FieldInfo]]] = defaultdict(list)
        group_order: List[str] = []  # Tracks insertion order of group names

        for field_name, field_info in type(category_model).model_fields.items():
            if not self._is_field_visible(field_info):
                continue

            field_value = getattr(category_model, field_name)
            ui_config = (field_info.json_schema_extra or {}).get("ui", {})
            group_name = ui_config.get("group")

            if group_name:
                if group_name not in grouped:
                    group_order.append(group_name)
                grouped[group_name].append((field_name, field_value, field_info))
            else:
                ungrouped.append((field_name, field_value, field_info))

        # --- Render ungrouped fields first ---
        for field_name, field_value, field_info in ungrouped:
            field_path = f"{category_name}.{field_name}"
            self._render_field(field_name, field_value, field_path, field_info, layout)

        # --- Render grouped fields in collapsible sections ---
        # Remember which collapsible containers belong to this category for search integration
        category_idx = len(self.category_names)  # Will be set after this call; store reference by title
        category_collapsibles: Dict[str, QWidget] = {}

        for group_name in group_order:
            fields = grouped[group_name]
            group_container = self._create_collapsible_group(group_name)
            group_layout = group_container.content_layout

            for field_name, field_value, field_info in fields:
                field_path = f"{category_name}.{field_name}"
                self._render_field(field_name, field_value, field_path, field_info, group_layout)

            layout.addWidget(group_container)
            category_collapsibles[group_name] = group_container

        # Store so search can expand groups on match
        self.collapsible_groups[category_idx] = category_collapsibles

        layout.addStretch()
        content_widget.setLayout(layout)
        scroll.setWidget(content_widget)

        return scroll

    def _render_field(self,
                      field_name: str,
                      field_value: Any,
                      field_path: str,
                      field_info: FieldInfo,
                      layout: QVBoxLayout) -> None:
        """Dispatch a single field to the correct builder and add it to *layout*."""
        ui_config = (field_info.json_schema_extra or {}).get("ui", {})
        ui_type = ui_config.get("type", "text_box")

        if isinstance(field_value, BaseModel):
            if ui_type == "reorderable_view":
                widget = self._build_reorderable_view(field_name, field_value, field_path, field_info)
                layout.addWidget(widget)
            elif ui_type == "group_box":
                widget = self._build_group_box(field_name, field_value, field_path, field_info)
                layout.addWidget(widget)
            else:
                widget = self._build_nested_group(field_name, field_value, field_path, field_info)
                layout.addWidget(widget)
        elif isinstance(field_value, dict):
            widget = self._build_dict_field(field_name, field_value, field_path, field_info)
            if widget:
                layout.addWidget(widget)
        else:
            widget = self._build_field_widget(field_name, field_value, field_path, field_info)
            if widget:
                layout.addWidget(widget)

    # -------------------------------------- FIELD WIDGET BUILDERS -----------------------------------------------------

    def _build_field_widget(self,
                            field_name: str,
                            field_value: Any,
                            field_path: str,
                            field_info: FieldInfo) -> Optional[QWidget]:
        """Build a widget for a simple field"""
        ui_meta = field_info.json_schema_extra or {}
        ui_config = ui_meta.get("ui", {})
        ui_type = ui_config.get("type", "text_box")
        description = field_info.description or field_name
        ext_info = ui_config.get("ext_info", [])  # Get extended info list for tooltips

        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Track the label widget for highlighting (if applicable)
        label_widget = None

        if ui_type == "check_box":
            label_widget = self._build_field_widget_check_box(layout, description, field_value, field_path, ext_info)

        elif ui_type == "slider":
            label_widget = self._build_field_widget_slider(layout, description, field_value, field_path, ui_config, ext_info)

        elif ui_type == "text_box":
            label_widget = self._build_field_widget_text_box(layout, description, field_value, field_path, field_info, ext_info)

        elif ui_type == "radio_buttons":
            label_widget = self._build_field_widget_radio_button(layout, description, field_value, field_path,
                                                  ui_config, container, ext_info)

        container.setLayout(layout)
        # Track container for search filtering
        self._register_searchable(container, description, field_name, label_widget)
        return container

    def _build_field_widget_check_box(self,
                                      layout: QVBoxLayout,
                                      description: str,
                                      field_value: bool,
                                      field_path: str,
                                      ext_info: Optional[str] = None) -> QLabel:

        # Create a label for the description (separate from checkbox for proper HTML highlighting)
        label = QLabel(description)
        label.setFont(QFont("Roboto", 10))
        label.setTextFormat(Qt.TextFormat.RichText)  # Enable rich text for highlighting

        # Create checkbox without text (label provides the description)
        checkbox = QCheckBox()
        checkbox.setChecked(field_value)
        checkbox.stateChanged.connect(
            lambda state, path=field_path: self._on_field_changed(path, state == Qt.CheckState.Checked.value)
        )
        self.field_widgets[field_path] = checkbox

        # Create horizontal layout for label and checkbox
        checkbox_layout = QHBoxLayout()
        checkbox_layout.setContentsMargins(0, 0, 0, 0)
        checkbox_layout.addWidget(checkbox)
        checkbox_layout.addWidget(label)

        # Wrap with info icons if ext_info is provided
        if ext_info:
            checkbox_container = QWidget()
            checkbox_container.setLayout(checkbox_layout)
            checkbox_with_info = self._wrap_widget_with_info_icons(checkbox_container, ext_info)
            layout.addWidget(checkbox_with_info)
        else:
            checkbox_layout.addStretch()
            layout.addLayout(checkbox_layout)

        return label

    def _build_field_widget_slider(self,
                                   layout: QVBoxLayout,
                                   description: str,
                                   field_value: float,
                                   field_path: str,
                                   ui_config: dict,
                                   ext_info: Optional[str] = None
                                   ) -> QLabel:

        label = QLabel(description)
        label.setFont(QFont("Roboto", 10))
        label.setTextFormat(Qt.TextFormat.RichText)  # Enable rich text for highlighting

        # Wrap label with info icons if ext_info is provided
        if ext_info:
            label_widget = self._wrap_widget_with_info_icons(label, ext_info)
            layout.addWidget(label_widget)
        else:
            layout.addWidget(label)

        slider_container = QWidget()
        slider_layout = QHBoxLayout()
        slider_layout.setContentsMargins(0, 0, 0, 0)

        # Determine slider value based on conversion type
        if ui_config.get("convert") == "percent":
            slider_min = ui_config.get("min_ui", 50)
            slider_max = ui_config.get("max_ui", 200)
            slider_value = int(field_value * 100)
            label_text = f"{slider_value}%"
        else:
            slider_min = ui_config.get("min", 0)
            slider_max = ui_config.get("max", 100)
            slider_value = field_value
            label_text = str(field_value)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(slider_min)
        slider.setMaximum(slider_max)
        slider.setValue(slider_value)

        value_label = QLabel(label_text)

        value_label.setFont(QFont("Formula1"))
        value_label.setMinimumWidth(40)
        value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        slider.valueChanged.connect(
            lambda val, path=field_path, lbl=value_label: self._on_slider_changed(path, val, lbl)
        )

        slider_layout.addWidget(slider)
        slider_layout.addWidget(value_label)
        slider_layout.addStretch()
        slider_container.setLayout(slider_layout)
        layout.addWidget(slider_container)

        self.field_widgets[field_path] = slider

        return label

    def _build_field_widget_text_box(self,
                                     layout: QVBoxLayout,
                                     description: str,
                                     field_value: str,
                                     field_path: str,
                                     field_info: FieldInfo,
                                     ext_info: Optional[str] = None
                                     ) -> QLabel:

        label = QLabel(description)
        label.setFont(QFont("Roboto", 10))
        label.setTextFormat(Qt.TextFormat.RichText)  # Enable rich text for highlighting

        # Wrap label with info icons if ext_info is provided
        if ext_info:
            label_widget = self._wrap_widget_with_info_icons(label, ext_info)
            layout.addWidget(label_widget)
        else:
            layout.addWidget(label)

        text_box = QLineEdit(str(field_value) if field_value is not None else "")
        text_box.setFont(QFont("Formula1", 8))
        text_box.setMaximumWidth(300)  # Fixed width for text boxes
        text_box.textChanged.connect(
            lambda text, path=field_path: self._on_text_changed(path, text, field_info)
        )
        layout.addWidget(text_box)
        self.field_widgets[field_path] = text_box

        return label

    def _build_field_widget_radio_button(self,
                                         layout: QVBoxLayout,
                                         description: str,
                                         field_value: str,
                                         field_path: str,
                                         ui_config: dict,
                                         container: QWidget,
                                         ext_info: Optional[str] = None
                                         ) -> Optional[QLabel]:
        label = QLabel(description)
        label.setFont(QFont("Roboto", 10))
        label.setTextFormat(Qt.TextFormat.RichText)  # Enable rich text for highlighting

        if ext_info:
            label_widget = self._wrap_widget_with_info_icons(label, ext_info)
            layout.addWidget(label_widget)
        else:
            layout.addWidget(label)

        options = ui_config.get("options", [])
        if not options:
            self.parent_window.warning_log(f"No options provided for radio_buttons field {field_path}")
            return None

        radio_container = QWidget()
        radio_layout = QHBoxLayout()
        radio_layout.setContentsMargins(0, 0, 0, 0)
        radio_layout.setSpacing(16)

        button_group = QButtonGroup(container)

        for option in options:
            radio_btn = QRadioButton(str(option))
            radio_btn.setFont(QFont("Roboto", 10))

            if option == field_value:
                radio_btn.setChecked(True)

            radio_btn.toggled.connect(
                lambda checked, opt=option, path=field_path:
                self._on_radio_changed(path, opt, checked)
            )

            button_group.addButton(radio_btn)
            radio_layout.addWidget(radio_btn)

        radio_layout.addStretch()
        radio_container.setLayout(radio_layout)
        layout.addWidget(radio_container)

        self.field_widgets[field_path] = button_group

        return label

    def _build_dict_field(self,
                          field_name: str,
                          field_value: Dict[str, Any],
                          field_path: str,
                          field_info: FieldInfo) -> Optional[QWidget]:
        """Build a widget for a dict field"""

        # Check if this is a reorderable collection
        collection_meta = ReorderableCollection(field_info)

        if collection_meta.is_reorderable:
            # Build reorderable group for the dict
            return self._build_reorderable_dict_group(field_name, field_value, field_path, field_info)
        # Just show the dict items
        group_box = QGroupBox(field_info.description or field_name)
        # Track for search
        self._register_searchable(
            group_box,
            field_info.description or field_name,
            field_name
        )
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        for dict_key, dict_value in field_value.items():
            if isinstance(dict_value, BaseModel):
                item_widget = self._build_dict_item(dict_key, dict_value, field_path)
                layout.addWidget(item_widget)

        group_box.setLayout(layout)
        return group_box

    def _build_reorderable_view(self,
                           field_name: str,
                           field_value: BaseModel,
                           field_path: str,
                           field_info: FieldInfo
                           ) -> QWidget:
        """Build a collapsible nested page"""
        group_box = QGroupBox(field_info.description or field_name)
        # Track for search
        self._register_searchable(
            group_box,
            field_info.description or field_name,
            field_name
        )
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Add fields from nested model
        for nested_field_name, nested_field_info in type(field_value).model_fields.items():
            if not self._is_field_visible(nested_field_info):
                continue

            nested_value = getattr(field_value, nested_field_name)
            nested_path = f"{field_path}.{nested_field_name}"

            # Check if nested value is a dict
            if isinstance(nested_value, dict):
                # Check if it's a reorderable collection
                collection_meta = ReorderableCollection(nested_field_info)

                if collection_meta.is_reorderable:
                    # Build reorderable group for the dict
                    dict_widget = self._build_reorderable_dict_group(
                        nested_field_name, nested_value, nested_path, nested_field_info
                    )
                    layout.addWidget(dict_widget)
                else:
                    # Just show the dict items
                    for dict_key, dict_value in nested_value.items():
                        if isinstance(dict_value, BaseModel):
                            item_widget = self._build_dict_item(dict_key, dict_value, nested_path)
                            layout.addWidget(item_widget)
            elif isinstance(nested_value, BaseModel):
                # Nested model
                widget = self._build_nested_group(nested_field_name, nested_value, nested_path, nested_field_info)
                layout.addWidget(widget)
            else:
                # Simple field
                widget = self._build_field_widget(nested_field_name, nested_value, nested_path, nested_field_info)
                if widget:
                    layout.addWidget(widget)

        group_box.setLayout(layout)
        return group_box

    def _build_nested_group(self,
                            field_name: str,
                            field_value: BaseModel,
                            field_path: str,
                            field_info: FieldInfo
                            ) -> QWidget:
        """Build a nested group of fields"""
        group_box = QGroupBox(field_info.description or field_name)
        # Track for search
        self._register_searchable(
            group_box,
            field_info.description or field_name,
            field_name
        )
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Add fields from nested model
        for nested_field_name, nested_field_info in type(field_value).model_fields.items():
            if not self._is_field_visible(nested_field_info):
                continue

            nested_value = getattr(field_value, nested_field_name)
            nested_path = f"{field_path}.{nested_field_name}"

            # Check if it's another nested model
            if isinstance(nested_value, BaseModel):
                widget = self._build_nested_group(nested_field_name, nested_value, nested_path, nested_field_info)
            elif isinstance(nested_value, dict):
                widget = self._build_dict_field(nested_field_name, nested_value, nested_path, nested_field_info)
            else:
                widget = self._build_field_widget(nested_field_name, nested_value, nested_path, nested_field_info)

            if widget:
                layout.addWidget(widget)

        group_box.setLayout(layout)
        return group_box

    def _build_group_box(self,
                        field_name: str,
                        field_value: BaseModel,
                        field_path: str,
                        field_info: FieldInfo
                        ) -> QWidget:
        """Build a group box - handles reorderable collections and simple fields"""
        # Use a simple container instead of QGroupBox to avoid borders
        container = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(4)

        # Add title label
        title_label = QLabel(field_info.description or field_name)
        title_label.setFont(QFont("Roboto", 11, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #d4d4d4; background-color: transparent; padding: 4px 0px;")
        main_layout.addWidget(title_label)

        # Iterate through all fields in the BaseModel
        for nested_field_name, nested_field_info in type(field_value).model_fields.items():
            if not self._is_field_visible(nested_field_info):
                continue

            nested_value = getattr(field_value, nested_field_name)
            nested_path = f"{field_path}.{nested_field_name}"

            # Handle different field types
            if isinstance(nested_value, dict):
                collection_meta = ReorderableCollection(nested_field_info)
                if collection_meta.is_reorderable:
                    widget = self._build_reorderable_dict_group(
                        nested_field_name, nested_value, nested_path, nested_field_info
                    )
                    main_layout.addWidget(widget)
                else:
                    # Non-reorderable dict
                    widget = self._build_dict_field(nested_field_name, nested_value, nested_path, nested_field_info)
                    if widget:
                        main_layout.addWidget(widget)
            elif isinstance(nested_value, BaseModel):
                # Nested BaseModel
                widget = self._build_nested_group(nested_field_name, nested_value, nested_path, nested_field_info)
                main_layout.addWidget(widget)
            else:
                # Simple field (bool, int, str, etc.)
                widget = self._build_field_widget(nested_field_name, nested_value, nested_path, nested_field_info)
                if widget:
                    main_layout.addWidget(widget)

        container.setLayout(main_layout)
        return container

    def _build_reorderable_dict_group(self,
                                    _title: str,
                                    items_dict: Dict[str, BaseModel],
                                    field_path: str,
                                    field_info: FieldInfo) -> QWidget:
        """Build a group for a dict of items with optional reordering"""
        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Store metadata on the container
        collection_meta = ReorderableCollection(field_info)
        container.items_layout = layout
        container.field_path = field_path
        container.items_dict = items_dict
        container.collection_meta = collection_meta

        sorted_items = collection_meta.get_sorted_all_items(items_dict)

        # Check if this is truly reorderable (has position field)
        is_truly_reorderable = collection_meta.is_reorderable and any(
            hasattr(item, collection_meta.position_field)
            for _, item in sorted_items
        )

        for item_name, item_settings in sorted_items:
            if is_truly_reorderable:
                # Build with up/down buttons and frame
                item_row = self._build_reorderable_item_row(
                    item_name, item_settings, field_path, items_dict, container, collection_meta
                )
            else:
                # Build simple checkbox without frame
                item_row = self._build_simple_item_row(
                    item_name, item_settings, field_path, collection_meta
                )
            layout.addWidget(item_row)

        container.setLayout(layout)

        # Store reference for reordering
        self.field_widgets[f"{field_path}_items_container"] = container

        return container

    def _build_simple_item_row(self,
                            item_name: str,
                            item_settings: BaseModel,
                            parent_path: str,
                            collection_meta: ReorderableCollection) -> QWidget:
        """Build a simple row for a non-reorderable item (just checkbox, no frame)"""
        row_widget = QWidget()

        # Store metadata on the widget
        row_widget.item_key = item_name
        row_widget.item_settings = item_settings

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Enabled checkbox
        item_path = f"{parent_path}.{item_name}"
        enabled_path = f"{item_path}.{collection_meta.enabled_field}"
        enabled_cb = QCheckBox(item_name.replace("_", " ").title())
        enabled_cb.setFont(QFont("Roboto", 10))
        enabled_cb.setChecked(collection_meta.get_enabled(item_settings))
        enabled_cb.stateChanged.connect(
            lambda state, path=enabled_path: self._on_field_changed(path, state == Qt.CheckState.Checked.value)
        )
        self.field_widgets[enabled_path] = enabled_cb
        layout.addWidget(enabled_cb)

        layout.addStretch()

        row_widget.setLayout(layout)
        return row_widget

    def _build_dict_item(self, key: str, value: BaseModel, parent_path: str) -> QWidget:
        """Build a widget for a dict item"""
        item_path = f"{parent_path}.{key}"

        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Add a label for the key
        key_label = QLabel(key.replace("_", " ").title())
        key_label.setFont(QFont("Exo 2", 10, QFont.Weight.Bold))
        layout.addWidget(key_label)

        # Add fields from the value
        for field_name, field_info in type(value).model_fields.items():
            if not self._is_field_visible(field_info):
                continue

            field_value = getattr(value, field_name)
            field_path = f"{item_path}.{field_name}"

            widget = self._build_field_widget(field_name, field_value, field_path, field_info)
            if widget:
                layout.addWidget(widget)

        container.setLayout(layout)
        return container

    def _build_reorderable_item_row(self,
                                    item_name: str,
                                    item_settings: BaseModel,
                                    parent_path: str,
                                    items_dict: Dict[str, BaseModel],
                                    items_container: QWidget,
                                    collection_meta: ReorderableCollection) -> QWidget:
        """Build a row for a reorderable item"""
        row_widget = QFrame()
        row_widget.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
        row_widget.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #3e3e3e;
                border-radius: 4px;
                padding: 4px;
            }
            QCheckBox {
                background-color: transparent;
            }
        """)

        # Store metadata on the widget
        row_widget.item_key = item_name
        row_widget.item_settings = item_settings

        layout = QHBoxLayout()
        layout.setContentsMargins(8, 4, 8, 4)

        # Enabled checkbox
        item_path = f"{parent_path}.{item_name}"
        enabled_path = f"{item_path}.{collection_meta.enabled_field}"
        enabled_cb = QCheckBox(item_name.replace("_", " ").title())
        enabled_cb.setFont(QFont("Exo 2", 10))
        enabled_cb.setChecked(collection_meta.get_enabled(item_settings))
        enabled_cb.stateChanged.connect(
            lambda state, path=enabled_path: self._on_field_changed(path, state == Qt.CheckState.Checked.value)
        )
        self.field_widgets[enabled_path] = enabled_cb
        layout.addWidget(enabled_cb)

        layout.addStretch()

        # Up/Down buttons
        up_btn = QPushButton()
        up_btn.setIcon(self.icons_dict['arrow-up'])
        up_btn.setFixedSize(32, 28)
        up_btn.clicked.connect(
            lambda: self._move_item_up(item_name, items_dict, items_container, collection_meta)
        )
        layout.addWidget(up_btn)

        down_btn = QPushButton()
        down_btn.setIcon(self.icons_dict['arrow-down'])
        down_btn.setFixedSize(32, 28)
        down_btn.clicked.connect(
            lambda: self._move_item_down(item_name, items_dict, items_container, collection_meta)
        )
        layout.addWidget(down_btn)

        row_widget.setLayout(layout)
        return row_widget

    def _move_item_up(self,
                    item_name: str,
                    items_dict: Dict[str, BaseModel],
                    items_container: QWidget,
                    collection_meta: ReorderableCollection):
        """Move an item up in ordering"""
        current_item = items_dict[item_name]

        current_position = collection_meta.get_position(current_item)
        if current_position == 1:
            return

        # Find item with position - 1
        target_position = current_position - 1
        for _, other_item in items_dict.items():
            if collection_meta.get_position(other_item) == target_position:
                # Swap positions
                collection_meta.set_position(other_item, current_position)
                collection_meta.set_position(current_item, target_position)
                self._reorder_item_widgets(items_container, items_dict, collection_meta)
                self.parent_window.debug_log(f"Moved item {item_name} up to position {target_position}")
                break

    def _move_item_down(self,
                        item_name: str,
                        items_dict: Dict[str, BaseModel],
                        items_container: QWidget,
                        collection_meta: ReorderableCollection):
        """Move an item down in ordering"""
        current_item = items_dict[item_name]

        current_position = collection_meta.get_position(current_item)
        max_position = max(
            collection_meta.get_position(item)
            for item in items_dict.values()
        )
        if current_position == max_position:
            return

        # Find item with position + 1
        target_position = current_position + 1
        for other_item in items_dict.values():
            if collection_meta.get_position(other_item) == target_position:
                # Swap positions
                collection_meta.set_position(other_item, current_position)
                collection_meta.set_position(current_item, target_position)
                self._reorder_item_widgets(items_container, items_dict, collection_meta)
                self.parent_window.debug_log(f"Moved item {item_name} down to position {target_position}")
                break

    def _reorder_item_widgets(self,
                              items_container: QWidget,
                              _items_dict: Dict[str, BaseModel],
                              collection_meta: ReorderableCollection):
        """Reorder the item widgets in the layout based on their positions with animation"""
        layout: QVBoxLayout = items_container.items_layout

        # Get all reorderable item widgets from the layout with their current positions
        widgets_with_positions: List[Tuple[QFrame, int, int]] = []
        for i in range(layout.count()):
            widget = layout.itemAt(i).widget()
            if widget and hasattr(widget, 'item_key') and hasattr(widget, 'item_settings'):
                current_y = widget.pos().y()
                # Get the position from the item's settings
                target_position = collection_meta.get_position(widget.item_settings)
                widgets_with_positions.append((widget, current_y, target_position))

        # Sort by target position to get the new order
        widgets_with_positions.sort(key=lambda x: x[2])

        # Calculate target Y positions (based on layout spacing and widget height)
        spacing = layout.spacing()
        target_y = 0
        widget_positions: List[Tuple[QFrame, int, int]] = []

        for widget, current_y, target_position in widgets_with_positions:
            widget_positions.append((widget, current_y, target_y))
            target_y += widget.height() + spacing

        # Create animation group
        animation_group = QParallelAnimationGroup(items_container)

        # Remove all widgets from layout temporarily
        for widget, _, _ in widget_positions:
            layout.removeWidget(widget)

        # Add widgets back in new order
        for widget, _, _ in widget_positions:
            layout.addWidget(widget)

        # Force layout update to get new positions
        layout.update()
        items_container.update()

        # Create animations for each widget that needs to move
        for widget, old_y, new_y in widget_positions:
            if old_y != new_y:
                # Get actual geometry positions
                start_pos = widget.pos()

                # Create position animation
                animation = QPropertyAnimation(widget, b"pos")
                animation.setDuration(250)  # 250ms animation
                animation.setStartValue(QPoint(start_pos.x(), old_y))
                animation.setEndValue(QPoint(start_pos.x(), new_y))
                animation.setEasingCurve(QEasingCurve.Type.OutCubic)

                animation_group.addAnimation(animation)

        # Start all animations
        if animation_group.animationCount() > 0:
            animation_group.start()

    # -------------------------------------- EVENT HANDLERS & UTILITIES ------------------------------------------------

    def _on_field_changed(self, field_path: str, value: Any):
        """Handle field value change"""
        try:
            self._set_nested_value(self.working_settings, field_path, value)
            self.parent_window.debug_log(f"Field {field_path} changed to {value}")
        except Exception as e: # pylint: disable=broad-exception-caught
            self.parent_window.error_log(f"Error updating field {field_path}: {e}")

    def _on_slider_changed(self, field_path: str, value: int, label: QLabel):
        # find field_info from path
        field_info = self._get_field_info_from_path(field_path)
        ui_config = (field_info.json_schema_extra or {}).get("ui", {})

        if ui_config.get("convert") == "percent":
            label.setText(f"{value}%")
            new_value = value / 100.0           # convert percent -> multiplier
        else:
            label.setText(str(value))
            new_value = value

        self._on_field_changed(field_path, new_value)

    def _get_field_info_from_path(self, path: str) -> FieldInfo:
        parts = path.split(".")
        model = self.working_settings
        for p in parts[:-1]:
            model = getattr(model, p)
        return type(model).model_fields[parts[-1]]

    def _on_text_changed(self, field_path: str, text: str, field_info: FieldInfo):
        """Handle text box change with type conversion that supports Optional types."""
        try:
            # Type may be optional
            annotation = field_info.annotation

            # Unwrap Optional[T]
            origin = get_origin(annotation)
            if origin is Union:
                args = get_args(annotation)
                if len(args) == 2 and type(None) in args:
                    # Optional[T]
                    annotation = args[0] if args[0] is not type(None) else args[1]

            # Convert according to actual type
            if annotation is int:
                value = int(text) if text else None
            elif annotation is float:
                value = float(text) if text else None
            else:
                value = text or None

            self._on_field_changed(field_path, value)
        except ValueError:
            self.parent_window.warning_log(f"Invalid value for {field_path}: {text}")

    def _set_nested_value(self, obj: Any, path: str, value: Any):
        """Set a nested value using dot-notation path"""
        parts = path.split(".")
        current = obj

        for part in parts[:-1]:
            if hasattr(current, part):
                current = getattr(current, part)
            elif isinstance(current, dict):
                current = current[part]
            else:
                raise AttributeError(f"Cannot access {part} in {type(current)}")

        final_attr = parts[-1]
        if hasattr(current, final_attr):
            setattr(current, final_attr, value)
        elif isinstance(current, dict):
            current[final_attr] = value
        else:
            raise AttributeError(f"Cannot set {final_attr} in {type(current)}")

    def _is_visible(self, model: BaseModel) -> bool:
        """Check if a model should be visible in UI"""
        if hasattr(type(model), 'ui_meta'):
            return type(model).ui_meta.get('visible', True)
        return True

    def _is_field_visible(self, field_info: Any) -> bool:
        """Check if a field should be visible in UI"""
        ui_meta = field_info.json_schema_extra or {}
        ui_config = ui_meta.get("ui", {})
        return ui_config.get("visible", True)

    def on_revert(self):
        """Reset settings to original values"""
        reply = QMessageBox.question(
            self,
            "Revert Changes",
            "Discard all unsaved changes and restore the last saved settings?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.working_settings = self.original_settings.model_copy(deep=True)
            self._populate_widgets_from_settings()
            self.parent_window.info_log("Settings reset to last saved values")

    def on_reset(self):
        """Reset settings to default values"""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to their factory default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.working_settings = PngSettings()
            self._populate_widgets_from_settings()
            self.parent_window.info_log("Settings reset to factory default values")

    def on_reset_section(self):
        """Reset only the currently selected settings section to default values"""
        current_row = self.category_list.currentRow()
        if current_row < 0 or current_row >= len(self.category_field_names):
            return

        category_name = self.category_field_names[current_row]
        display_name = self.category_names[current_row]

        reply = QMessageBox.question(
            self,
            "Reset Section to Defaults",
            f"Reset all settings in \"{display_name}\" to their factory default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Instantiate only the relevant section's model with its defaults
        section_type = self._get_field_info_from_path(category_name).annotation
        setattr(self.working_settings, category_name, section_type())
        self._populate_widgets_from_settings(category_name)
        self.parent_window.info_log(f'Settings section "{display_name}" reset to factory defaults')

    def _populate_widgets_from_settings(self, category_name: Optional[str] = None):
        """Update widgets from working_settings.

        Args:
            category_name: If given, only widgets whose field path starts with
                           ``category_name.`` are refreshed.  If None, all
                           widgets are refreshed.
        """
        prefix = f"{category_name}." if category_name else None
        for field_path, widget in self.field_widgets.items():
            if prefix and not field_path.startswith(prefix):
                continue
            try:
                value = self._get_nested_value(self.working_settings, field_path)

                if isinstance(widget, QCheckBox):
                    widget.setChecked(value)

                elif isinstance(widget, QButtonGroup):
                    for button in widget.buttons():
                        try:
                            btn_value = int(button.text())
                        except ValueError:
                            btn_value = button.text()
                        if btn_value == value:
                            button.setChecked(True)
                            break

                elif isinstance(widget, QSlider):
                    field_info = self._get_field_info_from_path(field_path)
                    ui_config = (field_info.json_schema_extra or {}).get("ui", {})
                    if ui_config.get("convert") == "percent":
                        widget.setValue(int(value * 100))
                    else:
                        widget.setValue(value)

                elif isinstance(widget, QLineEdit):
                    widget.setText(str(value) if value is not None else "")

            except Exception as e:  # pylint: disable=broad-exception-caught
                self.parent_window.debug_log(f"Could not update widget {field_path}: {e}")

    def _get_nested_value(self, obj: Any, path: str) -> Any:
        """Get a nested value using dot-notation path"""
        parts = path.split(".")
        current = obj

        for part in parts:
            if hasattr(current, part):
                current = getattr(current, part)
            elif isinstance(current, dict):
                current = current[part]
            else:
                raise AttributeError(f"Cannot access {part} in {type(current)}")

        return current

    def on_save(self):
        """Validate and save settings"""
        try:
            # Validate the working settings
            validated_settings = PngSettings.model_validate(self.working_settings.model_dump())
            diff = self.original_settings.diff(validated_settings)
            if not diff:
                self.parent_window.debug_log("Settings unchanged, not saving")
                return

            # Call the callback if provided
            self.parent_window.debug_log(f"Settings changed: {json.dumps(diff, indent=2)}")
            if self.on_settings_change:
                self.on_settings_change(validated_settings)

            # Update original_settings to the newly saved settings
            self.original_settings = validated_settings.model_copy(deep=True)
            self.parent_window.debug_log("Settings saved successfully")

        except ValidationError as e:
            # Format error messages in a user-friendly way
            error_lines = []
            for err in e.errors():
                # Convert location tuple to readable field path using descriptions
                # pylint: disable=unsupported-membership-test, unsubscriptable-object
                field_path_parts = []
                current_model = PngSettings
                for loc in err['loc']:
                    model_fields = current_model.model_fields
                    if str(loc) in model_fields:
                        field_info = current_model.model_fields[str(loc)]
                        field_path_parts.append(field_info.description)
                        # Update current_model for nested fields
                        if hasattr(field_info.annotation, 'model_fields'):
                            current_model = field_info.annotation
                    else:
                        field_path_parts.append(str(loc))

                field_path = " → ".join(field_path_parts)

                # Clean up the error message (remove "Value error, " prefix if present)
                msg = err['msg']
                if msg.startswith("Value error, "):
                    msg = msg[13:]  # Remove "Value error, " prefix
                error_lines.append(f"• {field_path}:\n  {msg}")

            error_msg = "\n\n".join(error_lines)
            QMessageBox.critical(
                self,
                "Validation Error",
                f"Please fix the following issues:\n\n{error_msg}"
            )
            self.parent_window.debug_log(f"Settings validation failed: {e}")

    def _has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes"""
        return self.original_settings.has_changed(self.working_settings)

    def reject(self):
        """Handle cancel/close with confirmation if there are unsaved changes"""
        if self._has_unsaved_changes():
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Are you sure you want to close without saving?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.No:
                return

        super().reject()

    def closeEvent(self, event: QCloseEvent):
        """Handle window close event (X button)"""
        if self._has_unsaved_changes():
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Are you sure you want to close without saving?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return

        event.accept()

    def _wrap_widget_with_info_icons(self, widget: QWidget, ext_info_list: List[str]) -> QWidget:
        """Add multiple ⓘ tooltip icons to the right of a widget, one for each ext_info item."""
        container = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        layout.addWidget(widget)

        # Add an info icon for each item in ext_info_list
        for tooltip_text in ext_info_list:
            info_label = QLabel("ⓘ")
            info_label.setToolTip(tooltip_text)
            info_label.setFixedWidth(20)
            info_label.setCursor(Qt.CursorShape.WhatsThisCursor)  # Change cursor on hover
            layout.addWidget(info_label)
        layout.addStretch()

        container.setLayout(layout)
        return container

    def _on_radio_changed(self, field_path: str, option: Any, checked: bool):
        """Handle radio button change"""
        if checked:
            self._on_field_changed(field_path, option)

    def _on_search_changed(self, search_text: str):
        """Filter visible settings based on search text, auto-expanding groups that contain matches."""
        search_text = search_text.lower().strip()

        # If search is empty, show all widgets and reset category labels
        if not search_text:
            for sw in self.searchable_widgets:
                sw.widget.setVisible(True)
                sw.apply_highlight("")  # Remove highlighting

            # Restore all collapsible groups to their natural (expanded) state
            for groups_in_category in self.collapsible_groups.values():
                for group_container in groups_in_category.values():
                    if group_container.is_collapsed:
                        group_container.is_collapsed = False
                        group_container.content_wrapper.setVisible(True)
                        group_container.toggle_label.setPixmap(self.icons_dict['caret-down'].pixmap(16, 16))

            # Reset category labels to original names and unhide all categories
            for i, category_name in enumerate(self.category_names):
                item = self.category_list.item(i)
                item.setText(category_name)
                item.setHidden(False)

            # Ensure stacked widget follows current selection
            current_row = self.category_list.currentRow()
            if current_row >= 0:
                self.stacked_widget.setCurrentIndex(current_row)
            elif self.category_list.count() > 0:
                # If no selection, select the first category
                self.category_list.setCurrentRow(0)
                self.stacked_widget.setCurrentIndex(0)
            return

        # Count visible items per category
        category_visible_counts: Dict[int, int] = {}

        # Hide/show widgets based on whether their description or field_name matches the search
        for sw in self.searchable_widgets:
            if sw.matches(search_text):
                sw.widget.setVisible(True)
                sw.apply_highlight(search_text)  # Apply highlighting
                # Count which category this widget belongs to
                if sw.category_index is not None:
                    category_visible_counts[sw.category_index] = (
                        category_visible_counts.get(sw.category_index, 0) + 1
                    )
            else:
                sw.widget.setVisible(False)
                sw.apply_highlight("")  # Remove highlighting from hidden widgets

        # Auto-expand any collapsible group that has at least one visible (matching) child
        for groups_in_category in self.collapsible_groups.values():
            for group_container in groups_in_category.values():
                content_layout = group_container.content_layout
                has_visible_child = any(
                    content_layout.itemAt(i).widget() is not None
                    and content_layout.itemAt(i).widget().isVisible()
                    for i in range(content_layout.count())
                )
                if has_visible_child and group_container.is_collapsed:
                    group_container.is_collapsed = False
                    group_container.content_wrapper.setVisible(True)
                    group_container.toggle_label.setPixmap(self.icons_dict['caret-down'].pixmap(16, 16))

        # Update category labels with counts and hide empty categories
        first_visible_category = None
        for i, category_name in enumerate(self.category_names):
            item = self.category_list.item(i)
            visible_count = category_visible_counts.get(i, 0)

            if visible_count > 0:
                # Show category with count
                item.setText(f"{category_name} ({visible_count})")
                item.setHidden(False)
                # Track the first visible category
                if first_visible_category is None:
                    first_visible_category = i
            else:
                # Hide empty category
                item.setHidden(True)

        # Adjust current category and stacked widget
        current_row = self.category_list.currentRow()
        if current_row < 0 or self.category_list.item(current_row).isHidden():
            if first_visible_category is not None:
                self.category_list.setCurrentRow(first_visible_category)
                self.stacked_widget.setCurrentIndex(first_visible_category)
            else:
                # No results: clear selection (stacked widget will show empty category content)
                self.category_list.setCurrentRow(-1)
