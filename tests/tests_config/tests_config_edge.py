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

import allure
import pytest
from pydantic import ValidationError

from lib.config import (CaptureSettings, DisplaySettings, ForwardingSettings,
                        HudSettings, NetworkSettings, PngSettings,
                        PrivacySettings, StreamOverlaySettings)

pytestmark = allure.feature("Config edge cases")

# ----------------------------------------------------------------------------------------------------------------------

@allure.story("Validation edge cases")
@allure.title("Forwarding target {raw!r} is stored as {expected!r}")
@pytest.mark.parametrize(("raw", "expected"), [
    ("  localhost:8080", "localhost:8080"),
    ("localhost:8080   ", "localhost:8080"),
    ("localhost:8080", "localhost:8080"),
    ("   ", ""),
])
def test_forwarding_target_whitespace(raw, expected):
    """
    Builds ForwardingSettings with target_1 padded by leading, trailing or only whitespace.

    Expected: the whitespace is stripped, and a whitespace-only target becomes the empty string (no forwarding).
    """
    assert ForwardingSettings(target_1=raw).target_1 == expected

@allure.story("Validation edge cases")
@allure.title("The same UDP action code in Network and HUD is rejected")
def test_udp_action_code_duplicate_across_sections():
    """
    Builds PngSettings with UDP action code 1 bound to both the tyre delta action (Network) and the overlay toggle
    (HUD).

    Expected: ValidationError, since one button cannot trigger two actions.
    """
    with pytest.raises(ValidationError):
        PngSettings(
            Network=NetworkSettings(udp_tyre_delta_action_code=1),
            HUD=HudSettings(toggle_overlays_udp_action_code=1),
        )

@allure.story("Default settings")
@allure.title("PngSettings built from default sections equals PngSettings()")
def test_default_settings():
    """
    Builds PngSettings from default-constructed sections.

    Expected: it equals PngSettings() and uses the default telemetry port 20777.
    """
    settings = PngSettings(
        Network=NetworkSettings(),
        Capture=CaptureSettings(),
        Display=DisplaySettings(),
        Privacy=PrivacySettings(),
        Forwarding=ForwardingSettings(),
        StreamOverlay=StreamOverlaySettings(),
    )

    assert settings == PngSettings()
    assert settings.Network.telemetry_port == 20777
