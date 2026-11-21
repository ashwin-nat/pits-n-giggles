"""Compact live-telemetry snapshot for the local (offline) engineer.

Small local LLMs on CPU are too slow to run a multi-round tool-calling loop, so
instead we fetch the relevant MCP tools directly (in parallel, ~50 ms, no LLM),
trim them to the numbers that matter and hand the LLM one short text block.
"""

import asyncio
import json
import logging

from dataclasses import replace
from collections.abc import Callable, Mapping

from .contracts import Evidence, Intent, SourceStamp
from .session_tracker import SessionProgressTracker, finite
from typing import Any, Dict, Iterator, List, Optional, Tuple

LOGGER = logging.getLogger(__name__)

ROW_KEYS = (
    "driver_name",
    "team_name",
    "position",
    "dnf_status",
    "delta_to_leader_ms",
    "last_lap_time_ms",
    "best_lap_time_ms",
    "tyre_compound",
    "tyre_age",
    "fl_wear_pct",
    "fr_wear_pct",
    "rl_wear_pct",
    "rr_wear_pct",
    "ers_percent",
    "ers_mode",
    "fuel_surplus_laps_live_est",
    "fl_wing_damage",
    "fr_wing_damage",
)
DROP_KEYS = ("schema", "icon", "uid", "timestamp", "error", "ok", "available")


