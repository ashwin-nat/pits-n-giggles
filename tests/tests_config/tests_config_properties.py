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

"""Property tests for settings fields: each field's accepted range is one entry in FIELDS, and Hypothesis checks
the model accepts everything inside it and rejects what lies outside."""

# ------------------------- IMPORTS ------------------------------------------------------------------------------------

import math
import string
import typing
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple, Type, Union

import allure
import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import BaseModel, ValidationError

from lib.config import (AutoOpenDashboardMode, CaptureSettings, DisplaySettings, ForwardingSettings,
                        HarvestPowerSmoothing, HttpsSettings, HudSettings, MfdPageSettings, MfdSettings,
                        MfdTyreWearRateType, NetworkSettings, OverlayPosition, OverlaysFuelEstimationMode,
                        OverlaysSpeedUnit, PitTimeLossF1, PitTimeLossF2, PngSettings, PredictionSettings,
                        PrivacySettings, StreamOverlaySettings, TimingTowerColOptions, TimingTowerColSettings,
                        TimingTowerTyreInfoMode, WeatherMFDUIType)
from lib.config.schema.mcp_cfg import McpSettings

pytestmark = allure.feature("Field constraints")

# ------------------------- SPECS --------------------------------------------------------------------------------------

_LETTERS = st.text(alphabet=string.ascii_letters, min_size=1)
# Strings pydantic's lax bool parses, case-insensitively
_BOOL_WORDS = {"0", "off", "f", "false", "n", "no", "1", "on", "t", "true", "y", "yes"}
# Strings pydantic's float parses as non-finite, case-insensitively and signed
_FLOAT_WORDS = {"inf", "infinity", "nan"}
_NON_FINITE = [math.inf, -math.inf, math.nan]


def _case_variants(word: str) -> st.SearchStrategy:
    """The word in random letter case, optionally signed."""
    cased = st.lists(st.booleans(), min_size=len(word), max_size=len(word)).map(
        lambda upper: "".join(c.upper() if u else c for c, u in zip(word, upper)))
    return st.tuples(st.sampled_from(["", "+", "-"]), cased).map("".join)


@dataclass(frozen=True)
class IntRange:
    """An int field accepting lo..hi inclusive (None = unbounded on that side), and None when nullable."""
    lo: Optional[int] = None
    hi: Optional[int] = None
    nullable: bool = False

    def valid(self) -> st.SearchStrategy:
        ints = st.integers(self.lo, self.hi)
        return ints | st.none() if self.nullable else ints

    def invalid(self) -> st.SearchStrategy:
        bad = _LETTERS | st.floats(allow_nan=False, allow_infinity=False).filter(lambda f: not f.is_integer())
        if self.lo is not None:
            bad |= st.integers(max_value=self.lo - 1)
        if self.hi is not None:
            bad |= st.integers(min_value=self.hi + 1)
        return bad if self.nullable else bad | st.none()

    def edges_in(self) -> List[Any]:
        return [b for b in (self.lo, self.hi) if b is not None] + ([None] if self.nullable else [])

    def edges_out(self) -> List[Any]:
        out = ([self.lo - 1] if self.lo is not None else []) + ([self.hi + 1] if self.hi is not None else [])
        return out + ([] if self.nullable else [None])

    def __str__(self) -> str:
        return _range_str(self.lo, self.hi, self.nullable)


