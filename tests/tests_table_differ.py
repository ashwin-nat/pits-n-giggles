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

from typing import Any, Dict, List

import pytest

from lib.event_counter import EventCounter
from lib.table_differ import TableDiffer

# -------------------------------------- TYPES -------------------------------------------------------------------------

Row = Dict[str, str]

# -------------------------------------- FIXTURES ----------------------------------------------------------------------

@pytest.fixture
def differ() -> TableDiffer:
    return TableDiffer(EventCounter())

def rows(*names: str) -> List[Row]:
    return [{"name": name} for name in names]

def reset(*names: str) -> Dict[str, Any]:
    return {"kind": "reset", "rows": rows(*names)}

def patch(*entries: Any) -> Dict[str, Any]:
    """patch((1, "x"), ...) -> the payload for those index/name pairs."""
    return {"kind": "patch", "rows": [{"index": i, "row": {"name": n}} for i, n in entries]}

# -------------------------------------- TESTS: reset ----------------------------------------------------------------

def test_first_update_returns_reset(differ: TableDiffer) -> None:
    assert differ.update(rows("a", "b")) == reset("a", "b")

def test_first_update_with_empty_table_returns_reset(differ: TableDiffer) -> None:
    assert differ.update([]) == {"kind": "reset", "rows": []}

def test_row_count_growth_returns_reset(differ: TableDiffer) -> None:
    differ.update(rows("a"))
    assert differ.update(rows("a", "b")) == reset("a", "b")

def test_row_count_shrink_returns_reset(differ: TableDiffer) -> None:
    differ.update(rows("a", "b"))
    assert differ.update(rows("a")) == reset("a")

def test_clearing_to_empty_returns_an_empty_reset_not_none(differ: TableDiffer) -> None:
    differ.update(rows("a", "b"))
    assert differ.update([]) == {"kind": "reset", "rows": []}

def test_empty_to_empty_returns_none(differ: TableDiffer) -> None:
    differ.update([])
    assert differ.update([]) is None

def test_reset_payload_carries_the_caller_rows(differ: TableDiffer) -> None:
    table = rows("a", "b")
    assert differ.update(table)["rows"] is table

# -------------------------------------- TESTS: patches --------------------------------------------------------------

def test_identical_update_returns_none(differ: TableDiffer) -> None:
    differ.update(rows("a", "b"))
    assert differ.update(rows("a", "b")) is None

def test_single_changed_row_returns_one_patch(differ: TableDiffer) -> None:
    differ.update(rows("a", "b", "c"))
    assert differ.update(rows("a", "x", "c")) == patch((1, "x"))

def test_multiple_changed_rows_are_listed_in_index_order(differ: TableDiffer) -> None:
    differ.update(rows("a", "b", "c"))
    assert differ.update(rows("x", "b", "y")) == patch((0, "x"), (2, "y"))

def test_patches_compare_against_the_latest_table(differ: TableDiffer) -> None:
    differ.update(rows("a", "b"))
    differ.update(rows("a", "x"))
    assert differ.update(rows("a", "x")) is None

def test_rows_may_be_any_comparable_object(differ: TableDiffer) -> None:
    differ.update([1, 2, 3])
    assert differ.update([1, 9, 3]) == {"kind": "patch", "rows": [{"index": 1, "row": 9}]}

# -------------------------------------- TESTS: invalidate -----------------------------------------------------------

def test_invalidate_forces_a_reset_on_identical_data(differ: TableDiffer) -> None:
    differ.update(rows("a", "b"))
    differ.invalidate()
    assert differ.update(rows("a", "b")) == reset("a", "b")

def test_invalidate_on_a_fresh_differ_is_harmless(differ: TableDiffer) -> None:
    differ.invalidate()
    assert differ.update(rows("a")) == reset("a")

# -------------------------------------- TESTS: payload contract -------------------------------------------------------

def test_kind_strings_are_the_documented_constants(differ: TableDiffer) -> None:
    assert differ.update(rows("a"))["kind"] == TableDiffer.RESET
    assert differ.update(rows("b"))["kind"] == TableDiffer.PATCH

def test_patch_payload_carries_the_new_row_object(differ: TableDiffer) -> None:
    differ.update(rows("a"))
    table = rows("b")
    assert differ.update(table)["rows"][0]["row"] is table[0]
