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

from .common import *
from .common import _split_list, _extract_sublist

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
    """

    PACKET_FORMAT = ("<"
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
    PACKET_LEN:int = struct.calcsize(PACKET_FORMAT)

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
            else:
                min_value = min(member.value for member in LapData.DriverStatus)
                max_value = max(member.value for member in LapData.DriverStatus)
                return min_value <= driver_status <= max_value

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
            else:
                min_value = min(member.value for member in LapData.PitStatus)
                max_value = max(member.value for member in LapData.PitStatus)
                return min_value <= pit_status <= max_value

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
            else:
                min_value = min(member.value for member in LapData.Sector)
                max_value = max(member.value for member in LapData.Sector)
                return min_value <= sector <= max_value

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

    def __init__(self, data) -> None:
        """
        Initialize LapData instance by unpacking binary data.

        Args:
        - data (bytes): Binary data containing lap information.

        Raises:
        - struct.error: If the binary data does not match the expected format.
        """

        # Assign the members from unpacked_data
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
        ) = struct.unpack(self.PACKET_FORMAT, data)

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
            "sector-1-time-str": F1Utils.millisecondsToSecondsMilliseconds(self.m_sector1TimeInMS),
            "sector-2-time-in-ms": self.m_sector2TimeInMS,
            "sector-2-time-minutes": self.m_sector2TimeMinutes,
            "sector-2-time-str": F1Utils.millisecondsToSecondsMilliseconds(self.m_sector2TimeInMS),
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
            "pit-stop-should-serve-pen": self.m_pitStopShouldServePen
        }

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
        self.m_header: PacketHeader = header
        self.m_LapData: List[LapData] = []  # LapData[22]
        self.m_LapDataCount = 22
        len_of_lap_data_array = self.m_LapDataCount * LapData.PACKET_LEN

        # 2 extra bytes for the two uint8 that follow LapData
        expected_len = (len_of_lap_data_array + 2)
        if len(packet) != expected_len:
            raise InvalidPacketLengthError(
                f"Received LapDataPacket length {len(packet)} is not of expected length {expected_len}"
            )

        lap_data_packet_raw = _extract_sublist(packet, 0, len_of_lap_data_array)
        for lap_data_packet in _split_list(lap_data_packet_raw, LapData.PACKET_LEN):
            self.m_LapData.append(LapData(lap_data_packet))

        time_trial_section_raw = _extract_sublist(packet, len_of_lap_data_array, len(packet))
        unpacked_data = struct.unpack('<bb', time_trial_section_raw)
        (
            self.m_timeTrialPBCarIdx,
            self.m_timeTrialRivalCarIdx
        ) = unpacked_data

    def __str__(self) -> str:
        """
        Return a string representation of the PacketLapData instance.

        Returns:
        - str: String representation of PacketLapData.
        """
        lap_data_str = ", ".join(str(data) for data in self.m_LapData)
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
            "lap-data": [lap_data.toJSON() for lap_data in self.m_LapData],
            "lap-data-count": self.m_LapDataCount,
            "time-trial-pb-car-idx": int(self.m_timeTrialPBCarIdx),
            "time-trial-rival-car-idx": int(self.m_timeTrialRivalCarIdx),
        }
        if include_header:
            json_data["header"] = self.m_header.toJSON()
        return json_data
