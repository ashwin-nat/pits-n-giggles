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
from hypothesis.provisional import domains
from pydantic import BaseModel, ValidationError

from lib.config import (AutoOpenDashboardMode, CaptureSettings, DisplaySettings, ForwardingSettings,
                        HarvestPowerSmoothing, HttpsSettings, HudSettings, LapAnalyzerSensorSettings,
                        LapAnalyzerSettings, MfdPageSettings, MfdSettings,
                        MfdTyreWearRateType, NetworkSettings, OpacityOverride, OverlayId, OverlayPosition,
                        OverlaysFuelEstimationMode,
                        OverlaysSpeedUnit, PitTimeLossF1, PitTimeLossF2, PngSettings, PredictionSettings,
                        PrivacySettings, SaveViewerSettings, StreamOverlaySettings, TimingTowerColOptions,
                        TimingTowerColSettings, TimingTowerTyreInfoMode, WeatherMFDUIType)
from lib.config.schema.mcp_cfg import McpSettings

pytestmark = allure.feature("Field constraints")

# ------------------------- SPECS --------------------------------------------------------------------------------------

_LETTERS = st.text(alphabet=string.ascii_letters, min_size=1)
# No field takes a container, so every field must reject these
_CONTAINERS = st.lists(st.integers(), max_size=3) | st.dictionaries(st.text(max_size=2), st.integers(), max_size=2)
# Strings pydantic's lax bool parses, case-insensitively
# Same as pydantic.v1.validators.BOOL_TRUE/BOOL_FALSE; v2 parses in pydantic-core and exposes no constant
_TRUE_WORDS = {"1", "on", "t", "true", "y", "yes"}
_BOOL_WORDS = _TRUE_WORDS | {"0", "off", "f", "false", "n", "no"}
# Strings pydantic's float parses as non-finite, case-insensitively and signed
_FLOAT_WORDS = {"inf", "infinity", "nan"}
_NON_FINITE = [math.inf, -math.inf, math.nan]


def _random_case(word: str) -> st.SearchStrategy:
    """The word with each letter upper or lower case."""
    return st.lists(st.booleans(), min_size=len(word), max_size=len(word)).map(
        lambda upper: "".join(c.upper() if u else c for c, u in zip(word, upper)))


def _case_variants(word: str) -> st.SearchStrategy:
    """The word in random letter case, optionally signed."""
    return st.tuples(st.sampled_from(["", "+", "-"]), _random_case(word)).map("".join)


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
        # Ints in range are accepted too, stored as float(value); capped where floats still hold ints exactly
        ints = st.integers(-10**15 if self.lo is None else math.ceil(self.lo),
                           10**15 if self.hi is None else math.floor(self.hi))
        numbers = floats | ints
        return numbers | st.none() if self.nullable else numbers

    def expected(self, value: Any) -> Any:
        return float(value) if isinstance(value, int) else value

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
        # A member added to the enum but not listed here must fail, so the table stays the record of stored values.
        # Values are case-sensitive: other casings of a stored value must fail too
        recased = {c for v in self.values for c in (v.lower(), v.upper()) if c not in self.values}
        return [None, ""] + [m.value for m in self.enum if m.value not in self.values] + sorted(recased)

    def __str__(self) -> str:
        return self.enum.__name__


@dataclass(frozen=True)
class Flag:
    """A bool field. Also accepts pydantic's bool words in any case, and 0/1, stored as the matching bool."""

    def valid(self) -> st.SearchStrategy:
        return (st.booleans() | st.sampled_from([0, 1]) |
                st.sampled_from(sorted(_BOOL_WORDS)).flatmap(_random_case))

    def invalid(self) -> st.SearchStrategy:
        return (st.none() | st.integers().filter(lambda i: i not in (0, 1)) |
                _LETTERS.filter(lambda s: s.lower() not in _BOOL_WORDS))

    def expected(self, value: Any) -> bool:
        return value.lower() in _TRUE_WORDS if isinstance(value, str) else bool(value)

    def edges_in(self) -> List[Any]:
        return [False, True, 0, 1, "True", "False", "yes", "NO"]

    def edges_out(self) -> List[Any]:
        return [None, 2, "", "maybe"]

    def __str__(self) -> str:
        return "bool"


@dataclass(frozen=True)
class Text:
    """A str field with no rule beyond its type."""
    nullable: bool = False

    def valid(self) -> st.SearchStrategy:
        return st.text() | st.none() if self.nullable else st.text()

    def invalid(self) -> st.SearchStrategy:
        non_str = st.integers() | st.floats() | st.booleans()
        return non_str if self.nullable else non_str | st.none()

    def edges_in(self) -> List[Any]:
        return [""] + ([None] if self.nullable else [])

    def edges_out(self) -> List[Any]:
        return [0] + ([] if self.nullable else [None])

    def __str__(self) -> str:
        return "str" + (" or None" if self.nullable else "")


