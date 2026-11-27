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
# pylint: skip-file

"""LapAnalyzerSettings rules the field spec table does not cover: defaults, sensor annotations, unknown and stale
keys. Accepted and rejected values of every flag, sensors included, are in tests_config_properties.py."""

import allure
import pytest

from lib.config import (SENSOR_GROUP_INFO, LapAnalyzerSensorSettings, LapAnalyzerSettings, PngSettings,
                        SensorGroup)

pytestmark = allure.feature("Lap analyzer settings")

SENSOR_FIELDS = list(LapAnalyzerSensorSettings.model_fields)


def _sensor_meta(field: str) -> dict:
    return LapAnalyzerSensorSettings.model_fields[field].json_schema_extra["sensor"]

# -------------------------------------- DEFAULTS ----------------------------------------------------------------------

@allure.story("Defaults")
@allure.title("Default LapAnalyzerSettings hold the shipped values")
def test_default_values():
    """
    Builds LapAnalyzerSettings with no arguments.

    Expected: the analyzer is on and records race and qualifying laps, not free practice or time trial.
    """
    settings = LapAnalyzerSettings()

    assert settings.enable is True
    assert settings.record_in_race is True
    assert settings.record_in_quali is True
    assert settings.record_in_fp is False
    assert settings.record_in_tt is False

# -------------------------------------- SENSORS -----------------------------------------------------------------------

@allure.story("Sensors")
@allure.title("Sensor {field} has a complete annotation")
@pytest.mark.parametrize("field", SENSOR_FIELDS)
def test_sensor_annotation_complete(field):
    """
    Reads the sensor metadata the launcher builds its sensor page from.

    Expected: a known group, a boolean restricted flag, an info text that is absent or not blank, and a label.
    """
    meta = _sensor_meta(field)

    assert SensorGroup(meta["group"])
    assert isinstance(meta["restricted"], bool)
    assert meta["info"] is None or meta["info"].strip()
    assert LapAnalyzerSensorSettings.model_fields[field].description


@allure.story("Sensors")
@allure.title("Group tooltips only name known sensor groups")
def test_group_info_keys_are_known_groups():
    """
    Compares the keys of SENSOR_GROUP_INFO with SensorGroup.

    Expected: every tooltip belongs to a group that exists.
    """
    assert set(SENSOR_GROUP_INFO) <= set(SensorGroup)


@allure.story("Sensors")
@allure.title("An unknown sensor key is ignored")
def test_unknown_sensor_key_is_ignored():
    """
    Builds Sensors from a known key and one that is not a sensor.

    Expected: the known key applies and the unknown one is dropped, not stored.
    """
    settings = LapAnalyzerSettings(Sensors={"throttle": False, "not_a_sensor": True})

    assert settings.Sensors.throttle is False
    assert not hasattr(settings.Sensors, "not_a_sensor")


@allure.story("Sensors")
@allure.title("Every sensor off with the analyzer enabled is valid")
def test_all_sensors_off_with_enable_is_valid():
    """
    Enables the analyzer with every sensor turned off.

    Expected: the model builds; no rule requires a sensor.
    """
    settings = LapAnalyzerSettings(enable=True, Sensors=dict.fromkeys(SENSOR_FIELDS, False))

    assert settings.enable
    assert not any(getattr(settings.Sensors, field) for field in SENSOR_FIELDS)

# -------------------------------------- DIFF AND LOAD -----------------------------------------------------------------

@allure.story("Diff")
@allure.title("A sensor change shows in the diff")
def test_sensor_change_shows_in_diff():
    """
    Diffs default settings against settings with the steering sensor off.

    Expected: a non-empty diff, so the launcher sees the change.
    """
    assert LapAnalyzerSettings().diff(LapAnalyzerSettings(Sensors={"steering": False}))


@allure.story("Load")
@allure.title("A stale LapRecording section is dropped on load")
def test_stale_lap_recording_key_is_dropped():
    """
    Loads PngSettings holding the section's old name, LapRecording, with the analyzer disabled.

    Expected: the old section is dropped, not kept, and LapAnalyzer keeps its default (enabled).
    """
    settings = PngSettings.model_validate({"LapRecording": {"enable": False}})

    assert "LapRecording" not in settings.model_dump()
    assert settings.LapAnalyzer.enable
