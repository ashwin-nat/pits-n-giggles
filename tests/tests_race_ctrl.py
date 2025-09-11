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

import asyncio
import os
import sys
from typing import Set

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests_base import F1TelemetryUnitTestsBase

from lib.race_ctrl import SessionRaceControlManager, RaceControlMessage, MessageType, DriverRaceControlManager

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class TestRaceControlMessages(F1TelemetryUnitTestsBase):

    def setUp(self) -> None:
        self.session_mgr = SessionRaceControlManager()
        self.driver1_mgr = DriverRaceControlManager(driver_index=1)
        self.driver2_mgr = DriverRaceControlManager(driver_index=2)
        self.session_mgr.register_driver(1, self.driver1_mgr)
        self.session_mgr.register_driver(2, self.driver2_mgr)

    async def test_add_message_and_index_as_id(self):
        msg = RaceControlMessage(
            timestamp=1.23,
            message_type=MessageType.FLAG,
            involved_drivers=set(),
        )
        msg_id = self.session_mgr.add_message(msg)

        self.assertEqual(msg_id, 0)  # first message gets index 0
        self.assertIs(self.session_mgr.messages[msg_id], msg)

    async def test_message_stored_in_driver_refs(self):
        msg = RaceControlMessage(
            timestamp=2.34,
            message_type=MessageType.PENALTY,
            involved_drivers={1, 2},
        )
        self.session_mgr.add_message(msg)

        self.assertIn(msg, self.driver1_mgr.messages)
        self.assertIn(msg, self.driver2_mgr.messages)
        self.assertIs(self.driver1_mgr.messages[0], msg)  # reference, not copy
        self.assertIs(self.driver2_mgr.messages[0], msg)

    async def test_message_with_no_driver_involvement(self):
        msg = RaceControlMessage(
            timestamp=3.45,
            message_type=MessageType.NOTE,
            involved_drivers=set(),
        )
        self.session_mgr.add_message(msg)

        self.assertEqual(len(self.driver1_mgr.messages), 0)
        self.assertEqual(len(self.driver2_mgr.messages), 0)

    async def test_clear_resets_session_and_drivers(self):
        msg = RaceControlMessage(
            timestamp=4.56,
            message_type=MessageType.OTHER,
            involved_drivers={1},
        )
        self.session_mgr.add_message(msg)

        self.assertTrue(self.session_mgr.messages)
        self.assertTrue(self.driver1_mgr.messages)

        self.session_mgr.clear()

        self.assertEqual(len(self.session_mgr.messages), 0)
        self.assertEqual(len(self.driver1_mgr.messages), 0)
        self.assertEqual(len(self.driver2_mgr.messages), 0)
        self.assertEqual(len(self.session_mgr.drivers), 0)

    async def test_to_json_exports_ids_and_data(self):
        msg1 = RaceControlMessage(
            timestamp=5.0,
            message_type=MessageType.FLAG,
            involved_drivers={1},
        )
        msg2 = RaceControlMessage(
            timestamp=6.0,
            message_type=MessageType.NOTE,
            involved_drivers={2},
        )
        self.session_mgr.add_message(msg1)
        self.session_mgr.add_message(msg2)

        exported = self.session_mgr.to_json()

        self.assertEqual(exported[0]["id"], 0)
        self.assertEqual(exported[0]["message_type"], "FLAG")
        self.assertEqual(exported[1]["id"], 1)
        self.assertEqual(exported[1]["message_type"], "NOTE")

    async def test_message_is_immutable(self):
        msg = RaceControlMessage(
            timestamp=7.89,
            message_type=MessageType.FLAG,
            involved_drivers={1},
        )
        with self.assertRaises(Exception):
            msg.timestamp = 9.99  # frozen dataclass, should not allow reassignment

    async def test_message_with_single_driver(self):
        msg = RaceControlMessage(
            timestamp=8.88,
            message_type=MessageType.PENALTY,
            involved_drivers={1},
        )
        self.session_mgr.add_message(msg)

        # Stored in session
        self.assertIn(msg, self.session_mgr.messages)
        # Stored only in driver 1 manager
        self.assertIn(msg, self.driver1_mgr.messages)
        self.assertEqual(len(self.driver1_mgr.messages), 1)
        # Not stored in driver 2 manager
        self.assertEqual(len(self.driver2_mgr.messages), 0)