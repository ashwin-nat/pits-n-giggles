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

from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, List, Tuple
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QCheckBox,
    QLineEdit, QSlider, QLabel, QScrollArea, QWidget, QGroupBox,
    QListWidget, QStackedWidget, QMessageBox, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QParallelAnimationGroup
from PySide6.QtGui import QFont
from pydantic import BaseModel, ValidationError
from pydantic.fields import FieldInfo

from lib.config import PngSettings

if TYPE_CHECKING:
    from .main_window import PngLauncherWindow


class SettingsWindow(QDialog):
    """Dynamic settings window that builds UI from PngSettings schema"""

    def __init__(self,
                 parent_window: "PngLauncherWindow",
                 settings: PngSettings,
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

        # Track widgets for validation and updates
        self.field_widgets: Dict[str, Any] = {}

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
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Content area with list and stacked widget
        content_layout = QHBoxLayout()

        # Category list on the left
        self.category_list = QListWidget()
        self.category_list.setMaximumWidth(200)
        self.category_list.currentRowChanged.connect(self.on_category_changed)

        # Stacked widget for category content on the right
        self.stacked_widget = QStackedWidget()

        # Build categories
        for category_name, category_model in self.working_settings:
            if not self._is_visible(category_model):
                continue

            self.category_list.addItem(category_name)
            category_widget = self._build_category_content(category_name, category_model)
            self.stacked_widget.addWidget(category_widget)

        content_layout.addWidget(self.category_list)
        content_layout.addWidget(self.stacked_widget, stretch=1)

        main_layout.addLayout(content_layout)

        # Button bar
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self.on_reset)
        button_layout.addWidget(reset_btn)

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

    def _build_category_content(self, category_name: str, category_model: BaseModel) -> QScrollArea:
        """Build content for a settings category"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        # Category title
        title_label = QLabel(category_name)
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #d4d4d4; background-color: transparent;")
        layout.addWidget(title_label)

        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #3e3e3e;")
        layout.addWidget(separator)

        # Iterate through fields in the category
        for field_name, field_info in type(category_model).model_fields.items():
            if not self._is_field_visible(field_info):
                continue

            field_value = getattr(category_model, field_name)
            field_path = f"{category_name}.{field_name}"

            # Get UI metadata
            ui_meta = field_info.json_schema_extra or {}
            ui_config = ui_meta.get("ui", {})
            ui_type = ui_config.get("type", "text_box")

            # Handle complex types (nested BaseModel)
            if isinstance(field_value, BaseModel):
                if ui_type == "page":
                    # Nested page - create expandable section
                    widget = self._build_nested_page(field_name, field_value, field_path, field_info)
                    layout.addWidget(widget)
                elif ui_type == "group_box":
                    # Group box with reorderable items
                    widget = self._build_group_box(field_name, field_value, field_path, field_info)
                    layout.addWidget(widget)
                else:
                    # Default: treat as nested group
                    widget = self._build_nested_group(field_name, field_value, field_path, field_info)
                    layout.addWidget(widget)
            else:
                # Simple field
                widget = self._build_field_widget(field_name, field_value, field_path, field_info)
                if widget:
                    layout.addWidget(widget)

        layout.addStretch()
        content_widget.setLayout(layout)
        scroll.setWidget(content_widget)

        return scroll

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

        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        if ui_type == "check_box":
            # Checkbox
            checkbox = QCheckBox(description)
            checkbox.setChecked(field_value)
            checkbox.stateChanged.connect(
                lambda state, path=field_path: self._on_field_changed(path, state == Qt.CheckState.Checked.value)
            )
            self.field_widgets[field_path] = checkbox
            layout.addWidget(checkbox)

        elif ui_type == "slider":
            # Slider with label
            label = QLabel(description)
            layout.addWidget(label)

            slider_container = QWidget()
            slider_layout = QHBoxLayout()
            slider_layout.setContentsMargins(0, 0, 0, 0)

            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setMinimum(ui_config.get("min", 0))
            slider.setMaximum(ui_config.get("max", 100))
            slider.setValue(field_value)
            slider.setTickPosition(QSlider.TickPosition.TicksBelow)
            slider.setTickInterval(10)
            slider.setMaximumWidth(300)  # Fixed width for sliders

            value_label = QLabel(str(field_value))
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

        elif ui_type == "text_box":
            # Text box with label
            label = QLabel(description)
            layout.addWidget(label)

            text_box = QLineEdit(str(field_value))
            text_box.setMaximumWidth(300)  # Fixed width for text boxes
            text_box.textChanged.connect(
                lambda text, path=field_path: self._on_text_changed(path, text, field_info)
            )
            layout.addWidget(text_box)

            self.field_widgets[field_path] = text_box

        container.setLayout(layout)
        return container

    def _build_nested_page(self,
                           field_name: str,
                           field_value: BaseModel,
                           field_path: str,
                           field_info: FieldInfo
                           ) -> QWidget:
        """Build a collapsible nested page"""
        group_box = QGroupBox(field_info.description or field_name)
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Add fields from nested model
        for nested_field_name, nested_field_info in type(field_value).model_fields.items():
            if not self._is_field_visible(nested_field_info):
                continue

            nested_value = getattr(field_value, nested_field_name)
            nested_path = f"{field_path}.{nested_field_name}"

            # Check if nested value is a dict (like MFD pages)
            if isinstance(nested_value, dict):
                # This is the pages dict - handle specially
                nested_ui_meta = nested_field_info.json_schema_extra or {}
                nested_ui_config = nested_ui_meta.get("ui", {})
                nested_ui_type = nested_ui_config.get("type", "")

                if nested_ui_type == "group_box":
                    # Build reorderable group for the pages dict
                    pages_widget = self._build_pages_dict_group(nested_field_name, nested_value,
                                                                nested_path, field_value)
                    layout.addWidget(pages_widget)
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
        """Build a group box with reorderable items (for MFD pages, etc.)"""
        group_box = QGroupBox(field_info.description or field_name)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # For MfdSettings, we have a 'pages' dict
        if hasattr(field_value, 'pages') and isinstance(field_value.pages, dict):
            pages_widget = self._build_pages_dict_group("MFD Pages", field_value.pages, field_path, field_value)
            main_layout.addWidget(pages_widget)

        group_box.setLayout(main_layout)
        return group_box

    def _build_pages_dict_group(self,
                                _title: str,
                                pages_dict: Dict[str, BaseModel],
                                parent_path: str,
                                parent_model: BaseModel) -> QWidget:
        """Build a group for a dict of items with reordering"""
        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Store the layout reference for reordering
        container.items_layout = layout
        container.parent_path = parent_path
        container.parent_model = parent_model

        # Add each item in sorted order
        sorted_items = sorted(
            [(name, settings) for name, settings in pages_dict.items() if settings.enabled],
            key=lambda x: x[1].position
        )

        for item_name, item_settings in sorted_items:
            item_row = self._build_group_box_item_row(item_name, item_settings, parent_path, parent_model, container)
            layout.addWidget(item_row)

        container.setLayout(layout)

        # Store reference for reordering
        self.field_widgets[f"{parent_path}_items_container"] = container

        return container

    def _build_dict_item(self, key: str, value: BaseModel, parent_path: str) -> QWidget:
        """Build a widget for a dict item"""
        item_path = f"{parent_path}.{key}"

        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Add a label for the key
        key_label = QLabel(key.replace("_", " ").title())
        key_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
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

    def _build_group_box_item_row(self,
                                  item_name: str,
                                  item_settings: BaseModel,
                                  parent_path: str,
                                  parent_model: BaseModel,
                                  items_container: QWidget) -> QWidget:
        """Build a row for a reorderable group_box item"""
        row_widget = QFrame()
        row_widget.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
        row_widget.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #3e3e3e;
                border-radius: 4px;
                padding: 4px;
            }
        """)

        # Store metadata on the widget (generic item identifier and settings)
        row_widget.item_key = item_name
        row_widget.item_settings = item_settings

        layout = QHBoxLayout()
        layout.setContentsMargins(8, 4, 8, 4)

        # Enabled checkbox
        item_path = f"{parent_path}.pages.{item_name}"
        enabled_cb = QCheckBox(item_name.replace("_", " ").title())
        enabled_cb.setChecked(item_settings.enabled)
        enabled_cb.stateChanged.connect(
            lambda state, path=f"{item_path}.enabled": self._on_field_changed(path, state == Qt.CheckState.Checked.value)
        )
        self.field_widgets[f"{item_path}.enabled"] = enabled_cb
        layout.addWidget(enabled_cb)

        layout.addStretch()

        # Up/Down buttons
        up_btn = QPushButton("↑")
        up_btn.setFixedSize(32, 28)
        up_btn.clicked.connect(lambda: self._move_group_box_item_up(item_name, parent_path, parent_model, items_container))
        layout.addWidget(up_btn)

        down_btn = QPushButton("↓")
        down_btn.setFixedSize(32, 28)
        down_btn.clicked.connect(lambda: self._move_group_box_item_down(item_name, parent_path, parent_model, items_container))
        layout.addWidget(down_btn)

        row_widget.setLayout(layout)
        return row_widget

    def _move_group_box_item_up(self,
                                item_name: str,
                                _parent_path: str,
                                parent_model: BaseModel,
                                items_container: QWidget):
        """Move a group_box item up in ordering"""
        pages = parent_model.pages
        current_item = pages[item_name]

        if not current_item.enabled or current_item.position == 1:
            return

        # Find item with position - 1
        target_position = current_item.position - 1
        for other_name, other_item in pages.items():
            if other_item.enabled and other_item.position == target_position:
                # Swap positions
                other_item.position = current_item.position
                current_item.position = target_position
                self._reorder_group_box_item_widgets(items_container, parent_model)
                self.parent_window.debug_log(f"Moved item {item_name} up to position {target_position}")
                break

    def _move_group_box_item_down(self,
                                  item_name: str,
                                  _parent_path: str,
                                  parent_model: BaseModel,
                                  items_container: QWidget):
        """Move a group_box item down in ordering"""
        pages = parent_model.pages
        current_item = pages[item_name]

        if not current_item.enabled:
            return

        # Find max position
        max_position = max(p.position for p in pages.values() if p.enabled)
        if current_item.position == max_position:
            return

        # Find item with position + 1
        target_position = current_item.position + 1
        for other_name, other_item in pages.items():
            if other_item.enabled and other_item.position == target_position:
                # Swap positions
                other_item.position = current_item.position
                current_item.position = target_position
                self._reorder_group_box_item_widgets(items_container, parent_model)
                self.parent_window.debug_log(f"Moved item {item_name} down to position {target_position}")
                break

    def _reorder_group_box_item_widgets(self, items_container: QWidget, _parent_model: BaseModel):
        """Reorder the group_box item widgets in the layout based on their positions with animation"""
        layout: QVBoxLayout = items_container.items_layout

        # Get all reorderable item widgets from the layout with their current positions
        widgets_with_positions: List[Tuple[QFrame, int, int]] = []
        for i in range(layout.count()):
            widget = layout.itemAt(i).widget()
            if widget and hasattr(widget, 'item_key') and hasattr(widget, 'item_settings'):
                current_y = widget.pos().y()
                # Get the position from the item's settings
                target_position = widget.item_settings.position
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

    def _rebuild_pages_group(self, _parent_path: str, _parent_model: BaseModel):
        """Rebuild the pages group after reordering"""
        # Find the parent widget in the stacked widget
        current_category_idx = self.category_list.currentRow()
        if current_category_idx < 0:
            return

        # Get the scroll area
        scroll_area = self.stacked_widget.widget(current_category_idx)
        if not isinstance(scroll_area, QScrollArea):
            return

        # Get the content widget
        content_widget = scroll_area.widget()
        if not content_widget:
            return

        # Find and rebuild the pages container
        # This is a simplified approach - we'll rebuild the entire category
        category_name = self.category_list.item(current_category_idx).text()
        category_model = getattr(self.working_settings, category_name)

        # Rebuild the category content
        new_content = self._build_category_content(category_name, category_model)
        scroll_area.setWidget(new_content.widget())

    def _on_field_changed(self, field_path: str, value: Any):
        """Handle field value change"""
        try:
            self._set_nested_value(self.working_settings, field_path, value)
            self.parent_window.debug_log(f"Field {field_path} changed to {value}")
        except Exception as e:
            self.parent_window.error_log(f"Error updating field {field_path}: {e}")

    def _on_slider_changed(self, field_path: str, value: int, label: QLabel):
        """Handle slider value change"""
        label.setText(str(value))
        self._on_field_changed(field_path, value)

    def _on_text_changed(self, field_path: str, text: str, field_info: FieldInfo):
        """Handle text box change with type conversion"""
        try:
            # Try to convert to appropriate type
            annotation = field_info.annotation
            if annotation == int:
                value = int(text) if text else 0
            elif annotation == float:
                value = float(text) if text else 0.0
            else:
                value = text

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

    def on_reset(self):
        """Reset settings to original values"""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to their original values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.working_settings = self.original_settings.model_copy(deep=True)
            self._update_all_widgets()
            self.parent_window.info_log("Settings reset to original values")

    def _update_all_widgets(self):
        """Update all widgets from working_settings"""
        for field_path, widget in self.field_widgets.items():
            try:
                value = self._get_nested_value(self.working_settings, field_path)

                if isinstance(widget, QCheckBox):
                    widget.setChecked(value)
                elif isinstance(widget, QSlider):
                    widget.setValue(value)
                elif isinstance(widget, QLineEdit):
                    widget.setText(str(value))
            except Exception as e:
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
            if not self.original_settings.has_changed(validated_settings):
                self.parent_window.debug_log("Settings unchanged, not saving")
                return

            # Call the callback if provided
            if self.on_settings_change:
                self.on_settings_change(validated_settings)

            self.parent_window.info_log("Settings saved successfully")
            self.accept()

        except ValidationError as e:
            error_msg = "\n".join([f"• {err['loc']}: {err['msg']}" for err in e.errors()])
            QMessageBox.critical(
                self,
                "Validation Error",
                f"Settings validation failed:\n\n{error_msg}"
            )
            self.parent_window.error_log(f"Settings validation failed: {e}")
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save settings:\n\n{str(e)}"
            )
            self.parent_window.error_log(f"Failed to save settings: {e}")
