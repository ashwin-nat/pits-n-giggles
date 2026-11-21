"""Pure, conservative templates over validated Step0 evidence.

No clock or I/O: collection and pre-speech revalidation own actual deadlines.
Cache receipt/progress validation does not establish per-field game-packet age.
"""

import math
import re
from collections.abc import Mapping

from .contracts import Answer, Evidence, Intent

_SESSION = "get_session_info"
_TYRES = "get_player_tyre_wear"
_FUEL = "get_player_fuel_info"
_TABLE = "get_race_table"
_CORNERS = (("fl", "FL"), ("fr", "FR"), ("rl", "RL"), ("rr", "RR"))


def classify(question: str) -> Intent:
    """Route only recognized factual requests; ambiguous topics go to fallback."""
    q = " ".join(re.findall(r"[\w]+", question.casefold()))
    q = re.sub(r"\s+please$", "", q)
    wetness = bool(re.search(r"\b(wetness)\b|how wet|track wet", q))
    wet = bool(re.search(r"\b(intermediates?|inters?|wets?)\b", q)) and not wetness
    weather = wet or wetness or bool(re.search(r"\b(weather|rain|forecast)\b", q))
    tyres = bool(re.search(r"\b(tyres?|tires?|compound|wear)\b", q)) and not wet
    fuel = bool(re.search(r"\bfuel\b", q))
    pit = bool(re.search(r"\b(pit|pits|pitting|box|rejoin|undercut|overcut)\b", q))
    gaps = bool(re.search(r"\b(gaps?|ahead|behind|closing)\b", q))
    topics = [
        t
        for t, yes in (
            ("weather", weather),
            ("tyres", tyres),
            ("fuel", fuel),
            ("pit", pit),
            ("gaps", gaps),
        )
        if yes
    ]
    if len(topics) > 1:
        # Wet-tyre crossover is one weather question, not a pit prediction.
        if weather and pit and not (fuel or tyres or gaps) and wet:
            return Intent("weather", "crossover")
        return Intent("complex")
    if not topics or re.search(
        r"\b(pump|blanket|joke|define|meaning|designed|like)\b", q
    ):
        return Intent("unknown")
    topic = topics[0]
    if topic == "weather":
        return Intent(
            topic,
            "wetness" if wetness else "crossover" if wet or "crossover" in q else None,
        )
    if topic == "tyres":
        target = "life" if re.search(r"\b(last|life|remaining)\b", q) else None
        if re.search(r"\b(rate|degradation|degrading)\b", q):
            target = "rate"
        return Intent(topic, target)
    if topic == "fuel":
        if (
            not re.search(
                r"\b(left|remaining|much|quantity|level|status|surplus|"
                r"deficit|enough|burn|rate|target|save|saving)\b",
                q,
            )
            and q != "fuel"
        ):
            return Intent("unknown")
        target = "rate" if re.search(r"\b(burn|rate|target)\b", q) else None
        return Intent(topic, target)
    if topic == "gaps":
        for direction in ("ahead", "behind"):
            if direction in q.split():
                return Intent(topic, direction)
        match = re.fullmatch(r"(?:what is (?:the )?)?gap to (.+)", q)
        return Intent(topic, match[1] if match else None)
    return Intent(topic)


def _number(value, low=0, high=math.inf):
    return type(value) in (int, float) and math.isfinite(value) and low <= value <= high


def _mapping(value):
    return value if isinstance(value, Mapping) else {}


def _metadata_valid(e):
    session = _mapping(e.facts.get(_SESSION))
    identity = _mapping(session.get("identity"))
    control = _mapping(session.get("race_control"))
    return (
        type(e.session_uid) is int
        and e.session_uid > 0
        and type(e.player_index) is int
        and e.player_index >= 0
        and type(e.generation) is int
        and e.generation >= 0
        and _number(e.expires_mono)
        and e.expires_mono > 0
        and _number(e.progress_valid_until_mono)
        and e.progress_valid_until_mono > 0
        and type(identity.get("session_uid")) is int
        and identity.get("session_uid") == e.session_uid
        and identity.get("session-ended") is False
        and control.get("is_spectating") is False
        and bool(e.stamps)
        and all(
            _number(s.cache_received_epoch) and _number(s.collected_mono)
            for s in e.stamps
        )
    )