def _walk(obj: Any, path: str = "") -> Iterator[Tuple[str, Any]]:
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _walk(v, f"{path}.{k}" if path else str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk(v, f"{path}[{i}]")
    else:
        yield path, obj


def _leaf(row: Dict[str, Any], key: str) -> Any:
    for p, v in _walk(row):
        if p.split(".")[-1] == key:
            return v
    return None


def _ms(v: Any) -> Any:
    """Milliseconds -> seconds string so the LLM never has to do the maths."""
    if isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0:
        s = v / 1000.0
        return f"{int(s // 60)}:{s % 60:06.3f}" if s >= 60 else f"{s:.3f}s"
    return v


def _flatten(data: Dict[str, Any], limit: int = 40) -> str:
    out: List[str] = []
    for p, v in _walk(data):
        name = p.split(".")[-1]
        if v is None or any(d in p.lower() for d in DROP_KEYS):
            continue
        if name.endswith("_ms"):
            v = _ms(v)
        elif isinstance(v, float):
            v = round(v, 2)
        out.append(f"{p}={v}")
        if len(out) >= limit:
            break
    return ", ".join(out)


def _standings(table: Dict[str, Any]) -> List[Dict[str, Any]]:
    for key in ("standings", "table", "rows", "drivers"):
        rows = table.get(key)
        if isinstance(rows, list):
            return [r for r in rows if isinstance(r, dict)]
    return []


def _row_text(row: Dict[str, Any], player_delta: Optional[float]) -> str:
    parts = []
    for k in ROW_KEYS:
        v = _leaf(row, k)
        if v is None:
            continue
        if k.endswith("_ms"):
            v = _ms(v)
        elif isinstance(v, float):
            v = round(v, 1)
        parts.append(f"{k}={v}")
    delta = _leaf(row, "delta_to_leader_ms")
    if player_delta is not None and isinstance(delta, (int, float)):
        gap = (delta - player_delta) / 1000.0
        parts.append(
            f"gap_to_you={gap:+.3f}s ({'behind you' if gap > 0 else 'ahead of you'})"
        )
    return "  - " + ", ".join(parts)


async def snapshot(client, question: str) -> str:
    """Return a compact text snapshot relevant to ``question``."""

    async def call(tool: str) -> Dict[str, Any]:
        try:
            res = await client.call_tool(tool, {}, raise_on_error=False)
            data = getattr(res, "structured_content", None) or getattr(
                res, "data", None
            )
            if isinstance(data, dict):
                return data
            return json.loads(res.content[0].text)
        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.debug("tool %s failed: %s", tool, exc)
            return {}

    session, tyres, fuel, table = await asyncio.gather(
        call("get_session_info"),
        call("get_player_tyre_wear"),
        call("get_player_fuel_info"),
        call("get_race_table"),
    )

    if not session or session.get("available") is False:
        return "NO LIVE SESSION: telemetry is not available right now."

    lines = [f"SESSION: {_flatten(session, 30)}"]
    if session.get("connected") is False:
        lines.append("WARNING: telemetry disconnected, data may be stale.")

    rows = _standings(table)
    player = next((r for r in rows if _leaf(r, "is_player") is True), None)
    if player is not None:
        p_pos = _leaf(player, "position") or 0
        p_delta = _leaf(player, "delta_to_leader_ms")
        q = question.lower()
        picked = []
        for r in rows:
            pos = _leaf(r, "position") or 0
            name = str(_leaf(r, "driver_name") or "")
            surname = name.split()[-1].lower() if name else ""
            if abs(pos - p_pos) <= 2 or pos == 1 or (surname and surname in q):
                picked.append((pos, r))
        lines.append(
            f"STANDINGS (you are P{p_pos} of {len(rows)}; nearby + leader + mentioned):"
        )
        for _, r in sorted(picked, key=lambda x: x[0]):
            tag = " <== YOU" if r is player else ""
            lines.append(_row_text(r, p_delta) + tag)

    if tyres:
        lines.append(f"YOUR TYRES: {_flatten(tyres, 30)}")
    if fuel:
        lines.append(f"YOUR FUEL: {_flatten(fuel, 25)}")
    return "\n".join(lines)


# The legacy snapshot above remains deployed until the integration step. Only the
# adapter below is authoritative: recent cache receipt is NOT game-packet age.
_SESSION = "get_session_info"
_TABLE = "get_race_table"
_TYRES = "get_player_tyre_wear"
_FUEL = "get_player_fuel_info"
_FLAT_KEYS = {
    _TYRES: (
        "driver_index",
        "driver_name",
        "tyre_compound",
        "tyre_age_laps",
        "current_wear_avg_pct",
        "fl_wear_pct",
        "fr_wear_pct",
        "rl_wear_pct",
        "rr_wear_pct",
        "wear_rate_available",
        "fl_rate_pct_per_lap",
        "fr_rate_pct_per_lap",
        "rl_rate_pct_per_lap",
        "rr_rate_pct_per_lap",
    ),
    _FUEL: (
        "driver_index",
        "driver_name",
        "fuel_in_tank_kg",
        "fuel_capacity_kg",
        "fuel_mix",
        "last_lap_fuel_used_kg",
        "avg_burn_rate_kg_per_lap",
        "target_burn_rate_kg_per_lap",
        "target_next_lap_fuel_kg",
        "surplus_laps_live",
        "surplus_laps_builtin",
        "data_sufficient",
    ),
}


class _Unavailable(ValueError):
    pass


class TelemetryAdapter:
    """Coherent recent MCP receipts plus observed progress, never packet freshness."""

    def __init__(
        self,
        client,
        tracker: SessionProgressTracker,
        *,
        epoch_clock: Callable[[], float],
        mono_clock: Callable[[], float],
    ) -> None:
        self.client = client
        self.tracker = tracker
        self._epoch = epoch_clock
        self._mono = mono_clock
        self._clock_origin = (epoch_clock(), mono_clock())

    def _now(self):
        epoch, mono = self._epoch(), self._mono()
        origin_epoch, origin_mono = self._clock_origin
        if not finite(epoch) or not finite(mono):
            raise _Unavailable("Invalid local clock")
        if (
            mono < origin_mono
            or abs((epoch - origin_epoch) - (mono - origin_mono)) > 0.1
        ):
            raise _Unavailable("Local clock jump; freshness unavailable")
        return epoch, mono

    async def _call(self, tool, deadline, stamps, expiries):
        _, start = self._now()
        budget = min(1.0, deadline - start)
        if budget <= 0:
            raise _Unavailable("Telemetry collection deadline exceeded")
        try:
            response = await asyncio.wait_for(
                self.client.call_tool(tool, {}, raise_on_error=False), budget
            )
        except Exception as exc:
            raise _Unavailable(f"{tool}: telemetry unavailable ({type(exc).__name__})")
        # Sample at actual completion, not before awaiting the client.
        epoch, mono = self._epoch(), self._mono()
        data = getattr(response, "structured_content", None)
        if data is None:
            data = getattr(response, "data", None)
        if data is None:
            try:
                data = json.loads(response.content[0].text)
            except (AttributeError, IndexError, TypeError, ValueError):
                raise _Unavailable(f"{tool}: unknown response schema") from None
        if not isinstance(data, Mapping):
            raise _Unavailable(f"{tool}: unknown response schema")
        received = data.get("last-update-timestamp")
        stamps.append(SourceStamp(tool, received, mono))
        self._now()
        if mono >= deadline or mono - start > 1.0:
            raise _Unavailable(f"{tool}: telemetry deadline exceeded")
        if not finite(received) or not 0 <= epoch - received <= 2.0:
            raise _Unavailable(f"{tool}: cache receipt freshness unavailable")
        if data.get("connected") is False:
            # Order disconnects under the same lock as connected observations;
            # a delayed response must not invalidate a newer session generation.
            _, _, reason = self.tracker.observe({"connected": False}, stamp=stamps[-1])
            raise _Unavailable(reason or "Telemetry disconnected")
        if data.get("connected") is not True:
            raise _Unavailable(f"{tool}: unknown connection status")
        if data.get("available") is not True or data.get("error"):
            raise _Unavailable(f"{tool}: telemetry unavailable")
        if type(data.get("ok")) is not bool or (
            tool != _SESSION and data["ok"] is not True
        ):
            raise _Unavailable(f"{tool}: unsuccessful or unknown status")
        expiries.append(mono + 2.0 - (epoch - received))
        return data

    @staticmethod
    def _session(data):
        identity = data.get("identity")
        control = data.get("race_control")
        if not isinstance(identity, Mapping) or not isinstance(control, Mapping):
            raise _Unavailable("Unknown session schema")
        uid = identity.get("session_uid")
        if type(uid) is not int or uid <= 0:
            raise _Unavailable("Invalid session UID")
        if identity.get("session-ended") is not False:
            raise _Unavailable("Session ended or unknown")
        if control.get("is_spectating") is not False:
            raise _Unavailable("Player identity unavailable while spectating")
        if not isinstance(data.get("progress"), Mapping):
            raise _Unavailable("Session progress unavailable")
        return uid

    async def collect(self, intent: Intent, deadline_mono: float) -> Evidence:
        stamps, expiries = [], []
        uid = player = None
        generation = self.tracker.current_generation()
        progress_until = 0.0
        facts, paths = {}, []
        try:
            _, start = self._now()
            deadline = min(deadline_mono, start + 2.0)
            if not finite(deadline_mono):
                raise _Unavailable("Invalid collection deadline")
            if intent.topic not in ("weather", "tyres", "fuel", "gaps", "pit"):
                raise _Unavailable("Unsupported telemetry topic")
            for attempt in range(2):
                before = await self._call(_SESSION, deadline, stamps, expiries)
                uid = self._session(before)
                generation, progress_until, before_reason = self.tracker.observe(
                    before, stamp=stamps[-1]
                )
                table = await self._call(_TABLE, deadline, stamps, expiries)
                rows = table.get("standings")
                if not isinstance(rows, list) or not all(
                    isinstance(r, Mapping) and isinstance(r.get("driver_info"), Mapping)
                    for r in rows
                ):
                    raise _Unavailable("Unknown standings schema")
                players = [
                    r["driver_info"]
                    for r in rows
                    if r["driver_info"].get("is_player") is True
                ]
                if len(players) != 1 or type(players[0].get("index")) is not int:
                    raise _Unavailable("Unique player identity unavailable")
                player = players[0]["index"]
                if (
                    player < 0
                    or sum(r["driver_info"].get("index") == player for r in rows) != 1
                ):
                    raise _Unavailable("Invalid or ambiguous player index")
                flat = {}
                tools = []
                if intent.topic in ("tyres", "pit"):
                    tools.append(_TYRES)
                if intent.topic in ("fuel", "pit"):
                    tools.append(_FUEL)
                for tool in tools:
                    flat[tool] = await self._call(tool, deadline, stamps, expiries)
                after = await self._call(_SESSION, deadline, stamps, expiries)
                after_uid = self._session(after)
                table_identity = table.get("identity")
                if not isinstance(table_identity, Mapping):
                    raise _Unavailable("Unknown standings identity schema")
                coherent = (
                    after_uid == uid == table_identity.get("session_uid")
                    and table_identity.get("session_ended") is False
                    and before["identity"] == after["identity"]
                    and all(
                        d.get("driver_index") == player
                        and type(d.get("driver_index")) is int
                        and d.get("last-update-timestamp")
                        == table.get("last-update-timestamp")
                        for d in flat.values()
                    )
                )
                # Track the validated player through the same shared locked owner.
                generation, progress_until, reason = self.tracker.observe(
                    {**after, "player_index": player}, stamp=stamps[-1]
                )
                if not coherent:
                    if attempt == 0:
                        continue
                    raise _Unavailable("Incoherent session/player cache generation")
                if before_reason and "Out-of-order" in before_reason:
                    raise _Unavailable(before_reason)
                if reason:
                    raise _Unavailable(reason)
                facts = self._facts(intent, after, rows, players[0], flat)
                paths = list(self._paths(facts))
                _, now = self._now()
                if now >= min(min(expiries), progress_until, deadline):
                    raise _Unavailable("Telemetry freshness expired during collection")
                if generation != self.tracker.current_generation():
                    raise _Unavailable("Session generation changed during collection")
                return Evidence(
                    intent.topic,
                    uid,
                    generation,
                    player,
                    min(expiries),
                    progress_until,
                    None,
                    facts,
                    tuple(paths),
                    tuple(stamps),
                )
            raise _Unavailable("Incoherent telemetry")
        except _Unavailable as exc:
            return Evidence(
                intent.topic,
                uid,
                self.tracker.current_generation(),
                player,
                min(expiries, default=0.0),
                progress_until,
                str(exc),
                {},
                (),
                tuple(stamps),
            )

    @staticmethod
    def _facts(intent, session, rows, player, flat):
        session_keys = {
            "identity": (
                "session_uid",
                "session_type",
                "formula_type",
                "circuit_name",
                "session-ended",
            ),
            "progress": (
                "current_lap",
                "total_laps",
                "duration_elapsed_sec",
                "time_remaining_sec",
            ),
            "race_control": (
                "is_spectating",
                "safety_car_status",
                "safety_car_deployments",
                "virtual_safety_car_deployments",
                "red_flag_count",
            ),
        }
        facts = {
            _SESSION: {
                section: {k: session[section][k] for k in keys if k in session[section]}
                for section, keys in session_keys.items()
            }
        }
        if intent.topic in ("weather", "pit"):
            environment = session.get("environment")
            if not isinstance(environment, Mapping):
                raise _Unavailable("Unknown session environment schema")
            facts[_SESSION]["environment"] = {
                k: environment[k]
                for k in (
                    "air_temperature_c",
                    "track_temperature_c",
                    "weather_forecast",
                )
                if k in environment
            }
        keys = ("index", "driver_name", "position", "is_player", "dnf_status")
        selected = [player]
        if intent.topic == "gaps":
            position = player.get("position")
            target = (intent.target or "").casefold()
            selected = [
                r["driver_info"]
                for r in rows
                if (
                    r["driver_info"] is player
                    or (
                        type(position) is int
                        and type(r["driver_info"].get("position")) is int
                        and abs(r["driver_info"]["position"] - position) == 1
                    )
                    or (
                        target
                        and target
                        in str(r["driver_info"].get("driver_name", "")).casefold()
                    )
                )
            ]
        facts[_TABLE] = {
            "standings": [
                {"driver_info": {k: row[k] for k in keys if k in row}}
                for row in selected
            ]
        }
        for tool, data in flat.items():
            kept = {k: data[k] for k in _FLAT_KEYS[tool] if k in data}
            for key, value in list(kept.items()):
                if type(value) in (int, float) and not finite(value):
                    del kept[key]
                elif isinstance(value, bool) and key not in (
                    "wear_rate_available",
                    "data_sufficient",
                ):
                    del kept[key]
                elif tool == _TYRES and "_rate_" in key:
                    if data.get("wear_rate_available") is not True:
                        del kept[key]
                elif (
                    tool == _FUEL
                    and key
                    in (
                        "avg_burn_rate_kg_per_lap",
                        "target_burn_rate_kg_per_lap",
                        "target_next_lap_fuel_kg",
                        "surplus_laps_live",
                    )
                    and data.get("data_sufficient") is not True
                ):
                    del kept[key]
            facts[tool] = kept
        return facts

    @classmethod
    def _paths(cls, value, prefix=""):
        if isinstance(value, Mapping):
            for key, child in value.items():
                yield from cls._paths(child, f"{prefix}.{key}" if prefix else key)
        elif isinstance(value, (list, tuple)):
            for index, child in enumerate(value):
                yield from cls._paths(child, f"{prefix}[{index}]")
        else:
            yield prefix

    async def revalidate(self, evidence: Evidence, deadline_mono: float) -> Evidence:
        if evidence.reason is not None:
            return evidence
        try:
            epoch, now = self._now()
            if now >= min(
                evidence.expires_mono, evidence.progress_valid_until_mono, deadline_mono
            ):
                raise _Unavailable("Original telemetry freshness expired")
            if not evidence.stamps or any(
                not finite(s.cache_received_epoch)
                or not 0 <= epoch - s.cache_received_epoch <= 2.0
                or now < s.collected_mono
                for s in evidence.stamps
            ):
                raise _Unavailable("Original source freshness unavailable")
            refreshed = await self.collect(Intent(evidence.topic), deadline_mono)
            if refreshed.reason:
                raise _Unavailable(refreshed.reason)
            _, now = self._now()
            if (
                refreshed.session_uid != evidence.session_uid
                or refreshed.player_index != evidence.player_index
                or refreshed.generation != evidence.generation
                or self.tracker.current_generation() != evidence.generation
            ):
                raise _Unavailable("Session/player generation changed")
            if now >= min(
                evidence.expires_mono, evidence.progress_valid_until_mono, deadline_mono
            ):
                raise _Unavailable("Original telemetry freshness expired")
            return evidence
        except _Unavailable as exc:
            return replace(evidence, reason=str(exc))
