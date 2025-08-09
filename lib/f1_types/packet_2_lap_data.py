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
from enum import Enum
from typing import Any, Dict, List

from .common import (F1Utils, InvalidPacketLengthError, PacketHeader,
                     ResultStatus, _validate_parse_fixed_segments)

# --------------------- CLASS DEFINITIONS --------------------------------------

class LapData:
    """
    Class representing lap data.
    Attributes:
        m_lastLapTimeInMS (uint32): Last lap time in milliseconds.
        m_currentLapTimeInMS (uint32): Current time around the lap in milliseconds.
        m_sector1TimeInMS (uint16): Sector 1 time in milliseconds.
        m_sector1TimeMinutes (uint8): Sector 1 whole minute part.
        m_sector2TimeInMS (uint16): Sector 2 time in milliseconds.
        m_sector2TimeMinutes (uint8): Sector 2 whole minute part.
        m_deltaToCarInFrontInMS (uint16): Time delta to the car in front in milliseconds.
        m_deltaToRaceLeaderInMS (uint16): Time delta to the race leader in milliseconds.
        m_lapDistance (float): Distance vehicle is around the current lap in meters.
        m_totalDistance (float): Total distance traveled in the session in meters.
        m_safetyCarDelta (float): Delta in seconds for the safety car.
        m_carPosition (uint8): Car race position.
        m_currentLapNum (uint8): Current lap number.
        m_pitStatus (PitStatus): See the PitStatus enumeration
        m_numPitStops (uint8): Number of pit stops taken in this race.
        m_sector (Sector): See the sector enumeration
        m_currentLapInvalid (bool): Current lap validity (False = valid, True = invalid).
        m_penalties (uint8): Accumulated time penalties in seconds to be added.
        m_totalWarnings (uint8): Accumulated number of warnings issued.
        m_cornerCuttingWarnings (uint8): Accumulated number of corner cutting warnings issued.
        m_numUnservedDriveThroughPens (uint8): Number of drive-through penalties left to serve.
        m_numUnservedStopGoPens (uint8): Number of stop-go penalties left to serve.
        m_gridPosition (uint8): Grid position the vehicle started the race in.
        m_driverStatus (DriverStatus): Status of the driver.
        m_resultStatus (ResultStatus): Result status of the driver.
        m_pitLaneTimerActive (bool): Pit lane timing (False = inactive, True = active).
        m_pitLaneTimeInLaneInMS (uint16): If active, the current time spent in the pit lane in ms.
        m_pitStopTimerInMS (uint16): Time of the actual pit stop in ms.
        m_pitStopShouldServePen (uint8): Whether the car should serve a penalty at this stop.
        m_speedTrapFastestSpeed (float): Fastest speed trap speed in kmph.
        m_speedTrapFastestLap (uint8): Fastest speed trap lap number.
    """

    COMPILED_PACKET_STRUCT_23 = struct.Struct("<"
        "I" # uint32 - Last lap time in milliseconds
        "I" # uint32 - Current time around the lap in milliseconds
        "H" # uint16 - Sector 1 time in milliseconds
        "B" # uint8  - Sector 1 whole minute part
        "H" # uint16 - Sector 2 time in milliseconds
        "B" # uint8  - Sector 2 whole minute part
        "H" # uint16 - Time delta to car in front in milliseconds
        "H" # uint16 - Time delta to race leader in milliseconds
        "f" # float  - Distance vehicle is around current lap in metres - could be negative if line hasn't been crossed yet
        "f" # float  - Total distance travelled in session in metres - could be negative if line hasn't been crossed yet
        "f" # float  - Delta in seconds for safety car
        "B" # uint8  - Car race position
        "B" # uint8  - Current lap number
        "B" # uint8  - 0 = none, 1 = pitting, 2 = in pit area
        "B" # uint8  - Number of pit stops taken in this race
        "B" # uint8  - 0 = sector1, 1 = sector2, 2 = sector3
        "B" # uint8  - Current lap invalid - 0 = valid, 1 = invalid
        "B" # uint8  - Accumulated time penalties in seconds to be added
        "B" # uint8  - Accumulated number of warnings issued
        "B" # uint8  - Accumulated number of corner cutting warnings issued
        "B" # uint8  - Num drive through pens left to serve
        "B" # uint8  - Num stop go pens left to serve
        "B" # uint8  - Grid position the vehicle started the race in
        "B" # uint8  - Status of driver - 0 = in garage, 1 = flying lap 2 = in lap, 3 = out lap, 4 = on track
        "B" # uint8  - Result status - 0 = invalid, 1 = inactive, 2 = active 3 = finished, 4 = didnotfinish, 5 = disqualified
                    #                        // 6 = not classified, 7 = retired
        "B" # uint8  - Pit lane timing, 0 = inactive, 1 = active
        "H" # uint16 - If active, the current time spent in the pit lane in ms
        "H" # uint16 - Time of the actual pit stop in ms
        "B" # uint8  - Whether the car should serve a penalty at this stop
    )
    PACKET_LEN_23 = COMPILED_PACKET_STRUCT_23.size

    COMPILED_PACKET_STRUCT_24 = struct.Struct("<"
        "I" # uint32   m_lastLapTimeInMS;                // Last lap time in milliseconds
        "I" # uint32   m_currentLapTimeInMS;      // Current time around the lap in milliseconds
        "H" # uint16   m_sector1TimeMSPart;         // Sector 1 time milliseconds part
        "B" # uint8    m_sector1TimeMinutesPart;    // Sector 1 whole minute part
        "H" # uint16   m_sector2TimeMSPart;         // Sector 2 time milliseconds part
        "B" # uint8    m_sector2TimeMinutesPart;    // Sector 2 whole minute part
        "H" # uint16   m_deltaToCarInFrontMSPart;   // Time delta to car in front milliseconds part
        "B" # uint8    m_deltaToCarInFrontMinutesPart; // Time delta to car in front whole minute part
        "H" # uint16   m_deltaToRaceLeaderMSPart;      // Time delta to race leader milliseconds part
        "B" # uint8    m_deltaToRaceLeaderMinutesPart; // Time delta to race leader whole minute part
        "f" # float    m_lapDistance;         // Distance vehicle is around current lap in metres – could
                      #  // be negative if line hasn’t been crossed yet
        "f" # float    m_totalDistance;         // Total distance travelled in session in metres – could
                      #  // be negative if line hasn’t been crossed yet
        "f" # float    m_safetyCarDelta;            // Delta in seconds for safety car
        "B" # uint8   # m_carPosition;                // Car race position
        "B" # uint8    m_currentLapNum;         // Current lap number
        "B" # uint8    m_pitStatus;                 // 0 = none, 1 = pitting, 2 = in pit area
        "B" # uint8    m_numPitStops;                 // Number of pit stops taken in this race
        "B" # uint8    m_sector;                    // 0 = sector1, 1 = sector2, 2 = sector3
        "B" # uint8    m_currentLapInvalid;         // Current lap invalid - 0 = valid, 1 = invalid
        "B" # uint8    m_penalties;                 // Accumulated time penalties in seconds to be added
        "B" # uint8    m_totalWarnings;             // Accumulated number of warnings issued
        "B" # uint8    m_cornerCuttingWarnings;     // Accumulated number of corner cutting warnings issued
        "B" # uint8    m_numUnservedDriveThroughPens;  // Num drive through pens left to serve
        "B" # uint8    m_numUnservedStopGoPens;        // Num stop go pens left to serve
        "B" # uint8    m_gridPosition;              // Grid position the vehicle started the race in
        "B" # uint8    m_driverStatus;              // Status of driver - 0 = in garage, 1 = flying lap
                      #                      // 2 = in lap, 3 = out lap, 4 = on track
        "B" # uint8    m_resultStatus;              // Result status - 0 = invalid, 1 = inactive, 2 = active
                      #                      // 3 = finished, 4 = didnotfinish, 5 = disqualified
                      #                      // 6 = not classified, 7 = retired
        "B" # uint8    m_pitLaneTimerActive;          // Pit lane timing, 0 = inactive, 1 = active
        "H" # uint16   m_pitLaneTimeInLaneInMS;        // If active, the current time spent in the pit lane in ms
        "H" # uint16   m_pitStopTimerInMS;             // Time of the actual pit stop in ms
        "B" # uint8    m_pitStopShouldServePen;        // Whether the car should serve a penalty at this stop
        "f" # float    m_speedTrapFastestSpeed;     // Fastest speed through speed trap for this car in kmph
        "B" # uint8   # m_speedTrapFastestLap;       // Lap no the fastest speed was achieved, 255 = not set
    )
    PACKET_LEN_24 = COMPILED_PACKET_STRUCT_24.size

    # Type hints declaration for fields
    m_packetFormat: int
    m_lastLapTimeInMS: int
    m_currentLapTimeInMS: int
    m_sector1TimeInMS: int
    m_sector1TimeMinutes: int
    m_sector2TimeInMS: int
    m_sector2TimeMinutes: int
    m_deltaToCarInFrontInMS: int
    m_deltaToRaceLeaderInMS: int
    m_lapDistance: float
    m_totalDistance: float
    m_safetyCarDelta: float
    m_carPosition: int
    m_currentLapNum: int
    m_pitStatus: "LapData.PitStatus"
    m_numPitStops: int
    m_sector: "LapData.Sector"
    m_currentLapInvalid: bool
    m_penalties: int
    m_totalWarnings: int
    m_cornerCuttingWarnings: int
    m_numUnservedDriveThroughPens: int
    m_numUnservedStopGoPens: int
    m_gridPosition: int
    m_driverStatus: "LapData.DriverStatus"
    m_resultStatus: ResultStatus
    m_pitLaneTimerActive: bool
    m_pitLaneTimeInLaneInMS: int
    m_pitStopTimerInMS: int
    m_pitStopShouldServePen: bool
    m_speedTrapFastestSpeed: float
    m_speedTrapFastestLap: int

    class DriverStatus(Enum):
        """
        Enumeration representing the status of a driver during a racing session.

        Note:
            Each attribute represents a unique driver status identified by an integer value.
        """

        IN_GARAGE = 0
        FLYING_LAP = 1
        IN_LAP = 2
        OUT_LAP = 3
        ON_TRACK = 4

        @staticmethod
        def isValid(driver_status: int) -> bool:
            """Check if the given driver status is valid.

            Args:
                driver_status (int): The driver status to be validated.

            Returns:
                bool: True if valid.
            """
            if isinstance(driver_status, LapData.DriverStatus):
                return True  # It's already an instance of DriverStatus
            return any(driver_status == member.value for member in  LapData.DriverStatus)

        def __str__(self) -> str:
            """
            Returns a human-readable string representation of the driver status.

            Returns:
                str: String representation of the driver status.
            """
            status_mapping = {
                0: "IN_GARAGE",
                1: "FLYING_LAP",
                2: "IN_LAP",
                3: "OUT_LAP",
                4: "ON_TRACK",
            }
            return status_mapping.get(self.value, "---")
    class PitStatus(Enum):
        """
        Enumeration representing the pit status of a driver during a racing session.
        """

        NONE = 0
        PITTING = 1
        IN_PIT_AREA = 2

        @staticmethod
        def isValid(pit_status: int) -> bool:
            """Check if the given pit status is valid.

            Args:
                pit_status (int): The pit status to be validated.

            Returns:
                bool: True if valid.
            """
            if isinstance(pit_status, LapData.PitStatus):
                return True  # It's already an instance of PitStatus
            return any(pit_status == member.value for member in  LapData.PitStatus)

        def __str__(self) -> str:
            """
            Returns a human-readable string representation of the pit status.

            Returns:
                str: String representation of the pit status.
            """
            status_mapping = {
                0: "NONE",
                1: "PITTING",
                2: "IN_PIT_AREA",
            }
            return status_mapping.get(self.value, "---")

    class Sector(Enum):
        """
        Enumeration representing the sector of a racing track.
        """

        SECTOR1 = 0
        SECTOR2 = 1
        SECTOR3 = 2

        @staticmethod
        def isValid(sector: int) -> bool:
            """Check if the given sector is valid.

            Args:
                sector (int): The sector to be validated.

            Returns:
                bool: True if valid.
            """
            if isinstance(sector, LapData.Sector):
                return True  # It's already an instance of Sector
            return any(sector == member.value for member in  LapData.Sector)


        def __str__(self) -> str:
            """
            Returns a human-readable string representation of the sector.

            Returns:
                str: String representation of the sector.
            """
            sector_mapping = {
                0: "SECTOR1",
                1: "SECTOR2",
                2: "SECTOR3",
            }
            return sector_mapping.get(self.value, "---")

    def __init__(self, data: bytes, packet_format: int) -> None:
        """
        Initialize LapData instance by unpacking binary data.

        Args:
        - data (bytes): Binary data containing lap information.
        - packet_format (int): The format version of the packet.

        Raises:
        - struct.error: If the binary data does not match the expected format.
        """

        # Assign the members from unpacked_data
        self.m_packetFormat = packet_format
        if packet_format == 2023:
            raw_data = data[:self.PACKET_LEN_23]
            (
                self.m_lastLapTimeInMS,
                self.m_currentLapTimeInMS,
                self.m_sector1TimeInMS,
                self.m_sector1TimeMinutes,
                self.m_sector2TimeInMS,
                self.m_sector2TimeMinutes,
                self.m_deltaToCarInFrontInMS,
                self.m_deltaToRaceLeaderInMS,
                self.m_lapDistance,
                self.m_totalDistance,
                self.m_safetyCarDelta,
                self.m_carPosition,
                self.m_currentLapNum,
                self.m_pitStatus,
                self.m_numPitStops,
                self.m_sector,
                self.m_currentLapInvalid,
                self.m_penalties,
                self.m_totalWarnings,
                self.m_cornerCuttingWarnings,
                self.m_numUnservedDriveThroughPens,
                self.m_numUnservedStopGoPens,
                self.m_gridPosition,
                self.m_driverStatus,
                self.m_resultStatus,
                self.m_pitLaneTimerActive,
                self.m_pitLaneTimeInLaneInMS,
                self.m_pitStopTimerInMS,
                self.m_pitStopShouldServePen,
            ) = self.COMPILED_PACKET_STRUCT_23.unpack(raw_data)
            self.m_deltaToCarInFrontMinutes: int = 0
            self.m_deltaToRaceLeaderMinutes: int = 0
            self.m_speedTrapFastestSpeed: float = 0
            self.m_speedTrapFastestLap: int = 0
        else: # 24
            raw_data = data[0:self.PACKET_LEN_24]
            (
                self.m_lastLapTimeInMS,
                self.m_currentLapTimeInMS,
                self.m_sector1TimeInMS,
                self.m_sector1TimeMinutes,
                self.m_sector2TimeInMS,
                self.m_sector2TimeMinutes,
                self.m_deltaToCarInFrontInMS,
                self.m_deltaToCarInFrontMinutes,
                self.m_deltaToRaceLeaderInMS,
                self.m_deltaToRaceLeaderMinutes,
                self.m_lapDistance,
                self.m_totalDistance,
                self.m_safetyCarDelta,
                self.m_carPosition,
                self.m_currentLapNum,
                self.m_pitStatus,
                self.m_numPitStops,
                self.m_sector,
                self.m_currentLapInvalid,
                self.m_penalties,
                self.m_totalWarnings,
                self.m_cornerCuttingWarnings,
                self.m_numUnservedDriveThroughPens,
                self.m_numUnservedStopGoPens,
                self.m_gridPosition,
                self.m_driverStatus,
                self.m_resultStatus,
                self.m_pitLaneTimerActive,
                self.m_pitLaneTimeInLaneInMS,
                self.m_pitStopTimerInMS,
                self.m_pitStopShouldServePen,
                self.m_speedTrapFastestSpeed,
                self.m_speedTrapFastestLap
            ) = self.COMPILED_PACKET_STRUCT_24.unpack(raw_data)

        if LapData.DriverStatus.isValid(self.m_driverStatus):
            self.m_driverStatus = LapData.DriverStatus(self.m_driverStatus)
        if ResultStatus.isValid(self.m_resultStatus):
            self.m_resultStatus = ResultStatus(self.m_resultStatus)
        if LapData.PitStatus.isValid(self.m_pitStatus):
            self.m_pitStatus = LapData.PitStatus(self.m_pitStatus)
        if LapData.Sector.isValid(self.m_sector):
            self.m_sector = LapData.Sector(self.m_sector)
        self.m_currentLapInvalid = bool(self.m_currentLapInvalid)
        self.m_pitLaneTimerActive = bool(self.m_pitLaneTimerActive)

    def __str__(self) -> str:
        """
        Return a string representation of the LapData instance.

        Returns:
        - str: String representation of LapData.
        """
        return (
            f"LapData("
            f"Last Lap Time: {self.m_lastLapTimeInMS} ms, "
            f"Current Lap Time: {self.m_currentLapTimeInMS} ms, "
            f"Sector 1 Time: {self.m_sector1TimeInMS} ms, "
            f"Sector 1 Time (Minutes): {self.m_sector1TimeMinutes}, "
            f"Sector 2 Time: {self.m_sector2TimeInMS} ms, "
            f"Sector 2 Time (Minutes): {self.m_sector2TimeMinutes}, "
            f"Delta To Car In Front: {self.m_deltaToCarInFrontInMS} ms, "
            f"Delta To Race Leader: {self.m_deltaToRaceLeaderInMS} ms, "
            f"Lap Distance: {self.m_lapDistance} meters, "
            f"Total Distance: {self.m_totalDistance} meters, "
            f"Safety Car Delta: {self.m_safetyCarDelta} seconds, "
            f"Car Position: {self.m_carPosition}, "
            f"Current Lap Number: {self.m_currentLapNum}, "
            f"Pit Status: {self.m_pitStatus}, "
            f"Number of Pit Stops: {self.m_numPitStops}, "
            f"Sector: {self.m_sector}, "
            f"Current Lap Invalid: {self.m_currentLapInvalid}, "
            f"Penalties: {self.m_penalties}, "
            f"Total Warnings: {self.m_totalWarnings}, "
            f"Corner Cutting Warnings: {self.m_cornerCuttingWarnings}, "
            f"Unserved Drive Through Pens: {self.m_numUnservedDriveThroughPens}, "
            f"Unserved Stop Go Pens: {self.m_numUnservedStopGoPens}, "
            f"Grid Position: {self.m_gridPosition}, "
            f"Driver Status: {self.m_driverStatus}, "
            f"Result Status: {self.m_resultStatus}, "
            f"Pit Lane Timer Active: {self.m_pitLaneTimerActive}, "
            f"Pit Lane Time in Lane: {self.m_pitLaneTimeInLaneInMS} ms, "
            f"Pit Stop Timer: {self.m_pitStopTimerInMS} ms, "
            f"Pit Stop Should Serve Penalty: {self.m_pitStopShouldServePen})"
        )

    def toJSON(self) -> Dict[str, Any]:
        """
        Convert LapData instance to JSON format.

        Returns:
        - dict: JSON representation of LapData.
        """

        return {
            "last-lap-time-in-ms": self.m_lastLapTimeInMS,
            "last-lap-time-str": F1Utils.millisecondsToMinutesSecondsMilliseconds(self.m_lastLapTimeInMS),
            "current-lap-time-in-ms": self.m_currentLapTimeInMS,
            "current-lap-time-str": F1Utils.millisecondsToMinutesSecondsMilliseconds(self.m_currentLapTimeInMS),
            "sector-1-time-in-ms": self.m_sector1TimeInMS,
            "sector-1-time-minutes": self.m_sector1TimeMinutes,
            "sector-1-time-str": F1Utils.getLapTimeStrSplit(self.m_sector1TimeMinutes, self.m_sector1TimeInMS),
            "sector-2-time-in-ms": self.m_sector2TimeInMS,
            "sector-2-time-minutes": self.m_sector2TimeMinutes,
            "sector-2-time-str": F1Utils.getLapTimeStrSplit(self.m_sector2TimeMinutes, self.m_sector2TimeInMS),
            "delta-to-car-in-front-in-ms": self.m_deltaToCarInFrontInMS,
            "delta-to-race-leader-in-ms": self.m_deltaToRaceLeaderInMS,
            "lap-distance": self.m_lapDistance,
            "total-distance": self.m_totalDistance,
            "safety-car-delta": self.m_safetyCarDelta,
            "car-position": self.m_carPosition,
            "current-lap-num": self.m_currentLapNum,
            "pit-status": str(self.m_pitStatus) if LapData.PitStatus.isValid(self.m_pitStatus) else self.m_pitStatus,
            "num-pit-stops": self.m_numPitStops,
            "sector": str(self.m_sector.value) if LapData.Sector.isValid(self.m_sector) else self.m_sector,
            "current-lap-invalid": self.m_currentLapInvalid,
            "penalties": self.m_penalties,
            "total-warnings": self.m_totalWarnings,
            "corner-cutting-warnings": self.m_cornerCuttingWarnings,
            "num-unserved-drive-through-pens": self.m_numUnservedDriveThroughPens,
            "num-unserved-stop-go-pens": self.m_numUnservedStopGoPens,
            "grid-position": self.m_gridPosition,
            "driver-status": str(self.m_driverStatus),
            "result-status": str(self.m_resultStatus),
            "pit-lane-timer-active": self.m_pitLaneTimerActive,
            "pit-lane-time-in-lane-in-ms": self.m_pitLaneTimeInLaneInMS,
            "pit-stop-timer-in-ms": self.m_pitStopTimerInMS,
            "pit-stop-should-serve-pen": self.m_pitStopShouldServePen,
            "speed-trap-fastest-speed" : self.m_speedTrapFastestSpeed,
            "speed-trap-fastest-lap" : self.m_speedTrapFastestLap,
        }

    def __eq__(self, other: object) -> bool:
        """
        Check if two LapData instances are equal.

        Args:
            other (object): The object to compare with.

        Returns:
            bool: True if both instances are equal, False otherwise.
        """
        if not isinstance(other, LapData):
            return False

        return (
            self.m_packetFormat == other.m_packetFormat and
            self.m_lastLapTimeInMS == other.m_lastLapTimeInMS and
            self.m_currentLapTimeInMS == other.m_currentLapTimeInMS and
            self.m_sector1TimeInMS == other.m_sector1TimeInMS and
            self.m_sector1TimeMinutes == other.m_sector1TimeMinutes and
            self.m_sector2TimeInMS == other.m_sector2TimeInMS and
            self.m_sector2TimeMinutes == other.m_sector2TimeMinutes and
            self.m_deltaToCarInFrontInMS == other.m_deltaToCarInFrontInMS and
            self.m_deltaToRaceLeaderInMS == other.m_deltaToRaceLeaderInMS and
            self.m_lapDistance == other.m_lapDistance and
            self.m_totalDistance == other.m_totalDistance and
            self.m_safetyCarDelta == other.m_safetyCarDelta and
            self.m_carPosition == other.m_carPosition and
            self.m_currentLapNum == other.m_currentLapNum and
            self.m_pitStatus == other.m_pitStatus and
            self.m_numPitStops == other.m_numPitStops and
            self.m_sector == other.m_sector and
            self.m_currentLapInvalid == other.m_currentLapInvalid and
            self.m_penalties == other.m_penalties and
            self.m_totalWarnings == other.m_totalWarnings and
            self.m_cornerCuttingWarnings == other.m_cornerCuttingWarnings and
            self.m_numUnservedDriveThroughPens == other.m_numUnservedDriveThroughPens and
            self.m_numUnservedStopGoPens == other.m_numUnservedStopGoPens and
            self.m_gridPosition == other.m_gridPosition and
            self.m_driverStatus == other.m_driverStatus and
            self.m_resultStatus == other.m_resultStatus and
            self.m_pitLaneTimerActive == other.m_pitLaneTimerActive and
            self.m_pitLaneTimeInLaneInMS == other.m_pitLaneTimeInLaneInMS and
            self.m_pitStopTimerInMS == other.m_pitStopTimerInMS and
            self.m_pitStopShouldServePen == other.m_pitStopShouldServePen and
            self.m_speedTrapFastestSpeed == other.m_speedTrapFastestSpeed and
            self.m_speedTrapFastestLap == other.m_speedTrapFastestLap
        )

    def __ne__(self, other: object) -> bool:
        """
        Check if two LapData instances are not equal.

        Args:
            other (object): The object to compare with.

        Returns:
            bool: True if both instances are not equal, False otherwise.
        """
        return not self.__eq__(other)

