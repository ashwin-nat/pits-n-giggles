"""Step1 deterministic gates over real MCP readers; no service/model/audio."""

import importlib
import logging
from dataclasses import replace
from types import SimpleNamespace

import pytest

from apps.voice.contracts import Intent
from apps.voice.session_tracker import SessionProgressTracker
from apps.voice.telemetry import TelemetryAdapter


@pytest.fixture
def direct():
    return importlib.import_module("apps.voice.direct_answers")


@pytest.fixture
def cache(monkeypatch):
    root = "apps.mcp_server.mcp_server.tools."
    modules = {
        name: importlib.import_module(root + name)
        for name in (
            "common",
            "get_session_info",
            "get_race_table",
            "get_tyre_wear",
            "get_fuel_info",
        )
    }
    row = {
        "driver-info": {
            "index": 3,
            "name": "Driver",
            "position": 2,
            "is-player": True,
            "dnf-status": "",
        },
        "tyre-info": {
            "visual-tyre-compound": "Medium",
            "tyre-age": 4,
            "current-wear": {
                "average": 12,
                "front-left-wear": 10,
                "front-right-wear": 11,
                "rear-left-wear": 13,
                "rear-right-wear": 14,
            },
            "wear-prediction": {
                "status": True,
                "rate": {
                    "front-left": 1,
                    "front-right": 2,
                    "rear-left": 3,
                    "rear-right": 4,
                },
            },
        },
        "fuel-info": {
            "fuel-in-tank": 0.0,
            "fuel-capacity": 110,
            "fuel-mix": "Standard",
            "last-lap-fuel-used": 2,
            "current-fuel-rate": 2.1,
            "surplus-laps-game": 0.0,
            "target-fuel-rate-average": 2,
            "target-fuel-rate-next-lap": 1.9,
            "surplus-laps-png": -0.5,
        },
    }
    other = {
        "driver-info": {
            "index": 4,
            "name": "Alex",
            "position": 1,
            "is-player": False,
            "dnf-status": "",
        }
    }
    raw = {
        "session-uid": 42,
        "event-type": "Race",
        "formula": "F1",
        "circuit": "Monza",
        "race-ended": False,
        "is-spectating": False,
        "session-duration-so-far": 20.0,
        "session-time-left": 100.0,
        "current-lap": 5,
        "total-laps": 20,
        "air-temperature": 22,
        "track-temperature": 30,
        "safety-car-status": "None",
        "num-sc": 0,
        "num-vsc": 0,
        "num-red-flags": 0,
        "table-entries": [row, other],
        "weather-forecast-samples": [
            {
                "session-type": "Practice 1",
                "time-offset": 0,
                "weather": "Heavy rain",
                "rain-percentage": 100,
            },
            {
                "session-type": "Race",
                "time-offset": 10,
                "weather": "Light rain",
                "rain-percentage": 70,
            },
            {
                "session-type": "Race",
                "time-offset": 0,
                "weather": "Clear",
                "rain-percentage": 0,
            },
        ],
    }
    clock = SimpleNamespace(epoch=1000.0, mono=10.0)
    entry = SimpleNamespace(data=raw, ts=clock.epoch)
    monkeypatch.setattr(
        modules["common"],
        "get_state_data",
        lambda key, *args: (
            entry if key == "race-table-update" else SimpleNamespace(data=True)
        ),
    )
    logger = logging.getLogger(__name__)
    builders = {
        "get_session_info": lambda: modules["get_session_info"].get_session_info(
            logger
        ),
        "get_race_table": lambda: modules["get_race_table"].get_race_table(logger),
        "get_player_tyre_wear": lambda: modules["get_tyre_wear"].get_tyre_wear(
            logger, 3
        ),
        "get_player_fuel_info": lambda: modules["get_fuel_info"].get_fuel_info(
            logger, 3
        ),
    }

    class Client:
        async def call_tool(self, tool, args, raise_on_error=False):
            return SimpleNamespace(structured_content=builders[tool]())

    async def collect(topic, target=None):
        adapter = TelemetryAdapter(
            Client(),
            SessionProgressTracker(),
            epoch_clock=lambda: clock.epoch,
            mono_clock=lambda: clock.mono,
        )
        await adapter.collect(Intent(topic, target), clock.mono + 2)
        clock.epoch += 0.1
        clock.mono += 0.1
        entry.ts = clock.epoch
        raw["session-duration-so-far"] += 0.1
        raw["session-time-left"] -= 0.1
        evidence = await adapter.collect(Intent(topic, target), clock.mono + 2)
        assert evidence.reason is None
        return evidence

    return SimpleNamespace(raw=raw, row=row, other=other, collect=collect)


