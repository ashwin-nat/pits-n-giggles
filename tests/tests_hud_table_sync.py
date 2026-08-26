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

"""QmlBridge.sync_table: the differ's baseline must never outrun what QML got.

QmlBridge is pure Python (it touches QObject only for typing), so these run
with no QApplication, no window and no display.
"""

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

from typing import Any, Dict, List, Optional

import pytest

from apps.hud.ui.overlays.base.qml_bridge import QmlBridge
from lib.table_differ import TableDiffer

# -------------------------------------- HELPERS -----------------------------------------------------------------------

class FakeQmlTarget:
    """Stands in for the QQuickWindow/QQuickItem, recording what QML would receive."""

    def __init__(self) -> None:
        self.writes: List[tuple] = []

    def setProperty(self, name: str, value: Any) -> None:  # pylint: disable=invalid-name
        self.writes.append((name, value))


class FakeBridge(QmlBridge):
    """QmlBridge with a target that can be detached, the way a hidden overlay's is."""

    def __init__(self) -> None:
        super().__init__()
        self.target: Optional[FakeQmlTarget] = FakeQmlTarget()

    @property
    def _qml_target(self) -> Optional[FakeQmlTarget]:
        return self.target


def rows(*names: str) -> List[Dict[str, str]]:
    """Freshly built rows; TableDiffer stores by reference, so never reuse one."""
    return [{"name": name} for name in names]


@pytest.fixture(name="bridge")
def _bridge() -> FakeBridge:
    return FakeBridge()


@pytest.fixture(name="differ")
def _differ(bridge: FakeBridge) -> TableDiffer:
    return TableDiffer(bridge._stats)  # pylint: disable=protected-access

# -------------------------------------- TESTS -------------------------------------------------------------------------

def test_first_sync_pushes_a_reset(bridge: FakeBridge, differ: TableDiffer) -> None:
    bridge.sync_table(differ, "tableUpdate", rows("a", "b"))

    assert len(bridge.target.writes) == 1
    name, payload = bridge.target.writes[0]
    assert name == "tableUpdate"
    assert payload["kind"] == TableDiffer.RESET


def test_unchanged_rows_push_nothing(bridge: FakeBridge, differ: TableDiffer) -> None:
    bridge.sync_table(differ, "tableUpdate", rows("a", "b"))
    bridge.sync_table(differ, "tableUpdate", rows("a", "b"))

    assert len(bridge.target.writes) == 1


def test_changed_row_pushes_only_that_row(bridge: FakeBridge, differ: TableDiffer) -> None:
    bridge.sync_table(differ, "tableUpdate", rows("a", "b"))
    bridge.sync_table(differ, "tableUpdate", rows("a", "B"))

    _, payload = bridge.target.writes[-1]
    assert payload["kind"] == TableDiffer.PATCH
    assert payload["rows"] == [{"index": 1, "row": {"name": "B"}}]


def test_write_dropped_with_no_target_forces_a_reset_on_return(
        bridge: FakeBridge, differ: TableDiffer) -> None:
    """The regression this guards: an overlay hidden mid-stream came back blank.

    A push with no target writes nothing, but the differ had already advanced.
    Once the target returned, a same-row-count table produced only patches,
    which QML drops against its empty model - so the table stayed behind until
    something else forced a reset.
    """
    bridge.sync_table(differ, "tableUpdate", rows("a", "b"))
    bridge.target.writes.clear()

    # Overlay hidden: the target goes away, updates keep arriving.
    bridge.target = None
    bridge.sync_table(differ, "tableUpdate", rows("a", "B"))
    bridge.sync_table(differ, "tableUpdate", rows("a", "C"))

    # Shown again, with the same row count as before.
    bridge.target = FakeQmlTarget()
    bridge.sync_table(differ, "tableUpdate", rows("a", "D"))

    assert len(bridge.target.writes) == 1
    _, payload = bridge.target.writes[0]
    assert payload["kind"] == TableDiffer.RESET, \
        "a table rebuilt after a dropped write must reset, not patch"
    assert payload["rows"] == rows("a", "D")


def test_row_count_change_still_resets(bridge: FakeBridge, differ: TableDiffer) -> None:
    bridge.sync_table(differ, "tableUpdate", rows("a", "b"))
    bridge.sync_table(differ, "tableUpdate", rows("a", "b", "c"))

    _, payload = bridge.target.writes[-1]
    assert payload["kind"] == TableDiffer.RESET
