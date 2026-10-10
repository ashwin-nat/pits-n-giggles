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

import os
import sys

import pytest
from pydantic import ValidationError

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.config import (ENTROPY_BYTES_PER_SAMPLE, SENSOR_GROUP_INFO, PngSettings,
                        SensorEntropy, SensorGroup, SensorPreset,
                        LapAnalyzerSettings, LapAnalyzerSensorSettings)

from .tests_config_base import TestF1ConfigBase

# ----------------------------------------------------------------------------------------------------------------------

class TestLapAnalyzerSettings(TestF1ConfigBase):
    """Test LapAnalyzerSettings model"""

    def test_default_values(self):
        """Test default values"""
        settings = LapAnalyzerSettings()
        self.assertTrue(settings.enable)
        self.assertTrue(settings.record_other_cars)
        self.assertFalse(settings.record_in_spectator_mode)
        self.assertTrue(settings.record_in_race)
        self.assertTrue(settings.record_in_quali)
        self.assertFalse(settings.record_in_fp)
        self.assertFalse(settings.record_in_tt)

    def test_boolean_validation_enable(self):
        self.assertTrue(LapAnalyzerSettings(enable=True).enable)
        self.assertFalse(LapAnalyzerSettings(enable=False).enable)

        # Also test coercion from strings
        self.assertTrue(LapAnalyzerSettings(enable="True").enable)
        self.assertFalse(LapAnalyzerSettings(enable="False").enable)

    def test_boolean_validation_record_other_cars(self):
        self.assertTrue(LapAnalyzerSettings(record_other_cars=True).record_other_cars)
        self.assertFalse(LapAnalyzerSettings(record_other_cars=False).record_other_cars)

        self.assertTrue(LapAnalyzerSettings(record_other_cars="True").record_other_cars)
        self.assertFalse(LapAnalyzerSettings(record_other_cars="False").record_other_cars)

    def test_boolean_validation_record_in_spectator_mode(self):
        self.assertTrue(LapAnalyzerSettings(record_in_spectator_mode=True).record_in_spectator_mode)
        self.assertFalse(LapAnalyzerSettings(record_in_spectator_mode=False).record_in_spectator_mode)

        self.assertTrue(LapAnalyzerSettings(record_in_spectator_mode="True").record_in_spectator_mode)
        self.assertFalse(LapAnalyzerSettings(record_in_spectator_mode="False").record_in_spectator_mode)

    def test_boolean_validation_record_in_race(self):
        self.assertTrue(LapAnalyzerSettings(record_in_race=True).record_in_race)
        self.assertFalse(LapAnalyzerSettings(record_in_race=False).record_in_race)

        self.assertTrue(LapAnalyzerSettings(record_in_race="True").record_in_race)
        self.assertFalse(LapAnalyzerSettings(record_in_race="False").record_in_race)

    def test_boolean_validation_record_in_quali(self):
        self.assertTrue(LapAnalyzerSettings(record_in_quali=True).record_in_quali)
        self.assertFalse(LapAnalyzerSettings(record_in_quali=False).record_in_quali)

        self.assertTrue(LapAnalyzerSettings(record_in_quali="True").record_in_quali)
        self.assertFalse(LapAnalyzerSettings(record_in_quali="False").record_in_quali)

    def test_boolean_validation_record_in_fp(self):
        self.assertTrue(LapAnalyzerSettings(record_in_fp=True).record_in_fp)
        self.assertFalse(LapAnalyzerSettings(record_in_fp=False).record_in_fp)

        self.assertTrue(LapAnalyzerSettings(record_in_fp="True").record_in_fp)
        self.assertFalse(LapAnalyzerSettings(record_in_fp="False").record_in_fp)

    def test_boolean_validation_record_in_tt(self):
        self.assertTrue(LapAnalyzerSettings(record_in_tt=True).record_in_tt)
        self.assertFalse(LapAnalyzerSettings(record_in_tt=False).record_in_tt)

        self.assertTrue(LapAnalyzerSettings(record_in_tt="True").record_in_tt)
        self.assertFalse(LapAnalyzerSettings(record_in_tt="False").record_in_tt)

    def test_invalid_type_raises(self):
        with self.assertRaises(ValidationError):
            LapAnalyzerSettings(enable="notaboolean")

        with self.assertRaises(ValidationError):
            LapAnalyzerSettings(record_other_cars="notaboolean")

        with self.assertRaises(ValidationError):
            LapAnalyzerSettings(record_in_spectator_mode="notaboolean")

        with self.assertRaises(ValidationError):
            LapAnalyzerSettings(record_in_race="notaboolean")

        with self.assertRaises(ValidationError):
            LapAnalyzerSettings(record_in_quali="notaboolean")

        with self.assertRaises(ValidationError):
            LapAnalyzerSettings(record_in_fp="notaboolean")

        with self.assertRaises(ValidationError):
            LapAnalyzerSettings(record_in_tt="notaboolean")

