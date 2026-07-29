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

"""Tests for DriverInfo."""

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

import pytest

from apps.backend.state_mgmt_layer.data_per_driver import DriverInfo
from lib.f1_types import SafetyCarType

# -------------------------------------- TESTS -------------------------------------------------------------------------

class TestIsCurrLapRacing:
    """`is_curr_lap_racing` decides whether a lap's samples feed the wear/fuel regressions.

    It has to be a comparison against NO_SAFETY_CAR, never the raw status. SafetyCarType
    derives from Enum rather than IntEnum, so *every* member is truthy - NO_SAFETY_CAR
    included, despite its value being 0. Assigning the raw status into a bool field
    therefore reads as "racing" under a safety car just as much as under green flags.
    """

    def test_no_safety_car_is_a_racing_lap(self):
        assert DriverInfo(m_curr_lap_max_sc_status=SafetyCarType.NO_SAFETY_CAR).is_curr_lap_racing

    @pytest.mark.parametrize("sc_status", [
        sc for sc in SafetyCarType if sc != SafetyCarType.NO_SAFETY_CAR
    ])
    def test_any_safety_car_is_not_a_racing_lap(self, sc_status):
        assert not DriverInfo(m_curr_lap_max_sc_status=sc_status).is_curr_lap_racing

    def test_unknown_status_is_not_a_racing_lap(self):
        """No session packet seen yet this lap - do not claim it was green."""

        assert not DriverInfo().is_curr_lap_racing

    @pytest.mark.parametrize("sc_status", list(SafetyCarType))
    def test_raw_status_is_never_a_substitute_for_the_comparison(self, sc_status):
        """The regression guard: every SafetyCarType member is truthy, value 0 included.

        So `is_racing_lap=<raw status>` collapses to True for all four statuses, silently
        recording safety car laps as green ones.
        """

        assert bool(sc_status), "precondition: Enum members are truthy regardless of value"

        expected = sc_status == SafetyCarType.NO_SAFETY_CAR
        assert DriverInfo(m_curr_lap_max_sc_status=sc_status).is_curr_lap_racing is expected
