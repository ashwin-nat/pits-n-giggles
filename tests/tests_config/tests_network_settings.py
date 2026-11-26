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

"""NetworkSettings rules the field spec table does not cover: defaults, cross-field rules and derived values.
Per-field ranges and types, bind_address included, are in tests_config_properties.py."""

import allure
import pytest
from pydantic import ValidationError

from lib.config import NetworkSettings
from lib.config.schema.utils import PortConflictError, UdpActionCodeConflictError

pytestmark = allure.feature("Network settings")

# -------------------------------------- DEFAULTS ----------------------------------------------------------------------

@allure.story("Defaults")
@allure.title("Default NetworkSettings hold the shipped values")
def test_default_values():
    """
    Builds NetworkSettings with no arguments.

    Expected: every field holds its shipped default.
    """
    settings = NetworkSettings()

    assert settings.telemetry_port == 20777
    assert settings.server_port == 4768
    assert settings.broker_xpub_port == 53838
    assert settings.broker_xsub_port == 53835
    assert settings.broker_router_port == 53836
    assert settings.bind_address == "0.0.0.0"
    assert settings.udp_tyre_delta_action_code is None
    assert settings.udp_custom_action_code is None
    assert settings.wdt_interval_sec == 30
    assert settings.enable_pkt_ordering is False
    assert settings.udp_action_button_debounce_ms == 100

# -------------------------------------- CROSS-FIELD RULES -------------------------------------------------------------

@allure.story("Cross-field rules")
@allure.title("The tyre delta and custom UDP action codes must differ")
def test_udp_action_codes_must_differ():
    """
    Sets both UDP action codes to 5.

    Expected: a ValidationError saying the two must not be the same.
    """
    with pytest.raises(ValidationError, match="must not be the same") as exc:
        NetworkSettings(udp_tyre_delta_action_code=5, udp_custom_action_code=5)
    assert isinstance(exc.value.errors()[0]["ctx"]["error"], UdpActionCodeConflictError)


_PORT_CONFLICTS = {
    "two TCP ports": {"server_port": 5000, "broker_xpub_port": 5000},
    "three TCP ports": {"server_port": 7000, "broker_xpub_port": 7000, "broker_xsub_port": 7000},
    "router and xsub": {"broker_xsub_port": 9000, "broker_router_port": 9000},
}

@allure.story("Cross-field rules")
@allure.title("Two TCP port fields cannot share a port ({case})")
@pytest.mark.parametrize("case", list(_PORT_CONFLICTS))
def test_tcp_port_conflict_rejected(case):
    """
    Sets two or three TCP port fields to the same port.

    Expected: a ValidationError reporting the port conflict.
    """
    with pytest.raises(ValidationError, match="Port conflict") as exc:
        NetworkSettings(**_PORT_CONFLICTS[case])
    assert isinstance(exc.value.errors()[0]["ctx"]["error"], PortConflictError)


@allure.story("Cross-field rules")
@allure.title("A UDP and a TCP port field may share a port number")
def test_udp_and_tcp_may_share_port():
    """
    Sets the UDP telemetry port and the TCP server port to the same number.

    Expected: the model builds, since conflicts are checked per protocol.
    """
    settings = NetworkSettings(telemetry_port=6000, server_port=6000)

    assert settings.telemetry_port == settings.server_port == 6000

# -------------------------------------- DERIVED VALUES ----------------------------------------------------------------

@allure.story("Derived values")
@allure.title("udp_action_debounce_sec is {ms} ms in seconds")
@pytest.mark.parametrize("ms, sec", [(0, 0.0), (100, 0.1), (500, 0.5)])
def test_udp_action_debounce_sec(ms, sec):
    """
    Sets udp_action_button_debounce_ms and reads udp_action_debounce_sec.

    Expected: the property is the same duration in seconds.
    """
    assert NetworkSettings(udp_action_button_debounce_ms=ms).udp_action_debounce_sec == pytest.approx(sec)
