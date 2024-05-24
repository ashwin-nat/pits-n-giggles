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

## NOTE: Please refer to the F1 23 UDP specification document to understand fully how the telemetry data works.
## All classes in supported in this library are documented with the members, but it is still recommended to read the
## official document. https://answers.ea.com/t5/General-Discussion/F1-23-UDP-Specification/m-p/12633159

import struct
from typing import Dict, Any, List
from .common import _split_list, PacketHeader, F1Utils, ResultStatus

# --------------------- CLASS DEFINITIONS --------------------------------------

class PacketFinalClassificationData:
    """
    Class representing the packet for final classification data.

    Attributes:
        m_header (PacketHeader): Header information.
        m_numCars (int): Number of cars in the final classification.
        m_classificationData (List[FinalClassificationData]): List of final classification data for each car.

    Note:
        The class is designed to parse and represent the final classification data packet.
    """

    max_cars = 22

    def __init__(self, header: PacketHeader, packet: bytes) -> None:
        """
        Initializes PacketFinalClassificationData with raw data.

        Args:
            header (PacketHeader): Header information for the packet.
            packet (bytes): Raw data representing the packet for final classification data.
        """

        self.m_header: PacketHeader = header
        self.m_numCars: int = struct.unpack("<B", packet[0:1])[0]
        self.m_classificationData: List[FinalClassificationData] = []

        for classification_per_car_raw_data in _split_list(packet[1:], FinalClassificationData.PACKET_LEN):
            self.m_classificationData.append(FinalClassificationData(classification_per_car_raw_data))

        # strip the non-applicable data
        self.m_classificationData = self.m_classificationData[:self.m_numCars]

    def __str__(self) -> str:
        """
        Returns a string representation of PacketFinalClassificationData.

        Returns:
            str: String representation of PacketFinalClassificationData.
        """

        classification_data_str = ", ".join(str(data) for data in self.m_classificationData[:self.m_numCars])
        return (
            f"PacketFinalClassificationData("
            f"Number of Cars: {self.m_numCars}, "
            f"Classification Data: [{classification_data_str}])"
        )

    def toJSON(self, include_header: bool=False) -> Dict[str, Any]:
        """
        Convert the PacketFinalClassificationData instance to a JSON-compatible dictionary with kebab-case keys.

        Arguments:
            - include_header - Whether the header dump must be included in the JSON

        Returns:
            Dict[str, Any]: JSON-compatible dictionary with kebab-case keys representing the PacketFinalClassificationData instance.
        """

        json_data = {
            "num-cars": self.m_numCars,
            "classification-data": [data.toJSON() for data in self.m_classificationData[:self.m_numCars]],
        }
        if include_header:
            json_data["header"] = self.m_header.toJSON()
        return json_data