_OCTETS = st.lists(st.integers(0, 255), min_size=4, max_size=4)


def _dotted(octets: List[int]) -> str:
    return ".".join(map(str, octets))


@dataclass(frozen=True)
class IPv4:
    """A str field holding a dotted-quad IPv4 address."""

    def valid(self) -> st.SearchStrategy:
        return st.ip_addresses(v=4).map(str)

    def invalid(self) -> st.SearchStrategy:
        # Four octets with one replaced by 256..999, or 1-3 / 5-6 valid octets
        octet_too_big = st.tuples(_OCTETS, st.integers(0, 3), st.integers(256, 999)).map(
            lambda t: _dotted(t[0][:t[1]] + [t[2]] + t[0][t[1] + 1:]))
        wrong_count = st.lists(st.integers(0, 255), min_size=1, max_size=6).filter(lambda o: len(o) != 4).map(_dotted)
        return (st.ip_addresses(v=6).map(str) | octet_too_big | wrong_count | _LETTERS | st.just("") |
                st.none() | st.integers())

    def edges_in(self) -> List[Any]:
        return ["0.0.0.0", "127.0.0.1", "255.255.255.255"]

    def edges_out(self) -> List[Any]:
        return ["256.0.0.0", "0.0.0.256", "1.2.3", "1.2.3.4.5", "::1", "", None]

    def __str__(self) -> str:
        return "IPv4 address"


# Short domains: full-length ones (up to 255 chars) overrun Hypothesis's per-example data budget
_DOMAINS = domains(max_length=40, max_element_length=12)
_HOSTS = st.ip_addresses(v=4).map(str) | _DOMAINS | st.just("localhost")
_TCP_UDP_PORTS = st.integers(1, 65535)
# One character the host pattern [a-zA-Z0-9.-] does not allow
_BAD_HOST_CHAR = st.sampled_from([" ", "_", "/", "@", "!", ",", "é", "#"])


def _not_ipv4_quad(octets: List[int]) -> bool:
    return len(octets) != 4 or any(o > 255 for o in octets)


# Hosts made of allowed characters that are still not an IPv4 address or an RFC 1123 hostname
_BAD_HOSTS = st.one_of(
    st.lists(st.integers(0, 999), min_size=1, max_size=6).filter(_not_ipv4_quad).map(_dotted),  # numeric, not IPv4
    _DOMAINS.map(lambda d: "-" + d),                                     # label starts with a hyphen
    _DOMAINS.map(lambda d: d.replace(".", "-.", 1)),                     # label ends with a hyphen
    _DOMAINS.map(lambda d: d.replace(".", "..", 1)),                     # empty label
    _DOMAINS.map(lambda d: "." + d) | _DOMAINS.map(lambda d: d + ".."),  # leading dot / two trailing dots
    st.tuples(_DOMAINS, st.integers(0, 999)).map(lambda t: f"{t[0]}.{t[1]}"),  # all-digit last label
    st.integers(64, 80).map(lambda n: "a" * n + ".com"),                 # label over 63 chars
    st.integers(254, 300).map(lambda n: ("a." * n)[:n - 3] + "com"),     # name over 253 chars
)


