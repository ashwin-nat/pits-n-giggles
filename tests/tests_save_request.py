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
#
# Tests for the pure parts of apps.backend.state_mgmt_layer.save_request (stem, session data entry).
# build_save_request() itself snapshots a live SessionState, so its gating-table rows wait for the
# state test infrastructure.

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from apps.backend.state_mgmt_layer.save_request import (SaveReason, SaveRequest, build_stem, claim_stem, release_claim)

# ----------------------------------------------------------------------------------------------------------------------

NOW = datetime(2026, 10, 21, 19, 59, 31)


@pytest.mark.parametrize("reason, expected", [
    (SaveReason.AUTO, "Race_Mexico_2026_10_21_19_59_31"),
    (SaveReason.MANUAL, "Race_Mexico_Manual_2026_10_21_19_59_31"),
    (SaveReason.JUST_IN_CASE, "Race_Mexico_Just_in_case_2026_10_21_19_59_31"),
])
def test_build_stem(reason, expected):
    assert build_stem("Race_Mexico_", reason, NOW) == expected


def test_debug_reason_auto_is_descriptive():
    assert SaveReason.AUTO.debug_reason == "Auto-save after final classification"


def test_debug_reason_matches_loose_file_values():
    assert SaveReason.MANUAL.debug_reason == "Manual"
    assert SaveReason.JUST_IN_CASE.debug_reason == "Just_in_case"


def _request(session_data):
    return SaveRequest(
        stem="Race_Mexico_Manual_2026_10_21_19_59_31",
        dest_path=Path("data/2026_10_21/telemetry/x.pngt"),
        reason=SaveReason.MANUAL,
        session_uid=1,
        session_data=session_data,
        lap_telemetry_args=None,
    )


def test_session_data_entry_none_without_json():
    assert _request(None).session_data_entry() is None


def test_session_data_entry_is_named_after_stem_and_compact():
    data = {"a": [1, 2], "debug": {"reason": "Manual"}}
    entry = _request(data).session_data_entry()

    assert entry.file_name == "Race_Mexico_Manual_2026_10_21_19_59_31.json"
    assert entry.entry_name == "session_data/Race_Mexico_Manual_2026_10_21_19_59_31.json"
    assert entry.payload == json.dumps(data, separators=(",", ":")).encode("utf-8")


@pytest.mark.parametrize("session_data, lap_telemetry_args, expected", [
    ({"a": 1}, None, "lap_telemetry=False | session_data=True"),
    (None, ("args",), "lap_telemetry=True | session_data=False"),
    ({"a": 1}, ("args",), "lap_telemetry=True | session_data=True"),
])
def test_str(session_data, lap_telemetry_args, expected):
    request = SaveRequest(
        stem="s", dest_path=Path("s.pngt"), reason=SaveReason.AUTO, session_uid=1,
        session_data=session_data, lap_telemetry_args=lap_telemetry_args)
    assert str(request) == expected


def test_claim_stem_never_hands_out_the_same_container_twice(tmp_path):
    first = claim_stem("Race_Mexico_", SaveReason.MANUAL, NOW, tmp_path)
    second = claim_stem("Race_Mexico_", SaveReason.MANUAL, NOW, tmp_path)
    third = claim_stem("Race_Mexico_", SaveReason.MANUAL, NOW, tmp_path)

    assert first == "Race_Mexico_Manual_2026_10_21_19_59_31"
    assert second == "Race_Mexico_Manual_2026_10_21_19_59_32"
    assert third == "Race_Mexico_Manual_2026_10_21_19_59_33"


def test_claim_stem_skips_a_container_already_on_disk(tmp_path):
    (tmp_path / "Race_Mexico_2026_10_21_19_59_31.pngt").write_bytes(b"")

    assert claim_stem("Race_Mexico_", SaveReason.AUTO, NOW, tmp_path) == "Race_Mexico_2026_10_21_19_59_32"


def test_released_claim_can_be_claimed_again(tmp_path):
    first = claim_stem("Race_Mexico_", SaveReason.MANUAL, NOW, tmp_path)
    release_claim(tmp_path / f"{first}.pngt")

    assert claim_stem("Race_Mexico_", SaveReason.MANUAL, NOW, tmp_path) == first