def _weather(e):
    session = _mapping(e.facts.get(_SESSION))
    kind = _mapping(session.get("identity")).get("session_type")
    samples = _mapping(session.get("environment")).get("weather_forecast")
    if not isinstance(kind, str) or not isinstance(samples, (tuple, list)):
        return [], []
    valid = []
    for i, sample in enumerate(samples):
        sample = _mapping(sample)
        offset, probability = sample.get("time-offset"), sample.get("rain-percentage")
        weather = sample.get("weather")
        if (
            sample.get("session-type") == kind
            and _number(offset)
            and _number(probability, 0, 100)
            and weather
            in (
                "Clear",
                "Light Cloud",
                "Light cloud",
                "Overcast",
                "Light Rain",
                "Light rain",
                "Heavy Rain",
                "Heavy rain",
                "Storm",
                "Thunderstorm",
            )
        ):
            prefix = f"{_SESSION}.environment.weather_forecast[{i}]"
            paths = [f"{_SESSION}.identity.session_type"] + [
                f"{prefix}.{k}"
                for k in ("session-type", "time-offset", "weather", "rain-percentage")
            ]
            if all(p in e.sources for p in paths):
                valid.append((offset, i, probability, weather, paths))
    texts, paths = [], []
    for offset, _, probability, weather, used in sorted(valid)[:3]:
        texts.append(
            f"{weather} at +{offset:g} min, rain probability {probability:g}%."
        )
        paths.extend(used)
    return texts, paths


def _flat(e, tool):
    data = _mapping(e.facts.get(tool))
    index = data.get("driver_index")
    return data if type(index) is int and index == e.player_index else {}


def _tyres(e, target):
    data = _flat(e, _TYRES)
    texts, paths = [], []

    def add(key, text, valid):
        path = f"{_TYRES}.{key}"
        if valid and path in e.sources:
            texts.append(text)
            paths.append(path)

    if target == "rate":
        if (
            data.get("wear_rate_available") is True
            and f"{_TYRES}.wear_rate_available" in e.sources
        ):
            for short, label in _CORNERS:
                key = f"{short}_rate_pct_per_lap"
                value = data.get(key)
                if _number(value, 0, 100):
                    add(key, f"{label} {value:g}%/lap.", True)
            if texts:
                paths.append(f"{_TYRES}.wear_rate_available")
                return texts, paths, "estimate"
        return ["Insufficient validated tyre wear rate history."], [], "insufficient"
    compound = data.get("tyre_compound")
    add(
        "tyre_compound",
        f"Current compound: {compound}.",
        compound
        in (
            "Soft",
            "Medium",
            "Hard",
            "Intermediate",
            "Inter",
            "Inters",
            "Wet",
            "Super Soft",
            "Ultra Soft",
            "Hyper Soft",
            "Super Hard",
        ),
    )
    age = data.get("tyre_age_laps")
    if type(age) is int and age >= 0:
        add("tyre_age_laps", f"Age {age} laps.", True)
    for short, label in _CORNERS:
        key = f"{short}_wear_pct"
        value = data.get(key)
        if _number(value, 0, 100):
            add(key, f"{label} {value:g}% wear.", True)
    if target == "life":
        return (
            ["Cannot determine remaining tyre life without validated stint history."]
            + texts,
            paths,
            "insufficient",
        )
    return (
        texts or ["Current tyre data unavailable."],
        paths,
        "fact" if texts else "insufficient",
    )


def _fuel(e, target):
    data = _flat(e, _FUEL)
    texts, paths = [], []
    fields = (
        (
            ("avg_burn_rate_kg_per_lap", "Backend estimated burn", "kg/lap", 0),
            ("target_burn_rate_kg_per_lap", "Backend target burn", "kg/lap", 0),
            ("target_next_lap_fuel_kg", "Backend next-lap target", "kg", 0),
        )
        if target == "rate"
        else (
            ("fuel_in_tank_kg", "Fuel remaining", "kg", 0),
            ("surplus_laps_builtin", "Fuel surplus (game estimate)", "laps", -math.inf),
            ("surplus_laps_live", "Fuel surplus (backend estimate)", "laps", -math.inf),
        )
    )
    sufficient = (
        data.get("data_sufficient") is True
        and _number(data.get("avg_burn_rate_kg_per_lap"), 0.000001)
        and f"{_FUEL}.data_sufficient" in e.sources
        and f"{_FUEL}.avg_burn_rate_kg_per_lap" in e.sources
    )
    for key, label, unit, low in fields:
        derived = key not in ("fuel_in_tank_kg", "surplus_laps_builtin")
        if derived and not sufficient:
            continue
        value = data.get(key)
        path = f"{_FUEL}.{key}"
        if _number(value, low) and path in e.sources:
            texts.append(f"{label}: {value:g} {unit}.")
            paths.append(path)
            if derived:
                paths.extend(
                    (f"{_FUEL}.data_sufficient", f"{_FUEL}.avg_burn_rate_kg_per_lap")
                )
    if not texts:
        return (
            [
                (
                    "Insufficient validated fuel burn history."
                    if target == "rate"
                    else "Fuel quantity and surplus unavailable."
                )
            ],
            [],
            "insufficient",
        )
    return texts, paths, "estimate" if target == "rate" else "fact"


