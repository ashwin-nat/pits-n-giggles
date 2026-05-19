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

import sys
from collections import defaultdict
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Inject PySide6 mocks before any lib.assets_loader import so Qt is never needed.
_mock_qtgui = MagicMock()
sys.modules.setdefault('PySide6', MagicMock())
sys.modules['PySide6.QtGui'] = _mock_qtgui

from lib.assets_loader.icons import (
    _get_resource_base,
    load_icon,
    load_team_icons_dict,
    load_team_logos_uri_dict,
    load_tyre_icons_dict,
    load_tyre_icons_uri_dict,
)
from lib.assets_loader.fonts import _load_font, load_fonts

# ----------------------------------------------------------------------------------------------------------------------

_EXPECTED_TYRE_KEYS = {"Soft", "Super Soft", "Medium", "Hard", "Inters", "Wet"}

_EXPECTED_TEAM_KEYS = {
    "Alpine", "Alpine '24",
    "Aston Martin", "Aston Martin '24",
    "Ferrari", "Ferrari '24",
    "Haas", "Haas '24",
    "McLaren", "Mclaren", "Mclaren '24",
    "Mercedes", "Mercedes '24",
    "RB", "Rb '24", "VCARB", "Alpha Tauri",
    "Red Bull", "Red Bull Racing", "Red Bull Racing '24",
    "Sauber", "Sauber '24", "Alfa Romeo",
    "Williams", "Williams '24",
}


# ---- _get_resource_base -------------------------------------------------------------------------

class TestAssetsLoaderResourceBase:

    def test_normal_path_returns_cwd(self):
        # Temporarily remove _MEIPASS if present
        had_attr = hasattr(sys, '_MEIPASS')
        saved = getattr(sys, '_MEIPASS', None)
        if had_attr:
            del sys._MEIPASS
        try:
            result = _get_resource_base()
            assert result == Path.cwd()
        finally:
            if had_attr:
                sys._MEIPASS = saved

    def test_pyinstaller_path_returns_meipass(self):
        fake_bundle = "/fake/bundle"
        with patch.object(sys, '_MEIPASS', fake_bundle, create=True):
            result = _get_resource_base()
        assert result == Path(fake_bundle)


# ---- URI dict functions -------------------------------------------------------------------------

class TestAssetsLoaderUriDicts:

    def test_tyre_icons_uri_dict_keys(self):
        assert set(load_tyre_icons_uri_dict().keys()) == _EXPECTED_TYRE_KEYS

    def test_tyre_icons_uri_dict_values_are_file_uris(self):
        for key, uri in load_tyre_icons_uri_dict().items():
            assert isinstance(uri, str), f"URI for '{key}' should be a string"
            assert uri.startswith("file"), f"URI for '{key}' should start with 'file': {uri}"

    def test_tyre_icons_uri_dict_custom_path(self):
        result = load_tyre_icons_uri_dict(relative_path=Path("custom") / "tyres")
        assert set(result.keys()) == _EXPECTED_TYRE_KEYS

    def test_team_logos_uri_dict_keys(self):
        assert set(load_team_logos_uri_dict().keys()) == _EXPECTED_TEAM_KEYS

    def test_team_logos_uri_dict_values_are_file_uris(self):
        for key, uri in load_team_logos_uri_dict().items():
            assert isinstance(uri, str), f"URI for '{key}' should be a string"
            assert uri.startswith("file"), f"URI for '{key}' should start with 'file': {uri}"

    def test_team_logos_uri_dict_default_for_unknown_team(self):
        result = load_team_logos_uri_dict()
        default_uri = result["__unknown_team_xyz__"]
        assert isinstance(default_uri, str)
        assert default_uri.startswith("file")
        assert "default.svg" in default_uri

    def test_team_logos_uri_dict_custom_path(self):
        result = load_team_logos_uri_dict(relative_path=Path("custom") / "logos")
        assert set(result.keys()) == _EXPECTED_TEAM_KEYS


# ---- load_icon ---------------------------------------------------------------------------------

