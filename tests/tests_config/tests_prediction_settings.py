# MIT License
#
# Copyright (c) [2025] [Ashwin Natarajan]
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
# pylint: skip-file

"""PredictionSettings defaults and derived values. Per-field ranges, types and enum values are in
tests_config_properties.py; diff behaviour is in tests_diff_mixin.py."""

import allure
import pytest

from lib.config import HarvestPowerSmoothing, PredictionSettings

pytestmark = allure.feature("Prediction settings")


@allure.story("Defaults")
@allure.title("Default PredictionSettings hold the shipped values")
def test_default_values():
    """
    Builds PredictionSettings with no arguments.

    Expected: weather-aware prediction off, no sliding tyre wear window, balanced harvest power smoothing.
    """
    settings = PredictionSettings()

    assert settings.weather_aware_prediction is False
    assert settings.tyre_wear_window_size is None
    assert settings.harvest_power_smoothing == HarvestPowerSmoothing.BALANCED


@allure.story("Derived values")
@allure.title("Harvest power smoothing '{profile.value}' uses a {window}-sample filter window")
@pytest.mark.parametrize("profile, window", [
    (HarvestPowerSmoothing.VERY_RESPONSIVE, 7),
    (HarvestPowerSmoothing.RESPONSIVE, 11),
    (HarvestPowerSmoothing.BALANCED, 15),
    (HarvestPowerSmoothing.STABLE, 21),
    (HarvestPowerSmoothing.VERY_STABLE, 27),
], ids=lambda v: v.value if isinstance(v, HarvestPowerSmoothing) else str(v))
def test_harvest_power_window_size(profile, window):
    """
    Sets harvest_power_smoothing to one profile and reads harvest_power_window_size.

    Expected: the profile's filter window, growing from very responsive to very stable.
    """
    assert PredictionSettings(harvest_power_smoothing=profile).harvest_power_window_size == window
