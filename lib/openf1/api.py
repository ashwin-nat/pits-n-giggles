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
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

import aiohttp

from lib.f1_types import TrackID

from .circuit_id import OpenF1CircuitID, to_openf1

# -------------------------------------- CLASSES -----------------------------------------------------------------------

@dataclass
class MostRecentPoleLap:
    """
    Represents the most recent pole lap information for a given circuit.

    Attributes:
        circuit_id (TrackID): Pits n' Giggles parser friendly circuit ID.
        year (Optional[int]): Year of the pole lap event.
        driver_name (Optional[str]): Name of the driver who set the pole lap.
        driver_num (Optional[int]): Car number of the driver.
        team_name (Optional[str]): Name of the driver's team.
        lap_ms (Optional[int]): Full lap time in milliseconds.
        s1_ms (Optional[int]): Sector 1 time in milliseconds.
        s2_ms (Optional[int]): Sector 2 time in milliseconds.
        s3_ms (Optional[int]): Sector 3 time in milliseconds.
        speed_trap_kmph (Optional[int]): Speed trap time in kilometers per hour.
    """

    circuit_id: TrackID
    year: Optional[int] = None
    driver_name: Optional[str] = None
    driver_num: Optional[int] = None
    team_name: Optional[str] = None
    lap_ms: Optional[int] = None
    s1_ms: Optional[int] = None
    s2_ms: Optional[int] = None
    s3_ms: Optional[int] = None
    speed_trap_kmph: Optional[int] = None

    def toJSON(self) -> Dict[str, Any]:
        """
        Convert the dataclass instance into a JSON-serializable dictionary.

        Returns:
            Dict[str, Any]: Dictionary with pole lap information.
        """
        return {
            "circuit": str(self.circuit_id),
            "year": self.year,
            "driver-name": self.driver_name,
            "driver-num": self.driver_num,
            "team-name": self.team_name,
            "lap-ms": self.lap_ms,
            "s1-ms": self.s1_ms,
            "s2-ms": self.s2_ms,
            "s3-ms": self.s3_ms,
            "speed-trap-kmph": self.speed_trap_kmph,
        }

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

async def getMostRecentPoleLap(
        track_id: TrackID,
        logger: logging.Logger,
        num_recent_years = 3) -> Optional[MostRecentPoleLap]:
    """Get the OpenF1CircuitID for a given TrackID

    Args:
        track_id (TrackID): The track ID
        logger (logging.Logger): Logger
        num_recent_years (int, optional): Number of recent years to search. Defaults to 3.

    Returns:
        OpenF1CircuitID: OpenF1 API friendly circuit ID. May be None
    """

    current_year = datetime.now().year
    circuit_id = to_openf1(track_id)
    if not circuit_id:
        logger.info("Unsupported circuit: %s", track_id)
        return None
    years = list(range(current_year, current_year - num_recent_years, -1))

    for year in years:
        rsp = await _fetchPoleLapByYear(circuit_id, year, logger)
        if not rsp:
            continue
        return MostRecentPoleLap(
            circuit_id=track_id,
            year=year,
            driver_name=rsp["driver_name"],
            driver_num=rsp["driver_number"],
            team_name=rsp["team_name"],
            lap_ms=int(rsp["lap_duration"] * 1000),
            s1_ms=int(rsp["duration_sector_1"] * 1000),
            s2_ms=int(rsp["duration_sector_2"] * 1000),
            s3_ms=int(rsp["duration_sector_3"] * 1000),
            speed_trap_kmph=rsp["st_speed"])

    return None

async def _fetchPoleLapByYear(circuit_id: OpenF1CircuitID, year: int, logger: logging.Logger) -> Dict[str, Any]:
    """
    Fetch pole lap data for a specific circuit and year.

    Args:
        circuit_id: OpenF1 API circuit identifier.
        year: Year to fetch data for.
        logger: Logger instance for debugging and error reporting.

    Returns:
        Dictionary containing pole lap data if successful, None otherwise.
    """

    # Step 1 - Get list of sessions for given year and circuit
    sessions = await _make_openf1_request("sessions", {"year": year, "circuit_key": circuit_id.value}, logger=logger)
    if not sessions:
        logger.debug("Failed to get sessions for circuit %s and year %s", circuit_id, year)
        return None

    # Step 2 - Get session ID for quali
    quali_session = next((session for session in sessions if session["session_name"] == "Qualifying"), None)
    if not quali_session:
        logger.debug("Failed to get quali session for circuit %s and year %s", circuit_id, year)
        return None

    # Step 3 - Get the pole position driver
    pole_driver = await _make_openf1_request("starting_grid", {
        "session_key": quali_session["session_key"],
        "position": 1
    }, logger=logger)
    if not pole_driver:
        logger.debug("Failed to get pole driver for circuit %s and year %s", circuit_id, year)
        return None
    pole_driver = pole_driver[0]

    # Step 4 - Get driver details and find pole position driver details
    drivers = await _make_openf1_request("drivers", {
        "driver_number": pole_driver["driver_number"],
        "session_key": quali_session["session_key"]
    }, logger=logger)
    if not drivers:
        logger.debug("Failed to get drivers for circuit %s and year %s", circuit_id, year)
        return None
    pole_driver = next((driver for driver in drivers if driver["driver_number"] == pole_driver["driver_number"]), None)
    if not pole_driver:
        logger.debug("Failed to get pole driver details for circuit %s and year %s", circuit_id, year)
        return None

    # Step 5 - Get fastest lap
    laps = await _make_openf1_request("laps", {
        "session_key": quali_session["session_key"],
        "driver_number": pole_driver["driver_number"]
    }, logger=logger)
    fastest_lap = min(
        (lap for lap in laps if lap["lap_duration"] is not None),
        key=lambda lap: lap["lap_duration"],
        default=None
    )
    if not fastest_lap:
        logger.debug("Failed to get fastest lap for circuit %s and year %s", circuit_id, year)
        return None

    # Insert the driver details and return
    fastest_lap["driver_name"] = pole_driver["broadcast_name"].replace(" ", ". ", 1)
    fastest_lap["team_name"] = pole_driver["team_name"]
    return fastest_lap

async def _make_openf1_request(endpoint: str, params: Optional[Dict[str, Any]], logger: logging.Logger) -> Dict[str, Any]:
    """
    Asynchronously fetch data from the OpenF1 API using aiohttp.

    Args:
        endpoint (str): The API endpoint (relative to base_url).
        params (dict, optional): Query parameters.
        logger (logging.Logger): Logger

    Returns:
        dict | None: JSON response if successful, otherwise None.
    """
    base_url = "https://api.openf1.org/v1/"
    url = f"{base_url}{endpoint}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                response.raise_for_status()  # Raise an exception for HTTP errors
                return await response.json()
    except (aiohttp.ClientError, asyncio.TimeoutError, asyncio.CancelledError) as e:
        logger.debug(f"Error fetching data from {url}: {e}")
        return None
