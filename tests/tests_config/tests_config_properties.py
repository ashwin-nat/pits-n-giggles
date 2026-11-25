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

import string
from dataclasses import dataclass
from typing import Any, Dict, List, Set, Type, Union

import allure
import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import BaseModel, ValidationError

from lib.config import NetworkSettings

pytestmark = allure.feature("Field constraints")

# ------------------------- SPECS --------------------------------------------------------------------------------------

_LETTERS = st.text(alphabet=string.ascii_letters, min_size=1)
# Strings pydantic's lax bool parses, case-insensitively
_BOOL_WORDS = {"0", "off", "f", "false", "n", "no", "1", "on", "t", "true", "y", "yes"}


@dataclass(frozen=True)
class IntRange:
    """An int field accepting lo..hi inclusive, and None when nullable."""
    lo: int
    hi: int
    nullable: bool = False

    def valid(self) -> st.SearchStrategy:
        ints = st.integers(self.lo, self.hi)
        return ints | st.none() if self.nullable else ints

    def invalid(self) -> st.SearchStrategy:
        bad = (st.integers(max_value=self.lo - 1) | st.integers(min_value=self.hi + 1) | _LETTERS |
               st.floats(allow_nan=False, allow_infinity=False).filter(lambda f: not f.is_integer()))
        return bad if self.nullable else bad | st.none()

    def edges_in(self) -> List[Any]:
        return [self.lo, self.hi] + ([None] if self.nullable else [])

    def edges_out(self) -> List[Any]:
        return [self.lo - 1, self.hi + 1] + ([] if self.nullable else [None])

    def __str__(self) -> str:
        return f"{self.lo}..{self.hi}" + (" or None" if self.nullable else "")


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


FieldSpec = Union[IntRange, Flag]

PORT = IntRange(1, 65535)
UDP_ACTION_CODE = IntRange(1, 12, nullable=True)

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
        "enable_pkt_ordering": Flag(),
        "udp_action_button_debounce_ms": IntRange(0, 500),
    },
}

# Fields no spec above can express; their example tests stay the only coverage
EXAMPLE_ONLY: Dict[Type[BaseModel], Set[str]] = {
    NetworkSettings: {"bind_address"},
}

# ------------------------- HELPERS ------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Case:
    model: Type[BaseModel]
    field: str
    spec: FieldSpec

    def __str__(self) -> str:
        return f"{self.model.__name__}.{self.field}"

    def field_errors(self, exc: ValidationError) -> list:
        return [err for err in exc.errors() if err["loc"][:1] == (self.field,)]

    def assert_accepts(self, value: Any) -> None:
        try:
            model = self.model(**{self.field: value})
        except ValidationError as exc:
            # A model-level rule (a port clashing with another field's default) does not count against the field
            assert not self.field_errors(exc), f"{self} ({self.spec}) rejected {value!r}: {self.field_errors(exc)}"
            return
        assert getattr(model, self.field) == value

    def assert_rejects(self, value: Any) -> None:
        with pytest.raises(ValidationError) as exc:
            self.model(**{self.field: value})
        assert self.field_errors(exc.value), f"{self} ({self.spec}) {value!r} failed elsewhere: {exc.value.errors()}"


CASES = [pytest.param(Case(model, field, spec), id=f"{model.__name__}.{field}")
         for model, specs in FIELDS.items() for field, spec in specs.items()]

# ------------------------- TESTS --------------------------------------------------------------------------------------

@allure.story("Coverage")
@allure.title("Every {model.__name__} field has a spec or is listed as example-only")
@pytest.mark.parametrize("model", list(FIELDS), ids=lambda m: m.__name__)
def test_every_field_is_covered(model: Type[BaseModel]) -> None:
    """Compares the model's declared fields with FIELDS and EXAMPLE_ONLY.

    Expected: each field is in exactly one of the two, and neither names a field the model no longer has.
    """
    declared = set(model.model_fields)
    specced = set(FIELDS[model])
    example_only = EXAMPLE_ONLY.get(model, set())

    assert declared - specced - example_only == set(), "fields with no spec and no example-only entry"
    assert (specced | example_only) - declared == set(), "entries for fields the model does not declare"
    assert specced & example_only == set(), "fields listed in both FIELDS and EXAMPLE_ONLY"


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
