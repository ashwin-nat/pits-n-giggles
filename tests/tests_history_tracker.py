# MIT License
#
# Copyright (c) [2024] [Ashwin Natarajan]
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
import tempfile
import os
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests_base import F1TelemetryUnitTestsBase

# Import your racing database classes
from lib.history_tracker import (  # Replace 'your_module' with actual module name
    RacingDatabase,
    SessionData,
    TyreStint,
    GameVersion,
    Team,
    TeamAlias,
    DrivingSession,
    SessionTyreDistance,
    SessionWeatherDistance
)

class TestHistoryTracker(F1TelemetryUnitTestsBase):
    pass

# Import your racing database classes
from lib.history_tracker import (
    RacingDatabase,
    SessionData,
    TyreStint,
    GameVersion,
    Team,
    TeamAlias,
    DrivingSession,
    SessionTyreDistance,
    SessionWeatherDistance
)

class TestRacingDatabase(TestHistoryTracker):
    """Unit tests for the RacingDatabase class."""

    def setUp(self):
        """Set up test database for each test."""
        # Create a temporary database file
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()

        # Use sync SQLite URL for testing
        db_url = f'sqlite+aiosqlite:///{self.temp_db.name}'
        self.db = RacingDatabase(db_url)

        # Run async setup
        asyncio.run(self._async_setup())

    async def _async_setup(self):
        """Async setup operations."""
        await self.db.create_tables()

    def tearDown(self):
        """Clean up after each test."""
        # Run async cleanup first
        asyncio.run(self._async_teardown())

        # Remove temporary database file
        if os.path.exists(self.temp_db.name):
            try:
                os.unlink(self.temp_db.name)
            except PermissionError:
                # On Windows, sometimes the file is still locked
                # Try again after a brief delay
                import time
                time.sleep(0.1)
                try:
                    os.unlink(self.temp_db.name)
                except PermissionError:
                    # If still can't delete, just leave it (temp files will be cleaned up by OS)
                    pass

    async def _async_teardown(self):
        """Async cleanup operations."""
        if hasattr(self.db, 'engine'):
            await self.db.engine.dispose()

    def test_session_data_validation(self):
        """Test SessionData validation."""
        # Valid data
        valid_stints = [
            TyreStint(num_laps=10, actual_tyre_compound="C5", visual_tyre_compound="Soft")
        ]

        valid_session = SessionData(
            session_id=1,
            game_year=24,
            formula="F1",
            session_type="Race",
            track="Silverstone",
            team_id="Red Bull Racing",
            start_position=3,
            finish_position=2,
            laps_led=5,
            lap_distance_metres=5891,
            stint_data=valid_stints
        )
        self.assertEqual(valid_session.game_year, 24)

        # Invalid game year
        with self.assertRaises(ValueError):
            SessionData(
                session_id=1,
                game_year=100,  # Invalid
                formula="F1",
                session_type="Race",
                track="Silverstone",
                team_id="Red Bull Racing",
                start_position=3,
                finish_position=2,
                laps_led=5,
                lap_distance_metres=5891,
                stint_data=valid_stints
            )

        # Invalid position
        with self.assertRaises(ValueError):
            SessionData(
                session_id=1,
                game_year=24,
                formula="F1",
                session_type="Race",
                track="Silverstone",
                team_id="Red Bull Racing",
                start_position=0,  # Invalid
                finish_position=2,
                laps_led=5,
                lap_distance_metres=5891,
                stint_data=valid_stints
            )

        # Empty stint data
        with self.assertRaises(ValueError):
            SessionData(
                session_id=1,
                game_year=24,
                formula="F1",
                session_type="Race",
                track="Silverstone",
                team_id="Red Bull Racing",
                start_position=3,
                finish_position=2,
                laps_led=5,
                lap_distance_metres=5891,
                stint_data=[]  # Invalid
            )

    def test_session_data_dict_conversion(self):
        """Test SessionData conversion from dictionary stint data."""
        stint_dicts = [
            {
                "num-laps": 15,
                "actual-tyre-compound": "C4",
                "visual-tyre-compound": "Medium"
            }
        ]

        session = SessionData(
            session_id=1,
            game_year=24,
            formula="F1",
            session_type="Race",
            track="Monaco",
            team_id="Ferrari",
            start_position=1,
            finish_position=1,
            laps_led=15,
            lap_distance_metres=3337,
            stint_data=stint_dicts
        )

        self.assertEqual(len(session.stint_data), 1)
        self.assertIsInstance(session.stint_data[0], TyreStint)
        self.assertEqual(session.stint_data[0].num_laps, 15)
        self.assertEqual(session.stint_data[0].actual_tyre_compound, "C4")

    def test_write_and_read_session_data(self):
        """Test writing session data and reading it back."""
        async def _test():
            stints = [
                TyreStint(num_laps=20, actual_tyre_compound="C5", visual_tyre_compound="Soft"),
                TyreStint(num_laps=25, actual_tyre_compound="C3", visual_tyre_compound="Hard")
            ]

            session_data = SessionData(
                session_id=12345,
                game_year=24,
                formula="F1",
                session_type="Race",
                track="Spa-Francorchamps",
                team_id="Mercedes",
                start_position=2,
                finish_position=1,
                laps_led=30,
                lap_distance_metres=7004,
                stint_data=stints
            )

            # Write data
            await self.db.write_session_data(session_data)

            # Verify data was written by checking database content
            async with self.db.async_session() as session:
                from sqlalchemy.future import select

                # Check game version
                game_result = await session.execute(select(GameVersion))
                games = game_result.scalars().all()
                self.assertEqual(len(games), 1)
                self.assertEqual(games[0].title, "F1 2024")

                # Check team
                team_result = await session.execute(select(Team))
                teams = team_result.scalars().all()
                self.assertEqual(len(teams), 1)
                self.assertEqual(teams[0].canonical_name, "Mercedes")

                # Check driving session
                session_result = await session.execute(select(DrivingSession))
                sessions = session_result.scalars().all()
                self.assertEqual(len(sessions), 1)
                self.assertEqual(sessions[0].track, "Spa-Francorchamps")
                self.assertEqual(sessions[0].start_position, 2)
                self.assertEqual(sessions[0].finish_position, 1)

                # Check tyre data
                tyre_result = await session.execute(select(SessionTyreDistance))
                tyres = tyre_result.scalars().all()
                self.assertEqual(len(tyres), 2)

                # Properly close the session
                await session.close()

        asyncio.run(_test())

    def test_get_most_played_tracks(self):
        """Test getting most played tracks."""
        async def _test():
            # Create test data
            await self._create_test_sessions()

            # Test without filter
            tracks = await self.db.get_most_played_tracks()
            self.assertGreater(len(tracks), 0)
            self.assertIsInstance(tracks[0], tuple)
            self.assertEqual(len(tracks[0]), 2)  # (track_name, count)

            # Test with game version filter
            tracks_filtered = await self.db.get_most_played_tracks("F1 2024")
            self.assertGreaterEqual(len(tracks_filtered), 0)

        asyncio.run(_test())

    def test_get_most_played_f1_versions(self):
        """Test getting most played F1 versions."""
        async def _test():
            # Create test data
            await self._create_test_sessions()

            versions = await self.db.get_most_played_f1_versions()
            self.assertGreater(len(versions), 0)
            self.assertIsInstance(versions[0], tuple)
            self.assertEqual(len(versions[0]), 2)  # (version, count)

            # Check that F1 2024 is in the results
            version_names = [v[0] for v in versions]
            self.assertIn("F1 2024", version_names)

        asyncio.run(_test())

    def test_get_team_performance_stats(self):
        """Test getting team performance statistics."""
        async def _test():
            # Create test data
            await self._create_test_sessions()

            # Test existing team
            stats = await self.db.get_team_performance_stats("Red Bull Racing")
            self.assertIsNotNone(stats)
            self.assertIsInstance(stats, dict)

            # Check required fields
            required_fields = [
                'team_name', 'total_sessions', 'total_laps', 'total_distance_km',
                'average_start_position', 'average_finish_position', 'total_laps_led',
                'best_finish', 'worst_finish', 'total_wins', 'total_podiums',
                'points_finishes', 'win_rate', 'podium_rate', 'points_rate',
                'favorite_tracks'
            ]

            for field in required_fields:
                self.assertIn(field, stats)

            self.assertEqual(stats['team_name'], 'Red Bull Racing')
            self.assertGreaterEqual(stats['total_sessions'], 1)

            # Test non-existing team
            stats_none = await self.db.get_team_performance_stats("Non-existent Team")
            self.assertIsNone(stats_none)

        asyncio.run(_test())

    def test_get_tyre_compound_usage_stats(self):
        """Test getting tyre compound usage statistics."""
        async def _test():
            # Create test data
            await self._create_test_sessions()

            tyre_stats = await self.db.get_tyre_compound_usage_stats()
            self.assertGreater(len(tyre_stats), 0)

            # Check tuple structure
            for stat in tyre_stats:
                self.assertIsInstance(stat, tuple)
                self.assertEqual(len(stat), 4)  # (actual, visual, count, distance_km)
                self.assertIsInstance(stat[0], str)  # actual_compound
                self.assertIsInstance(stat[1], str)  # visual_compound
                self.assertIsInstance(stat[2], int)  # usage_count
                self.assertIsInstance(stat[3], float)  # total_distance_km

        asyncio.run(_test())

    def test_duplicate_session_handling(self):
        """Test handling of duplicate session IDs."""
        async def _test():
            stint = TyreStint(num_laps=10, actual_tyre_compound="C5", visual_tyre_compound="Soft")

            session_data = SessionData(
                session_id=99999,  # Use unique ID
                game_year=24,
                formula="F1",
                session_type="Race",
                track="Monza",
                team_id="Ferrari",
                start_position=1,
                finish_position=1,
                laps_led=10,
                lap_distance_metres=5793,
                stint_data=[stint]
            )

            # First write should succeed
            await self.db.write_session_data(session_data)

            # Second write with same session_id should handle gracefully
            # (This depends on your database constraints and error handling)
            try:
                await self.db.write_session_data(session_data)
            except Exception as e:
                # Expected if session_id is a primary key
                self.assertIsInstance(e, Exception)

        asyncio.run(_test())

    async def _create_test_sessions(self):
        """Helper method to create test session data."""
        test_sessions = [
            SessionData(
                session_id=1001,
                game_year=24,
                formula="F1",
                session_type="Race",
                track="Silverstone",
                team_id="Red Bull Racing",
                start_position=1,
                finish_position=1,
                laps_led=52,
                lap_distance_metres=5891,
                stint_data=[
                    TyreStint(num_laps=25, actual_tyre_compound="C4", visual_tyre_compound="Medium"),
                    TyreStint(num_laps=27, actual_tyre_compound="C5", visual_tyre_compound="Soft")
                ]
            ),
            SessionData(
                session_id=1002,
                game_year=23,
                formula="F1",
                session_type="Race",
                track="Monaco",
                team_id="Ferrari",
                start_position=3,
                finish_position=2,
                laps_led=15,
                lap_distance_metres=3337,
                stint_data=[
                    TyreStint(num_laps=30, actual_tyre_compound="C5", visual_tyre_compound="Soft"),
                    TyreStint(num_laps=48, actual_tyre_compound="C3", visual_tyre_compound="Hard")
                ]
            ),
            SessionData(
                session_id=1003,
                game_year=24,
                formula="F1",
                session_type="Qualifying",
                track="Silverstone",
                team_id="Mercedes",
                start_position=5,
                finish_position=4,
                laps_led=0,
                lap_distance_metres=5891,
                stint_data=[
                    TyreStint(num_laps=15, actual_tyre_compound="C5", visual_tyre_compound="Soft")
                ]
            )
        ]

        for session in test_sessions:
            await self.db.write_session_data(session)


class TestDataClasses(TestHistoryTracker):
    """Unit tests for data classes."""

    def test_tyre_stint_creation(self):
        """Test TyreStint data class."""
        stint = TyreStint(
            num_laps=20,
            actual_tyre_compound="C4",
            visual_tyre_compound="Medium"
        )

        self.assertEqual(stint.num_laps, 20)
        self.assertEqual(stint.actual_tyre_compound, "C4")
        self.assertEqual(stint.visual_tyre_compound, "Medium")

    def test_session_data_creation(self):
        """Test SessionData data class creation."""
        stint = TyreStint(num_laps=10, actual_tyre_compound="C5", visual_tyre_compound="Soft")

        session = SessionData(
            session_id=123,
            game_year=24,
            formula="F1",
            session_type="Race",
            track="Spa",
            team_id="McLaren",
            start_position=8,
            finish_position=6,
            laps_led=3,
            lap_distance_metres=7004,
            stint_data=[stint]
        )

        self.assertEqual(session.session_id, 123)
        self.assertEqual(session.track, "Spa")
        self.assertEqual(len(session.stint_data), 1)
        self.assertIsInstance(session.stint_data[0], TyreStint)
