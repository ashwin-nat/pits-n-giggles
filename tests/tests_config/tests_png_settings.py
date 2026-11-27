# ----------------------------------------------------------------------------------------------------------------------
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

"""PngSettings rules that span sections. Each section's own fields are in tests_config_properties.py, and diff
behaviour is in tests_diff_mixin.py."""

import allure
import pytest
from pydantic import ValidationError

from lib.config import (ForwardingSettings, HudSettings, NetworkSettings, OpacityOverride, OverlayId,
                        OverlayPosition, PngSettings)
from lib.config.schema.mcp_cfg import McpSettings
from lib.config.schema.utils import PortConflictError, UdpActionCodeConflictError

pytestmark = allure.feature("PngSettings")

# -------------------------------------- DEFAULTS ----------------------------------------------------------------------

@allure.story("Defaults")
@allure.title("The save viewer write API is on by default")
def test_save_viewer_write_api_on_by_default():
    """
    Builds PngSettings with no arguments.

    Expected: the SaveViewer section exists with enable_write_api on. Accepted and rejected values of the flag are
    in tests_config_properties.py.
    """
    assert PngSettings().SaveViewer.enable_write_api is True

# -------------------------------------- UDP ACTION CODES --------------------------------------------------------------

@allure.story("Cross-section rules")
@allure.title("A UDP action code cannot be used in both Network and HUD")
def test_udp_action_code_shared_across_sections_rejected():
    """
    Sets Network.udp_custom_action_code and HUD.mfd_toggle_udp_action_code to 3. Each section is valid on its own.

    Expected: PngSettings raises a ValidationError naming the duplicate code.
    """
    with pytest.raises(ValidationError, match="Duplicate UDP action code 3") as exc:
        PngSettings(Network=NetworkSettings(udp_custom_action_code=3),
                    HUD=HudSettings(mfd_toggle_udp_action_code=3))
    assert isinstance(exc.value.errors()[0]["ctx"]["error"], UdpActionCodeConflictError)


@allure.story("Cross-section rules")
@allure.title("Two HUD UDP action codes cannot share a code")
def test_udp_action_code_shared_within_hud_rejected():
    """
    Sets HUD.lap_timer_toggle_udp_action_code and HUD.mfd_toggle_udp_action_code to 3. HudSettings has no
    uniqueness check of its own, so this clash is only caught at the PngSettings level.

    Expected: PngSettings raises a ValidationError naming the duplicate code.
    """
    with pytest.raises(ValidationError, match="Duplicate UDP action code 3") as exc:
        PngSettings(HUD=HudSettings(lap_timer_toggle_udp_action_code=3, mfd_toggle_udp_action_code=3))
    assert isinstance(exc.value.errors()[0]["ctx"]["error"], UdpActionCodeConflictError)


@allure.story("Cross-section rules")
@allure.title("Distinct UDP action codes in Network and HUD are accepted")
def test_udp_action_codes_distinct_across_sections_accepted():
    """
    Sets Network.udp_custom_action_code to 3 and HUD.mfd_toggle_udp_action_code to 4.

    Expected: PngSettings builds and keeps both codes.
    """
    settings = PngSettings(Network=NetworkSettings(udp_custom_action_code=3),
                           HUD=HudSettings(mfd_toggle_udp_action_code=4))

    assert (settings.Network.udp_custom_action_code, settings.HUD.mfd_toggle_udp_action_code) == (3, 4)

# -------------------------------------- PORTS -------------------------------------------------------------------------

@allure.story("Cross-section rules")
@allure.title("A TCP port cannot be used in both Network and MCP")
def test_tcp_port_shared_across_sections_rejected():
    """
    Sets Network.server_port and MCP.mcp_http_port to 4770. Each section is valid on its own.

    Expected: PngSettings raises a ValidationError naming the duplicate TCP port.
    """
    with pytest.raises(ValidationError, match="Duplicate TCP port 4770") as exc:
        PngSettings(Network=NetworkSettings(server_port=4770), MCP=McpSettings(mcp_http_port=4770))
    assert isinstance(exc.value.errors()[0]["ctx"]["error"], PortConflictError)


@allure.story("Cross-section rules")
@allure.title("A UDP port in Network and a TCP port in MCP may share a number")
def test_udp_and_tcp_port_shared_across_sections_accepted():
    """
    Sets the UDP Network.telemetry_port and the TCP MCP.mcp_http_port both to 5000.

    Expected: PngSettings builds, since ports only clash within one protocol.
    """
    settings = PngSettings(Network=NetworkSettings(telemetry_port=5000), MCP=McpSettings(mcp_http_port=5000))

    assert settings.Network.telemetry_port == settings.MCP.mcp_http_port == 5000

# -------------------------------------- FORWARDING LOOP ---------------------------------------------------------------

_NO_LOOP = {
    "localhost, other port": {"target_1": "localhost:20778"},
    "remote host, same port": {"target_1": "192.168.1.50:20777"},
    "several targets, none looping": {"target_1": "localhost:3000", "target_2": "example.com:20777"},
}

_LOOP = {
    "localhost, same port": {"target_1": "localhost:20777"},
    "127.0.0.1 among several targets": {"target_1": "example.com:3000", "target_2": "127.0.0.1:20777"},
    "localhost in mixed case": {"target_1": "LocalHost:20777"},
    "localhost with a trailing dot": {"target_1": "localhost.:20777"},
    "another 127.x address": {"target_1": "127.0.0.2:20777"},
}