@pytest.mark.parametrize(
    "question,topic,target",
    [
        ("When switch to intermediates?", "weather", "crossover"),
        ("Should I use wet tyres?", "weather", "crossover"),
        ("When will rain start?", "weather", None),
        ("Weather forecast", "weather", None),
        ("What tyres am I on?", "tyres", None),
        ("How long will my tires last?", "tyres", "life"),
        ("Tyre wear rate?", "tyres", "rate"),
        ("How much fuel is left?", "fuel", None),
        ("Fuel burn rate?", "fuel", "rate"),
        ("Who is ahead?", "gaps", "ahead"),
        ("Gap to Alex?", "gaps", "alex"),
        ("Where will I rejoin after pitting?", "pit", None),
        ("When should I box?", "pit", None),
        ("Fuel and tyre wear?", "complex", None),
        ("Tell me a joke", "unknown", None),
        ("Is the fuel pump broken?", "unknown", None),
        ("What is a tyre blanket?", "unknown", None),
        ("I like fuel", "unknown", None),
        ("Who designed the tyres?", "unknown", None),
        ("When do I need inter tyres?", "weather", "crossover"),
        ("How wet is the track?", "weather", "wetness"),
        ("Gap to Alex please", "gaps", "alex"),
    ],
)
def test_routing(direct, question, topic, target):
    assert direct.classify(question) == Intent(topic, target)


def assert_provenance(answer, evidence):
    assert answer.evidence is evidence
    assert answer.card_ids == ()
    assert all(path in evidence.sources for path in answer.evidence_paths)
    assert len(answer.evidence_paths) == len(set(answer.evidence_paths))


async def test_weather_current_session_order_probability(direct, cache):
    e = await cache.collect("weather")
    a = direct.answer_direct(Intent("weather"), e)
    assert a.kind == "fact"
    assert a.text.index("Clear") < a.text.index("Light rain")
    assert "70%" in a.text and "probability" in a.text
    assert "Heavy rain" not in a.text and "wetness" not in a.text
    assert (
        "get_session_info.environment.weather_forecast[1].rain-percentage"
        in a.evidence_paths
    )
    assert_provenance(a, e)


async def test_crossover_is_not_a_recommendation(direct, cache):
    e = await cache.collect("weather")
    a = direct.answer_direct(direct.classify("When switch to intermediates?"), e)
    assert a.kind == "insufficient"
    assert "grip" in a.text and "wetness" in a.text
    assert "Light rain" in a.text and "lap 10" not in a.text
    assert_provenance(a, e)


async def test_current_tyres_do_not_require_rate_history(direct, cache):
    cache.row["tyre-info"]["wear-prediction"]["status"] = False
    e = await cache.collect("tyres")
    a = direct.answer_direct(Intent("tyres"), e)
    assert a.kind == "fact"
    assert all(s in a.text for s in ("Medium", "4 laps", "FL 10%", "RR 14%"))
    assert_provenance(a, e)


async def test_backend_wear_rate_only(direct, cache):
    e = await cache.collect("tyres")
    a = direct.answer_direct(Intent("tyres", "rate"), e)
    assert a.kind == "estimate" and "FL 1%/lap" in a.text
    assert_provenance(a, e)
    b = direct.answer_direct(Intent("tyres", "life"), e)
    assert b.kind == "insufficient" and "history" in b.text


async def test_actual_fuel_key_mismatch_is_not_repaired_by_guess(direct, cache):
    e = await cache.collect("fuel")
    a = direct.answer_direct(Intent("fuel"), e)
    assert "0 kg" in a.text and "game estimate" in a.text
    assert "0 laps" in a.text
    b = direct.answer_direct(Intent("fuel", "rate"), e)
    assert b.kind == "insufficient" and "history" in b.text
    assert_provenance(a, e)


