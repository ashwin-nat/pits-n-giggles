"""Frozen internal race-engineer contracts; no runtime service dependencies."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass, fields
from types import MappingProxyType
from typing import Literal

Topic = Literal["tyres", "weather", "fuel", "gaps", "pit", "complex", "unknown"]


def _freeze(value):
    if value is None or type(value) in (str, int, float, bool, bytes):
        return value
    if isinstance(value, Mapping):
        return MappingProxyType({_freeze(k): _freeze(v) for k, v in value.items()})
    if isinstance(value, (tuple, list)):
        return tuple(_freeze(v) for v in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_freeze(v) for v in value)
    if isinstance(value, _Record):
        return value
    raise TypeError(f"Unsupported contract value: {type(value).__name__}")


class _Record:
    def __post_init__(self):
        for field in fields(self):
            value = getattr(self, field.name)
            if field.name == "cancelled" and callable(value):
                continue
            object.__setattr__(self, field.name, _freeze(value))


@dataclass(frozen=True)
class Intent(_Record):
    topic: Topic
    target: str | None = None


@dataclass(frozen=True)
class SourceStamp(_Record):
    tool: str
    cache_received_epoch: float
    collected_mono: float


@dataclass(frozen=True)
class Evidence(_Record):
    topic: Topic
    session_uid: int | None
    generation: int
    player_index: int | None
    expires_mono: float
    progress_valid_until_mono: float
    reason: str | None
    facts: Mapping[str, object]
    sources: tuple[str, ...]
    stamps: tuple[SourceStamp, ...]


@dataclass(frozen=True)
class Answer(_Record):
    text: str
    kind: Literal["fact", "estimate", "advice", "insufficient"]
    evidence: Evidence | None
    evidence_paths: tuple[str, ...]
    card_ids: tuple[str, ...]


@dataclass(frozen=True)
class KnowledgeCard(_Record):
    id: str
    topics: tuple[Topic, ...]
    text: str
    source: str
    scope: Literal["general", "game"]
    applicability: str
    game_seasons: tuple[int, ...]
    reviewed_on: str
    limitations: str


@dataclass(frozen=True)
class CalloutCondition(_Record):
    event: Literal["tyre_wear", "fuel_deficit", "safety_car", "weather"]
    baseline: Mapping[str, object]


@dataclass(frozen=True)
class RadioWork(_Record):
    id: str
    kind: Literal["question", "callout", "ack", "greeting"]
    text: str
    generation: int
    created_mono: float
    expires_mono: float
    answer: Answer | None = None
    dedupe_key: str | None = None
    condition: CalloutCondition | None = None


@dataclass(frozen=True)
class RequestContext(_Record):
    request_id: str
    generation: int
    deadline_mono: float
    cancelled: Callable[[], bool]
