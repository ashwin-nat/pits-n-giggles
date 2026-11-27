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

"""DisplaySettings defaults. Per-field ranges, types and enum values are in tests_config_properties.py."""

import allure

from lib.config import AutoOpenDashboardMode, DisplaySettings

pytestmark = allure.feature("Display settings")


@allure.story("Defaults")
@allure.title("Default DisplaySettings hold the shipped values")
def test_default_values():
    """
    Builds DisplaySettings with no arguments.

    Expected: every field holds its shipped default.
    """
    settings = DisplaySettings()

    assert settings.auto_open_dashboard == AutoOpenDashboardMode.HUB
    assert settings.refresh_interval == 200
    assert settings.local_telemetry_rate == 5
    assert settings.realtime_overlay_fps == 60
    assert settings.use_cpu_acceleration is False
    assert settings.save_viewer_poll_interval_secs == 10
    assert settings.wdt_timeout == 5.0