@dataclass(frozen=True)
class HostPort:
    """A str field holding "host:port" or empty. Host is an IPv4 address or an RFC 1123 hostname (localhost
    included), port 1..65535. None and whitespace are stored as "", and the value is stored stripped."""

    def valid(self) -> st.SearchStrategy:
        target = st.tuples(_HOSTS, _TCP_UDP_PORTS).map(lambda t: f"{t[0]}:{t[1]}")
        padded = st.tuples(st.sampled_from(["", " ", "  "]), target, st.sampled_from(["", " ", "\t"])).map("".join)
        return padded | st.sampled_from([None, "", "   "])

    def invalid(self) -> st.SearchStrategy:
        def with_bad_char(t: Tuple[str, int, str]) -> str:
            # Strictly inside the host: a leading space would just be whitespace the validator strips
            host, pos, char = t
            pos = 1 + pos % (len(host) - 1)
            return host[:pos] + char + host[pos:]

        ipv6 = st.tuples(st.ip_addresses(v=6).map(str), _TCP_UDP_PORTS, st.booleans()).map(
            lambda t: f"[{t[0]}]:{t[1]}" if t[2] else f"{t[0]}:{t[1]}")
        port_out = st.tuples(_HOSTS, st.just(0) | st.integers(65536, 99999)).map(lambda t: f"{t[0]}:{t[1]}")
        bad_char = st.tuples(_HOSTS, st.integers(0, 50), _BAD_HOST_CHAR).map(with_bad_char)
        bad_host = st.tuples(bad_char | _BAD_HOSTS, _TCP_UDP_PORTS).map(lambda t: f"{t[0]}:{t[1]}")
        malformed = st.one_of(
            _HOSTS,                                                               # no port
            _HOSTS.map(lambda h: f"{h}:"),                                        # empty port
            _TCP_UDP_PORTS.map(lambda p: f":{p}"),                                # no host
            st.tuples(_HOSTS, _LETTERS).map(lambda t: f"{t[0]}:{t[1]}"),          # non-numeric port
            st.tuples(_HOSTS, _TCP_UDP_PORTS, _TCP_UDP_PORTS).map(lambda t: f"{t[0]}:{t[1]}:{t[2]}"),  # extra part
        )
        return ipv6 | port_out | bad_host | malformed | st.integers()

    def expected(self, value: Any) -> str:
        return "" if value is None else value.strip()

    def edges_in(self) -> List[Any]:
        return ["localhost:1", "localhost:65535", "127.0.0.1:20777", "255.255.255.255:80", "my-server.domain:65535",
                "MyPC:80", "1a.example:80", "a" * 63 + ".com:80", ("a." * 125) + "com:80",  # 253-char host
                "nas.lan.:80", ("a." * 125) + "com.:80",  # absolute names: one trailing dot
                "  myhost.com:1234 ",
                "", "   ", None]

    def edges_out(self) -> List[Any]:
        return ["localhost:0", "localhost:65536", "localhost", "localhost:", ":8080", "localhost:abc",
                "host:1:2", "local host:8080", "a_b:80", "[::1]:80", "::1:80",
                "999.999.999.999:80", "256.0.0.1:80", "1.2.3:80", "1.2.3.4.5:80", "010.0.0.1:80",
                "-:80", "-a.com:80", "a-.com:80", "a..b:80", ".host:80", "host..:80", ".:80", "a.123:80",
                "a.123.:80",
                "a" * 64 + ".com:80", "b" + ("a." * 125) + "com:80", 5]  # last host: 254 chars

    def __str__(self) -> str:
        return "host:port or empty"


def _range_str(lo: Any, hi: Any, nullable: bool) -> str:
    return f"{'' if lo is None else lo}..{'' if hi is None else hi}" + (" or None" if nullable else "")


FieldSpec = Union[IntRange, FloatRange, IntChoice, Choice, Flag, Text, IPv4, HostPort]

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
        "bind_address": IPv4(),
        "udp_tyre_delta_action_code": UDP_ACTION_CODE,
        "udp_custom_action_code": UDP_ACTION_CODE,
        "wdt_interval_sec": IntRange(1, 120),
        "enable_pkt_ordering": FLAG,
        "udp_action_button_debounce_ms": IntRange(0, 500),
    },
    CaptureSettings: _flags("post_race_data_autosave", "post_quali_data_autosave", "post_fp_data_autosave",
                            "post_tt_data_autosave", "save_race_ctrl_msg", "just_in_case_autosave",
                            "unified_save_format"),
    SaveViewerSettings: _flags("enable_write_api"),
    LapAnalyzerSettings: _flags("enable", "record_in_race", "record_in_quali", "record_in_fp", "record_in_tt"),
    LapAnalyzerSensorSettings: _flags(*LapAnalyzerSensorSettings.model_fields),
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
    ForwardingSettings: dict.fromkeys(("target_1", "target_2", "target_3"), HostPort()),
    StreamOverlaySettings: {
        "show_sample_data_at_start": FLAG,
        "stream_overlay_update_interval_ms": IntRange(lo=50),
    },
    # With HTTPS off (the default) the paths are plain optional strings; existence is checked only when enabled
    HttpsSettings: {"enabled": FLAG, "key_file_path": Text(nullable=True), "cert_file_path": Text(nullable=True)},
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
    OpacityOverride: {"enabled": FLAG, "value": PERCENT},
}