class TestAssetsLoaderIcons:

    @pytest.fixture(autouse=True)
    def reset_mocks(self):
        _mock_qtgui.QIcon.reset_mock()
        _mock_qtgui.QIcon.side_effect = None
        _mock_qtgui.QIcon.return_value = MagicMock()
        yield

    def test_load_icon_returns_something(self):
        result = load_icon(Path("some/icon.svg"))
        assert result is not None

    def test_load_icon_calls_qicon_with_string_arg(self):
        load_icon(Path("assets/icon.svg"))
        _mock_qtgui.QIcon.assert_called()
        call_arg = _mock_qtgui.QIcon.call_args[0][0]
        assert isinstance(call_arg, str)

    def test_load_icon_calls_debug_logger(self):
        msgs = []
        load_icon(Path("assets/icon.svg"), debug_log_printer=msgs.append)
        assert len(msgs) == 1

    def test_load_icon_returns_empty_icon_on_exception(self):
        # First call (the actual load) raises; second call (fallback QIcon()) succeeds.
        _mock_qtgui.QIcon.side_effect = [RuntimeError("Qt exploded"), MagicMock()]
        result = load_icon(Path("assets/icon.svg"))
        assert result is not None  # fallback empty QIcon returned

    def test_load_icon_calls_error_logger_on_exception(self):
        _mock_qtgui.QIcon.side_effect = [RuntimeError("Qt exploded"), MagicMock()]
        msgs = []
        load_icon(Path("assets/icon.svg"), error_log_printer=msgs.append)
        assert len(msgs) == 1

    def test_load_tyre_icons_dict_has_expected_keys(self):
        assert set(load_tyre_icons_dict().keys()) == _EXPECTED_TYRE_KEYS

    def test_load_team_icons_dict_has_expected_keys(self):
        assert set(load_team_icons_dict().keys()) == _EXPECTED_TEAM_KEYS

    def test_load_team_icons_dict_is_defaultdict(self):
        assert isinstance(load_team_icons_dict(), defaultdict)

    def test_load_team_icons_dict_default_for_unknown_team(self):
        result = load_team_icons_dict()
        default_icon = result["__no_such_team__"]
        assert default_icon is not None


# ---- _load_font / load_fonts -------------------------------------------------------------------

class TestAssetsLoaderFonts:

    @pytest.fixture(autouse=True)
    def reset_font_mocks(self):
        _mock_qtgui.QFontDatabase.reset_mock()
        _mock_qtgui.QFontDatabase.addApplicationFont.side_effect = None
        _mock_qtgui.QFontDatabase.addApplicationFont.return_value = 0
        _mock_qtgui.QFontDatabase.applicationFontFamilies.return_value = ["F1"]
        yield

    def test_load_font_returns_true_on_success(self):
        assert _load_font(Path("assets/fonts/f1-regular.ttf")) is True

    def test_load_font_returns_false_when_font_id_minus_one(self):
        _mock_qtgui.QFontDatabase.addApplicationFont.return_value = -1
        assert _load_font(Path("assets/fonts/f1-regular.ttf")) is False

    def test_load_font_calls_debug_logger_on_success(self):
        msgs = []
        _load_font(Path("assets/fonts/f1-regular.ttf"), debug_log_printer=msgs.append)
        assert len(msgs) == 1

    def test_load_font_calls_debug_logger_on_failure(self):
        _mock_qtgui.QFontDatabase.addApplicationFont.return_value = -1
        msgs = []
        _load_font(Path("assets/fonts/f1-regular.ttf"), debug_log_printer=msgs.append)
        assert len(msgs) == 1

    def test_load_font_returns_false_and_calls_error_logger_on_exception(self):
        _mock_qtgui.QFontDatabase.addApplicationFont.side_effect = RuntimeError("Qt exploded")
        msgs = []
        result = _load_font(Path("assets/fonts/f1-regular.ttf"), error_log_printer=msgs.append)
        assert result is False
        assert len(msgs) == 1

    def test_load_fonts_calls_add_application_font_for_default_list(self):
        load_fonts()
        assert _mock_qtgui.QFontDatabase.addApplicationFont.call_count == 8

    def test_load_fonts_calls_add_application_font_for_custom_list(self):
        load_fonts(fonts_list=["myfont.ttf", "otherfont.ttf"])
        assert _mock_qtgui.QFontDatabase.addApplicationFont.call_count == 2

    def test_load_fonts_uses_custom_base_path(self):
        load_fonts(base_path=Path("custom") / "fonts", fonts_list=["test.ttf"])
        call_arg = str(_mock_qtgui.QFontDatabase.addApplicationFont.call_args[0][0])
        assert "custom" in call_arg
        assert "test.ttf" in call_arg