async def test_fuel_backend_estimates(direct, cache):
    cache.row["fuel-info"]["curr-fuel-rate"] = 2.1
    e = await cache.collect("fuel")
    a = direct.answer_direct(Intent("fuel", "rate"), e)
    assert a.kind == "estimate" and "2.1 kg/lap" in a.text
    assert_provenance(a, e)


async def test_gap_names_positions_not_delta_subtraction(direct, cache):
    cache.other["driver-info"]["delta-to-leader"] = 1000
    e = await cache.collect("gaps", "alex")
    a = direct.answer_direct(Intent("gaps", "alex"), e)
    assert "Alex" in a.text and "P1" in a.text
    assert "seconds" in a.text and "cannot" in a.text.lower()
    assert a.kind == "insufficient"
    assert_provenance(a, e)


@pytest.mark.parametrize("target", ["missing", "a"])
async def test_gap_unknown_or_ambiguous_reference(direct, cache, target):
    if target == "a":
        cache.raw["table-entries"].append(
            {
                "driver-info": {
                    "index": 5,
                    "name": "Alexis",
                    "position": 3,
                    "is-player": False,
                    "dnf-status": "",
                }
            }
        )
    e = await cache.collect("gaps", target)
    a = direct.answer_direct(Intent("gaps", target), e)
    assert a.kind == "insufficient" and "P1" not in a.text


async def test_pit_refuses_window_with_relevant_facts(direct, cache):
    e = await cache.collect("pit")
    a = direct.answer_direct(Intent("pit"), e)
    assert a.kind == "insufficient"
    assert "pit-loss" in a.text and "pit-state" in a.text
    assert "Medium" in a.text and "0 kg" in a.text
    assert_provenance(a, e)


@pytest.mark.parametrize(
    "reason",
    [
        "Stale receipt",
        "Disconnected",
        "Deadline exceeded",
        "Session ended",
        "Frozen progress",
    ],
)
async def test_invalid_evidence_no_cached_numbers(direct, cache, reason):
    e = replace(await cache.collect("tyres"), reason=reason)
    a = direct.answer_direct(Intent("tyres"), e)
    assert a.kind == "insufficient" and reason in a.text
    assert "Medium" not in a.text and a.evidence_paths == ()
    assert_provenance(a, e)


@pytest.mark.parametrize(
    "value", [-0.001, 100.001, True, float("nan"), float("inf"), None, "12"]
)
async def test_invalid_wear_not_spoken(direct, cache, value):
    e = await cache.collect("tyres")
    facts = {
        **e.facts,
        "get_player_tyre_wear": {
            **e.facts["get_player_tyre_wear"],
            "fl_wear_pct": value,
        },
    }
    a = direct.answer_direct(Intent("tyres"), replace(e, facts=facts))
    assert "FL " not in a.text


@pytest.mark.parametrize("value", [0, 0.001, 99.999, 100])
async def test_valid_wear_boundaries(direct, cache, value):
    cache.row["tyre-info"]["current-wear"]["front-left-wear"] = value
    e = await cache.collect("tyres")
    a = direct.answer_direct(Intent("tyres"), e)
    assert f"FL {value:g}%" in a.text


@pytest.mark.parametrize(
    "offset,probability",
    [
        (-1, 70),
        (True, 70),
        (float("inf"), 70),
        (10, -1),
        (10, 101),
        (10, True),
        (10, float("nan")),
    ],
)
async def test_invalid_forecast_samples(direct, cache, offset, probability):
    cache.raw["weather-forecast-samples"][1].update(
        {"time-offset": offset, "rain-percentage": probability}
    )
    e = await cache.collect("weather")
    a = direct.answer_direct(Intent("weather"), e)
    assert "Light rain" not in a.text


async def test_forecast_never_borrows_practice(direct, cache):
    cache.raw["weather-forecast-samples"] = cache.raw["weather-forecast-samples"][:1]
    e = await cache.collect("weather")
    a = direct.answer_direct(Intent("weather"), e)
    assert a.kind == "insufficient" and "Heavy rain" not in a.text


