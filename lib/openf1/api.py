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
import aiohttp
from typing import Dict, Any, Optional
from lib.f1_types import TrackID
from dataclasses import dataclass

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

    def __str__(self) -> str:
        """Return the string representation of the circuit ID."""
        return str(self.circuit_id)

    def __repr__(self) -> str:
        """Return the debug representation of the object (circuit ID)."""
        return str(self.circuit_id)

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
            "s3-ms": self.s3_ms
        }

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

async def getMostRecentPoleLap(track_id: TrackID) -> MostRecentPoleLap:
    """Get the OpenF1CircuitID for a given TrackID

    Args:
        track_id (TrackID): The track ID

    Returns:
        OpenF1CircuitID: OpenF1 API friendly circuit ID
    """

    await asyncio.sleep(5) # Simulate API call
    return MostRecentPoleLap(
        circuit_id=track_id,
        year=2023,
        driver_name="Max Verstappen",
        driver_num=33,
        team_name="Red Bull Racing",
        lap_ms=68012,
        s1_ms=22000,
        s2_ms=23000,
        s3_ms=23012
    )
