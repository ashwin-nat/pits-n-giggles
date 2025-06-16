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

from lib.f1_types import SessionType23, SessionType24
from .tests_parser_base import F1TypesTest


class TestSessionType23(F1TypesTest):

    def test_is_fp_type_session(self):
        fp_sessions = [
            SessionType23.PRACTICE_1,
            SessionType23.PRACTICE_2,
            SessionType23.PRACTICE_3,
            SessionType23.SHORT_PRACTICE
        ]
        for session in fp_sessions:
            with self.subTest(session=session):
                self.assertTrue(session.isFpTypeSession())

        non_fp_sessions = [
            SessionType23.QUALIFYING_1,
            SessionType23.RACE,
            SessionType23.TIME_TRIAL
        ]
        for session in non_fp_sessions:
            with self.subTest(session=session):
                self.assertFalse(session.isFpTypeSession())

    def test_is_quali_type_session(self):
        quali_sessions = [
            SessionType23.QUALIFYING_1,
            SessionType23.QUALIFYING_2,
            SessionType23.QUALIFYING_3,
            SessionType23.SHORT_QUALIFYING,
            SessionType23.ONE_SHOT_QUALIFYING
        ]
        for session in quali_sessions:
            with self.subTest(session=session):
                self.assertTrue(session.isQualiTypeSession())

        non_quali_sessions = [
            SessionType23.PRACTICE_1,
            SessionType23.RACE,
            SessionType23.TIME_TRIAL
        ]
        for session in non_quali_sessions:
            with self.subTest(session=session):
                self.assertFalse(session.isQualiTypeSession())

    def test_is_race_type_session(self):
        race_sessions = [
            SessionType23.RACE,
            SessionType23.RACE_2,
            SessionType23.RACE_3
        ]
        for session in race_sessions:
            with self.subTest(session=session):
                self.assertTrue(session.isRaceTypeSession())

        non_race_sessions = [
            SessionType23.QUALIFYING_1,
            SessionType23.PRACTICE_1,
            SessionType23.TIME_TRIAL
        ]
        for session in non_race_sessions:
            with self.subTest(session=session):
                self.assertFalse(session.isRaceTypeSession())

class TestSessionType24(F1TypesTest):

    def test_is_fp_type_session(self):
        fp_sessions = [
            SessionType24.PRACTICE_1,
            SessionType24.PRACTICE_2,
            SessionType24.PRACTICE_3,
            SessionType24.SHORT_PRACTICE
        ]
        for session in fp_sessions:
            with self.subTest(session=session):
                self.assertTrue(session.isFpTypeSession())

        non_fp_sessions = [
            SessionType24.QUALIFYING_1,
            SessionType24.SPRINT_SHOOTOUT_1,
            SessionType24.RACE,
            SessionType24.TIME_TRIAL
        ]
        for session in non_fp_sessions:
            with self.subTest(session=session):
                self.assertFalse(session.isFpTypeSession())

    def test_is_quali_type_session(self):
        quali_sessions = [
            SessionType24.QUALIFYING_1,
            SessionType24.QUALIFYING_2,
            SessionType24.QUALIFYING_3,
            SessionType24.SHORT_QUALIFYING,
            SessionType24.ONE_SHOT_QUALIFYING,
            SessionType24.SPRINT_SHOOTOUT_1,
            SessionType24.SPRINT_SHOOTOUT_2,
            SessionType24.SPRINT_SHOOTOUT_3,
            SessionType24.SHORT_SPRINT_SHOOTOUT,
            SessionType24.ONE_SHOT_SPRINT_SHOOTOUT,
        ]
        for session in quali_sessions:
            with self.subTest(session=session):
                self.assertTrue(session.isQualiTypeSession())

        non_quali_sessions = [
            SessionType24.PRACTICE_1,
            SessionType24.RACE,
            SessionType24.TIME_TRIAL
        ]
        for session in non_quali_sessions:
            with self.subTest(session=session):
                self.assertFalse(session.isQualiTypeSession())

    def test_is_race_type_session(self):
        race_sessions = [
            SessionType24.RACE,
            SessionType24.RACE_2,
            SessionType24.RACE_3,
            SessionType24.TIME_TRIAL
        ]
        for session in race_sessions:
            with self.subTest(session=session):
                self.assertTrue(session.isRaceTypeSession())

        non_race_sessions = [
            SessionType24.QUALIFYING_1,
            SessionType24.SPRINT_SHOOTOUT_1,
            SessionType24.PRACTICE_1
        ]
        for session in non_race_sessions:
            with self.subTest(session=session):
                self.assertFalse(session.isRaceTypeSession())

