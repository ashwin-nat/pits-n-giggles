# ----------------------------------------------------------------------------------------------------------------------
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

"""HudSettings rules the field spec table does not cover: defaults, cross-field rules, the MFD page and timing
tower column containers, the overlay layout, and derived values. Per-field ranges, types and enum values are in
tests_config_properties.py; diff behaviour is in tests_diff_mixin.py."""

import allure
import pytest
from pydantic import ValidationError

from lib.config import (HudSettings, MfdPageId, MfdPageSettings, MfdSettings, MfdTyreWearRateType, OverlayId,
                        OverlayPosition, OverlaysFuelEstimationMode, OverlaysSpeedUnit, TimingTowerColId,
                        TimingTowerColOptions, TimingTowerColSettings, TimingTowerTyreInfoMode, WeatherMFDUIType)
from lib.config.schema.hud.mfd import DEFAULT_PAGES

pytestmark = allure.feature("HUD settings")

# -------------------------------------- HELPERS -----------------------------------------------------------------------

_OVERLAY_FLAGS = [name for name, field in HudSettings.model_fields.items()
                  if (field.json_schema_extra or {}).get("ui", {}).get("overlay_enable")]


def _all_overlays_off() -> dict:
    return dict.fromkeys(_OVERLAY_FLAGS, False)


def _pages(*enabled: MfdPageId) -> dict:
    """The default MFD pages, with only the given ones enabled."""
    return {key: page.model_copy(update={"enabled": key in enabled}) for key, page in DEFAULT_PAGES.items()}


def _cols(enabled_positions: dict) -> dict:
    """Every timing tower column disabled at its own position, except the given {col_id: position}, enabled."""
    cols = {col.value: TimingTowerColSettings(enabled=False, position=i + 1) for i, col in enumerate(TimingTowerColId)}
    for col_id, position in enabled_positions.items():
        cols[col_id.value] = TimingTowerColSettings(enabled=True, position=position)
    return cols

# -------------------------------------- DEFAULTS ----------------------------------------------------------------------

_DEFAULTS = {
    "enabled": True,
    "toggle_overlays_udp_action_code": None,
    "use_windowed_overlays": False,
    "overlays_speed_unit": OverlaysSpeedUnit.KMPH,
    "overlays_fuel_estimation_mode": OverlaysFuelEstimationMode.LINEAR_REGRESSION,
    "show_lap_timer": True,
    "lap_timer_minimal": False,
    "lap_timer_toggle_udp_action_code": None,
    "show_timing_tower": True,
    "timing_tower_max_rows": 5,
    "timing_tower_tyre_info_mode": TimingTowerTyreInfoMode.HYBRID,
    "timing_tower_relative_best_last_lap": False,
    "timing_tower_combined_tl_pens": False,
    "timing_tower_toggle_udp_action_code": None,
    "show_mfd": True,
    "mfd_tyre_wear_threshold": 80,
    "mfd_tyre_wear_rate_type": MfdTyreWearRateType.MAX,
    "mfd_weather_page_ui_type": WeatherMFDUIType.CARDS,
    "mfd_toggle_udp_action_code": None,
    "mfd_interaction_udp_action_code": None,
    "cycle_mfd_udp_action_code": None,
    "prev_mfd_page_udp_action_code": None,
    "show_track_map": False,
    "track_map_toggle_udp_action_code": None,
    "show_input_overlay": True,
    "input_overlay_toggle_udp_action_code": None,
    "input_overlay_buffer_duration_sec": 5.0,
    "show_track_radar_overlay": True,
    "track_radar_overlay_toggle_udp_action_code": None,
    "track_radar_idle_opacity": 30,
    "track_radar_range_m": 25,
    "show_hud_overlay": True,
    "hud_overlay_toggle_udp_action_code": None,
    "show_circuit_info": True,
    "circuit_info_toggle_udp_action_code": None,
    "circuit_info_length": 800,
    "circuit_info_minimal": False,
    "show_pu_info": True,
    "pu_display_harvest_info": False,
    "pu_toggle_udp_action_code": None,
    "show_fuel_info": False,
    "fuel_info_show_title": True,
    "show_tyre_info": False,
    "tyre_info_show_title": True,
    "show_lap_times": False,
    "lap_times_show_title": True,
    "show_weather": False,
    "weather_show_title": True,
    "show_pit_rejoin": False,
    "pit_rejoin_show_title": True,
    "show_tyre_sets": False,
    "tyre_sets_show_title": True,
    "show_pace_comp": False,
    "pace_comp_show_title": True,
    "show_traffic_monitor": False,
    "traffic_monitor_show_title": True,
    "show_last_corner_stats": False,
    "show_rivals_status": False,
    "rivals_status_show_title": True,
    "show_tyres_status": False,
    "tyres_status_show_title": True,
    "auto_hide_in_menu": True,
    "menu_silence_threshold_sec": 3.0,
    "overlays_opacity": 100,
}

