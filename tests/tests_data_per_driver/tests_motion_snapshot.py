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

"""addTelemetrySnapshot wiring for the motion sensors: values pass through from the stored
motion packet untouched, and read as None until that packet has arrived."""

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

import logging
from unittest.mock import MagicMock

import pytest

from apps.backend.state_mgmt_layer.data_per_driver.data_per_driver import \
    DataPerDriver

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

# TelemetrySnapshot field -> CarMotionData attribute
MOTION_FIELDS = {
    "motion_pos_x": "m_worldPositionX",
    "motion_pos_y": "m_worldPositionY",
    "motion_pos_z": "m_worldPositionZ",
    "motion_yaw": "m_yaw",
}

# -------------------------------------- FIXTURES ----------------------------------------------------------------------

@pytest.fixture(name="driver")
def _driver() -> DataPerDriver:
    obj = DataPerDriver(
        index=0,
        logger=logging.getLogger("test"),
        total_laps=50,
        state_ref=MagicMock(),
        weather_aware_prediction=False,
        tyre_wear_window_size=None,
        harvest_power_window_size=5,
        track_segments_db=MagicMock(),
    )
    obj.m_tel_rec = MagicMock()
    return obj

def _recorded_snapshot(driver: DataPerDriver):
    driver.addTelemetrySnapshot(frame_id=1)
    return driver.m_tel_rec.update.call_args.args[0]

# -------------------------------------- TESTS -------------------------------------------------------------------------

def test_motion_values_pass_through_unchanged(driver):
    pkt = MagicMock()
    expected = {}
    for i, (field, attr) in enumerate(MOTION_FIELDS.items(), start=1):
        setattr(pkt, attr, i * 1.5)
        expected[field] = i * 1.5
    driver.m_packet_copies.m_packet_motion = pkt

    snapshot = _recorded_snapshot(driver)

    assert {f: getattr(snapshot, f) for f in MOTION_FIELDS} == expected

def test_motion_is_none_before_packet_arrives(driver):
    assert driver.m_packet_copies.m_packet_motion is None

    snapshot = _recorded_snapshot(driver)

    assert all(getattr(snapshot, f) is None for f in MOTION_FIELDS)
