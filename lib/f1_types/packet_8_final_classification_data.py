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


import struct
from typing import Any, Dict, List

from .common import (ActualTyreCompound, F1Utils, PacketHeader, ResultReason,
                     ResultStatus, VisualTyreCompound)

# --------------------- CLASS DEFINITIONS --------------------------------------

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

    PACKET_FORMAT_25 = ("<"
        "B" # uint8     m_position;              // Finishing position
        "B" # uint8     m_numLaps;               // Number of laps completed
        "B" # uint8     m_gridPosition;          // Grid position of the car
        "B" # uint8     m_points;                // Number of points scored
        "B" # uint8     m_numPitStops;           // Number of pit stops made
        "B" # uint8     m_resultStatus;          // Result status - 0 = invalid, 1 = inactive, 2 = active
                                            #    // 3 = finished, 4 = didnotfinish, 5 = disqualified
                                            #    // 6 = not classified, 7 = retired
        "B" # uint8 m_resultReason;               // Result reason - 0 = invalid, 1 = retired, 2 = finished
                                                # // 3 = terminal damage, 4 = inactive, 5 = not enough laps completed
                                                # // 6 = black flagged, 7 = red flagged, 8 = mechanical failure
                                                # // 9 = session skipped, 10 = session simulated
        "I" # uint32    m_bestLapTimeInMS;       // Best lap time of the session in milliseconds
        "d" # double    m_totalRaceTime;         // Total race time in seconds without penalties
        "B" # uint8     m_penaltiesTime;         // Total penalties accumulated in seconds
        "B" # uint8     m_numPenalties;          // Number of penalties applied to this driver
        "B" # uint8     m_numTyreStints;         // Number of tyres stints up to maximum
        "8B" # uint8     m_tyreStintsActual[8];   // Actual tyres used by this driver
        "8B" # uint8     m_tyreStintsVisual[8];   // Visual tyres used by this driver
        "8B" # uint8     m_tyreStintsEndLaps[8];  // The lap number stints end on
    )
    PACKET_LEN_25 = struct.calcsize(PACKET_FORMAT_25)

    def __init__(self, data: bytes, game_year: int) -> None:
        """
        Initializes FinalClassificationData with raw data.

        Args:
            data (bytes): Raw data representing final classification for a car in a race.
            game_year (int): The year of the game.
        """

        self.m_tyreStintsActual: List[int] = [0] * 8
        self.m_tyreStintsVisual: List[int] = [0] * 8
        self.m_tyreStintsEndLaps: List[int] = [0] * 8
        self.m_resultReason: ResultReason = ResultReason.INVALID
        self.m_gameYear = game_year
        if game_year <= 24:
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
        else: # F1 25+
            (
                self.m_position,
                self.m_numLaps,
                self.m_gridPosition,
                self.m_points,
                self.m_numPitStops,
                self.m_resultStatus,
                self.m_resultReason,
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
            ) = struct.unpack(self.PACKET_FORMAT_25, data)

        if ResultStatus.isValid(self.m_resultStatus):
            self.m_resultStatus = ResultStatus(self.m_resultStatus)
        if ResultReason.isValid(self.m_resultReason):
            self.m_resultReason = ResultReason(self.m_resultReason)

        # Trim the tyre stints info
        self.m_tyreStintsActual     = self.m_tyreStintsActual[:self.m_numTyreStints]
        self.m_tyreStintsVisual     = self.m_tyreStintsVisual[:self.m_numTyreStints]
        self.m_tyreStintsEndLaps    = self.m_tyreStintsEndLaps[:self.m_numTyreStints]

        # Make tyre stint values as enum
        self.m_tyreStintsActual = [ActualTyreCompound(compound) \
                                    if ActualTyreCompound.isValid(compound) \
                                        else compound for compound in self.m_tyreStintsActual]

        self.m_tyreStintsVisual = [VisualTyreCompound(compound) \
                                    if VisualTyreCompound.isValid(compound) \
                                        else compound for compound in self.m_tyreStintsVisual]

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

        res = {
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
            "tyre-stints-actual": [str(compound) for compound in self.m_tyreStintsActual],
            "tyre-stints-visual": [str(compound) for compound in self.m_tyreStintsVisual],
            "tyre-stints-end-laps": self.m_tyreStintsEndLaps,
        }

        if self.m_gameYear >= 25:
            res["result-reason"] = str(self.m_resultReason)

        return res

    def __eq__(self, other: "FinalClassificationData") -> bool:
        """
        Check if two FinalClassificationData instances are equal.

        Args:
            other (FinalClassificationData): The other FinalClassificationData instance to compare with.

        Returns:
            bool: True if the FinalClassificationData instances are equal, False otherwise.
        """

        return (
            self.m_position == other.m_position and
            self.m_numLaps == other.m_numLaps and
            self.m_gridPosition == other.m_gridPosition and
            self.m_points == other.m_points and
            self.m_numPitStops == other.m_numPitStops and
            self.m_resultStatus == other.m_resultStatus and
            self.m_resultReason == other.m_resultReason and
            self.m_bestLapTimeInMS == other.m_bestLapTimeInMS and
            self.m_totalRaceTime == other.m_totalRaceTime and
            self.m_penaltiesTime == other.m_penaltiesTime and
            self.m_numPenalties == other.m_numPenalties and
            self.m_numTyreStints == other.m_numTyreStints and
            self.m_tyreStintsActual == other.m_tyreStintsActual and
            self.m_tyreStintsVisual == other.m_tyreStintsVisual and
            self.m_tyreStintsEndLaps == other.m_tyreStintsEndLaps
        )

    def __ne__(self, other: "FinalClassificationData") -> bool:
        """
        Check if two FinalClassificationData instances are not equal.

        Args:
            other (FinalClassificationData): The other FinalClassificationData instance to compare with.

        Returns:
            bool: True if the FinalClassificationData instances are not equal, False otherwise.
        """

        return not self.__eq__(other)

    def to_bytes(self) -> bytes:
        """Serialize the FinalClassificationData object to bytes based on PACKET_FORMAT.

        Returns:
            bytes: The serialized bytes.
        """

        def pad_array(arr: List[Any]) -> List[Any]:
            """
            Pads an array of integers with 0's if it has fewer than 8 items.

            Args:
                arr (List[int]): The input array of integers.

            Returns:
                List[int]: A new array of integers, padded with 0's to a length of 8.
            """

            # Create a new array with the elements of the input array
            new_arr = arr[:]

            # Pad the new array with 0's if it has fewer than 8 items
            while len(new_arr) < 8:
                new_arr.append(0)

            return new_arr

        tyre_stints_visual: List[VisualTyreCompound] = pad_array(self.m_tyreStintsVisual)
        tyre_stints_actual: List[ActualTyreCompound] = pad_array(self.m_tyreStintsActual)
        tyre_stints_end_laps = pad_array(self.m_tyreStintsEndLaps)

        return struct.pack(self.PACKET_FORMAT,
            self.m_position,
            self.m_numLaps,
            self.m_gridPosition,
            self.m_points,
            self.m_numPitStops,
            self.m_resultStatus.value,
            self.m_bestLapTimeInMS,
            self.m_totalRaceTime,
            self.m_penaltiesTime,
            self.m_numPenalties,
            self.m_numTyreStints,
            tyre_stints_actual[0].value if ActualTyreCompound.isValid(tyre_stints_actual[0]) else 0,
            tyre_stints_actual[1].value if ActualTyreCompound.isValid(tyre_stints_actual[1]) else 0,
            tyre_stints_actual[2].value if ActualTyreCompound.isValid(tyre_stints_actual[2]) else 0,
            tyre_stints_actual[3].value if ActualTyreCompound.isValid(tyre_stints_actual[3]) else 0,
            tyre_stints_actual[4].value if ActualTyreCompound.isValid(tyre_stints_actual[4]) else 0,
            tyre_stints_actual[5].value if ActualTyreCompound.isValid(tyre_stints_actual[5]) else 0,
            tyre_stints_actual[6].value if ActualTyreCompound.isValid(tyre_stints_actual[6]) else 0,
            tyre_stints_actual[7].value if ActualTyreCompound.isValid(tyre_stints_actual[7]) else 0,
            tyre_stints_visual[0].value if VisualTyreCompound.isValid(tyre_stints_visual[0]) else 0,
            tyre_stints_visual[1].value if VisualTyreCompound.isValid(tyre_stints_visual[1]) else 0,
            tyre_stints_visual[2].value if VisualTyreCompound.isValid(tyre_stints_visual[2]) else 0,
            tyre_stints_visual[3].value if VisualTyreCompound.isValid(tyre_stints_visual[3]) else 0,
            tyre_stints_visual[4].value if VisualTyreCompound.isValid(tyre_stints_visual[4]) else 0,
            tyre_stints_visual[5].value if VisualTyreCompound.isValid(tyre_stints_visual[5]) else 0,
            tyre_stints_visual[6].value if VisualTyreCompound.isValid(tyre_stints_visual[6]) else 0,
            tyre_stints_visual[7].value if VisualTyreCompound.isValid(tyre_stints_visual[7]) else 0,
            tyre_stints_end_laps[0],
            tyre_stints_end_laps[1],
            tyre_stints_end_laps[2],
            tyre_stints_end_laps[3],
            tyre_stints_end_laps[4],
            tyre_stints_end_laps[5],
            tyre_stints_end_laps[6],
            tyre_stints_end_laps[7]
        )

    @classmethod
    def from_values(cls,
            game_year: int,
            position: int,
            num_laps: int,
            grid_position: int,
            points: int,
            num_pit_stops: int,
            result_status: ResultStatus,
            best_lap_time_in_ms: int,
            total_race_time: float,
            penalties_time: int,
            num_penalties: int,
            num_tyre_stints: int,
            # tyre_stints_actual,  # array of 8
            tyre_stints_actual_0: ActualTyreCompound,
            tyre_stints_actual_1: ActualTyreCompound,
            tyre_stints_actual_2: ActualTyreCompound,
            tyre_stints_actual_3: ActualTyreCompound,
            tyre_stints_actual_4: ActualTyreCompound,
            tyre_stints_actual_5: ActualTyreCompound,
            tyre_stints_actual_6: ActualTyreCompound,
            tyre_stints_actual_7: ActualTyreCompound,
            # tyre_stints_visual,  # array of 8
            tyre_stints_visual_0: VisualTyreCompound,
            tyre_stints_visual_1: VisualTyreCompound,
            tyre_stints_visual_2: VisualTyreCompound,
            tyre_stints_visual_3: VisualTyreCompound,
            tyre_stints_visual_4: VisualTyreCompound,
            tyre_stints_visual_5: VisualTyreCompound,
            tyre_stints_visual_6: VisualTyreCompound,
            tyre_stints_visual_7: VisualTyreCompound,
            # tyre_stints_end_laps,  # array of 8
            tyre_stints_end_laps_0: int,
            tyre_stints_end_laps_1: int,
            tyre_stints_end_laps_2: int,
            tyre_stints_end_laps_3: int,
            tyre_stints_end_laps_4: int,
            tyre_stints_end_laps_5: int,
            tyre_stints_end_laps_6: int,
            tyre_stints_end_laps_7: int) -> "FinalClassificationData":
        # sourcery skip: low-code-quality
        """Create a new FinalClassificationData object from the given values.

        Args:
            Too many args to list.

        Returns:
            FinalClassificationData: A new FinalClassificationData object initialized with the provided values.
        """

        return cls(struct.pack(cls.PACKET_FORMAT,
            position,
            num_laps,
            grid_position,
            points,
            num_pit_stops,
            result_status.value,
            best_lap_time_in_ms,
            total_race_time,
            penalties_time,
            num_penalties,
            num_tyre_stints,
            # tyre_stints_actual,  # array of 8
            tyre_stints_actual_0.value if ActualTyreCompound.isValid(tyre_stints_actual_0) else 0,
            tyre_stints_actual_1.value if ActualTyreCompound.isValid(tyre_stints_actual_1) else 0,
            tyre_stints_actual_2.value if ActualTyreCompound.isValid(tyre_stints_actual_2) else 0,
            tyre_stints_actual_3.value if ActualTyreCompound.isValid(tyre_stints_actual_3) else 0,
            tyre_stints_actual_4.value if ActualTyreCompound.isValid(tyre_stints_actual_4) else 0,
            tyre_stints_actual_5.value if ActualTyreCompound.isValid(tyre_stints_actual_5) else 0,
            tyre_stints_actual_6.value if ActualTyreCompound.isValid(tyre_stints_actual_6) else 0,
            tyre_stints_actual_7.value if ActualTyreCompound.isValid(tyre_stints_actual_7) else 0,
            # tyre_stints_visual,  # array of 8
            tyre_stints_visual_0.value if VisualTyreCompound.isValid(tyre_stints_visual_0) else 0,
            tyre_stints_visual_1.value if VisualTyreCompound.isValid(tyre_stints_visual_1) else 0,
            tyre_stints_visual_2.value if VisualTyreCompound.isValid(tyre_stints_visual_2) else 0,
            tyre_stints_visual_3.value if VisualTyreCompound.isValid(tyre_stints_visual_3) else 0,
            tyre_stints_visual_4.value if VisualTyreCompound.isValid(tyre_stints_visual_4) else 0,
            tyre_stints_visual_5.value if VisualTyreCompound.isValid(tyre_stints_visual_5) else 0,
            tyre_stints_visual_6.value if VisualTyreCompound.isValid(tyre_stints_visual_6) else 0,
            tyre_stints_visual_7.value if VisualTyreCompound.isValid(tyre_stints_visual_7) else 0,
            # tyre_stints_end_laps,  # array of 8
            tyre_stints_end_laps_0,
            tyre_stints_end_laps_1,
            tyre_stints_end_laps_2,
            tyre_stints_end_laps_3,
            tyre_stints_end_laps_4,
            tyre_stints_end_laps_5,
            tyre_stints_end_laps_6,
            tyre_stints_end_laps_7
        ), game_year=game_year)

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
        self.m_numCars: int = struct.unpack("<B", packet[:1])[0]

        if header.m_gameYear <= 24:
            packet_len = FinalClassificationData.PACKET_LEN
        else:
            packet_len = FinalClassificationData.PACKET_LEN_25
        # Iterate over packet[1:] in steps of FinalClassificationData.PACKET_LEN,
        # creating FinalClassificationData objects for each segment.

        self.m_classificationData: List[FinalClassificationData] = [
            FinalClassificationData(packet[i:i + packet_len], header.m_gameYear)
            for i in range(1, len(packet), packet_len)
        ]
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

    def __eq__(self, other: "PacketFinalClassificationData") -> bool:
        """
        Compares two PacketFinalClassificationData objects.

        Args:
            other (PacketFinalClassificationData): The other PacketFinalClassificationData object to compare with.

        Returns:
            bool: True if the two objects are equal, False otherwise.
        """

        if not isinstance(other, PacketFinalClassificationData):
            return False
        if self.m_numCars != other.m_numCars:
            return False
        return self.m_classificationData == other.m_classificationData

    def __ne__(self, other: "PacketFinalClassificationData") -> bool:
        """
        Compares two PacketFinalClassificationData objects.

        Args:
            other (PacketFinalClassificationData): The other PacketFinalClassificationData object to compare with.

        Returns:
            bool: True if the two objects are not equal, False otherwise.
        """

        return not self.__eq__(other)

    def to_bytes(self) -> bytes:
        """
        Convert the PacketFinalClassificationData instance to bytes.

        Returns:
            bytes: Bytes representing the PacketFinalClassificationData instance.
        """

        return self.m_header.to_bytes() + \
            struct.pack("<B", self.m_numCars) + b"".join([data.to_bytes() for data in self.m_classificationData])

    @classmethod
    def from_values(cls,
                    header: PacketHeader,
                    num_cars: int,
                    classification_data: List[FinalClassificationData]) -> "PacketFinalClassificationData":
        """Create a PacketFinalClassificationData object from individual values.

        Args:
            header (PacketHeader): The header of the telemetry packet.
            num_cars (int): Number of cars in the final classification.
            classification_data (List[FinalClassificationData]): List of FinalClassificationData objects containing data for all cars on track.

        Returns:
            PacketFinalClassificationData: A PacketFinalClassificationData object initialized with the provided values.
        """

        return cls(header, struct.pack("<B", num_cars) + b''.join([data.to_bytes() for data in classification_data]))