@allure.story("Defaults")
@allure.title("Default HudSettings hold the shipped values for every scalar field")
def test_default_values():
    """
    Builds HudSettings with no arguments and compares each scalar field with _DEFAULTS. The three containers
    (MFD pages, timing tower columns, layout) have their own default tests.

    Expected: every field holds its shipped default, and _DEFAULTS names every scalar field the model has.
    """
    settings = HudSettings()
    scalar_fields = set(HudSettings.model_fields) - {"mfd_settings", "timing_tower_col_options", "layout"}

    assert set(_DEFAULTS) == scalar_fields
    for field, value in _DEFAULTS.items():
        assert getattr(settings, field) == value, field


@allure.story("Defaults")
@allure.title("The default MFD has the known pages, enabled ones at unique positions")
def test_default_mfd_pages():
    """
    Builds HudSettings with no arguments and reads its MFD pages.

    Expected: exactly the ten known pages (not the collapsed page), and no two enabled pages share a position.
    """
    pages = HudSettings().mfd_settings.pages

    assert set(pages) == {
        MfdPageId.LAP_TIMES, MfdPageId.WEATHER_FORECAST, MfdPageId.FUEL_INFO, MfdPageId.TYRE_INFO,
        MfdPageId.PIT_REJOIN, MfdPageId.TYRE_SETS, MfdPageId.PACE_COMP, MfdPageId.TRAFFIC_MONITOR,
        MfdPageId.RIVALS_STATUS, MfdPageId.TYRES_STATUS,
    }
    positions = [page.position for page in pages.values() if page.enabled]
    assert len(positions) == len(set(positions))


@allure.story("Defaults")
@allure.title("The default timing tower shows its column header and the five default columns")
def test_default_timing_tower_cols():
    """
    Builds TimingTowerColOptions with no arguments.

    Expected: the header is shown, every column id is present at a unique position, and only delta, tyre, ERS/DRS,
    penalties and track limit warnings are enabled.
    """
    opts = TimingTowerColOptions()
    enabled = {TimingTowerColId.DELTA, TimingTowerColId.TYRE, TimingTowerColId.ERS_DRS, TimingTowerColId.PENS,
               TimingTowerColId.TL_WARNS}

    assert opts.show_col_header is True
    assert set(opts.cols) == {col.value for col in TimingTowerColId}
    positions = [col.position for col in opts.cols.values()]
    assert len(positions) == len(set(positions))
    assert {col_id for col_id, col in opts.cols.items() if col.enabled} == {col.value for col in enabled}


@allure.story("Defaults")
@allure.title("The default layout places every overlay at scale 1.0")
def test_default_layout():
    """
    Builds HudSettings with no arguments and reads its overlay layout.

    Expected: one OverlayPosition per overlay id, each at scale factor 1.0.
    """
    layout = HudSettings().layout

    assert set(layout) == set(OverlayId)
    assert all(isinstance(pos, OverlayPosition) and pos.scale_factor == 1.0 for pos in layout.values())

# -------------------------------------- CROSS-FIELD RULES -------------------------------------------------------------

@allure.story("Cross-field rules")
@allure.title("An enabled HUD with every overlay off is rejected")
def test_enabled_hud_needs_an_overlay():
    """
    Turns every overlay flag off and leaves the HUD enabled.

    Expected: a ValidationError saying the HUD cannot be enabled with all overlays disabled.
    """
    with pytest.raises(ValidationError, match="all overlays are disabled"):
        HudSettings(enabled=True, **_all_overlays_off())