@dataclass(frozen=True)
class FloatRange:
    """A float field accepting lo..hi inclusive (None = unbounded on that side), and None when nullable.
    finite: inf and nan are rejected, as floats and as strings."""
    lo: Optional[float] = None
    hi: Optional[float] = None
    nullable: bool = False
    finite: bool = False

    def valid(self) -> st.SearchStrategy:
        floats = st.floats(self.lo, self.hi, allow_nan=False, allow_infinity=False)
        return floats | st.none() if self.nullable else floats

    def invalid(self) -> st.SearchStrategy:
        bad = _LETTERS.filter(lambda s: s.lower() not in _FLOAT_WORDS)
        if self.lo is not None:
            bad |= st.floats(max_value=self.lo, exclude_max=True)
        if self.hi is not None:
            bad |= st.floats(min_value=self.hi, exclude_min=True)
        if self.lo is not None or self.hi is not None:
            bad |= st.just(math.nan)
        if self.finite:
            bad |= st.sampled_from(_NON_FINITE) | st.sampled_from(sorted(_FLOAT_WORDS)).flatmap(_case_variants)
        return bad if self.nullable else bad | st.none()

    def edges_in(self) -> List[Any]:
        return [b for b in (self.lo, self.hi) if b is not None] + ([None] if self.nullable else [])

    def edges_out(self) -> List[Any]:
        out = ([math.nextafter(self.lo, -math.inf)] if self.lo is not None else []) + \
              ([math.nextafter(self.hi, math.inf)] if self.hi is not None else [])
        if self.finite:
            out += _NON_FINITE + ["inf", "-Infinity", "NaN"]
        return out + ([] if self.nullable else [None])

    def __str__(self) -> str:
        return _range_str(self.lo, self.hi, self.nullable) + (", finite" if self.finite else "")


@dataclass(frozen=True)
class IntChoice:
    """An int field accepting exactly the listed values."""
    values: FrozenSet[int]

    def valid(self) -> st.SearchStrategy:
        return st.sampled_from(sorted(self.values))

    def invalid(self) -> st.SearchStrategy:
        return st.none() | _LETTERS | st.integers().filter(lambda i: i not in self.values)

    def edges_in(self) -> List[Any]:
        return sorted(self.values)

    def edges_out(self) -> List[Any]:
        return [i for i in range(min(self.values) - 1, max(self.values) + 2) if i not in self.values] + [None]

    def __str__(self) -> str:
        return "one of " + ",".join(map(str, sorted(self.values)))


@dataclass(frozen=True)
class Choice:
    """An enum field accepting exactly the listed values (as strings or members). Values are stored in config
    files, so they are listed here rather than read from the enum."""
    enum: Type[Enum]
    values: Tuple[str, ...]

    def valid(self) -> st.SearchStrategy:
        return st.sampled_from(self.values) | st.sampled_from(self.values).map(self.enum)

    def invalid(self) -> st.SearchStrategy:
        return st.none() | st.integers() | st.text().filter(lambda s: s not in self.values)

    def edges_in(self) -> List[Any]:
        return list(self.values) + [self.enum(v) for v in self.values]

    def edges_out(self) -> List[Any]:
        # A member added to the enum but not listed here must fail, so the table stays the record of stored values
        return [None, ""] + [m.value for m in self.enum if m.value not in self.values]

    def __str__(self) -> str:
        return self.enum.__name__


@dataclass(frozen=True)
class Flag:
    """A bool field."""

    def valid(self) -> st.SearchStrategy:
        return st.booleans()

    def invalid(self) -> st.SearchStrategy:
        return (st.none() | st.integers().filter(lambda i: i not in (0, 1)) |
                _LETTERS.filter(lambda s: s.lower() not in _BOOL_WORDS))

    def edges_in(self) -> List[Any]:
        return [False, True]

    def edges_out(self) -> List[Any]:
        return [None, 2]

    def __str__(self) -> str:
        return "bool"


@dataclass(frozen=True)
class Text:
    """A str field with no rule beyond its type."""
    nullable: bool = False

    def valid(self) -> st.SearchStrategy:
        return st.text() | st.none() if self.nullable else st.text()

    def invalid(self) -> st.SearchStrategy:
        return st.integers() if self.nullable else st.integers() | st.none()

    def edges_in(self) -> List[Any]:
        return [""] + ([None] if self.nullable else [])

    def edges_out(self) -> List[Any]:
        return [0] + ([] if self.nullable else [None])

    def __str__(self) -> str:
        return "str" + (" or None" if self.nullable else "")


def _range_str(lo: Any, hi: Any, nullable: bool) -> str:
    return f"{'' if lo is None else lo}..{'' if hi is None else hi}" + (" or None" if nullable else "")


FieldSpec = Union[IntRange, FloatRange, IntChoice, Choice, Flag, Text]

