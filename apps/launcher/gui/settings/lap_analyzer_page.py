# MIT License
#
# Copyright (c) [2026] [Ashwin Natarajan]
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

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from pydantic import BaseModel
from pydantic.fields import FieldInfo
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (QCheckBox, QFrame, QHBoxLayout, QLabel,
                               QPushButton, QScrollArea, QVBoxLayout, QWidget)

from lib.config import (ENTROPY_BYTES_PER_SAMPLE, MANDATORY_BYTES_PER_SAMPLE,
                        SENSOR_GROUP_INFO, LapAnalyzerSensorSettings,
                        SensorEntropy, SensorGroup, SensorPreset)

from .collapsible_group import HeaderCollapsibleGroup

if TYPE_CHECKING:
    from .settings import SettingsWindow

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

SAMPLE_RATE_HZ = 60
SESSION_SECONDS = 45 * 60
FULL_GRID_CARS = 22

PUBLIC_ONLY_TOOLTIP = ("Public only: other drivers' values read zero if their in-game telemetry is set to "
                       "Restricted. Your own car is always recorded.")
MIXED_GROUP_TOOLTIP = "Some sensors in this group are Public only (marked below)"

# Partial state is a horizontal band, so it reads differently from the solid checked fill
_PARTIAL_INDICATOR_STYLE = (
    "QCheckBox::indicator:indeterminate {"
    " border-color: #0e639c;"
    " background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,"
    " stop:0 #1e1e1e, stop:0.3 #1e1e1e, stop:0.31 #0e639c, stop:0.69 #0e639c, stop:0.7 #1e1e1e, stop:1 #1e1e1e);"
    " }"
)

# -------------------------------------- HELPERS -----------------------------------------------------------------------

# Read once here, because pylint can't see through pydantic's model_fields at every use
_SENSOR_FIELDS: Dict[str, FieldInfo] = dict(LapAnalyzerSensorSettings.model_fields)

def _sensor_meta(field: str) -> Dict[str, Any]:
    return _SENSOR_FIELDS[field].json_schema_extra["sensor"]

def _format_size(num_bytes: float) -> str:
    return f"~{num_bytes / 1_000_000:.1f} MB"