@allure.story("Cross-field rules")
@allure.title("A disabled HUD may have every overlay off")
def test_disabled_hud_may_have_no_overlay():
    """
    Turns every overlay flag off and disables the HUD.

    Expected: the model builds; the overlay rule only applies to an enabled HUD.
    """
    HudSettings(enabled=False, **_all_overlays_off())


@allure.story("Cross-field rules")
@allure.title("An enabled HUD with one overlay on is accepted")
def test_enabled_hud_with_one_overlay():
    """
    Turns every overlay flag off except the lap timer.

    Expected: the model builds.
    """
    HudSettings(enabled=True, **{**_all_overlays_off(), "show_lap_timer": True})


@allure.story("Cross-field rules")
@allure.title("Showing the MFD with every MFD page disabled is rejected")
def test_mfd_needs_an_enabled_page():
    """
    Shows the MFD and disables all of its pages.

    Expected: a ValidationError saying the HUD cannot be enabled with all MFD pages disabled.
    """
    with pytest.raises(ValidationError, match="all MFD pages are disabled"):
        HudSettings(show_mfd=True, mfd_settings=MfdSettings(pages=_pages()))


@allure.story("Cross-field rules")
@allure.title("A hidden MFD may have every page disabled")
def test_hidden_mfd_may_have_no_page():
    """
    Hides the MFD and disables all of its pages, leaving the other default overlays on.

    Expected: the model builds.
    """
    HudSettings(show_mfd=False, mfd_settings=MfdSettings(pages=_pages()))


_OPACITIES = {
    "idle 0, overall 1": (0, 1, True),
    "idle just below overall": (29, 30, True),
    "idle equal to overall": (30, 30, False),
    "idle above overall": (80, 70, False),
}

@allure.story("Cross-field rules")
@allure.title("Track radar idle opacity must be below overlays opacity ({case})")
@pytest.mark.parametrize("case", list(_OPACITIES))
def test_idle_opacity_below_overlays_opacity(case):
    """
    Sets the track radar idle opacity and the overlays opacity on an enabled HUD.

    Expected: accepted when idle is strictly below overall, else a ValidationError naming the opacity rule.
    """
    idle, overall, accepted = _OPACITIES[case]
    if accepted:
        HudSettings(track_radar_idle_opacity=idle, overlays_opacity=overall)
    else:
        with pytest.raises(ValidationError, match="idle opacity"):
            HudSettings(track_radar_idle_opacity=idle, overlays_opacity=overall)


@allure.story("Cross-field rules")
@allure.title("A disabled HUD may have idle opacity above overlays opacity")
def test_disabled_hud_skips_opacity_rule():
    """
    Disables the HUD and sets the track radar idle opacity above the overlays opacity.

    Expected: the model builds; the opacity rule only applies to an enabled HUD.
    """
    HudSettings(enabled=False, track_radar_idle_opacity=80, overlays_opacity=70)

# -------------------------------------- MFD PAGES ---------------------------------------------------------------------

@allure.story("MFD pages")
@allure.title("Two enabled MFD pages at the same position are rejected")
def test_mfd_duplicate_enabled_positions_rejected():
    """
    Enables the lap times and fuel pages, both at position 1.

    Expected: a ValidationError reporting the duplicate position.
    """
    pages = {MfdPageId.LAP_TIMES: MfdPageSettings(enabled=True, position=1),
             MfdPageId.FUEL_INFO: MfdPageSettings(enabled=True, position=1)}
    with pytest.raises(ValidationError, match="duplicate position"):
        MfdSettings(pages=pages)


@allure.story("MFD pages")
@allure.title("Disabled MFD pages may share a position")
def test_mfd_duplicate_disabled_positions_allowed():
    """
    Puts the lap times and fuel pages, both disabled, at position 1.

    Expected: the model builds; only enabled pages need unique positions.
    """
    MfdSettings(pages={MfdPageId.LAP_TIMES: MfdPageSettings(enabled=False, position=1),
                       MfdPageId.FUEL_INFO: MfdPageSettings(enabled=False, position=1)})