FLAG = Flag()
PORT = IntRange(1, 65535)
UDP_ACTION_CODE = IntRange(1, 12, nullable=True)
PERCENT = IntRange(0, 100)
PIT_TIME_LOSS = FloatRange(lo=0.0, nullable=True, finite=True)   # None = cleared by the user
# lo for a gt=0 float: the edges then check this value is accepted and 0.0 rejected
_SMALLEST_POSITIVE = math.nextafter(0.0, 1.0)


def _flags(*names: str) -> Dict[str, FieldSpec]:
    return dict.fromkeys(names, FLAG)


FIELDS: Dict[Type[BaseModel], Dict[str, FieldSpec]] = {
    NetworkSettings: {
        "telemetry_port": PORT,
        "server_port": PORT,
        "broker_xpub_port": PORT,
        "broker_xsub_port": PORT,
        "broker_router_port": PORT,
        "udp_tyre_delta_action_code": UDP_ACTION_CODE,
        "udp_custom_action_code": UDP_ACTION_CODE,
        "wdt_interval_sec": IntRange(1, 120),
        "enable_pkt_ordering": FLAG,
        "udp_action_button_debounce_ms": IntRange(0, 500),
    },
    CaptureSettings: _flags("post_race_data_autosave", "post_quali_data_autosave", "post_fp_data_autosave",
                            "post_tt_data_autosave", "save_race_ctrl_msg", "just_in_case_autosave"),
    DisplaySettings: {
        "auto_open_dashboard": Choice(AutoOpenDashboardMode,
                                      ("Disabled", "Hub", "Driver View", "Engineer View", "Save View")),
        "refresh_interval": IntRange(lo=1),
        "local_telemetry_rate": IntRange(lo=1),
        "realtime_overlay_fps": IntRange(lo=1),
        "use_cpu_acceleration": FLAG,
        "save_viewer_poll_interval_secs": IntRange(1, 30, nullable=True),
        "wdt_timeout": FloatRange(lo=2.0, nullable=True, finite=True),   # None = overlays never hide
    },
    PrivacySettings: _flags("process_car_setup"),
    StreamOverlaySettings: {
        "show_sample_data_at_start": FLAG,
        "stream_overlay_update_interval_ms": IntRange(lo=50),
    },
    HttpsSettings: _flags("enabled"),
    PredictionSettings: {
        "weather_aware_prediction": FLAG,
        "tyre_wear_window_size": IntRange(lo=2, nullable=True),
        "harvest_power_smoothing": Choice(HarvestPowerSmoothing,
                                          ("Very responsive", "Responsive", "Balanced", "Stable", "Very stable")),
    },
    McpSettings: {
        "mcp_http_server_enable": FLAG,
        "mcp_http_port": PORT,
    },
    PitTimeLossF1: dict.fromkeys(PitTimeLossF1.model_fields, PIT_TIME_LOSS),
    PitTimeLossF2: dict.fromkeys(PitTimeLossF2.model_fields, PIT_TIME_LOSS),
    HudSettings: {
        **_flags("enabled", "use_windowed_overlays", "show_lap_timer", "lap_timer_minimal", "show_timing_tower",
                 "timing_tower_relative_best_last_lap", "timing_tower_combined_tl_pens", "show_mfd",
                 "show_track_map", "show_input_overlay", "show_track_radar_overlay", "show_hud_overlay",
                 "show_circuit_info", "circuit_info_minimal", "show_pu_info", "pu_display_harvest_info",
                 "show_fuel_info", "fuel_info_show_title", "show_tyre_info", "tyre_info_show_title",
                 "show_lap_times", "lap_times_show_title", "show_weather", "weather_show_title", "show_pit_rejoin",
                 "pit_rejoin_show_title", "show_tyre_sets", "tyre_sets_show_title", "show_pace_comp",
                 "pace_comp_show_title", "show_traffic_monitor", "traffic_monitor_show_title",
                 "show_last_corner_stats", "show_rivals_status", "rivals_status_show_title", "show_tyres_status",
                 "tyres_status_show_title", "auto_hide_in_menu"),
        **dict.fromkeys(("toggle_overlays_udp_action_code", "lap_timer_toggle_udp_action_code",
                         "timing_tower_toggle_udp_action_code", "mfd_toggle_udp_action_code",
                         "mfd_interaction_udp_action_code", "cycle_mfd_udp_action_code",
                         "prev_mfd_page_udp_action_code", "track_map_toggle_udp_action_code",
                         "input_overlay_toggle_udp_action_code", "track_radar_overlay_toggle_udp_action_code",
                         "hud_overlay_toggle_udp_action_code", "circuit_info_toggle_udp_action_code",
                         "pu_toggle_udp_action_code"), UDP_ACTION_CODE),
        "overlays_speed_unit": Choice(OverlaysSpeedUnit, ("km/h", "mph")),
        "overlays_fuel_estimation_mode": Choice(OverlaysFuelEstimationMode, ("Linear regression", "Game built-in")),
        "timing_tower_max_rows": IntChoice(frozenset({*range(1, 24, 2), 24})),
        "timing_tower_tyre_info_mode": Choice(TimingTowerTyreInfoMode, ("Tyre Age", "Tyre Wear", "Hybrid")),
        "mfd_tyre_wear_threshold": PERCENT,
        "mfd_tyre_wear_rate_type": Choice(MfdTyreWearRateType, ("Max", "Average")),
        "mfd_weather_page_ui_type": Choice(WeatherMFDUIType, ("Cards", "Graph")),
        "input_overlay_buffer_duration_sec": FloatRange(1.0, 20.0),
        "track_radar_idle_opacity": PERCENT,
        "track_radar_range_m": IntRange(5, 35),
        "circuit_info_length": IntRange(200, 1500),
        "menu_silence_threshold_sec": FloatRange(1.0, 30.0),
        "overlays_opacity": PERCENT,
    },
    TimingTowerColOptions: _flags("show_col_header"),
    TimingTowerColSettings: {
        "enabled": FLAG,
        "position": IntRange(lo=1),
        "description": Text(),
    },
    MfdPageSettings: {
        "enabled": FLAG,
        "position": IntRange(lo=1),
        "description": Text(nullable=True),
    },
    OverlayPosition: {
        "x": IntRange(),
        "y": IntRange(),
        "scale_factor": FloatRange(lo=_SMALLEST_POSITIVE, finite=True),
    },
}