class PacketLapData:
    """Class representing the incoming PacketLapData.

    Attributes:
        - m_header (PacketHeader) - The header object
        - m_lapData(List[LapData]) - The list of LapData objects, in the order of driver index
        - m_timeTrialPBCarIdx (int) - Index of Personal Best car in time trial (255 if invalid)
        - m_timeTrialRivalCarIdx (int) - Index of Rival car in time trial (255 if invalid)
    """
    def __init__(self, header: PacketHeader, packet: bytes) -> None:
        """
        Initialize PacketLapData instance by unpacking binary data.
        Args:
            - header (PacketHeader): Packet header information.
            - packet (bytes): Binary data containing lap data packet.
        Raises:
            - InvalidPacketLengthError: If the received packet length is not as expected.
        """
        # Store the header reference
        self.m_header = header

        # Set the fixed number of lap data entries (22 cars)
        self.m_lapDataCount = 22

        # Determine LapData size based on game year
        # F1 game data structures can vary between game versions
        lap_data_obj_size = LapData.PACKET_LEN_24  # Default to 2024 format
        if header.m_packetFormat == 2023:
            lap_data_obj_size = LapData.PACKET_LEN_23  # Use 2023 format if needed

        # Calculate expected packet length:
        # - Total lap data size (22 cars × bytes per car)
        # - Plus 2 bytes for the time trial indices at the end
        len_of_lap_data_array = self.m_lapDataCount * lap_data_obj_size
        expected_len = len_of_lap_data_array + 2

        # Validate that the packet is the correct length
        # This helps catch corrupted or incorrect data early
        if len(packet) != expected_len:
            raise InvalidPacketLengthError(
                f"Received LapDataPacket length {len(packet)} is not of expected length {expected_len}"
            )

        # Process each car's lap data individually
        # Extract chunks of the correct size and create LapData objects
        self.m_lapData: List[LapData] = []
        for i in range(self.m_lapDataCount):
            # Calculate start and end indices for this car's data
            start_idx = i * lap_data_obj_size
            end_idx = start_idx + lap_data_obj_size

            # Extract this car's binary data and create a LapData object
            car_data = packet[start_idx:end_idx]
            self.m_lapData.append(LapData(car_data, header.m_packetFormat))

        # Extract time trial indices from the last 2 bytes
        # These identify personal best and rival cars in time trial mode
        time_trial_data = packet[len_of_lap_data_array:]
        self.m_timeTrialPBCarIdx, self.m_timeTrialRivalCarIdx = struct.unpack('<bb', time_trial_data)

    def __str__(self) -> str:
        """
        Return a string representation of the PacketLapData instance.

        Returns:
        - str: String representation of PacketLapData.
        """
        lap_data_str = ", ".join(str(data) for data in self.m_lapData)
        return f"PacketLapData(Header: {str(self.m_header)}, Car Lap Data: [{lap_data_str}])"

    def toJSON(self, include_header: bool=False) -> Dict[str, Any]:
        """
        Convert PacketLapData instance to a JSON-formatted dictionary.

        Arguments:
            - include_header - Whether the header dump must be included in the JSON

        Returns:
        - dict: JSON-formatted dictionary representing the PacketLapData instance.
        """

        json_data = {
            "lap-data": [lap_data.toJSON() for lap_data in self.m_lapData],
            "lap-data-count": self.m_lapDataCount,
            "time-trial-pb-car-idx": int(self.m_timeTrialPBCarIdx),
            "time-trial-rival-car-idx": int(self.m_timeTrialRivalCarIdx),
        }
        if include_header:
            json_data["header"] = self.m_header.toJSON()
        return json_data

    def __eq__(self, other: object) -> bool:
        """
        Check if two PacketLapData instances are equal.

        Args:
            other (object): The object to compare with.

        Returns:
            bool: True if both instances are equal, False otherwise.
        """
        if not isinstance(other, PacketLapData):
            return False

        return (
            self.m_header == other.m_header and
            self.m_lapData == other.m_lapData and
            self.m_timeTrialPBCarIdx == other.m_timeTrialPBCarIdx and
            self.m_timeTrialRivalCarIdx == other.m_timeTrialRivalCarIdx
        )

    def __ne__(self, other: object) -> bool:
        """
        Check if two PacketLapData instances are not equal.

        Args:
            other (object): The object to compare with.

        Returns:
            bool: True if both instances are not equal, False otherwise.
        """
        return not self.__eq__(other)
