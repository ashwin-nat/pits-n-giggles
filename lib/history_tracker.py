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

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

import asyncio
import datetime
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import ForeignKey, and_, create_engine, desc, func
from sqlalchemy.ext.asyncio import (AsyncAttrs, AsyncSession,
                                    create_async_engine)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.future import select
from sqlalchemy.orm import (DeclarativeBase, Mapped, mapped_column,
                            relationship, sessionmaker)
from sqlalchemy.sql import text


@dataclass
class TyreStint:
    """Represents a single tyre stint within a driving session."""
    num_laps: int
    actual_tyre_compound: str
    visual_tyre_compound: str


@dataclass
class SessionData:
    """Represents a complete driving session with all associated data."""
    session_id: int
    game_year: int
    formula: str
    session_type: str
    track: str
    team_id: str
    start_position: int
    finish_position: int
    laps_led: int
    lap_distance_metres: int
    stint_data: List[TyreStint]

    def __post_init__(self):
        """Validate the session data after initialization."""
        if self.game_year < 0 or self.game_year > 99:
            raise ValueError("Game year must be between 0 and 99")
        if self.start_position < 1 or self.finish_position < 1:
            raise ValueError("Positions must be greater than 0")
        if self.laps_led < 0:
            raise ValueError("Laps led cannot be negative")
        if self.lap_distance_metres <= 0:
            raise ValueError("Lap distance must be positive")
        if not self.stint_data:
            raise ValueError("Session must have at least one stint")

        # Convert stint_data to TyreStint objects if they're dictionaries
        converted_stints = []
        for stint in self.stint_data:
            if isinstance(stint, dict):
                converted_stints.append(TyreStint(
                    num_laps=stint["num-laps"],
                    actual_tyre_compound=stint["actual-tyre-compound"],
                    visual_tyre_compound=stint["visual-tyre-compound"]
                ))
            else:
                converted_stints.append(stint)
        self.stint_data = converted_stints


# Base class for all models
class Base(AsyncAttrs, DeclarativeBase):
    pass


class GameVersion(Base):
    __tablename__ = "game_version"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]

    # Relationships
    team_aliases = relationship("TeamAlias", back_populates="game_version")
    driving_sessions = relationship("DrivingSession", back_populates="game_version")

    def __repr__(self):
        return f"<GameVersion(id={self.id}, title='{self.title}')>"


class Team(Base):
    __tablename__ = "team"

    id: Mapped[int] = mapped_column(primary_key=True)
    canonical_name: Mapped[str]

    # Relationships
    team_aliases = relationship("TeamAlias", back_populates="team")
    driving_sessions = relationship("DrivingSession", back_populates="team")

    def __repr__(self):
        return f"<Team(id={self.id}, canonical_name='{self.canonical_name}')>"


class TeamAlias(Base):
    __tablename__ = "team_alias"

    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("team.id"))
    game_version_id: Mapped[int] = mapped_column(ForeignKey("game_version.id"))
    alias_name: Mapped[str]

    # Relationships
    team = relationship("Team", back_populates="team_aliases")
    game_version = relationship("GameVersion", back_populates="team_aliases")

    def __repr__(self):
        return f"<TeamAlias(id={self.id}, team_id={self.team_id}, game_version_id={self.game_version_id}, alias_name='{self.alias_name}')>"


class DrivingSession(Base):
    __tablename__ = "driving_session"

    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("team.id"))
    game_version_id: Mapped[int] = mapped_column(ForeignKey("game_version.id"))
    track: Mapped[str]
    game_mode: Mapped[str]
    car: Mapped[str]
    distance_m: Mapped[int]
    distance_laps: Mapped[int]
    session_date: Mapped[datetime.datetime]
    start_position: Mapped[int]
    finish_position: Mapped[int]
    laps_led: Mapped[int]
    lap_distance_m: Mapped[int]

    # Relationships
    team = relationship("Team", back_populates="driving_sessions")
    game_version = relationship("GameVersion", back_populates="driving_sessions")
    tyre_distances = relationship("SessionTyreDistance", back_populates="session")
    weather_distances = relationship("SessionWeatherDistance", back_populates="session")

    def __repr__(self):
        return f"<DrivingSession(id={self.id}, team_id={self.team_id}, track='{self.track}')>"