# Fields no spec above can express; their example tests stay the only coverage
EXAMPLE_ONLY: Dict[Type[BaseModel], Set[str]] = {
    NetworkSettings: {"bind_address"},          # IPv4 validator
    CaptureSettings: {"session_dir"},           # non-empty validator
    ForwardingSettings: {"target_1", "target_2", "target_3"},  # host:port validator
    HttpsSettings: {"key_file_path", "cert_file_path"},       # FilePathStr
    HudSettings: {"layout"},                    # dict keyed by overlay id
    TimingTowerColOptions: {"cols"},            # dict keyed by column id
    MfdSettings: {"pages"},                     # dict keyed by page id
}

# Values for required fields, so a case can set one field and leave the rest to defaults
REQUIRED: Dict[Type[BaseModel], Dict[str, Any]] = {
    TimingTowerColSettings: {"position": 1},
    MfdPageSettings: {"position": 1},
    OverlayPosition: {"x": 0, "y": 0},
}

# ------------------------- HELPERS ------------------------------------------------------------------------------------

def _reachable_models(root: Type[BaseModel]) -> List[Type[BaseModel]]:
    """Every model reachable from root through field annotations, including Optional/Dict/List arguments."""
    found: List[Type[BaseModel]] = []

    def visit(tp: Any) -> None:
        if isinstance(tp, type) and issubclass(tp, BaseModel):
            if tp not in found:
                found.append(tp)
                for field in tp.model_fields.values():
                    visit(field.annotation)
            return
        for arg in typing.get_args(tp):
            visit(arg)

    visit(root)
    return found


def _nested_model_fields(model: Type[BaseModel]) -> Set[str]:
    """Fields typed directly as a model; that model's own entries cover them."""
    return {name for name, field in model.model_fields.items()
            if isinstance(field.annotation, type) and issubclass(field.annotation, BaseModel)}


MODELS = _reachable_models(PngSettings)