def estimate_bytes_per_car(enabled_fields: List[str]) -> float:
    """Estimated .pngt size of one car's session, given the enabled sensor fields."""
    per_sample = MANDATORY_BYTES_PER_SAMPLE + sum(
        ENTROPY_BYTES_PER_SAMPLE[SensorEntropy(_sensor_meta(f)["entropy"])] for f in enabled_fields)
    return per_sample * SAMPLE_RATE_HZ * SESSION_SECONDS

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class GroupCheckBox(QCheckBox):
    """Tri-state for display only: a user click always goes to all-on or all-off, never to partial."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setTristate(True)
        self.setStyleSheet(_PARTIAL_INDICATOR_STYLE)

    def nextCheckState(self) -> None:
        if self.checkState() == Qt.CheckState.Checked:
            self.setCheckState(Qt.CheckState.Unchecked)
        else:
            self.setCheckState(Qt.CheckState.Checked)


class LapAnalyzerPage(QWidget):
    """Settings page for the LapAnalyzer category: the plain fields, preset buttons, sensors grouped
    under tri-state checkboxes in their own scroll area, and a live .pngt size estimate.

    Always reads settings_window.working_settings, never a cached model, because revert and reset
    replace that object.
    """

    def __init__(self,
                 category_name: str,
                 category_model: BaseModel,
                 settings_window: "SettingsWindow") -> None:
        super().__init__(settings_window)
        self._category_name = category_name
        self._settings_window = settings_window
        self._icons: Dict[str, QIcon] = settings_window.icons_dict

        # field name -> leaf checkbox, and group name -> (group checkbox, [field names])
        self._leaf_checkboxes: Dict[str, QCheckBox] = {}
        self._group_boxes: Dict[str, Tuple[GroupCheckBox, List[str]]] = {}
        self._sensor_groups_widgets: List[HeaderCollapsibleGroup] = []
        self._bulk_updating = False

        # Same registry shape the generic pages use, so a search match expands the group holding it.
        # The settings window files it under this category's index.
        self.collapsibles: Dict[str, HeaderCollapsibleGroup] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        field_info = settings_window._get_field_info_from_path(category_name)
        title_label = QLabel(field_info.description or category_name)
        title_label.setFont(QFont("Roboto", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #d4d4d4; background-color: transparent;")
        layout.addWidget(title_label)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #3e3e3e;")
        layout.addWidget(separator)

        collapsibles = self.collapsibles
        general = self._build_general_group(category_model)
        collapsibles["General"] = general
        layout.addWidget(general)
        layout.addLayout(self._build_presets_row())

        sensor_groups: Dict[str, HeaderCollapsibleGroup] = {}
        sensors_layout = QVBoxLayout()
        sensors_layout.setContentsMargins(0, 0, 0, 0)
        sensors_layout.setSpacing(8)
        for group in self._sensor_groups():
            sensor_groups[group.value] = self._build_sensor_group(group)
            sensors_layout.addWidget(sensor_groups[group.value])
        sensors_layout.addStretch()
        self._sensor_groups_widgets = list(sensor_groups.values())
        collapsibles.update(sensor_groups)

        layout.addLayout(self._build_sensors_toolbar())
        layout.addWidget(self._build_sensors_scroll_area(sensors_layout), stretch=1)

        self._estimate_label = QLabel()
        self._estimate_label.setFont(QFont("Roboto", 10))
        self._estimate_label.setWordWrap(True)
        layout.addWidget(self._estimate_label)

        self.refresh()

    # ----------------------------------------------- PUBLIC ----------------------------------------------------------

    def refresh(self) -> None:
        """Recompute every derived widget. Leaf checkboxes are refreshed by the settings window itself."""
        for group_name in self._group_boxes:
            self._update_group_state(group_name)
        self._update_estimate()

    def on_field_changed(self, field_path: str) -> None:
        """Called by the settings window after any field changed, to keep derived widgets current."""
        if not self._bulk_updating and field_path.startswith(f"{self._category_name}."):
            self.refresh()

    # ----------------------------------------------- BUILDERS --------------------------------------------------------

    @property
    def _settings(self) -> Any:
        return getattr(self._settings_window.working_settings, self._category_name)

    @staticmethod
    def _sensor_groups() -> List[SensorGroup]:
        """The groups in use, alphabetical"""
        return sorted({SensorGroup(_sensor_meta(f)["group"]) for f in _SENSOR_FIELDS},
                      key=lambda g: g.value)

    def _build_general_group(self, category_model: BaseModel) -> HeaderCollapsibleGroup:
        general = HeaderCollapsibleGroup("General", self._icons, parent=self)
        fields: List[Tuple[str, Any, FieldInfo]] = []
        for field_name, field_info in type(category_model).model_fields.items():
            field_value = getattr(category_model, field_name)
            if isinstance(field_value, BaseModel) or not self._settings_window._is_field_visible(field_info):
                continue
            fields.append((field_name, field_value, field_info))
        self._settings_window._render_fields(fields, self._category_name, general.content_layout)
        return general

    def _build_presets_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)
        presets_label = QLabel("Presets:")
        presets_label.setFont(QFont("Roboto", 10))
        row.addWidget(presets_label)
        for preset in SensorPreset:
            button = QPushButton(preset.value)
            button.clicked.connect(lambda _checked=False, p=preset: self._apply_preset(p))
            row.addWidget(button)
        row.addStretch()
        return row

    def _build_sensors_toolbar(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)
        title = QLabel("Sensors")
        title.setFont(QFont("Roboto", 10, QFont.Weight.Bold))
        row.addWidget(title)
        row.addStretch()
        for text, collapsed in (("Expand all", False), ("Collapse all", True)):
            button = QPushButton(text)
            button.clicked.connect(lambda _checked=False, c=collapsed: self._set_all_collapsed(c))
            row.addWidget(button)
        return row

    @staticmethod
    def _build_sensors_scroll_area(sensors_layout: QVBoxLayout) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setMinimumHeight(150)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #3e3e3e; border-radius: 4px; }"
                             "QScrollBar:vertical { width: 12px; }")
        body = QWidget()
        body.setLayout(sensors_layout)
        sensors_layout.setContentsMargins(8, 8, 8, 8)
        scroll.setWidget(body)
        return scroll

    def _build_sensor_group(self, group: SensorGroup) -> HeaderCollapsibleGroup:
        fields = sorted((f for f in _SENSOR_FIELDS if _sensor_meta(f)["group"] == group.value),
                        key=lambda f: _SENSOR_FIELDS[f].description)
        restricted = [bool(_sensor_meta(f)["restricted"]) for f in fields]

        header_extra = QWidget()
        header_extra.setStyleSheet("background: transparent;")
        header_layout = QHBoxLayout(header_extra)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)
        if all(restricted):
            header_layout.addWidget(self._make_public_only_icon(PUBLIC_ONLY_TOOLTIP))
        elif any(restricted):
            header_layout.addWidget(self._make_public_only_icon(MIXED_GROUP_TOOLTIP))
        if group in SENSOR_GROUP_INFO:
            header_layout.addWidget(self._make_info_label(SENSOR_GROUP_INFO[group]))
        group_checkbox = GroupCheckBox()
        group_checkbox.clicked.connect(lambda _checked=False, g=group.value: self._on_group_clicked(g))
        header_layout.addWidget(group_checkbox)

        container = HeaderCollapsibleGroup(group.value, self._icons, header_extra=header_extra, parent=self)
        self._group_boxes[group.value] = (group_checkbox, fields)
        for field in fields:
            container.content_layout.addWidget(self._build_sensor_leaf(field))
        return container

    def _build_sensor_leaf(self, field: str) -> QWidget:
        field_info = _SENSOR_FIELDS[field]
        meta = _sensor_meta(field)
        field_path = f"{self._category_name}.Sensors.{field}"
        description = field_info.description or field

        checkbox = QCheckBox()
        checkbox.setChecked(bool(getattr(self._settings.Sensors, field)))
        checkbox.toggled.connect(lambda checked, p=field_path: self._settings_window._on_field_changed(p, checked))
        self._settings_window.field_widgets[field_path] = checkbox
        self._leaf_checkboxes[field] = checkbox

        label = QLabel(description)
        label.setFont(QFont("Roboto", 10))
        label.setTextFormat(Qt.TextFormat.RichText)  # needed for search highlighting
        if meta["info"]:
            label.setToolTip(meta["info"])

        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.addWidget(checkbox)
        row_layout.addWidget(label)
        if meta["restricted"]:
            row_layout.addWidget(self._make_public_only_icon(PUBLIC_ONLY_TOOLTIP))

        leaf: QWidget = row
        if meta["info"]:
            leaf = self._settings_window._wrap_widget_with_info_icons(row, [meta["info"]])
        else:
            row_layout.addStretch()
        self._settings_window._register_searchable(leaf, description, field, label)
        return leaf

    def _make_public_only_icon(self, tooltip: str) -> QLabel:
        icon_label = QLabel()
        icon_label.setPixmap(self._icons["public-only"].pixmap(16, 16))
        icon_label.setFixedSize(16, 16)
        icon_label.setToolTip(tooltip)
        icon_label.setStyleSheet("background: transparent; border: none;")
        return icon_label

    @staticmethod
    def _make_info_label(tooltip: str) -> QLabel:
        info_label = QLabel("ⓘ")
        info_label.setToolTip(tooltip)
        info_label.setStyleSheet("background: transparent; border: none;")
        info_label.setCursor(Qt.CursorShape.WhatsThisCursor)
        return info_label

    # ----------------------------------------------- BEHAVIOUR -------------------------------------------------------

    def _set_leaves(self, targets: Dict[str, bool]) -> None:
        """Set many leaf checkboxes, refreshing the derived widgets once instead of once per leaf."""
        self._bulk_updating = True
        try:
            for field, checked in targets.items():
                self._leaf_checkboxes[field].setChecked(checked)
        finally:
            self._bulk_updating = False
        self.refresh()

    def _apply_preset(self, preset: SensorPreset) -> None:
        self._set_leaves({field: preset.value in _sensor_meta(field)["presets"] for field in self._leaf_checkboxes})

    def _set_all_collapsed(self, collapsed: bool) -> None:
        for group in self._sensor_groups_widgets:
            group.set_collapsed(collapsed)

    def _on_group_clicked(self, group_name: str) -> None:
        group_checkbox, fields = self._group_boxes[group_name]
        check = group_checkbox.checkState() == Qt.CheckState.Checked
        self._set_leaves({field: check for field in fields})

    def _update_group_state(self, group_name: str) -> None:
        group_checkbox, fields = self._group_boxes[group_name]
        ticked = sum(1 for f in fields if self._leaf_checkboxes[f].isChecked())
        if ticked == 0:
            state = Qt.CheckState.Unchecked
        elif ticked == len(fields):
            state = Qt.CheckState.Checked
        else:
            state = Qt.CheckState.PartiallyChecked
        group_checkbox.blockSignals(True)
        group_checkbox.setCheckState(state)
        group_checkbox.blockSignals(False)

    def _update_estimate(self) -> None:
        settings = self._settings
        enabled = [f for f in _SENSOR_FIELDS if getattr(settings.Sensors, f)]
        any_session_type = (settings.record_in_race or settings.record_in_quali
                            or settings.record_in_fp or settings.record_in_tt)
        if not settings.enable or not enabled or not any_session_type:
            text = "Estimated size: nothing will be recorded"
        else:
            per_car = estimate_bytes_per_car(enabled)
            full_grid = _format_size(per_car * FULL_GRID_CARS)
            if settings.record_other_cars:
                text = f"Estimated size per 45-min session: {full_grid} ({FULL_GRID_CARS} cars)"
            elif settings.record_in_spectator_mode:
                text = (f"Estimated size per 45-min session: driving {_format_size(per_car)} (your car), "
                        f"spectating {full_grid} ({FULL_GRID_CARS} cars)")
            else:
                text = f"Estimated size per 45-min session: {_format_size(per_car)} (your car)"
        self._estimate_label.setText(text)
