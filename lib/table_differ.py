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

from typing import Any, Dict, List, Optional

from lib.event_counter import EventCounter

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class TableDiffer:
    """Row-granularity differ for table data pushed to a UI.

    A row is any `==`-comparable object; no particular shape is assumed. Each
    `update()` returns one payload describing everything that changed, or None
    when nothing did:

    - no stored table (fresh, or after `invalidate()`), or a row-count change
      -> {"kind": "reset", "rows": [row, ...]}
    - same row count -> {"kind": "patch", "rows": [{"index": i, "row": row}, ...]}
      carrying only the indices whose row compares unequal

    One payload per update means one QML property write per tick however many
    rows moved, and resets and patches cannot arrive out of order, since they
    travel through the same property.

    Note that {"kind": "reset", "rows": []} means "empty the table" and is quite
    different from None, which means "nothing to do".

    Contract: callers must pass a freshly built list of freshly built rows and
    must not mutate either after the call. The list is stored by reference, so
    any later mutation silently corrupts the next diff.

    Counts what it decided under __TABLE_DIFFER__ in the caller's EventCounter, which
    nests under the owning overlay in the stats tree:
        __RESET__           whole-table pushes (page activation, row-count change)
        __PATCH_NUM_ROWS__  rows patched, summed over all updates
        __UNCHANGED__       updates that produced no work at all
        __INVALIDATED__     times the stored table was dropped
    """

    # Payload discriminator. The QML side compares against these same strings.
    RESET = "reset"
    PATCH = "patch"

    def __init__(self, stats: EventCounter) -> None:
        """
        stats : the owning component's counter, so table stats land beside its others
        """
        self._stats = stats
        self._rows: Optional[List[Any]] = None

    # ------------------------------------------------------------------
    # Diffing
    # ------------------------------------------------------------------
    def update(self, new_rows: List[Any]) -> Optional[Dict[str, Any]]:
        """Diff new_rows against the stored table. Returns the payload, or None."""
        old_rows = self._rows
        self._rows = new_rows

        if old_rows is None or len(old_rows) != len(new_rows):
            self._stats.track_event("__TABLE_DIFFER__", "__RESET__")
            return {"kind": self.RESET, "rows": new_rows}

        patches = [
            {"index": index, "row": new_row}
            for index, (old_row, new_row) in enumerate(zip(old_rows, new_rows))
            if old_row != new_row
        ]
        if not patches:
            self._stats.track_event("__TABLE_DIFFER__", "__UNCHANGED__")
            return None

        self._stats.track_event("__TABLE_DIFFER__", "__PATCH_NUM_ROWS__", count=len(patches))
        return {"kind": self.PATCH, "rows": patches}

    def invalidate(self) -> None:
        """Drop the stored table so the next update() always fires a reset.

        Call this whenever the UI target is (re)created and has lost its rows.
        """
        self._stats.track_event("__TABLE_DIFFER__", "__INVALIDATED__")
        self._rows = None