@pytest.mark.parametrize(
    "field,value",
    [
        ("session_uid", True),
        ("player_index", -1),
        ("expires_mono", float("nan")),
        ("progress_valid_until_mono", 0),
    ],
)
async def test_invalid_metadata(direct, cache, field, value):
    e = replace(await cache.collect("tyres"), **{field: value})
    a = direct.answer_direct(Intent("tyres"), e)
    assert a.kind == "insufficient" and a.evidence_paths == ()


@pytest.mark.parametrize(
    "tool,flag",
    [
        ("get_player_tyre_wear", "wear_rate_available"),
        ("get_player_fuel_info", "data_sufficient"),
    ],
)
@pytest.mark.parametrize("value", [False, 1, "true", None])
async def test_rates_require_explicit_backend_flag(direct, cache, tool, flag, value):
    topic = "tyres" if tool == "get_player_tyre_wear" else "fuel"
    cache.row["fuel-info"]["curr-fuel-rate"] = 2.1
    e = await cache.collect(topic)
    e = replace(e, facts={**e.facts, tool: {**e.facts[tool], flag: value}})
    a = direct.answer_direct(Intent(topic, "rate"), e)
    assert a.kind == "insufficient" and a.evidence_paths == ()


@pytest.mark.parametrize("value", [True, -0.001, float("inf"), float("nan"), "2"])
async def test_invalid_fuel_quantity(direct, cache, value):
    e = await cache.collect("fuel")
    e = replace(
        e,
        facts={
            **e.facts,
            "get_player_fuel_info": {
                **e.facts["get_player_fuel_info"],
                "fuel_in_tank_kg": value,
            },
        },
    )
    a = direct.answer_direct(Intent("fuel"), e)
    assert "Fuel remaining" not in a.text


async def test_missing_provenance_cannot_be_spoken(direct, cache):
    e = replace(await cache.collect("tyres"), sources=())
    a = direct.answer_direct(Intent("tyres", "rate"), e)
    assert a.kind == "insufficient" and a.evidence_paths == ()


async def test_wetness_not_inferred_from_rain_probability(direct, cache):
    e = await cache.collect("weather")
    a = direct.answer_direct(Intent("weather", "wetness"), e)
    assert a.kind == "insufficient"
    assert "wetness is unavailable" in a.text
    assert "probability 70%" in a.text


async def test_inactive_gap_target(direct, cache):
    cache.other["driver-info"]["dnf-status"] = "DNF"
    e = await cache.collect("gaps", "alex")
    a = direct.answer_direct(Intent("gaps", "alex"), e)
    assert a.kind == "insufficient" and "P1" not in a.text


@pytest.mark.parametrize(
    "condition", ["LIGHT_CLOUD", "LIGHT_RAIN", "HEAVY_RAIN", "THUNDERSTORM"]
)
async def test_real_weather_enum_labels(direct, cache, condition):
    from lib.f1_types.packet_1_session_data import WeatherForecastSample

    label = str(WeatherForecastSample.WeatherCondition[condition])
    cache.raw["weather-forecast-samples"][1]["weather"] = label
    e = await cache.collect("weather")
    a = direct.answer_direct(Intent("weather"), e)
    assert label in a.text


async def test_real_inters_compound_label(direct, cache):
    from lib.f1_types.common import VisualTyreCompound

    cache.row["tyre-info"]["visual-tyre-compound"] = str(VisualTyreCompound.INTER)
    e = await cache.collect("tyres")
    a = direct.answer_direct(Intent("tyres"), e)
    assert "Current compound: Inters." in a.text


async def test_pure_function_does_not_read_real_clock(direct, cache):
    e = await cache.collect("tyres")
    assert direct.answer_direct(Intent("tyres"), e).kind == "fact"
    assert direct.answer_direct(Intent("fuel"), e).kind == "insufficient"
    assert direct.answer_direct(Intent("unknown"), e) is None
    assert direct.answer_direct(Intent("complex"), e) is None
