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

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

from typing import Any, Dict, List, NamedTuple, Union

import pytest

from lib.event_counter import EventCounter
from lib.table_differ import TableDiffer

# -------------------------------------- TYPES -------------------------------------------------------------------------

Row = Dict[str, str]

class Reset(NamedTuple):
    """A whole-table push, as seen by an on_reset callback."""
    table: List[Any]

class Patch(NamedTuple):
    """A single-row push, as seen by an on_row_patch callback."""
    index: int
    row: Any

CallLog = List[Union[Reset, Patch]]

# -------------------------------------- FIXTURES ----------------------------------------------------------------------

@pytest.fixture
def calls() -> CallLog:
    """Ordered log of everything the differ emitted. Empty means it stayed silent."""
    return []

@pytest.fixture
def stats() -> EventCounter:
    return EventCounter()

@pytest.fixture
def differ(calls: CallLog, stats: EventCounter) -> TableDiffer:
    obj = TableDiffer(stats)
    obj.on_reset(lambda table: calls.append(Reset(table)))
    obj.on_row_patch(lambda index, row: calls.append(Patch(index, row)))
    return obj

def rows(*names: str) -> List[Row]:
    return [{"name": name} for name in names]

# -------------------------------------- TESTS: reset ----------------------------------------------------------------

def test_first_update_fires_reset(differ: TableDiffer, calls: CallLog) -> None:
    differ.update(rows("a", "b"))
    assert calls == [Reset(rows("a", "b"))]

def test_first_update_with_empty_table_fires_reset(differ: TableDiffer, calls: CallLog) -> None:
    differ.update([])
    assert calls == [Reset([])]

def test_row_count_growth_fires_reset(differ: TableDiffer, calls: CallLog) -> None:
    differ.update(rows("a"))
    calls.clear()
    differ.update(rows("a", "b"))
    assert calls == [Reset(rows("a", "b"))]

def test_row_count_shrink_fires_reset(differ: TableDiffer, calls: CallLog) -> None:
    differ.update(rows("a", "b"))
    calls.clear()
    differ.update(rows("a"))
    assert calls == [Reset(rows("a"))]

def test_clearing_to_empty_fires_reset(differ: TableDiffer, calls: CallLog) -> None:
    differ.update(rows("a", "b"))
    calls.clear()
    differ.update([])
    assert calls == [Reset([])]

def test_empty_to_empty_fires_nothing(differ: TableDiffer, calls: CallLog) -> None:
    differ.update([])
    calls.clear()
    differ.update([])
    assert calls == []

# -------------------------------------- TESTS: patches --------------------------------------------------------------

def test_identical_update_fires_nothing(differ: TableDiffer, calls: CallLog) -> None:
    differ.update(rows("a", "b"))
    calls.clear()
    differ.update(rows("a", "b"))
    assert calls == []

def test_single_changed_row_fires_one_patch(differ: TableDiffer, calls: CallLog) -> None:
    differ.update(rows("a", "b", "c"))
    calls.clear()
    differ.update(rows("a", "x", "c"))
    assert calls == [Patch(1, {"name": "x"})]

def test_multiple_changed_rows_patch_in_index_order(differ: TableDiffer, calls: CallLog) -> None:
    differ.update(rows("a", "b", "c"))
    calls.clear()
    differ.update(rows("x", "b", "y"))
    assert calls == [Patch(0, {"name": "x"}), Patch(2, {"name": "y"})]

def test_patches_compare_against_the_latest_table(differ: TableDiffer, calls: CallLog) -> None:
    differ.update(rows("a", "b"))
    calls.clear()
    differ.update(rows("a", "x"))
    differ.update(rows("a", "x"))
    assert calls == [Patch(1, {"name": "x"})]

def test_rows_may_be_any_comparable_object(differ: TableDiffer, calls: CallLog) -> None:
    differ.update([1, 2, 3])
    calls.clear()
    differ.update([1, 9, 3])
    assert calls == [Patch(1, 9)]

# -------------------------------------- TESTS: invalidate -----------------------------------------------------------

def test_invalidate_forces_reset_on_identical_data(differ: TableDiffer, calls: CallLog) -> None:
    differ.update(rows("a", "b"))
    calls.clear()
    differ.invalidate()
    differ.update(rows("a", "b"))
    assert calls == [Reset(rows("a", "b"))]

def test_invalidate_on_a_fresh_differ_is_harmless(differ: TableDiffer, calls: CallLog) -> None:
    differ.invalidate()
    differ.update(rows("a"))
    assert calls == [Reset(rows("a"))]

# -------------------------------------- TESTS: registration ---------------------------------------------------------

def test_all_registered_callbacks_fire_in_registration_order() -> None:
    differ = TableDiffer(EventCounter())
    calls: List[Any] = []
    differ.on_reset(lambda table: calls.append(("first", Reset(table))))
    differ.on_reset(lambda table: calls.append(("second", Reset(table))))
    differ.on_row_patch(lambda index, row: calls.append(("first", Patch(index, row))))
    differ.on_row_patch(lambda index, row: calls.append(("second", Patch(index, row))))

    differ.update(rows("a"))
    differ.update(rows("b"))

    assert calls == [
        ("first", Reset(rows("a"))),
        ("second", Reset(rows("a"))),
        ("first", Patch(0, {"name": "b"})),
        ("second", Patch(0, {"name": "b"})),
    ]

def test_registration_works_as_a_decorator_and_returns_fn_unchanged() -> None:
    differ = TableDiffer(EventCounter())
    calls: CallLog = []

    @differ.on_reset
    def handle_reset(table: List[Any]) -> None:
        calls.append(Reset(table))

    @differ.on_row_patch
    def handle_patch(index: int, row: Any) -> None:
        calls.append(Patch(index, row))

    differ.update(rows("a"))
    differ.update(rows("b"))

    assert calls == [Reset(rows("a")), Patch(0, {"name": "b"})]
    assert handle_reset.__name__ == "handle_reset"
    assert handle_patch.__name__ == "handle_patch"

def test_differ_with_no_callbacks_still_tracks_state() -> None:
    differ = TableDiffer(EventCounter())
    differ.update(rows("a"))

    calls: CallLog = []
    differ.on_row_patch(lambda index, row: calls.append(Patch(index, row)))
    differ.update(rows("b"))

    assert calls == [Patch(0, {"name": "b"})]
