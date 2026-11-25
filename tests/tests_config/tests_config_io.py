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
# pylint: skip-file

import json
import logging
import tempfile
from pathlib import Path

import allure
import pytest
from hypothesis import given, reject
from hypothesis import strategies as st
from pydantic import ValidationError

from lib.config import (CaptureSettings, DisplaySettings, ForwardingSettings,
                        HttpsSettings, NetworkSettings, PngSettings,
                        PrivacySettings, StreamOverlaySettings,
                        load_config_from_json, save_config_to_json)

from .tests_config_properties import png_settings_dicts

pytestmark = allure.feature("Config file I/O")

# -------------------------------------- HELPERS -----------------------------------------------------------------------

@pytest.fixture
def config_path(tmp_path):
    return tmp_path / "config.json"

def _write_json(path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=4), encoding="utf-8")

def _backup_exists(path) -> bool:
    return path.with_name(path.name + ".invalid").exists()

# -------------------------------------- SAVE AND LOAD -----------------------------------------------------------------

@allure.story("JSON load and save")
@allure.title("Saving writes each section's values to the JSON file")
def test_save_writes_values(config_path):
    """
    Saves a PngSettings with non-default values in five sections, then reads the file back as plain JSON.

    Expected: the file exists and holds each value under its section and key.
    """
    settings = PngSettings(
        Network=NetworkSettings(telemetry_port=12345),
        Capture=CaptureSettings(post_race_data_autosave=True),
        Display=DisplaySettings(refresh_interval=150),
        Privacy=PrivacySettings(process_car_setup=True),
        Forwarding=ForwardingSettings(target_1="localhost:8080"),
        StreamOverlay=StreamOverlaySettings(),
    )

    save_config_to_json(settings, str(config_path))

    data = json.loads(config_path.read_text(encoding="utf-8"))
    assert data["Network"]["telemetry_port"] == 12345
    assert data["Capture"]["post_race_data_autosave"] is True
    assert data["Display"]["refresh_interval"] == 150
    assert data["Privacy"]["process_car_setup"] is True
    assert data["Forwarding"]["target_1"] == "localhost:8080"

@allure.story("JSON load and save")
@allure.title("Saved settings load back unchanged")
def test_roundtrip(config_path):
    """
    Saves a PngSettings with non-default values in every basic section, then loads it.

    Expected: the loaded settings equal the saved ones.
    """
    original = PngSettings(
        Network=NetworkSettings(telemetry_port=11111, server_port=22222),
        Capture=CaptureSettings(post_race_data_autosave=True),
        Display=DisplaySettings(refresh_interval=300),
        Privacy=PrivacySettings(process_car_setup=True),
        Forwarding=ForwardingSettings(target_1="host1.example.com:8000", target_2="host2.example.com:9000"),
        StreamOverlay=StreamOverlaySettings(show_sample_data_at_start=True),
    )

    save_config_to_json(original, str(config_path))

    assert load_config_from_json(str(config_path)) == original

@allure.story("JSON load and save")
@allure.title("Any valid settings, HTTPS included, save and load back unchanged")
@given(data=st.data())
def test_any_settings_roundtrip(data):
    """
    Generates a whole PngSettings from the field spec table: every section, nested models, forwarding targets,
    overlay layout entries, and HTTPS off, on with real key/cert files, or off with paths set. Saves it to JSON and
    loads it back, in a fresh temp dir per example.

    Expected: the loaded settings equal the saved ones, and no section was restored (no .invalid backup).
    """
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        key_path, cert_path = tmp_dir / "temp.key", tmp_dir / "temp.crt"
        key_path.touch()
        cert_path.touch()
        paths = {"key_file_path": str(key_path), "cert_file_path": str(cert_path)}
        https = st.sampled_from([{"enabled": False}, {"enabled": True, **paths}, {"enabled": False, **paths}])

        raw = data.draw(png_settings_dicts(extra={HttpsSettings: https}))
        try:
            original = PngSettings.model_validate(raw)
        except ValidationError:
            reject()  # a cross-field rule the strategy does not build in (e.g. every overlay disabled)
        config_path = tmp_dir / "config.json"

        save_config_to_json(original, str(config_path))
        loaded = load_config_from_json(str(config_path))

        assert loaded == original
        assert not _backup_exists(config_path)

@allure.story("JSON load and save")
@allure.title("A missing config file is created with defaults")
def test_missing_file_writes_defaults(config_path):
    """
    Loads from a path where no file exists.

    Expected: the loader returns default settings and writes them to that path.
    """
    settings = load_config_from_json(str(config_path))

    assert settings == PngSettings()
    assert config_path.exists()

@allure.story("JSON load and save")
@allure.title("An old config without newer sections loads with those sections at their defaults")
def test_old_config_gets_new_sections(config_path):
    """
    Loads a config written before the HTTPS section existed.

    Expected: the file's values are kept and HTTPS reads as its default (disabled).
    """
    _write_json(config_path, {
        "Network": {"telemetry_port": 12345, "server_port": 9999},
        "Capture": {"post_race_data_autosave": True},
        "Display": {"refresh_interval": 150},
        "Privacy": {"process_car_setup": True},
        "Forwarding": {"target_1": "localhost:8080"},
    })

    settings = load_config_from_json(str(config_path))

    assert settings.Network.telemetry_port == 12345
    assert settings.Network.server_port == 9999
    assert settings.HTTPS.enabled is False