# Fields no spec above can express; their example tests stay the only coverage
EXAMPLE_ONLY: Dict[Type[BaseModel], Set[str]] = {
    CaptureSettings: {"session_dir"},           # non-empty validator
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
        expected = self.spec.expected(value) if hasattr(self.spec, "expected") else value
        stored = getattr(model, self.field)
        # 1 == True, so also check a bool field stores a real bool
        assert stored == expected and isinstance(stored, bool) == isinstance(expected, bool), \
            f"{self} ({self.spec}) stored {stored!r} for {value!r}, expected {expected!r}"

    def assert_rejects(self, value: Any) -> None:
        with pytest.raises(ValidationError) as exc:
            self.build(value)
        assert self.field_errors(exc.value), f"{self} ({self.spec}) {value!r} failed elsewhere: {exc.value.errors()}"


CASES = [pytest.param(Case(model, field, spec), id=f"{model.__name__}.{field}")
         for model, specs in FIELDS.items() for field, spec in specs.items()]

# ------------------------- WHOLE-SETTINGS STRATEGY --------------------------------------------------------------------

# Up to 3 forwarding targets, distinct even with localhost aliases folded, none on localhost (no loop with telemetry)
_FORWARDING = st.lists(
    st.tuples(st.ip_addresses(v=4).map(str) | _DOMAINS, _TCP_UDP_PORTS).map(lambda t: f"{t[0]}:{t[1]}"),
    max_size=3, unique_by=str.lower).filter(lambda ts: not any(t.startswith("127.") for t in ts)).map(
        lambda targets: {f"target_{i + 1}": t for i, t in enumerate(targets + [""] * (3 - len(targets)))})

# Values for EXAMPLE_ONLY fields, so whole-settings strategies cover them too, plus fields whose cross-field rules
# need a joint draw (forwarding targets). Dict containers are left at defaults
EXAMPLE_ONLY_VALUES: Dict[Type[BaseModel], st.SearchStrategy] = {
    CaptureSettings: st.fixed_dictionaries({
        "session_dir": st.text(alphabet=string.ascii_letters + string.digits + "_-/", min_size=1)}),
    # Enabling HTTPS needs real key/cert files; a test that makes them passes its own via extra
    HttpsSettings: st.just({"enabled": False}),
    ForwardingSettings: _FORWARDING,
    HudSettings: st.fixed_dictionaries({"layout": st.dictionaries(
        st.sampled_from([o.value for o in OverlayId]),
        st.fixed_dictionaries({
            **{name: spec.valid() for name, spec in FIELDS[OverlayPosition].items()},
            "opacity_override": st.fixed_dictionaries(
                {name: spec.valid() for name, spec in FIELDS[OpacityOverride].items()}),
        }),
        max_size=4)}),
}


def _is_udp_action_code(field: Any) -> bool:
    return bool((field.json_schema_extra or {}).get("udp_action_code"))


def _port_type(field: Any) -> Optional[str]:
    return (field.json_schema_extra or {}).get("port_type")


@st.composite
def png_settings_dicts(draw: st.DrawFn,
                       extra: Optional[Dict[Type[BaseModel], st.SearchStrategy]] = None) -> Dict[str, Any]:
    """A PngSettings input dict with every FIELDS and EXAMPLE_ONLY_VALUES field drawn from its valid values.

    Cross-field rules are satisfied by construction: UDP action codes distinct, ports distinct per protocol.
    Validate the result anyway and reject() the draw if a rule still fails.
    extra adds or replaces a model's EXAMPLE_ONLY_VALUES entry (e.g. HTTPS paths that need real files).
    """
    example_values = {**EXAMPLE_ONLY_VALUES, **(extra or {})}
    all_fields = [(m, n, f) for m in FIELDS for n, f in m.model_fields.items() if n in FIELDS[m]]
    num_codes = sum(_is_udp_action_code(f) for _, _, f in all_fields)
    codes = iter(draw(st.permutations(list(range(1, 13)) + [None] * num_codes)))
    ports: Dict[str, Any] = {}
    for port_type in {_port_type(f) for _, _, f in all_fields} - {None}:
        specs = [FIELDS[m][n] for m, n, f in all_fields if _port_type(f) == port_type]
        assert all(s == specs[0] for s in specs), f"{port_type} port fields have different specs"
        ports[port_type] = iter(draw(st.lists(specs[0].valid(), min_size=len(specs), max_size=len(specs),
                                              unique=True), label=f"{port_type} ports"))

    def build(model: Type[BaseModel]) -> Dict[str, Any]:
        values: Dict[str, Any] = {}
        for name, spec in FIELDS.get(model, {}).items():
            field = model.model_fields[name]
            if _is_udp_action_code(field):
                values[name] = next(codes)
            elif _port_type(field):
                values[name] = next(ports[_port_type(field)])
            else:
                values[name] = draw(spec.valid(), label=f"{model.__name__}.{name}")
        if model in example_values:
            values.update(draw(example_values[model], label=model.__name__))
        for name in _nested_model_fields(model):
            values[name] = build(model.model_fields[name].annotation)
        return values

    return build(PngSettings)

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
    type (a list or dict included), or None for a non-nullable field.

    Expected: a ValidationError located at this field.
    """
    case.assert_rejects(data.draw(case.spec.invalid() | _CONTAINERS, label=case.field))


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
    for value in case.spec.edges_out() + [[1, 2, 3], {}]:
        case.assert_rejects(value)