class SessionTyreDistance(Base):
    __tablename__ = "session_tyre_distance"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("driving_session.id"))
    actual_compound: Mapped[str]
    visual_compound: Mapped[str]
    distance_m: Mapped[int]
    distance_laps: Mapped[int]

    # Relationships
    session = relationship("DrivingSession", back_populates="tyre_distances")

    def __repr__(self):
        return f"<SessionTyreDistance(id={self.id}, session_id={self.session_id}, actual_compound='{self.actual_compound}', distance_laps={self.distance_laps})>"


class SessionWeatherDistance(Base):
    __tablename__ = "session_weather_distance"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("driving_session.id"))
    weather_type: Mapped[str]
    distance_m: Mapped[int]
    distance_laps: Mapped[int]

    # Relationships
    session = relationship("DrivingSession", back_populates="weather_distances")

    def __repr__(self):
        return f"<SessionWeatherDistance(id={self.id}, session_id={self.session_id}, weather_type='{self.weather_type}', distance_laps={self.distance_laps})>"

class RacingDatabase:
    def __init__(self, logger: Optional[logging.Logger] = None, db_name: Optional[str] = 'png'):
        """
        Initialize the racing database.

        Args:
            logger: Logger to use for logging.
            db_name: Name of the database file to create. (without extension)
        """
        db_url = f'sqlite+aiosqlite:///{db_name}.db'
        self.logger = logger
        self.engine = create_async_engine(db_url, echo=False)
        self.async_session = sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )

    async def create_tables(self):
        """Create all tables in the database."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def get_or_create_game_version(self, session: AsyncSession, title: str) -> GameVersion:
        """Get an existing game version or create a new one."""
        result = await session.execute(select(GameVersion).where(GameVersion.title == title))
        game_version = result.scalars().first()

        if game_version is None:
            game_version = GameVersion(title=title)
            session.add(game_version)
            await session.flush()

        return game_version

    async def get_or_create_team(self, session: AsyncSession, canonical_name: str) -> Team:
        """Get an existing team or create a new one."""
        result = await session.execute(select(Team).where(Team.canonical_name == canonical_name))
        team = result.scalars().first()

        if team is None:
            team = Team(canonical_name=canonical_name)
            session.add(team)
            await session.flush()

        return team

    async def get_or_create_team_alias(
        self,
        session: AsyncSession,
        team: Team,
        game_version: GameVersion,
        alias_name: str
    ) -> TeamAlias:
        """Get an existing team alias or create a new one."""
        result = await session.execute(
            select(TeamAlias).where(
                TeamAlias.team_id == team.id,
                TeamAlias.game_version_id == game_version.id,
                TeamAlias.alias_name == alias_name
            )
        )
        team_alias = result.scalars().first()

        if team_alias is None:
            team_alias = TeamAlias(
                team_id=team.id,
                game_version_id=game_version.id,
                alias_name=alias_name
            )
            session.add(team_alias)
            await session.flush()

        return team_alias

    async def write_session_data(self, data: SessionData):
        """
        Write session data to the database using a SessionData object.

        Args:
            data: A SessionData object containing all session information.
        """
        async with self.async_session() as session:
            async with session.begin():
                # Get or create the game version (format: "F1 [year]")
                game_title = f"{data.formula} 20{data.game_year}"
                game_version = await self.get_or_create_game_version(session, game_title)

                # Get or create the team
                team = await self.get_or_create_team(session, data.team_id)

                # Create team alias if needed (assuming team name might be an alias)
                await self.get_or_create_team_alias(session, team, game_version, data.team_id)

                # Calculate total distance based on stint data
                total_laps = sum(stint.num_laps for stint in data.stint_data)
                total_distance_m = total_laps * data.lap_distance_metres

                # Create the driving session
                driving_session = DrivingSession(
                    id=data.session_id,
                    team_id=team.id,
                    game_version_id=game_version.id,
                    track=data.track,
                    game_mode=data.session_type,
                    car=data.formula,  # Using formula as car, update if needed
                    distance_m=total_distance_m,
                    distance_laps=total_laps,
                    session_date=datetime.datetime.now(),  # Using current date, update if needed
                    start_position=data.start_position,
                    finish_position=data.finish_position,
                    laps_led=data.laps_led,
                    lap_distance_m=data.lap_distance_metres
                )
                session.add(driving_session)
                await session.flush()

                # Add tyre stint data
                for stint in data.stint_data:
                    stint_distance_m = stint.num_laps * data.lap_distance_metres
                    tyre_distance = SessionTyreDistance(
                        session_id=driving_session.id,
                        actual_compound=stint.actual_tyre_compound,
                        visual_compound=stint.visual_tyre_compound,
                        distance_m=stint_distance_m,
                        distance_laps=stint.num_laps
                    )
                    session.add(tyre_distance)

                # Add default weather data (assuming a single weather for the session)
                # You can modify this if weather data is available in the input
                weather_distance = SessionWeatherDistance(
                    session_id=driving_session.id,
                    weather_type="Clear",  # Default value, update if actual weather is known
                    distance_m=total_distance_m,
                    distance_laps=total_laps
                )
                session.add(weather_distance)

    async def get_most_played_tracks(self, game_version_title: Optional[str] = None) -> List[Tuple[str, int]]:
        """
        Get the most played tracks, optionally filtered by game version.

        Args:
            game_version_title: Optional game version to filter by (e.g., "F1 2024")

        Returns:
            List of tuples containing (track_name, session_count) ordered by count descending
        """
        async with self.async_session() as session:
            query = select(
                DrivingSession.track,
                func.count(DrivingSession.id).label('session_count')
            )

            if game_version_title:
                query = query.join(GameVersion).where(GameVersion.title == game_version_title)

            query = query.group_by(DrivingSession.track).order_by(desc('session_count'))

            result = await session.execute(query)
            return [(row.track, row.session_count) for row in result]


    async def get_most_played_f1_versions(self) -> List[Tuple[str, int]]:
        """
        Get the most played F1 game versions ordered by session count.

        Returns:
            List of tuples containing (game_version, session_count) ordered by count descending
        """
        async with self.async_session() as session:
            query = select(
                GameVersion.title,
                func.count(DrivingSession.id).label('session_count')
            ).join(DrivingSession).group_by(GameVersion.title).order_by(desc('session_count'))

            result = await session.execute(query)
            return [(row.title, row.session_count) for row in result]


    async def get_team_performance_stats(self, team_name: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive performance statistics for a specific team.

        Args:
            team_name: The canonical name or alias of the team

        Returns:
            Dictionary containing various performance metrics, or None if team not found
        """
        async with self.async_session() as session:
            # First, try to find the team by canonical name
            team_query = select(Team).where(Team.canonical_name == team_name)
            team_result = await session.execute(team_query)
            team = team_result.scalars().first()

            # If not found by canonical name, try to find by alias
            if not team:
                alias_query = select(Team).join(TeamAlias).where(TeamAlias.alias_name == team_name)
                alias_result = await session.execute(alias_query)
                team = alias_result.scalars().first()

            if not team:
                return None

            # Get basic session statistics
            stats_query = select(
                func.count(DrivingSession.id).label('total_sessions'),
                func.sum(DrivingSession.distance_laps).label('total_laps'),
                func.sum(DrivingSession.distance_m).label('total_distance_m'),
                func.avg(DrivingSession.start_position).label('avg_start_position'),
                func.avg(DrivingSession.finish_position).label('avg_finish_position'),
                func.sum(DrivingSession.laps_led).label('total_laps_led'),
                func.min(DrivingSession.finish_position).label('best_finish'),
                func.max(DrivingSession.finish_position).label('worst_finish')
            ).where(DrivingSession.team_id == team.id)

            stats_result = await session.execute(stats_query)
            stats_row = stats_result.first()

            # Count wins (finish position = 1)
            wins_query = select(func.count(DrivingSession.id)).where(
                and_(DrivingSession.team_id == team.id, DrivingSession.finish_position == 1)
            )
            wins_result = await session.execute(wins_query)
            total_wins = wins_result.scalar()

            # Count podiums (finish position <= 3)
            podiums_query = select(func.count(DrivingSession.id)).where(
                and_(DrivingSession.team_id == team.id, DrivingSession.finish_position <= 3)
            )
            podiums_result = await session.execute(podiums_query)
            total_podiums = podiums_result.scalar()

            # Count points finishes (assuming top 10 get points)
            points_query = select(func.count(DrivingSession.id)).where(
                and_(DrivingSession.team_id == team.id, DrivingSession.finish_position <= 10)
            )
            points_result = await session.execute(points_query)
            points_finishes = points_result.scalar()

            # Get most used tracks
            tracks_query = select(
                DrivingSession.track,
                func.count(DrivingSession.id).label('count')
            ).where(DrivingSession.team_id == team.id).group_by(DrivingSession.track).order_by(desc('count')).limit(5)

            tracks_result = await session.execute(tracks_query)
            favorite_tracks = [(row.track, row.count) for row in tracks_result]

            return {
                'team_name': team.canonical_name,
                'total_sessions': stats_row.total_sessions or 0,
                'total_laps': stats_row.total_laps or 0,
                'total_distance_km': round((stats_row.total_distance_m or 0) / 1000, 2),
                'average_start_position': round(stats_row.avg_start_position or 0, 2),
                'average_finish_position': round(stats_row.avg_finish_position or 0, 2),
                'total_laps_led': stats_row.total_laps_led or 0,
                'best_finish': stats_row.best_finish,
                'worst_finish': stats_row.worst_finish,
                'total_wins': total_wins or 0,
                'total_podiums': total_podiums or 0,
                'points_finishes': points_finishes or 0,
                'win_rate': round((total_wins or 0) / max(stats_row.total_sessions or 1, 1) * 100, 2),
                'podium_rate': round((total_podiums or 0) / max(stats_row.total_sessions or 1, 1) * 100, 2),
                'points_rate': round((points_finishes or 0) / max(stats_row.total_sessions or 1, 1) * 100, 2),
                'favorite_tracks': favorite_tracks
            }


    async def get_tyre_compound_usage_stats(self) -> List[Tuple[str, str, int, float]]:
        """
        Get statistics about tyre compound usage across all sessions.

        Returns:
            List of tuples containing (actual_compound, visual_compound, usage_count, total_distance_km)
            ordered by usage count descending
        """
        async with self.async_session() as session:
            query = select(
                SessionTyreDistance.actual_compound,
                SessionTyreDistance.visual_compound,
                func.count(SessionTyreDistance.id).label('usage_count'),
                func.sum(SessionTyreDistance.distance_m).label('total_distance_m')
            ).group_by(
                SessionTyreDistance.actual_compound,
                SessionTyreDistance.visual_compound
            ).order_by(desc('usage_count'))

            result = await session.execute(query)
            return [
                (
                    row.actual_compound,
                    row.visual_compound,
                    row.usage_count,
                    round((row.total_distance_m or 0) / 1000, 2)
                )
                for row in result
            ]