@allure.story("JSON load and save")
@allure.title("HTTPS settings load when the key and cert files exist")
def test_https_with_existing_files(tmp_path, config_path):
    """
    Creates empty key and cert files, then loads a config that enables HTTPS with those paths.

    Expected: HTTPS is enabled and both paths are kept.
    """
    key_path = tmp_path / "temp.key"
    cert_path = tmp_path / "temp.crt"
    key_path.touch()
    cert_path.touch()
    _write_json(config_path, {
        "HTTPS": {"enabled": True, "key_file_path": str(key_path), "cert_file_path": str(cert_path)},
    })

    settings = load_config_from_json(str(config_path))

    assert settings.HTTPS.enabled is True
    assert str(settings.HTTPS.key_file_path) == str(key_path)
    assert str(settings.HTTPS.cert_file_path) == str(cert_path)

# -------------------------------------- BAD INPUT ---------------------------------------------------------------------

_GOOD_NETWORK = {"Network": {"telemetry_port": 20779}}

# File content, sections expected back at defaults, valid sections expected to survive
_BAD_CONFIGS = {
    "out-of-range value": (json.dumps({"Display": {"refresh_interval": 0}}), ["Display"], {}),
    "one bad forwarding target": (
        json.dumps({**_GOOD_NETWORK, "Forwarding": {"target_1": "bad-value"}}),
        ["Forwarding"],
        _GOOD_NETWORK,
    ),
    "several bad forwarding targets": (
        json.dumps({**_GOOD_NETWORK, "Forwarding": {"target_1": "bad-value", "target_2": 12345, "target_3": None}}),
        ["Forwarding"],
        _GOOD_NETWORK,
    ),
    "corrupted json": ("{ this is not valid json! ", list(PngSettings.model_fields), {}),
    "top level is a list": ("[1]", list(PngSettings.model_fields), {}),
    "top level is an empty list": ("[]", list(PngSettings.model_fields), {}),
    "top level is a string": ('"abc"', list(PngSettings.model_fields), {}),
    "top level is a number": ("5", list(PngSettings.model_fields), {}),
    "top level is null": ("null", list(PngSettings.model_fields), {}),
}

@allure.story("Bad input")
@allure.title("Bad input ({case}) restores only the affected sections and backs up the file")
@pytest.mark.parametrize("case", list(_BAD_CONFIGS))
def test_bad_input_restores_section(config_path, case):
    """
    Writes a config.json with an invalid value, invalid JSON, or valid JSON that is not an object, then loads it.

    Expected: each affected section reads as its defaults, valid sections in the same file keep their values, and
    the original file is moved to config.json.invalid.
    """
    content, restored, kept = _BAD_CONFIGS[case]
    config_path.write_text(content, encoding="utf-8")

    settings = load_config_from_json(str(config_path))

    defaults = PngSettings()
    for section in restored:
        assert getattr(settings, section) == getattr(defaults, section), section
    for section, fields in kept.items():
        for key, value in fields.items():
            assert getattr(getattr(settings, section), key) == value, f"{section}.{key}"
    assert _backup_exists(config_path)

# -------------------------------------- PARTIAL CONFIGS ---------------------------------------------------------------

_PARTIAL_CONFIGS = {
    "missing sections": {
        "Network": {"telemetry_port": 30777, "server_port": 5000},
        "Capture": {"post_race_data_autosave": True},
    },
    "missing keys": {
        "Network": {"telemetry_port": 25000},
        "Display": {"refresh_interval": 500},
        "Privacy": {},
        "Forwarding": {"target_1": "localhost:8080"},
        "StreamOverlay": {},
    },
    "partial network": {
        "Network": {"telemetry_port": 21000, "udp_custom_action_code": 5},
    },
    "empty sections": {
        "Network": {}, "Capture": {}, "Display": {}, "Privacy": {}, "Forwarding": {}, "StreamOverlay": {},
    },
    "mixed": {
        "Network": {"telemetry_port": 19999, "server_port": 6000},
        "Display": {"auto_open_dashboard": "Disabled"},
        "Privacy": {"process_car_setup": True},
        "Forwarding": {"target_2": "example.com:9090"},
    },
    "single section": {
        "Display": {"refresh_interval": 350, "auto_open_dashboard": "Disabled"},
    },
}

@allure.story("Partial config files")
@allure.title("Partial config ({case}) keeps its values, fills defaults and is rewritten in full")
@pytest.mark.parametrize("case", list(_PARTIAL_CONFIGS))
def test_partial_config_fills_defaults(config_path, case):
    """
    Writes a config.json with some sections or keys missing, then loads it.

    Expected: every value in the file is kept and every missing section and key reads as its default. The file on
    disk is rewritten with the full config, and no section was restored, so there is no .invalid backup.
    """
    raw = _PARTIAL_CONFIGS[case]
    _write_json(config_path, raw)

    expected = PngSettings().model_dump(mode="json")
    for section, fields in raw.items():
        expected[section].update(fields)

    loaded = load_config_from_json(str(config_path))

    assert loaded.model_dump(mode="json") == expected
    assert json.loads(config_path.read_text(encoding="utf-8")) == expected
    assert not _backup_exists(config_path)

@allure.story("Partial config files")
@allure.title("A key that differs only in case is ignored and logged as unknown")
def test_key_with_wrong_case_is_unknown(config_path, caplog):
    """
    Writes a config.json whose Network section has Telemetry_Port instead of telemetry_port, then loads it.

    Expected: keys are case-sensitive, so telemetry_port keeps its default and the key is logged as unknown.
    """
    _write_json(config_path, {"Network": {"Telemetry_Port": 30000}})
    logger = logging.getLogger("tests_config_io")

    with caplog.at_level(logging.DEBUG, logger=logger.name):
        loaded = load_config_from_json(str(config_path), logger=logger)

    assert loaded.Network.telemetry_port == NetworkSettings().telemetry_port
    assert "Ignored unknown key [Network].[Telemetry_Port]" in caplog.text