@allure.story("Cross-section rules")
@allure.title("Forwarding that does not loop back to the telemetry port is accepted ({case})")
@pytest.mark.parametrize("case", list(_NO_LOOP))
def test_forwarding_without_loop_accepted(case):
    """
    Sets Network.telemetry_port to 20777 and forwards to targets that are remote or on another port.

    Expected: PngSettings builds.
    """
    PngSettings(Network=NetworkSettings(telemetry_port=20777), Forwarding=ForwardingSettings(**_NO_LOOP[case]))


@allure.story("Cross-section rules")
@allure.title("Forwarding back to the local telemetry port is rejected ({case})")
@pytest.mark.parametrize("case", list(_LOOP))
def test_forwarding_loop_rejected(case):
    """
    Sets Network.telemetry_port to 20777 and forwards to a loopback host (localhost in any spelling, or a
    127.x address) on that same port.

    Expected: a ValidationError reporting the localhost loop.
    """
    with pytest.raises(ValidationError, match="localhost loop"):
        PngSettings(Network=NetworkSettings(telemetry_port=20777), Forwarding=ForwardingSettings(**_LOOP[case]))

# -------------------------------------- OVERLAY CHANGES ---------------------------------------------------------------

def _moved(oid: OverlayId, **changes) -> OverlayPosition:
    """oid's default layout entry with the given fields changed."""
    return HudSettings.get_default_layout_dict()[oid].model_copy(update=changes)


@allure.story("Overlay changes")
@allure.title("Overlay changes replace the given layout entries and keep the rest")
def test_overlay_changes_replace_only_given_layout_entries():
    """
    Starts from settings with the lap timer moved, then applies a layout holding only a moved MFD with an opacity
    override.

    Expected: the MFD entry is replaced, the lap timer keeps its moved entry, and the original settings are unchanged.
    """
    curr = PngSettings(HUD=HudSettings(layout={OverlayId.LAP_TIMER: _moved(OverlayId.LAP_TIMER, x=11, y=12)}))
    mfd = _moved(OverlayId.MFD, x=7, y=8, opacity_override=OpacityOverride(enabled=True, value=40))

    new = curr.with_overlay_changes({OverlayId.MFD: mfd}, {})

    assert new.HUD.layout[OverlayId.MFD] == mfd
    assert new.HUD.layout[OverlayId.LAP_TIMER] == curr.HUD.layout[OverlayId.LAP_TIMER]
    assert curr.HUD.layout[OverlayId.MFD] == HudSettings.get_default_layout_dict()[OverlayId.MFD]


_OWNED = {
    "track_radar_idle_opacity": 55,
    "track_radar_range_m": 30,
    "circuit_info_length": 900,
}

@allure.story("Overlay changes")
@allure.title("An overlay-owned HUD field is applied ({field})")
@pytest.mark.parametrize("field", list(_OWNED))
def test_overlay_changes_apply_owned_field(field):
    """
    Applies a new value for one HUD field an overlay edits in its popover, with no layout change.

    Expected: the field takes the new value; every other HUD field is unchanged.
    """
    curr = PngSettings()

    new = curr.with_overlay_changes({}, {field: _OWNED[field]})

    assert getattr(new.HUD, field) == _OWNED[field]
    assert curr.HUD.diff(new.HUD) == {field: {"old_value": getattr(curr.HUD, field), "new_value": _OWNED[field]}}


@allure.story("Overlay changes")
@allure.title("Overlay changes matching the current settings change nothing")
def test_overlay_changes_unchanged():
    """
    Applies the current layout and the current values of the overlay-owned HUD fields, as an unchanged lock does.

    Expected: the result does not differ from the current settings.
    """
    curr = PngSettings()

    new = curr.with_overlay_changes(dict(curr.HUD.layout), {field: getattr(curr.HUD, field) for field in _OWNED})

    assert not curr.has_changed(new)


_INVALID = {
    "radar range above its maximum": ({}, {"track_radar_range_m": 999}),
    "circuit info length below its minimum": ({}, {"circuit_info_length": 10}),
    # model_construct skips validation, so the bad value reaches with_overlay_changes
    "layout entry with a bad scale": ({OverlayId.MFD: OverlayPosition.model_construct(
        x=0, y=0, scale_factor=-1, opacity_override=OpacityOverride())}, {}),
}

@allure.story("Overlay changes")
@allure.title("Overlay changes that make the settings invalid are rejected ({case})")
@pytest.mark.parametrize("case", list(_INVALID))
def test_overlay_changes_invalid_rejected(case):
    """
    Applies a layout entry or overlay-owned HUD field value that fails its constraint.

    Expected: a ValidationError, so the launcher saves nothing.
    """
    layout, owned = _INVALID[case]
    with pytest.raises(ValidationError):
        PngSettings().with_overlay_changes(layout, owned)


@allure.story("Overlay changes")
@allure.title("Resetting an overlay restores its default layout entry, opacity override included")
def test_overlay_changes_reset_restores_default():
    """
    Starts from settings with the MFD moved and an opacity override on, then applies the MFD's default entry, as
    Reset Overlays does.

    Expected: the MFD entry equals the default, with the default (disabled) opacity override.
    """
    curr = PngSettings(HUD=HudSettings(layout={
        OverlayId.MFD: _moved(OverlayId.MFD, x=7, opacity_override=OpacityOverride(enabled=True, value=40))}))
    default = HudSettings.get_default_layout_dict()[OverlayId.MFD]

    new = curr.with_overlay_changes({OverlayId.MFD: default}, {})

    assert new.HUD.layout[OverlayId.MFD] == default
    assert new.HUD.layout[OverlayId.MFD].opacity_override == OpacityOverride()