@allure.story("MFD pages")
@allure.title("Known MFD pages missing from a stored config are added, disabled")
def test_mfd_missing_pages_added_disabled():
    """
    Validates stored MFD settings that only hold the lap times page.

    Expected: every known page is present; the stored one keeps its values and the added ones are disabled.
    """
    mfd = MfdSettings.model_validate({"pages": {MfdPageId.LAP_TIMES: {"enabled": True, "position": 1}}})

    assert set(mfd.pages) == set(DEFAULT_PAGES)
    assert mfd.pages[MfdPageId.LAP_TIMES].enabled is True
    assert not any(page.enabled for key, page in mfd.pages.items() if key != MfdPageId.LAP_TIMES)


@allure.story("MFD pages")
@allure.title("A known MFD page stored without a position gets its default position")
def test_mfd_page_without_position_gets_default():
    """
    Validates stored MFD settings where the weather page has only "enabled": True, as left by a repair that reset
    its position.

    Expected: the page keeps enabled and takes its default position, 2.
    """
    mfd = MfdSettings.model_validate({"pages": {MfdPageId.WEATHER_FORECAST.value: {"enabled": True}}})

    assert (mfd.pages[MfdPageId.WEATHER_FORECAST.value].enabled,
            mfd.pages[MfdPageId.WEATHER_FORECAST.value].position) == (True, 2)


@allure.story("MFD pages")
@allure.title("Unknown MFD pages in a stored config are dropped")
def test_mfd_unknown_pages_dropped():
    """
    Validates stored MFD settings that hold a page id no longer known (e.g. removed in an update).

    Expected: the unknown page is gone and the known pages are present.
    """
    mfd = MfdSettings.model_validate({"pages": {"retired_page": {"enabled": True, "position": 1}}})

    assert "retired_page" not in mfd.pages
    assert set(mfd.pages) == set(DEFAULT_PAGES)


@allure.story("MFD pages")
@allure.title("sorted_enabled_pages lists only enabled pages, in position order")
def test_mfd_sorted_enabled_pages():
    """
    Enables tyre info at position 1, fuel at 2 and lap times at 3, leaving the rest disabled, and reads
    sorted_enabled_pages.

    Expected: exactly those three pages, ordered by position.
    """
    pages = _pages()
    pages[MfdPageId.LAP_TIMES] = MfdPageSettings(enabled=True, position=3)
    pages[MfdPageId.FUEL_INFO] = MfdPageSettings(enabled=True, position=2)
    pages[MfdPageId.TYRE_INFO] = MfdPageSettings(enabled=True, position=1)

    order = [key for key, _ in MfdSettings(pages=pages).sorted_enabled_pages()]
    assert order == [MfdPageId.TYRE_INFO, MfdPageId.FUEL_INFO, MfdPageId.LAP_TIMES]

# -------------------------------------- TIMING TOWER COLUMNS ----------------------------------------------------------

@allure.story("Timing tower columns")
@allure.title("Timing tower column keys dump as plain strings")
def test_col_keys_dump_as_strings():
    """
    Dumps default TimingTowerColOptions with model_dump.

    Expected: every column key is a str (a plain str or a str-valued column id), so the config JSON has string keys.
    """
    assert all(isinstance(key, str) for key in TimingTowerColOptions().model_dump()["cols"])


@allure.story("Timing tower columns")
@allure.title("A known timing tower column stored without a position gets its default position")
def test_col_without_position_gets_default():
    """
    Validates stored column options where the tyre column has only "enabled": True, as left by a repair that
    reset its position.

    Expected: the column keeps enabled and takes its default position, 2.
    """
    opts = TimingTowerColOptions.model_validate({"cols": {TimingTowerColId.TYRE.value: {"enabled": True}}})

    assert (opts.cols[TimingTowerColId.TYRE.value].enabled, opts.cols[TimingTowerColId.TYRE.value].position) == (True, 2)