class FinalClassificationData:
    """
    Class representing final classification data for a car in a race.

    Attributes:
        m_position (uint8): Finishing position
        m_numLaps (uint8): Number of laps completed
        m_gridPosition (uint8): Grid position of the car
        m_points (uint8): Number of points scored
        m_numPitStops (uint8): Number of pit stops made
        m_resultStatus (ResultStatus): See ResultStatus enumeration for more info
        m_bestLapTimeInMS (uint32): Best lap time of the session in milliseconds
        m_totalRaceTime (double): Total race time in seconds without penalties
        m_penaltiesTime (uint8): Total penalties accumulated in seconds
        m_numPenalties (uint8): Number of penalties applied to this driver
        m_numTyreStints (uint8): Number of tyre stints up to maximum
        m_tyreStintsActual (List[uint8]): Actual tyres used by this driver (array of 8)
        m_tyreStintsVisual (List[uint8]): Visual tyres used by this driver (array of 8)
        m_tyreStintsEndLaps (List[uint8]): The lap number stints end on (array of 8)

    Note:
        The class is designed to parse and represent the final classification data for a car in a race.
    """

    PACKET_FORMAT = ("<"
        "B" # uint8     m_position;              // Finishing position
        "B" # uint8     m_numLaps;               // Number of laps completed
        "B" # uint8     m_gridPosition;          // Grid position of the car
        "B" # uint8     m_points;                // Number of points scored
        "B" # uint8     m_numPitStops;           // Number of pit stops made
        "B" # uint8     m_resultStatus;          // Result status - 0 = invalid, 1 = inactive, 2 = active
                                        #    // 3 = finished, 4 = didnotfinish, 5 = disqualified
                                        #    // 6 = not classified, 7 = retired
        "I" # uint32    m_bestLapTimeInMS;       // Best lap time of the session in milliseconds
        "d" # double    m_totalRaceTime;         // Total race time in seconds without penalties
        "B" # uint8     m_penaltiesTime;         // Total penalties accumulated in seconds
        "B" # uint8     m_numPenalties;          // Number of penalties applied to this driver
        "B" # uint8     m_numTyreStints;         // Number of tyres stints up to maximum
        "8B" # uint8     m_tyreStintsActual[8];   // Actual tyres used by this driver
        "8B" # uint8     m_tyreStintsVisual[8];   // Visual tyres used by this driver
        "8B" # uint8     m_tyreStintsEndLaps[8];  // The lap number stints end on
    )
    PACKET_LEN = struct.calcsize(PACKET_FORMAT)

    def __init__(self, data) -> None:
        """
        Initializes FinalClassificationData with raw data.

        Args:
            data (bytes): Raw data representing final classification for a car in a race.
        """

        self.m_tyreStintsActual: List[int] = [0] * 8
        self.m_tyreStintsVisual: List[int] = [0] * 8
        self.m_tyreStintsEndLaps: List[int] = [0] * 8
        (
            self.m_position,
            self.m_numLaps,
            self.m_gridPosition,
            self.m_points,
            self.m_numPitStops,
            self.m_resultStatus,
            self.m_bestLapTimeInMS,
            self.m_totalRaceTime,
            self.m_penaltiesTime,
            self.m_numPenalties,
            self.m_numTyreStints,
            # self.m_tyreStintsActual,  # array of 8
            self.m_tyreStintsActual[0],
            self.m_tyreStintsActual[1],
            self.m_tyreStintsActual[2],
            self.m_tyreStintsActual[3],
            self.m_tyreStintsActual[4],
            self.m_tyreStintsActual[5],
            self.m_tyreStintsActual[6],
            self.m_tyreStintsActual[7],
            # self.m_tyreStintsVisual,  # array of 8
            self.m_tyreStintsVisual[0],
            self.m_tyreStintsVisual[1],
            self.m_tyreStintsVisual[2],
            self.m_tyreStintsVisual[3],
            self.m_tyreStintsVisual[4],
            self.m_tyreStintsVisual[5],
            self.m_tyreStintsVisual[6],
            self.m_tyreStintsVisual[7],
            # self.m_tyreStintsEndLaps,  # array of 8
            self.m_tyreStintsEndLaps[0],
            self.m_tyreStintsEndLaps[1],
            self.m_tyreStintsEndLaps[2],
            self.m_tyreStintsEndLaps[3],
            self.m_tyreStintsEndLaps[4],
            self.m_tyreStintsEndLaps[5],
            self.m_tyreStintsEndLaps[6],
            self.m_tyreStintsEndLaps[7]
        ) = struct.unpack(self.PACKET_FORMAT, data)

        if ResultStatus.isValid(self.m_resultStatus):
            self.m_resultStatus = ResultStatus(self.m_resultStatus)

        # Trim the tyre stints info
        self.m_tyreStintsActual     = self.m_tyreStintsActual[:self.m_numTyreStints]
        self.m_tyreStintsVisual     = self.m_tyreStintsVisual[:self.m_numTyreStints]
        self.m_tyreStintsEndLaps    = self.m_tyreStintsEndLaps[:self.m_numTyreStints]

    def __str__(self):
        """
        Returns a string representation of FinalClassificationData.

        Returns:
            str: String representation of FinalClassificationData.
        """

        return (
            f"FinalClassificationData("
            f"m_position={self.m_position}, "
            f"m_numLaps={self.m_numLaps}, "
            f"m_gridPosition={self.m_gridPosition}, "
            f"m_points={self.m_points}, "
            f"m_numPitStops={self.m_numPitStops}, "
            f"m_resultStatus={self.m_resultStatus}, "
            f"m_bestLapTimeInMS={self.m_bestLapTimeInMS}, "
            f"m_totalRaceTime={self.m_totalRaceTime}, "
            f"m_penaltiesTime={self.m_penaltiesTime}, "
            f"m_numPenalties={self.m_numPenalties}, "
            f"m_numTyreStints={self.m_numTyreStints}, "
            f"m_tyreStintsActual={str(self.m_tyreStintsActual)}, "
            f"m_tyreStintsVisual={str(self.m_tyreStintsVisual)}, "
            f"m_tyreStintsEndLaps={str(self.m_tyreStintsEndLaps)})"
        )

    def toJSON(self) -> Dict[str, Any]:
        """
        Convert the FinalClassificationData instance to a JSON-compatible dictionary with kebab-case keys.

        Returns:
            Dict[str, Any]: JSON-compatible dictionary with kebab-case keys representing the FinalClassificationData instance.
        """

        return {
            "position": self.m_position,
            "num-laps": self.m_numLaps,
            "grid-position": self.m_gridPosition,
            "points": self.m_points,
            "num-pit-stops": self.m_numPitStops,
            "result-status": str(self.m_resultStatus),
            "best-lap-time-ms": self.m_bestLapTimeInMS,
            "best-lap-time-str": F1Utils.millisecondsToMinutesSecondsMilliseconds(self.m_bestLapTimeInMS),
            "total-race-time": self.m_totalRaceTime,
            "total-race-time-str": F1Utils.secondsToMinutesSecondsMilliseconds(self.m_totalRaceTime),
            "penalties-time": self.m_penaltiesTime,
            "num-penalties": self.m_numPenalties,
            "num-tyre-stints": self.m_numTyreStints,
            "tyre-stints-actual": self.m_tyreStintsActual,
            "tyre-stints-visual": self.m_tyreStintsVisual,
            "tyre-stints-end-laps": self.m_tyreStintsEndLaps,
        }