# ----------------------------------------------------------------------------------------------------------------------

SENSOR_FIELDS = list(LapAnalyzerSensorSettings.model_fields)


def _sensor_meta(field: str) -> dict:
    return LapAnalyzerSensorSettings.model_fields[field].json_schema_extra["sensor"]


@pytest.mark.parametrize("field", SENSOR_FIELDS)
def test_sensor_annotation_complete(field):
    meta = _sensor_meta(field)
    assert SensorEntropy(meta["entropy"]) in ENTROPY_BYTES_PER_SAMPLE
    assert SensorGroup(meta["group"])
    assert isinstance(meta["restricted"], bool)
    assert meta["info"] is None or meta["info"].strip()
    assert meta["presets"]
    assert all(SensorPreset(p) for p in meta["presets"])
    assert LapAnalyzerSensorSettings.model_fields[field].description


@pytest.mark.parametrize("field", SENSOR_FIELDS)
def test_sensor_default_matches_beginner_preset(field):
    in_beginner = SensorPreset.BEGINNER.value in _sensor_meta(field)["presets"]
    assert LapAnalyzerSensorSettings.model_fields[field].default is in_beginner


def test_beginner_preset_contents():
    beginner = {f for f in SENSOR_FIELDS if SensorPreset.BEGINNER.value in _sensor_meta(f)["presets"]}
    assert beginner == {"throttle", "brake", "steering", "speed", "gear", "engine_rpm"}


def test_advanced_preset_is_every_sensor():
    assert all(SensorPreset.ADVANCED.value in _sensor_meta(f)["presets"] for f in SENSOR_FIELDS)


def test_every_entropy_class_has_bytes_coefficient():
    assert set(ENTROPY_BYTES_PER_SAMPLE) == set(SensorEntropy)


def test_group_info_keys_are_known_groups():
    assert set(SENSOR_GROUP_INFO) <= set(SensorGroup)


def test_unknown_sensor_key_is_ignored():
    settings = LapAnalyzerSettings(Sensors={"throttle": False, "not_a_sensor": True})
    assert settings.Sensors.throttle is False
    assert not hasattr(settings.Sensors, "not_a_sensor")


def test_all_sensors_off_with_enable_is_valid():
    settings = LapAnalyzerSettings(enable=True, Sensors={f: False for f in SENSOR_FIELDS})
    assert settings.enable
    assert not any(getattr(settings.Sensors, f) for f in SENSOR_FIELDS)


def test_sensor_change_shows_in_diff():
    old = LapAnalyzerSettings()
    new = LapAnalyzerSettings(Sensors={"steering": False})
    assert old.diff(new)


def test_stale_lap_recording_key_is_dropped():
    settings = PngSettings.model_validate({"LapRecording": {"enable": False}})
    assert "LapRecording" not in settings.model_dump()
    assert settings.LapAnalyzer.enable