@dataclass(frozen=True)
class Case:
    model: Type[BaseModel]
    field: str
    spec: FieldSpec

    def __str__(self) -> str:
        return f"{self.model.__name__}.{self.field}"

    def field_errors(self, exc: ValidationError) -> list:
        return [err for err in exc.errors() if err["loc"][:1] == (self.field,)]

    def build(self, value: Any) -> BaseModel:
        return self.model(**{**REQUIRED.get(self.model, {}), self.field: value})

    def assert_accepts(self, value: Any) -> None:
        try:
            model = self.build(value)
        except ValidationError as exc:
            # A model-level rule (a port clashing with another field's default) does not count against the field
            assert not self.field_errors(exc), f"{self} ({self.spec}) rejected {value!r}: {self.field_errors(exc)}"
            return
        assert getattr(model, self.field) == value

    def assert_rejects(self, value: Any) -> None:
        with pytest.raises(ValidationError) as exc:
            self.build(value)
        assert self.field_errors(exc.value), f"{self} ({self.spec}) {value!r} failed elsewhere: {exc.value.errors()}"


CASES = [pytest.param(Case(model, field, spec), id=f"{model.__name__}.{field}")
         for model, specs in FIELDS.items() for field, spec in specs.items()]

# ------------------------- TESTS --------------------------------------------------------------------------------------

@allure.story("Coverage")
@allure.title("Every {model.__name__} field has a spec, is a nested model, or is listed as example-only")
@pytest.mark.parametrize("model", MODELS, ids=lambda m: m.__name__)
def test_every_field_is_covered(model: Type[BaseModel]) -> None:
    """Compares the declared fields of each model reachable from PngSettings with FIELDS and EXAMPLE_ONLY.

    Expected: each field is in exactly one of FIELDS, EXAMPLE_ONLY, or is itself a model (covered by that model's
    own entry), and neither table names a field the model no longer has.
    """
    declared = set(model.model_fields)
    specced = set(FIELDS.get(model, {}))
    example_only = EXAMPLE_ONLY.get(model, set())
    nested = _nested_model_fields(model)

    assert declared - specced - example_only - nested == set(), "fields with no spec and no example-only entry"
    assert (specced | example_only) - declared == set(), "entries for fields the model does not declare"
    assert specced & example_only == set(), "fields listed in both FIELDS and EXAMPLE_ONLY"


@allure.story("Coverage")
@allure.title("FIELDS and EXAMPLE_ONLY name only models reachable from PngSettings")
def test_no_stale_models() -> None:
    """Compares the models keyed in FIELDS, EXAMPLE_ONLY and REQUIRED with those reachable from PngSettings.

    Expected: no table keys a model the settings tree no longer contains.
    """
    assert set(FIELDS) | set(EXAMPLE_ONLY) | set(REQUIRED) <= set(MODELS)


@allure.story("Accept")
@allure.title("{case} accepts every value in its range")
@pytest.mark.parametrize("case", CASES)
@given(data=st.data())
def test_accepts_in_range(case: Case, data: st.DataObject) -> None:
    """Builds the model with this one field set to a generated value inside its spec, the rest left at defaults.

    Expected: no validation error on this field, and the model holds the value unchanged. A model-level rule
    tripped by the value (a port clashing with another field's default) does not count against the field.
    """
    case.assert_accepts(data.draw(case.spec.valid(), label=case.field))


@allure.story("Reject")
@allure.title("{case} rejects values outside its range")
@pytest.mark.parametrize("case", CASES)
@given(data=st.data())
def test_rejects_out_of_range(case: Case, data: st.DataObject) -> None:
    """Builds the model with this one field set to a generated value outside its spec: out of bounds, the wrong
    type, or None for a non-nullable field.

    Expected: a ValidationError located at this field.
    """
    case.assert_rejects(data.draw(case.spec.invalid(), label=case.field))


@allure.story("Edges")
@allure.title("{case} accepts its bounds and rejects one past each")
@pytest.mark.parametrize("case", CASES)
def test_edges(case: Case) -> None:
    """Builds the model with this field at each bound of its spec, then one step past each (and None for a
    non-nullable field). Random draws do not reliably land on a bound, so this pins off-by-one changes.

    Expected: every bound is accepted and every step past it is rejected at this field.
    """
    for value in case.spec.edges_in():
        case.assert_accepts(value)
    for value in case.spec.edges_out():
        case.assert_rejects(value)
