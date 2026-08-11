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

from typing import Any, Callable, List, Optional

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class TableDiffer:
    """Row-granularity differ for table data pushed to a UI.

    A row is any `==`-comparable object; no particular shape is assumed. Each
    `update()` either fires the reset hooks with the whole table, or fires the
    row-patch hooks once per changed row index:

    - no stored table (fresh, or after `invalidate()`), or a row-count change
      -> reset
    - same row count -> one patch per index where the row compares unequal

    Contract: callers must pass a freshly built list of freshly built rows and
    must not mutate either after the call. The list is stored by reference, so
    any later mutation silently corrupts the next diff.
    """

    def __init__(self) -> None:
        self._rows: Optional[List[Any]] = None
        self._reset_cbs: List[Callable[[List[Any]], None]] = []
        self._patch_cbs: List[Callable[[int, Any], None]] = []

    # ------------------------------------------------------------------
    # Callback registration (usable as a decorator or a plain call)
    # ------------------------------------------------------------------
    def on_reset(self, fn: Callable[[List[Any]], None]) -> Callable[[List[Any]], None]:
        """Register a whole-table callback. Returns fn unchanged."""
        self._reset_cbs.append(fn)
        return fn

    def on_row_patch(self, fn: Callable[[int, Any], None]) -> Callable[[int, Any], None]:
        """Register a single-row callback, called as (index, row). Returns fn unchanged."""
        self._patch_cbs.append(fn)
        return fn

    # ------------------------------------------------------------------
    # Diffing
    # ------------------------------------------------------------------
    def update(self, new_rows: List[Any]) -> None:
        """Diff new_rows against the stored table and fire the matching hooks."""
        old_rows = self._rows
        self._rows = new_rows

        if old_rows is None or len(old_rows) != len(new_rows):
            for cb in self._reset_cbs:
                cb(new_rows)
            return

        for index, (old_row, new_row) in enumerate(zip(old_rows, new_rows)):
            if old_row != new_row:
                for cb in self._patch_cbs:
                    cb(index, new_row)

    def invalidate(self) -> None:
        """Drop the stored table so the next update() always fires a reset.

        Call this whenever the UI target is (re)created and has lost its rows.
        """
        self._rows = None