def _gaps(e, target):
    rows = _mapping(e.facts.get(_TABLE)).get("standings", ())
    if not isinstance(rows, (tuple, list)):
        rows = ()
    rows = [(i, _mapping(_mapping(r).get("driver_info"))) for i, r in enumerate(rows)]
    players = [
        (i, r)
        for i, r in rows
        if r.get("is_player") is True
        and type(r.get("index")) is int
        and r["index"] == e.player_index
    ]
    refusal = (
        "Cannot report seconds or closing rate: "
        "same-lap timing compatibility is unavailable."
    )
    if len(players) != 1 or type(players[0][1].get("position")) is not int:
        return ["Player position unavailable.", refusal], []
    player = players[0][1]
    candidates = []
    for i, row in rows:
        pos = row.get("position")
        name = row.get("driver_name")
        if (
            type(pos) is not int
            or pos < 1
            or not isinstance(name, str)
            or not name.strip()
            or row.get("dnf_status") != ""
            or row.get("is_player") is not False
        ):
            continue
        if (
            (target == "ahead" and pos == player["position"] - 1)
            or (target == "behind" and pos == player["position"] + 1)
            or (
                target not in (None, "ahead", "behind")
                and target.casefold() in name.casefold()
            )
        ):
            candidates.append((i, row))
    if len(candidates) != 1:
        return ["No unique active target found.", refusal], []
    i, row = candidates[0]
    prefix = f"{_TABLE}.standings[{i}].driver_info"
    paths = [f"{prefix}.{k}" for k in ("driver_name", "position", "dnf_status")]
    if not all(p in e.sources for p in paths):
        return ["Target evidence unavailable.", refusal], []
    return [f"{row['driver_name']} is P{row['position']}.", refusal], paths


def answer_direct(intent: Intent, evidence: Evidence) -> Answer | None:
    """Preserve original evidence; never renew it or invent strategy inputs."""
    if intent.topic not in ("weather", "tyres", "fuel", "gaps", "pit"):
        return None
    if evidence.reason is not None:
        return Answer(
            f"Telemetry unavailable: {evidence.reason}.",
            "insufficient",
            evidence,
            (),
            (),
        )
    if evidence.topic != intent.topic or not _metadata_valid(evidence):
        return Answer(
            "Telemetry metadata unavailable or invalid.",
            "insufficient",
            evidence,
            (),
            (),
        )
    if intent.topic == "weather":
        texts, paths = _weather(evidence)
        kind = "fact" if texts else "insufficient"
        if not texts:
            texts = ["No applicable current-session forecast available."]
        if intent.target == "wetness":
            texts.insert(
                0,
                "Measured track wetness is unavailable; "
                "rain probability is not wetness.",
            )
            kind = "insufficient"
        if intent.target == "crossover":
            texts.insert(
                0,
                "Cannot determine intermediate/wet crossover "
                "without measured grip and track wetness.",
            )
            kind = "insufficient"
    elif intent.topic == "tyres":
        texts, paths, kind = _tyres(evidence, intent.target)
    elif intent.topic == "fuel":
        texts, paths, kind = _fuel(evidence, intent.target)
    elif intent.topic == "gaps":
        texts, paths = _gaps(evidence, intent.target)
        kind = "insufficient"
    else:
        tyre_text, tyre_paths, _ = _tyres(evidence, None)
        fuel_text, fuel_paths, _ = _fuel(evidence, None)
        texts = [
            "Cannot predict a pit window, rejoin position or optimal pit lap: "
            "pit-loss, pit-state and window inputs are unavailable."
        ]
        texts += tyre_text + fuel_text
        paths = tyre_paths + fuel_paths
        kind = "insufficient"
    return Answer(" ".join(texts), kind, evidence, tuple(dict.fromkeys(paths)), ())