@allure.story("Timing tower columns")
@allure.title("Two enabled timing tower columns at the same position are rejected")
def test_col_duplicate_enabled_positions_rejected():
    """
    Enables the delta and tyre columns, both at position 1.

    Expected: a ValidationError reporting the duplicate position.
    """
    with pytest.raises(ValidationError, match="duplicate position"):
        TimingTowerColOptions(cols={
            TimingTowerColId.DELTA.value: TimingTowerColSettings(enabled=True, position=1),
            TimingTowerColId.TYRE.value: TimingTowerColSettings(enabled=True, position=1),
        })


@allure.story("Timing tower columns")
@allure.title("Disabled timing tower columns may share a position")
def test_col_duplicate_disabled_positions_allowed():
    """
    Puts the delta and tyre columns, both disabled, at position 1.

    Expected: the model builds; only enabled columns need unique positions.
    """
    TimingTowerColOptions(cols={
        TimingTowerColId.DELTA.value: TimingTowerColSettings(enabled=False, position=1),
        TimingTowerColId.TYRE.value: TimingTowerColSettings(enabled=False, position=1),
    })


_STORED_COLS = {
    "empty": {},
    "one column": {TimingTowerColId.DELTA.value: {"enabled": True, "position": 1}},
    "three columns": {
        TimingTowerColId.DELTA.value: {"enabled": True, "position": 1},
        TimingTowerColId.TYRE.value: {"enabled": True, "position": 2},
        TimingTowerColId.PENS.value: {"enabled": False, "position": 3},
    },
}

@allure.story("Timing tower columns")
@allure.title("Columns missing from a stored config are added, disabled, at free positions ({case})")
@pytest.mark.parametrize("case", list(_STORED_COLS))
def test_missing_cols_added_disabled(case):
    """
    Validates stored timing tower columns that hold none, one or three of the known columns.

    Expected: every known column is present at a unique position; stored ones keep their values and added ones
    are disabled.
    """
    stored = _STORED_COLS[case]
    opts = TimingTowerColOptions.model_validate({"cols": stored})

    assert set(opts.cols) == {col.value for col in TimingTowerColId}
    positions = [col.position for col in opts.cols.values()]
    assert len(positions) == len(set(positions))
    for col_id, col in opts.cols.items():
        if col_id in stored:
            assert (col.enabled, col.position) == (stored[col_id]["enabled"], stored[col_id]["position"]), col_id
        else:
            assert col.enabled is False, col_id


@allure.story("Timing tower columns")
@allure.title("An old flat-boolean column config is ignored and the columns are filled in")
def test_old_flat_col_booleans_ignored():
    """
    Validates an old timing tower config made of flat show_* booleans instead of a cols dict.

    Expected: the unknown keys are ignored and every known column is present.
    """
    old = {"show_team_logos": True, "show_deltas": True, "show_tyre_info": True, "show_ers_drs_info": True,
           "show_pens": True, "show_tl_warns": True, "show_best_lap": False, "show_last_lap": False,
           "show_wing_dmg": False, "show_speed_trap": False, "show_fuel": False, "show_driver_status": False}

    assert set(TimingTowerColOptions.model_validate(old).cols) == {col.value for col in TimingTowerColId}


_ENABLED_COLS = {
    "default columns": None,
    "delta to leader only": {TimingTowerColId.DELTA_TO_LEADER: 1},
    "three, out of order": {TimingTowerColId.FUEL: 3, TimingTowerColId.DELTA: 1, TimingTowerColId.PENS: 2},
    "none": {},
}

@allure.story("Timing tower columns")
@allure.title("sorted_enabled_cols lists only enabled columns, in position order ({case})")
@pytest.mark.parametrize("case", list(_ENABLED_COLS))
def test_sorted_enabled_cols(case):
    """
    Enables a set of columns (or keeps the defaults) and reads sorted_enabled_cols.

    Expected: exactly the enabled columns, ordered by position.
    """
    enabled = _ENABLED_COLS[case]
    opts = TimingTowerColOptions() if enabled is None else TimingTowerColOptions(cols=_cols(enabled))
    expected = sorted(((col_id, col.position) for col_id, col in opts.cols.items() if col.enabled),
                      key=lambda pair: pair[1])

    assert [(col_id, col.position) for col_id, col in opts.sorted_enabled_cols()] == expected
    if enabled is not None:
        assert [col_id for col_id, _ in expected] == [c.value for c, _ in sorted(enabled.items(), key=lambda i: i[1])]

