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
                        HttpsSettings, HudSettings, NetworkSettings, OpacityOverride,
                        PngSettings, PrivacySettings, StreamOverlaySettings,
                        load_config_from_json, save_config_to_json)

from .tests_config_properties import FIELDS, _CONTAINERS, _nested_model_fields, png_settings_dicts

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

# File content, sections expected back at defaults (every value in them was bad), valid values expected to survive
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
@allure.title("Bad input ({case}) is reset to defaults, valid values survive, and the file is backed up")
@pytest.mark.parametrize("case", list(_BAD_CONFIGS))
def test_bad_input_restores_section(config_path, case):
    """
    Writes a config.json with invalid values, invalid JSON, or valid JSON that is not an object, then loads it.

    Expected: every invalid value reads as its default (here each section holds only bad values, so it equals its
    defaults), valid values elsewhere in the file are kept, and the original is moved to config.json.invalid.
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

# -------------------------------------- BAD VALUE ISOLATION -----------------------------------------------------------

def _leaf_paths(model: type, prefix: tuple = ()) -> list:
    """(path, spec) for every FIELDS leaf under model, following fields typed directly as a model."""
    leaves = [(prefix + (name,), spec) for name, spec in FIELDS.get(model, {}).items()]
    for name in _nested_model_fields(model):
        leaves += _leaf_paths(model.model_fields[name].annotation, prefix + (name,))
    return leaves


_LEAVES = _leaf_paths(PngSettings)


def _set(raw: dict, path: tuple, value) -> None:
    node = raw
    for key in path[:-1]:
        node = node.setdefault(key, {})
    node[path[-1]] = value


def _delete(raw: dict, path: tuple) -> None:
    node = raw
    for key in path[:-1]:
        node = node.get(key, {})
    node.pop(path[-1], None)


@allure.story("Bad value isolation")
@allure.title("One bad value in a saved config resets only that value")
@given(data=st.data())
def test_one_bad_value_resets_only_that_value(data):
    """
    Generates a valid whole config, replaces one field (any FIELDS leaf, at any depth) with a value its spec
    rejects, writes it as config.json and loads it.

    Expected: no exception; the loaded settings equal the config with that one value removed, so it reads as its
    default and every other value is kept; the original is backed up. Draws where the default itself breaks a rule
    with the rest of the config are skipped.
    """
    raw = data.draw(png_settings_dicts())
    try:
        PngSettings.model_validate(raw)
    except ValidationError:
        reject()
    path, spec = data.draw(st.sampled_from(_LEAVES), label="field")
    bad_value = data.draw(spec.invalid() | _CONTAINERS, label="bad value")

    without = json.loads(json.dumps(raw))
    _delete(without, path)
    try:
        expected = PngSettings.model_validate(without)
    except ValidationError:
        reject()  # the field's default clashes with a generated value elsewhere

    corrupted = json.loads(json.dumps(raw))
    _set(corrupted, path, bad_value)
    with tempfile.TemporaryDirectory() as tmp:
        config_path = Path(tmp) / "config.json"
        config_path.write_text(json.dumps(corrupted), encoding="utf-8")

        loaded = load_config_from_json(str(config_path))

        assert loaded == expected, ".".join(path)
        assert _backup_exists(config_path)


def _at(settings, path: str):
    """The value at a dotted path, through model attributes and dict keys."""
    node = settings
    for key in path.split("."):
        node = node[key] if isinstance(node, dict) else getattr(node, key)
    return node


_HUD_OVERLAY_FLAGS = [name for name, field in HudSettings.model_fields.items()
                      if (field.json_schema_extra or {}).get("ui", {}).get("overlay_enable")]

# File content breaking one rule, expected values afterwards, and values in the same file that must survive
_BROKEN_RULES = {
    "Network action codes equal": (
        {"Network": {"udp_tyre_delta_action_code": 5, "udp_custom_action_code": 5, "server_port": 4999}},
        {"Network.udp_tyre_delta_action_code": None, "Network.udp_custom_action_code": None},
        {"Network.server_port": 4999},
    ),
    "two Network TCP ports equal": (
        {"Network": {"server_port": 5000, "broker_xpub_port": 5000, "telemetry_port": 20800}},
        {"Network.server_port": 4768, "Network.broker_xpub_port": 53838},
        {"Network.telemetry_port": 20800},
    ),
    "duplicate forwarding targets": (
        {"Forwarding": {"target_1": "a.lan:5000", "target_2": "a.lan:5000", "target_3": "b.lan:6000"}},
        {"Forwarding.target_2": ""},
        {"Forwarding.target_1": "a.lan:5000", "Forwarding.target_3": "b.lan:6000"},
    ),
    "HUD on with every overlay off": (
        {"HUD": {**dict.fromkeys(_HUD_OVERLAY_FLAGS, False), "track_radar_range_m": 30}},
        {f"HUD.{flag}": getattr(HudSettings(), flag) for flag in _HUD_OVERLAY_FLAGS},
        {"HUD.track_radar_range_m": 30},
    ),
    "MFD shown with every page disabled": (
        {"HUD": {"show_mfd": True, "track_radar_range_m": 30,
                 "mfd_settings": {"pages": {page.value: {"enabled": False, "position": i + 1}
                                            for i, page in enumerate(HudSettings().mfd_settings.pages)}}}},
        {"HUD.show_mfd": True, "HUD.mfd_settings": HudSettings().mfd_settings},
        {"HUD.track_radar_range_m": 30},
    ),
    "radar idle opacity above overall": (
        {"HUD": {"track_radar_idle_opacity": 90, "overlays_opacity": 50, "track_radar_range_m": 30}},
        {"HUD.track_radar_idle_opacity": 30, "HUD.overlays_opacity": 100},
        {"HUD.track_radar_range_m": 30},
    ),
    "two timing tower columns at one position": (
        {"HUD": {"track_radar_range_m": 30, "timing_tower_col_options": {"cols": {
            "delta": {"enabled": True, "position": 3}, "tyre": {"enabled": True, "position": 3}}}}},
        {"HUD.timing_tower_col_options.cols.delta.position": 1, "HUD.timing_tower_col_options.cols.tyre.position": 2},
        {"HUD.timing_tower_col_options.cols.delta.enabled": True,
         "HUD.timing_tower_col_options.cols.tyre.enabled": True, "HUD.track_radar_range_m": 30},
    ),
    "two MFD pages at one position": (
        {"HUD": {"track_radar_range_m": 30, "mfd_settings": {"pages": {
            "lap_times": {"enabled": True, "position": 3}, "weather_forecast": {"enabled": True, "position": 3}}}}},
        {"HUD.mfd_settings.pages.lap_times.position": 1, "HUD.mfd_settings.pages.weather_forecast.position": 2},
        {"HUD.mfd_settings.pages.lap_times.enabled": True,
         "HUD.mfd_settings.pages.weather_forecast.enabled": True, "HUD.track_radar_range_m": 30},
    ),
    "HTTPS on without key or cert files": (
        {"HTTPS": {"enabled": True, "key_file_path": "/no/key.pem", "cert_file_path": "/no/cert.pem"},
         "Display": {"refresh_interval": 300}},
        {"HTTPS.enabled": False},
        {"HTTPS.key_file_path": "/no/key.pem", "HTTPS.cert_file_path": "/no/cert.pem",
         "Display.refresh_interval": 300},
    ),
    "UDP action code in Network and HUD": (
        {"Network": {"udp_custom_action_code": 3, "server_port": 4999},
         "HUD": {"mfd_toggle_udp_action_code": 3, "track_radar_range_m": 30}},
        {"Network.udp_custom_action_code": None, "HUD.mfd_toggle_udp_action_code": None},
        {"Network.server_port": 4999, "HUD.track_radar_range_m": 30},
    ),
    "TCP port in Network and MCP": (
        {"Network": {"server_port": 4770, "telemetry_port": 20800}, "MCP": {"mcp_http_port": 4770}},
        {"Network.server_port": 4768, "MCP.mcp_http_port": 4770},
        {"Network.telemetry_port": 20800},
    ),
    "MCP port set to the default server port": (
        {"Network": {"telemetry_port": 20800}, "MCP": {"mcp_http_port": 4768}},
        {"Network.server_port": 4768, "MCP.mcp_http_port": 4770},
        {"Network.telemetry_port": 20800},
    ),
    "forwarding loops back to the telemetry port": (
        {"Network": {"telemetry_port": 20800}, "Forwarding": {"target_1": "localhost:20800", "target_2": "b.lan:6000"}},
        {"Forwarding.target_1": ""},
        {"Network.telemetry_port": 20800, "Forwarding.target_2": "b.lan:6000"},
    ),
    "overlay layout entry with a bad scale": (
        {"HUD": {"layout": {"mfd": {"x": 7, "y": 8, "scale_factor": -1}}, "track_radar_range_m": 30}},
        {"HUD.layout.mfd.scale_factor": 1.0},
        {"HUD.layout.mfd.x": 7, "HUD.layout.mfd.y": 8, "HUD.track_radar_range_m": 30},
    ),
    "overlay layout entry missing a required field": (
        {"HUD": {"layout": {"mfd": {"y": 5}, "lap_timer": {"x": 11, "y": 12}}, "track_radar_range_m": 30}},
        {"HUD.layout.mfd": HudSettings().layout["mfd"]},
        {"HUD.layout.lap_timer.x": 11, "HUD.track_radar_range_m": 30},
    ),
    "radar opacity override at or below idle": (
        {"HUD": {"track_radar_idle_opacity": 40, "track_radar_range_m": 30, "layout": {
            "track_radar": {"x": 1, "y": 2, "opacity_override": {"enabled": True, "value": 20}}}}},
        {"HUD.layout.track_radar.opacity_override": OpacityOverride()},
        {"HUD.track_radar_idle_opacity": 40, "HUD.layout.track_radar.x": 1},
    ),
    "overlay layout entry with a bad opacity override value": (
        {"HUD": {"track_radar_range_m": 30, "layout": {
            "mfd": {"x": 7, "y": 8, "opacity_override": {"enabled": True, "value": 150}}}}},
        {"HUD.layout.mfd.opacity_override.value": 100},
        {"HUD.layout.mfd.opacity_override.enabled": True, "HUD.layout.mfd.x": 7, "HUD.layout.mfd.y": 8,
         "HUD.track_radar_range_m": 30},
    ),
}

@allure.story("Bad value isolation")
@allure.title("A config breaking a rule ({case}) resets the fields the rule names, and nothing else")
@pytest.mark.parametrize("case", list(_BROKEN_RULES))
def test_broken_rule_resets_involved_fields(config_path, caplog, case):
    """
    Writes a config.json where each value is valid alone but a rule between fields is broken (within a section,
    across sections, or in a dict entry), plus valid values elsewhere, then loads it.

    Expected: no exception; every field the rule names reads as its default, the other values are kept, a
    warning names what was reset, and the original is moved to config.json.invalid.
    """
    raw, expected, kept = _BROKEN_RULES[case]
    _write_json(config_path, raw)
    logger = logging.getLogger("tests_config_io")

    with caplog.at_level(logging.WARNING, logger=logger.name):
        settings = load_config_from_json(str(config_path), logger=logger)

    for path, value in {**expected, **kept}.items():
        assert _at(settings, path) == value, path
    assert "Invalid config" in caplog.text
    assert _backup_exists(config_path)


@allure.story("Bad value isolation")
@allure.title("After an upgrade, a new setting whose default clashes with a saved value loads with both reset")
def test_upgrade_default_clash_resets_both(config_path):
    """
    Loads a config saved before the MCP section existed, whose Network.server_port is 4770: the port the new
    MCP.mcp_http_port defaults to. The new field is already at its default, so only resetting both works.

    Expected: no exception; server_port reads as its default 4768, the MCP port as its default 4770, and the
    rest of the saved values are kept.
    """
    _write_json(config_path, {"Network": {"server_port": 4770, "telemetry_port": 20800},
                              "Display": {"refresh_interval": 300}})

    settings = load_config_from_json(str(config_path))

    assert (settings.Network.server_port, settings.MCP.mcp_http_port) == (4768, 4770)
    assert (settings.Network.telemetry_port, settings.Display.refresh_interval) == (20800, 300)


@allure.story("Schema upgrade")
@allure.title("A layout saved before opacity overrides loads with the default override (read_only={read_only})")
@pytest.mark.parametrize("read_only", [False, True])
def test_layout_without_opacity_override_upgrades(config_path, read_only):
    """
    Writes a full default config with mfd moved and rescaled, then strips opacity_override from every layout
    entry, as saved by a build before overrides existed, and loads it normally or read-only.

    Expected: x, y and scale are kept and every entry gets the default override. A normal load rewrites the file
    with the key added and no .invalid backup; a read-only load leaves the file untouched.
    """
    old = PngSettings().model_dump(mode="json")
    old["HUD"]["layout"]["mfd"].update(x=7, y=8, scale_factor=1.5)
    for entry in old["HUD"]["layout"].values():
        del entry["opacity_override"]
    _write_json(config_path, old)
    content = config_path.read_text(encoding="utf-8")

    settings = load_config_from_json(str(config_path), read_only=read_only)

    mfd = settings.HUD.layout["mfd"]
    assert (mfd.x, mfd.y, mfd.scale_factor) == (7, 8, 1.5)
    assert all(pos.opacity_override == OpacityOverride() for pos in settings.HUD.layout.values())
    if read_only:
        assert config_path.read_text(encoding="utf-8") == content
    else:
        saved = json.loads(config_path.read_text(encoding="utf-8"))["HUD"]["layout"]
        assert all(entry["opacity_override"] == {"enabled": False, "value": 100} for entry in saved.values())
    assert not _backup_exists(config_path)


@allure.story("Bad value isolation")
@allure.title("A section whose validation raises an unexpected exception is reset, not the whole config")
def test_unexpected_exception_resets_only_that_section(config_path, caplog, monkeypatch):
    """
    Makes NetworkSettings validation raise RuntimeError (as a validator raising something other than ValueError
    would), then loads a config with Network and Display values.

    Expected: no exception escapes the loader; Network reads as its defaults, Display keeps its value, and an
    error is logged.
    """
    def explode(cls, data, *args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(NetworkSettings, "model_validate", classmethod(explode))
    _write_json(config_path, {"Network": {"server_port": 4999}, "Display": {"refresh_interval": 300}})
    logger = logging.getLogger("tests_config_io")

    with caplog.at_level(logging.ERROR, logger=logger.name):
        settings = load_config_from_json(str(config_path), logger=logger)

    assert settings.Network == NetworkSettings()
    assert settings.Display.refresh_interval == 300
    assert "Unexpected RuntimeError" in caplog.text

# -------------------------------------- READ-ONLY LOAD ----------------------------------------------------------------

_READ_ONLY_FILES = {
    "a repairable bad value": json.dumps({"Network": {"telemetry_port": 0, "server_port": 4999}}),
    "corrupted json": "{ this is not valid json! ",
    "no file": None,
}

@allure.story("Read-only load")
@allure.title("A read-only load ({case}) repairs in memory and leaves the disk untouched")
@pytest.mark.parametrize("case", list(_READ_ONLY_FILES))
def test_read_only_load_never_writes(config_path, case):
    """
    Loads with read_only=True, as launcher-managed subsystems do, from a file with a bad value, an unparsable
    file, or no file.

    Expected: the settings are repaired in memory as a normal load would, but the file is not rewritten,
    created or moved to .invalid, so the launcher stays the only writer.
    """
    content = _READ_ONLY_FILES[case]
    if content is not None:
        config_path.write_text(content, encoding="utf-8")

    settings = load_config_from_json(str(config_path), read_only=True)

    assert settings.Network.telemetry_port == 20777
    if content is None:
        assert not config_path.exists()
    else:
        assert config_path.read_text(encoding="utf-8") == content
        if case == "a repairable bad value":
            assert settings.Network.server_port == 4999
    assert not _backup_exists(config_path)

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
