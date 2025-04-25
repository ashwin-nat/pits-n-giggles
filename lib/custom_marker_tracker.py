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

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

from typing import Any, Dict, List

from lib.f1_types import LapData

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

class CustomMarkerEntry:
    """Class representing the data points related to a custom time marker.
    """

    def __init__(self,
        track: str,
        event_type: str,
        lap: int,
        sector: LapData.Sector,
        curr_lap_time: str,
        curr_lap_perc: str):
        """
        Initializes a CustomMarkerEntry instance.

        Parameters:
            - track: A string representing the track name.
            - event_type: A string representing the type of event.
            - lap: An integer representing the lap number.
            - sector: An instance of LapData.Sector enum representing the sector.
            - curr_lap_time: A string representing the current lap time.
            - curr_lap_perc: A string representing the current lap percentage.
        """

        self.m_track: str               = track
        self.m_event_type: str          = event_type
        self.m_lap: int                 = lap
        self.m_sector: LapData.Sector   = sector
        self.m_curr_lap_time: str       = curr_lap_time
        self.m_curr_lap_percent: str    = curr_lap_perc

    def toJSON(self) -> Dict[str, Any]:
        """
        Convert CustomMarkerEntry instance to a JSON-compatible dictionary.

        Returns:
            A dictionary representation of the CustomMarkerEntry.
        """
        return {
            "track": self.m_track,
            "event-type": self.m_event_type,
            "lap": str(self.m_lap),
            "sector": str(self.m_sector),
            "curr-lap-time": self.m_curr_lap_time,
            "curr-lap-percentage": self.m_curr_lap_percent
        }

    def toCSV(self) -> str:
        """
        Convert CustomMarkerEntry instance to a CSV string.

        Returns:
            A CSV string representation of the CustomMarkerEntry.
        """
        return \
            f"{self.m_track}, " \
            f"{self.m_event_type}, " \
            f"{str(self.m_lap)}, " \
            f"{str(self.m_sector)}, " \
            f"{self.m_curr_lap_time}, " \
            f"{self.m_curr_lap_percent}"

    def __str__(self):
        """
        Return string representation of CustomMarkerEntry instance.

        Returns:
            A string representation of the CustomMarkerEntry instance.
        """
        return self.toCSV()

class CustomMarkersHistory:
    """Class representing the data points for a player's custom marker
    """

    def __init__(self):
        """Initialise the custom marker history tracker
        """

        self.m_custom_markers_history: List[CustomMarkerEntry] = []

    def insert(self, custom_marker_entry: CustomMarkerEntry) -> None:
        """Insert the custom marker into the history table. THREAD SAFE

        Args:
            custom_marker_entry (TelData.CustomMarkerEntry): The marker object
        """

        self.m_custom_markers_history.append(custom_marker_entry)

    def clear(self) -> None:
        """Clear the history table. THREAD SAFE
        """

        self.m_custom_markers_history.clear()

    def getCount(self) -> int:
        """Get the number of markers in the history table. THREAD SAFE

        Returns:
            int: The count value
        """

        return len(self.m_custom_markers_history)

    def getJSONList(self) -> List[Dict[str, Any]]:
        """Get the list of JSON objects representing the marker objects. THREAD SAFE

        Returns:
            List[Dict[str, Any]]: The JSON list
        """

        return [marker.toJSON() for marker in self.getMarkers()]

    def getMarkers(self) -> List[CustomMarkerEntry]:
        """
        Get all the custom markers

        Returns:
        - List[CustomMarkerEntry]: List of all custom markers
        """

        return self.m_custom_markers_history
