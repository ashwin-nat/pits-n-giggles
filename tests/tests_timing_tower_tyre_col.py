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

"""The timing tower's tyre column, across the three tyre info modes.

tyre-info is a producer-side guarantee: the backend always sends tyre-age and
current-wear, so _format_tyre_wear subscripts them directly and a violated
contract is meant to blow up rather than quietly render a dash. These tests
pin both halves of that - the formatting for well-formed rows, and the
deliberate raise for malformed ones.
"""

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

from typing import Any, Dict

import pytest

from apps.hud.ui.overlays.timing_tower.timing_tower_overlay import \
    TimingTowerOverlay
from lib.config import TimingTowerTyreInfoMode

# -------------------------------------- HELPERS -----------------------------------------------------------------------

def format_tyre(mode: TimingTowerTyreInfoMode, tyre_info: Dict[str, Any],
                telemetry_public: bool = True) -> str:
    """Format one tyre cell on a real overlay instance built without __init__.

    __new__ skips the constructor, which would need a window and a full
    settings object; the formatting path reads only self.tyre_info_mode.
    """
    overlay = TimingTowerOverlay.__new__(TimingTowerOverlay)
    overlay.tyre_info_mode = mode
    return overlay._format_tyre_wear(tyre_info, telemetry_public)  # pylint: disable=protected-access


ALL_MODES = list(TimingTowerTyreInfoMode)


def tyre(age: int = 12, wear: Any = None) -> Dict[str, Any]:
    """A row shaped the way the backend guarantees: both keys always present."""
    return {"tyre-age": age, "current-wear": wear}

# -------------------------------------- TESTS -------------------------------------------------------------------------

def test_age_mode_reports_age() -> None:
    assert format_tyre(TimingTowerTyreInfoMode.TYRE_AGE, tyre(age=12)) == "12L"


def test_age_mode_ignores_wear() -> None:
    wear = {"fl": 30.0, "fr": 30.0, "rl": 30.0, "rr": 30.0}
    assert format_tyre(TimingTowerTyreInfoMode.TYRE_AGE, tyre(age=7, wear=wear)) == "7L"


def test_wear_mode_dashes_when_wear_absent() -> None:
    assert format_tyre(TimingTowerTyreInfoMode.TYRE_WEAR, tyre(age=12)) == "--"


def test_wear_mode_dashes_for_restricted_telemetry() -> None:
    wear = {"fl": 30.0, "fr": 30.0, "rl": 30.0, "rr": 30.0}
    assert format_tyre(TimingTowerTyreInfoMode.TYRE_WEAR, tyre(wear=wear),
                       telemetry_public=False) == "--"


def test_hybrid_falls_back_to_age_when_wear_absent() -> None:
    assert format_tyre(TimingTowerTyreInfoMode.HYBRID, tyre(age=12)) == "12L"


def test_hybrid_falls_back_to_age_for_restricted_telemetry() -> None:
    wear = {"fl": 30.0, "fr": 30.0, "rl": 30.0, "rr": 30.0}
    assert format_tyre(TimingTowerTyreInfoMode.HYBRID, tyre(age=12, wear=wear),
                       telemetry_public=False) == "12L"


@pytest.mark.parametrize("mode", [TimingTowerTyreInfoMode.TYRE_WEAR,
                                  TimingTowerTyreInfoMode.HYBRID])
def test_wear_reported_as_percent_when_public(mode: TimingTowerTyreInfoMode) -> None:
    wear = {"fl": 30.0, "fr": 42.0, "rl": 30.0, "rr": 30.0}
    assert format_tyre(mode, tyre(wear=wear)).endswith("%")


@pytest.mark.parametrize("mode", ALL_MODES)
def test_missing_tyre_keys_raise_rather_than_render(mode: TimingTowerTyreInfoMode) -> None:
    """The subscripts are deliberate: tyre-info is guaranteed by the producer,
    so a row without it is a bug upstream and must not be papered over here."""
    with pytest.raises(KeyError):
        format_tyre(mode, {})