# -------------------------------------- LAYOUT ------------------------------------------------------------------------

@allure.story("Layout")
@allure.title("Overlays missing from a stored layout get their default positions")
def test_layout_missing_overlays_filled():
    """
    Builds HudSettings with a layout for four overlays, as a config saved before the others existed.

    Expected: the four keep their positions, and every other overlay gets its default position.
    """
    stored = {OverlayId.LAP_TIMER: OverlayPosition(x=1, y=1), OverlayId.TIMING_TOWER: OverlayPosition(x=2, y=2),
              OverlayId.MFD: OverlayPosition(x=3, y=3), OverlayId.TRACK_RADAR: OverlayPosition(x=4, y=4)}
    layout = HudSettings(layout=stored).layout
    defaults = HudSettings.get_default_layout_dict()

    assert set(layout) == set(OverlayId)
    for oid in OverlayId:
        assert layout[oid] == stored.get(oid, defaults[oid]), oid

# -------------------------------------- DERIVED VALUES ----------------------------------------------------------------

@allure.story("Derived values")
@allure.title("Speed unit {unit.value} sets the km/h and mph flags")
@pytest.mark.parametrize("unit, kmph, mph", [(OverlaysSpeedUnit.KMPH, True, False),
                                             (OverlaysSpeedUnit.MPH, False, True)],
                         ids=["km/h", "mph"])
def test_speed_unit_flags(unit, kmph, mph):
    """
    Sets overlays_speed_unit and reads hud_overlay_speed_unit_kmph/_mph.

    Expected: exactly the flag for the chosen unit is True.
    """
    settings = HudSettings(overlays_speed_unit=unit)

    assert (settings.hud_overlay_speed_unit_kmph, settings.hud_overlay_speed_unit_mph) == (kmph, mph)


@allure.story("Derived values")
@allure.title("Fuel estimation mode '{mode.value}' sets the linear regression and game built-in flags")
@pytest.mark.parametrize("mode, regression, built_in",
                         [(OverlaysFuelEstimationMode.LINEAR_REGRESSION, True, False),
                          (OverlaysFuelEstimationMode.GAME_BUILT_IN, False, True)],
                         ids=["linear regression", "game built-in"])
def test_fuel_estimation_flags(mode, regression, built_in):
    """
    Sets overlays_fuel_estimation_mode and reads the two fuel estimation flags.

    Expected: exactly the flag for the chosen mode is True.
    """
    settings = HudSettings(overlays_fuel_estimation_mode=mode)

    assert (settings.hud_overlay_fuel_estimation_linear_regression,
            settings.hud_overlay_fuel_estimation_game_built_in) == (regression, built_in)


@allure.story("Derived values")
@allure.title("A timing tower of {rows} rows shows {adjacent} cars either side")
@pytest.mark.parametrize("rows, adjacent", [(1, 0), (3, 1), (23, 11), (24, 12)])
def test_timing_tower_num_adjacent_cars(rows, adjacent):
    """
    Sets timing_tower_max_rows and reads timing_tower_num_adjacent_cars.

    Expected: (rows - 1) / 2 for odd rows, and 12 for 24 rows (the whole grid).
    """
    assert HudSettings(timing_tower_max_rows=rows).timing_tower_num_adjacent_cars == adjacent


@allure.story("Derived values")
@allure.title("enabled_overlays_by_id includes the tyres status overlay only when it is shown")
def test_enabled_overlays_by_id_tyres_status():
    """
    Reads enabled_overlays_by_id with the tyres status overlay hidden (the default) and shown.

    Expected: TYRES_STATUS is absent by default and present once show_tyres_status is True.
    """
    assert OverlayId.TYRES_STATUS not in HudSettings().enabled_overlays_by_id()
    assert OverlayId.TYRES_STATUS in HudSettings(show_tyres_status=True).enabled_overlays_by_id()