# Example usage
async def main():
    # Create racing database
    db = RacingDatabase()
    await db.create_tables()

    # Create sample data using the new data classes
    sample_stints = [
        TyreStint(
            num_laps=10,
            actual_tyre_compound="C5",
            visual_tyre_compound="Soft"
        ),
        TyreStint(
            num_laps=15,
            actual_tyre_compound="C4",
            visual_tyre_compound="Medium"
        )
    ]

    sample_session = SessionData(
        session_id=123456,
        game_year=24,
        formula="F1",
        session_type="Race",
        track="Silverstone",
        team_id="Red Bull Racing",
        start_position=6,
        finish_position=4,
        laps_led=2,
        lap_distance_metres=5891,
        stint_data=sample_stints
    )

    # Write sample data
    await db.write_session_data(sample_session)
    print("Data written successfully!")

    # Example queries
    print("\nMost played tracks for F1 2024:")
    tracks = await db.get_most_played_tracks("F1 2024")
    for track, count in tracks:
        print(f"  {track}: {count} sessions")

    print("\nMost played F1 versions:")
    versions = await db.get_most_played_f1_versions()
    for version, count in versions:
        print(f"  {version}: {count} sessions")

    print("\nTeam performance stats for Red Bull Racing:")
    stats = await db.get_team_performance_stats("Red Bull Racing")
    if stats:
        for key, value in stats.items():
            print(f"  {key}: {value}")

    print("\nTyre compound usage stats:")
    tyre_stats = await db.get_tyre_compound_usage_stats()
    for actual, visual, count, distance in tyre_stats[:5]:
        print(f"  {actual} ({visual}): {count} uses, {distance}km total")


if __name__ == "__main__":
    asyncio.run(main())