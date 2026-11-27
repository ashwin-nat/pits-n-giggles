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

"""ForwardingSettings rules the field spec table does not cover: defaults, the parsed target list and duplicate
targets. The host:port format of each target is in tests_config_properties.py."""

import allure
import pytest
from pydantic import ValidationError

from lib.config import ForwardingSettings

pytestmark = allure.feature("Forwarding settings")

# -------------------------------------- DEFAULTS ----------------------------------------------------------------------

@allure.story("Defaults")
@allure.title("Default ForwardingSettings forward nowhere")
def test_default_values():
    """
    Builds ForwardingSettings with no arguments.

    Expected: all three targets are empty, so the parsed target list is empty.
    """
    settings = ForwardingSettings()

    assert (settings.target_1, settings.target_2, settings.target_3) == ("", "", "")
    assert settings.forwarding_targets == []

# -------------------------------------- PARSED TARGETS ----------------------------------------------------------------

_TARGET_LISTS = {
    "all empty": ({"target_1": "", "target_2": "", "target_3": ""}, []),
    "all None": ({"target_1": None, "target_2": None, "target_3": None}, []),
    "one target": ({"target_1": "localhost:8080"}, [("localhost", 8080)]),
    "three targets": (
        {"target_1": "host1.example.com:1234", "target_2": "192.168.1.10:65535", "target_3": "myhost:1"},
        [("host1.example.com", 1234), ("192.168.1.10", 65535), ("myhost", 1)],
    ),
}

@allure.story("Derived values")
@allure.title("forwarding_targets lists the set targets as (host, port), in order ({case})")
@pytest.mark.parametrize("case", list(_TARGET_LISTS))
def test_forwarding_targets(case):
    """
    Sets some or all of the three targets and reads forwarding_targets.

    Expected: one (host, int port) pair per non-empty target, in target order.
    """
    targets, expected = _TARGET_LISTS[case]

    assert ForwardingSettings(**targets).forwarding_targets == expected

# -------------------------------------- DUPLICATE TARGETS -------------------------------------------------------------

_DISTINCT = {
    "different hosts, same port": {"target_1": "example.com:1234", "target_2": "example.org:1234"},
    "localhost and remote, same port": {"target_1": "localhost:5000", "target_2": "example.com:5000"},
}

_DUPLICATE = {
    "localhost and 127.0.0.1": {"target_1": "localhost:6000", "target_2": "127.0.0.1:6000"},
    "exact duplicate": {"target_1": "myhost:7000", "target_2": "myhost:7000"},
    "different letter case": {"target_1": "MyHost:7000", "target_2": "myhost:7000"},
    "absolute name": {"target_1": "nas.lan.:7000", "target_2": "nas.lan:7000"},
}

@allure.story("Cross-field rules")
@allure.title("Distinct forwarding targets are accepted ({case})")
@pytest.mark.parametrize("case", list(_DISTINCT))
def test_distinct_targets_accepted(case):
    """
    Sets two targets that differ in host.

    Expected: the model builds.
    """
    ForwardingSettings(**_DISTINCT[case])


@allure.story("Cross-field rules")
@allure.title("Duplicate forwarding targets are rejected ({case})")
@pytest.mark.parametrize("case", list(_DUPLICATE))
def test_duplicate_targets_rejected(case):
    """
    Sets two targets with the same port and the same host, counting localhost and 127.0.0.1 as one host, and
    ignoring letter case and a trailing dot.

    Expected: a ValidationError reporting the duplicate target.
    """
    with pytest.raises(ValidationError, match="Duplicate forwarding target"):
        ForwardingSettings(**_DUPLICATE[case])
