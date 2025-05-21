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
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, select, func
)
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, relationship


# --------------------- Base Model ---------------------
class Base(DeclarativeBase):
    pass


# --------------------- Models ---------------------
class Team(Base):
    __tablename__ = 'teams'

    id = Column(Integer, primary_key=True)
    canonical_name = Column(String, unique=True, nullable=False)
    aliases = relationship("TeamAlias", back_populates="team")
    sessions = relationship("DrivingSession", back_populates="team")


class TeamAlias(Base):
    __tablename__ = 'team_aliases'

    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    game_title = Column(String, nullable=False)
    alias_name = Column(String, nullable=False)

    team = relationship("Team", back_populates="aliases")


class DrivingSession(Base):
    __tablename__ = 'driving_sessions'

    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    title = Column(String, nullable=False)
    track = Column(String, nullable=False)
    game_mode = Column(String, nullable=False)
    car = Column(String, nullable=False)
    distance_km = Column(Float, nullable=False)
    distance_laps = Column(Float, nullable=False)
    session_date = Column(DateTime, default=datetime.utcnow)

    team = relationship("Team", back_populates="sessions")
    tyre_distances = relationship("SessionTyreDistance", back_populates="session")
    weather_distances = relationship("SessionWeatherDistance", back_populates="session")


class SessionTyreDistance(Base):
    __tablename__ = 'session_tyre_distances'

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('driving_sessions.id'), nullable=False)
    actual_compound = Column(String, nullable=False)  # e.g., C1, C2
    visual_compound = Column(String, nullable=False)  # e.g., Soft, Medium
    distance_km = Column(Float, nullable=False)
    distance_laps = Column(Float, nullable=False)

    session = relationship("DrivingSession", back_populates="tyre_distances")


class SessionWeatherDistance(Base):
    __tablename__ = 'session_weather_distances'

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('driving_sessions.id'), nullable=False)
    weather_type = Column(String, nullable=False)  # e.g., Dry, Wet
    distance_km = Column(Float, nullable=False)
    distance_laps = Column(Float, nullable=False)

    session = relationship("DrivingSession", back_populates="weather_distances")


# --------------------- Tracker Class ---------------------
class HistoricDistanceTracker:
    """
    Async database manager for historic distance tracking.
    Handles teams, aliases, sessions, and session split data.
    """

    def __init__(self, db_path: str = "sqlite+aiosqlite:///png.db"):
        self._engine = create_async_engine(db_path, echo=False)
        self._Session = async_sessionmaker(self._engine, expire_on_commit=False)

    async def init_schema(self):
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @asynccontextmanager
    async def _session_scope(self) -> AsyncGenerator[AsyncSession, None]:
        async with self._Session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def record_session(self,
                            canonical_team: str,
                            alias_name: str,
                            title: str,
                            track: str,
                            game_mode: str,
                            car: str,
                            distance_km: float,
                            distance_laps: float,
                            tyre_splits: list[dict],
                            weather_splits: list[dict]):
        """
        Entry-point to record a full session into the database.

        Args:
            canonical_team: The team’s canonical name (e.g., “Red Bull Racing”).
            alias_name: The name used for this team in the current game title.
            title: The game title (e.g., “F1 24”).
            track: The track name (e.g., “Spa-Francorchamps”).
            game_mode: Game mode string (e.g., “Career”, “Time Trial”).
            car: Car model or type (e.g., “RB20”).
            distance_km: Total session distance in kilometers.
            distance_laps: Total session distance in laps.
            tyre_splits: List of dicts with keys: actual_compound, visual_compound, distance_km, distance_laps.
            weather_splits: List of dicts with keys: weather_type, distance_km, distance_laps.
        """
        async with self._session_scope() as session:
            # Ensure team and alias exist
            team = await session.scalar(select(Team).where(Team.canonical_name == canonical_team))
            if not team:
                team = Team(canonical_name=canonical_team)
                session.add(team)
                await session.flush()

            alias = await session.scalar(
                select(TeamAlias)
                .where(TeamAlias.alias_name == alias_name, TeamAlias.game_title == title)
            )
            if not alias:
                alias = TeamAlias(team_id=team.id, game_title=title, alias_name=alias_name)
                session.add(alias)
                await session.flush()

            # Record driving session
            session_entry = DrivingSession(
                team_id=team.id,
                title=title,
                track=track,
                game_mode=game_mode,
                car=car,
                distance_km=distance_km,
                distance_laps=distance_laps
            )
            session.add(session_entry)
            await session.flush()

            # Tyres and weather breakdowns
            for t in tyre_splits:
                session.add(SessionTyreDistance(session_id=session_entry.id, **t))
            for w in weather_splits:
                session.add(SessionWeatherDistance(session_id=session_entry.id, **w))


    async def add_team_alias(self, canonical: str, title: str, alias: str):
        async with self._session_scope() as session:
            team = await session.scalar(select(Team).where(Team.canonical_name == canonical))
            if not team:
                team = Team(canonical_name=canonical)
                session.add(team)
                await session.flush()

            team_alias = TeamAlias(team_id=team.id, game_title=title, alias_name=alias)
            session.add(team_alias)

    async def add_driving_session(self, team_alias: str, title: str, track: str,
                                  game_mode: str, car: str, distance_km: float,
                                  distance_laps: float,
                                  tyre_splits: list[dict], weather_splits: list[dict]):
        async with self._session_scope() as session:
            alias = await session.scalar(
                select(TeamAlias).where(TeamAlias.alias_name == team_alias, TeamAlias.game_title == title)
            )
            if not alias:
                raise ValueError(f"No team alias '{team_alias}' found for title '{title}'")

            session_entry = DrivingSession(
                team_id=alias.team_id,
                title=title,
                track=track,
                game_mode=game_mode,
                car=car,
                distance_km=distance_km,
                distance_laps=distance_laps
            )
            session.add(session_entry)
            await session.flush()

            for t in tyre_splits:
                session.add(SessionTyreDistance(session_id=session_entry.id, **t))
            for w in weather_splits:
                session.add(SessionWeatherDistance(session_id=session_entry.id, **w))

    async def get_total_km_by_team(self, game_title: str) -> dict[str, float]:
        async with self._session_scope() as session:
            result = await session.execute(
                select(Team.canonical_name, func.sum(DrivingSession.distance_km))
                .join(DrivingSession)
                .join(TeamAlias)
                .where(TeamAlias.game_title == game_title)
                .group_by(Team.canonical_name)
            )
            return {row[0]: row[1] for row in result}


# --------------------- Example Usage ---------------------
if __name__ == "__main__":
    async def main():
        tracker = HistoricDistanceTracker()
        await tracker.init_schema()

    asyncio.run(main())
