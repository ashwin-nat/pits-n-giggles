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
from abc import ABC
from typing import Any, Dict, Optional

from .base_pkt import F1BaseEnum, F1PacketBase, F1SubPacketBase
from .common import SafetyCarEventType, SafetyCarType
from .header import PacketHeader
from abc import abstractmethod

# --------------------- CLASS DEFINITIONS --------------------------------------

class EventType(F1SubPacketBase, ABC):
    @abstractmethod
    def to_bytes(self, packet_format: int) -> bytes:
        """Serialize this event to raw bytes"""
        raise NotImplementedError

class PacketEventData(F1PacketBase):
    """Class representing the incoming PacketEventData message

    Raises:
        TypeError: Unsupported event type

    Attributes:
        m_header (PacketHeader) - Parsed header object
        m_eventStringCode (str) - The string code of the event type (IDK why they didnt just use a uint8)
        m_eventDetails (type depends on m_eventStringCode) - Holds the object with the event info.
                                                            May be None for certain event types.
                                                            Refer PacketEventData.event_type_map

    """
    class EventPacketType(F1BaseEnum):
        """
        Enum class representing different event types.
        """

        # None: No event
        NONE = "N/A"

        # Session Started: Sent when the session starts
        SESSION_STARTED = "SSTA"

        # Session Ended: Sent when the session ends
        SESSION_ENDED = "SEND"

        # Fastest Lap: When a driver achieves the fastest lap
        FASTEST_LAP = "FTLP"

        # Retirement: When a driver retires
        RETIREMENT = "RTMT"

        # DRS enabled: Race control have enabled DRS
        DRS_ENABLED = "DRSE"

        # DRS disabled: Race control have disabled DRS
        DRS_DISABLED = "DRSD"

        # Team mate in pits: Your team mate has entered the pits
        TEAM_MATE_IN_PITS = "TMPT"

        # Chequered flag: The chequered flag has been waved
        CHEQUERED_FLAG = "CHQF"

        # Race Winner: The race winner is announced
        RACE_WINNER = "RCWN"

        # Penalty Issued: A penalty has been issued – details in event
        PENALTY_ISSUED = "PENA"

        # Speed Trap Triggered: Speed trap has been triggered by fastest speed
        SPEED_TRAP_TRIGGERED = "SPTP"

        # Start lights: Start lights – number shown
        START_LIGHTS = "STLG"

        # Lights out: Lights out
        LIGHTS_OUT = "LGOT"

        # Drive through served: Drive through penalty served
        DRIVE_THROUGH_SERVED = "DTSV"

        # Stop go served: Stop go penalty served
        STOP_GO_SERVED = "SGSV"

        # Flashback: Flashback activated
        FLASHBACK = "FLBK"

        # Button status: Button status changed
        BUTTON_STATUS = "BUTN"

        # Red Flag: Red flag shown
        RED_FLAG = "RDFL"

        # Overtake: Overtake occurred
        OVERTAKE = "OVTK"

        # Safety car: Various safety car related events
        SAFETY_CAR = "SCAR"

        # Collion: Inter-car collision event
        COLLISION = "COLL"

    class FastestLap(EventType):
        """
        A class representing the data structure for the fastest lap information.

        Attributes:
            vehicleIdx (int): Vehicle index of the car achieving the fastest lap.
            lapTime (float): Lap time in seconds.
        """

        COMPILED_PACKET_STRUCT = struct.Struct("<Bf")
        PACKET_LEN = COMPILED_PACKET_STRUCT.size

        __slots__ = (
            "vehicleIdx",
            "lapTime",
        )

        def __init__(self, data: bytes, _packet_format: int) -> None:
            """
            Initializes a FastestLap object by unpacking the provided binary data.

            Parameters:
                data (bytes): Binary data to be unpacked.
                _packet_format (int): The packet format

            Raises:
                struct.error: If the binary data does not match the expected format.
            """
            (
                self.vehicleIdx,
                self.lapTime
            ) = self.COMPILED_PACKET_STRUCT.unpack(data[:self.PACKET_LEN])

        def __str__(self) -> str:
            """
            Returns a string representation of the FastestLap object.

            Returns:
                str: String representation of the object.
            """
            return f"FastestLap(vehicleIdx={self.vehicleIdx}, lapTime={self.lapTime})"

        def toJSON(self) -> Dict[str, Any]:
            """
            Convert FastestLap instance to a JSON-formatted dictionary.

            Returns:
                dict: JSON-formatted dictionary representing the FastestLap instance.
            """
            return {
                "vehicle-idx": self.vehicleIdx,
                "lap-time": self.lapTime,
            }

        def __eq__(self, other: "PacketEventData.FastestLap") -> bool:
            """
            Checks if two FastestLap objects are equal.

            Parameters:
                other (PacketEventData.FastestLap): The other FastestLap object to compare with.

            Returns:
                bool: True if the FastestLap objects are equal, False otherwise.
            """
            return self.vehicleIdx == other.vehicleIdx and self.lapTime == other.lapTime

        def __ne__(self, other: "PacketEventData.FastestLap") -> bool:
            """
            Checks if two FastestLap objects are not equal.

            Parameters:
                other (PacketEventData.FastestLap): The other FastestLap object to compare with.

            Returns:
                bool: True if the FastestLap objects are not equal, False otherwise.
            """
            return not self.__eq__(other)

    class Retirement(EventType):
        """
        The class representing the RETIREMENT event. This is sent when any driver retires or DNF's
        Attributes:
            vehicleIdx(int) - The index of the vehicle that retired
        """

        COMPILED_PACKET_STRUCT_25 = struct.Struct("<BB")
        PACKET_LEN_25 = COMPILED_PACKET_STRUCT_25.size

        COMPILED_PACKET_STRUCT_23_24 = struct.Struct("<B")
        PACKET_LEN_23_24 = COMPILED_PACKET_STRUCT_23_24.size

        __slots__ = (
            "vehicleIdx",
            "m_reason",
        )

        class Reason(F1BaseEnum):
            INVALID = 0
            RETIRED = 1
            FINISHED = 2
            TERMINAL_DAMAGE = 3
            INACTIVE = 4
            NOT_ENOUGH_LAPS = 5
            BLACK_FLAGGED = 6
            RED_FLAGGED = 7
            MECHANICAL_FAILURE = 8
            SESSION_SKIPPED = 9
            SESSION_SIMULATED = 10

            def __str__(self) -> str:
                return self.name.replace("_", " ").title()

        def __init__(self, data: bytes, packet_format: int):
            """
            Initializes a Retirement object by unpacking the provided binary data.

            Parameters:
                data (bytes): Binary data to be unpacked.
                packet_format (int): The packet format

            Raises:
                struct.error: If the binary data does not match the expected format.
            """
            if packet_format >= 2025:
                self.vehicleIdx, self.m_reason = self.COMPILED_PACKET_STRUCT_25.unpack(data[:self.PACKET_LEN_25])
                if PacketEventData.Retirement.Reason.isValid(self.m_reason):
                    self.m_reason = PacketEventData.Retirement.Reason(self.m_reason)
                else:
                    self.m_reason = PacketEventData.Retirement.Reason.INVALID

            else:
                self.vehicleIdx = self.COMPILED_PACKET_STRUCT_23_24.unpack(data[:self.PACKET_LEN_23_24])[0]
                self.m_reason = PacketEventData.Retirement.Reason.INVALID

        def __str__(self):
            return f"Retirement(vehicleIdx={self.vehicleIdx})"

        def toJSON(self) -> Dict[str, Any]:
            """
            Convert the Retirement object to a JSON-compatible dictionary.

            Returns:
                dict: JSON-compatible dictionary representing the Retirement object.
            """
            return {
                "vehicle-idx": self.vehicleIdx,
            }

        def __eq__(self, other: "PacketEventData.Retirement") -> bool:
            """
            Checks if two Retirement objects are equal.

            Parameters:
                other (PacketEventData.Retirement): The other Retirement object to compare with.

            Returns:
                bool: True if the Retirement objects are equal, False otherwise.
            """
            return self.vehicleIdx == other.vehicleIdx

        def __ne__(self, other: "PacketEventData.Retirement") -> bool:
            """
            Checks if two Retirement objects are not equal.

            Parameters:
                other (PacketEventData.Retirement): The other Retirement object to compare with.

            Returns:
                bool: True if the Retirement objects are not equal, False otherwise.
            """
            return not self.__eq__(other)

    class DrsDisabled(EventType):
        """
        The class representing the DRSEVENT disabled event. This is sent when DRS is disabled
        Attributes:
            reason(int) - The reason for disabling DRS
        """

        COMPILED_PACKET_STRUCT_25 = struct.Struct("<B")
        PACKET_LEN_25 = COMPILED_PACKET_STRUCT_25.size

        __slots__ = (
            "m_reason",
        )

        class Reason(F1BaseEnum):
            WET_TRACK = 0
            SAFETY_CAR_DEPLOYED = 1
            RED_FLAG = 2
            MIN_LAP_NOT_REACHED = 3

            def __str__(self):
                return self.name.replace("_", " ").title()

        def __init__(self, data: bytes, packet_format: int):
            """
            Initializes a DrsDisabled object by unpacking the provided binary data.

            Parameters:
                data (bytes): Binary data to be unpacked.
                packet_format (int): The packet format

            Raises:
                struct.error: If the binary data does not match the expected format.
            """
            if packet_format <= 2025:
                self.m_reason = None
                return
            self.m_reason = self.COMPILED_PACKET_STRUCT_25.unpack(data[:self.PACKET_LEN_25])[0]
            self.m_reason = PacketEventData.DrsDisabled.Reason.safeCast(self.m_reason)

        def __str__(self):
            return f"DrsDisabled(reason={self.m_reason})"

        def __eq__(self, other: "PacketEventData.DrsDisabled") -> bool:
            return self.m_reason == other.m_reason

        def __ne__(self, other: "PacketEventData.DrsDisabled") -> bool:
            return not self.__eq__(other)

    class TeamMateInPits(EventType):
        """
        The class representing the TEAMMATE IN PITS event. This is sent when the player's teammate pits.
        This is not sent in spectator mode
        Attributes:
            vehicleIdx(int) - The index of the vehicle that pitted (the teammates index)
        """
        COMPILED_PACKET_STRUCT = struct.Struct("<B")
        PACKET_LEN = COMPILED_PACKET_STRUCT.size

        __slots__ = (
            "vehicleIdx",
        )

        def __init__(self, data: bytes, _packet_format: int):
            """
            Initializes a TeamMateInPits object by unpacking the provided binary data.

            Parameters:
                data (bytes): Binary data to be unpacked.
                _packet_format (int): The packet format

            Raises:
                struct.error: If the binary data does not match the expected format.
            """
            self.vehicleIdx = self.COMPILED_PACKET_STRUCT.unpack(data[:self.PACKET_LEN])[0]

        def __str__(self):
            return f"TeamMateInPits(vehicleIdx={self.vehicleIdx})"

        def toJSON(self) -> Dict[str,Any]:
            """
            Convert the TeamMateInPits object to a JSON-compatible dictionary.

            Returns:
                Dict[str, str]: JSON-compatible dictionary representing the TeamMateInPits object.
            """
            return {
                "vehicle-idx": self.vehicleIdx,
            }

        def __eq__(self, other: "PacketEventData.TeamMateInPits") -> bool:
            """
            Checks if two TeamMateInPits objects are equal.

            Parameters:
                other (PacketEventData.TeamMateInPits): The other TeamMateInPits object to compare with.

            Returns:
                bool: True if the TeamMateInPits objects are equal, False otherwise.
            """
            return self.vehicleIdx == other.vehicleIdx

        def __ne__(self, other: "PacketEventData.TeamMateInPits") -> bool:
            """
            Checks if two TeamMateInPits objects are not equal.

            Parameters:
                other (PacketEventData.TeamMateInPits): The other TeamMateInPits object to compare with.

            Returns:
                bool: True if the TeamMateInPits objects are not equal, False otherwise.
            """
            return not self.__eq__(other)

    class RaceWinner(EventType):
        """
        The class representing the RACE WINNER event. This is sent when the race winner crosses the finish line
        Attributes:
            vehicleIdx(int) - The index of the vehicle that pitted (the teammates index)
        """
        COMPILED_PACKET_STRUCT = struct.Struct("<B")
        PACKET_LEN = COMPILED_PACKET_STRUCT.size

        __slots__ = (
            "vehicleIdx",
        )

        def __init__(self, data: bytes, _packet_format: int):
            """
            Initializes a RaceWinner object by unpacking the provided binary data.

            Parameters:
                data (bytes): Binary data to be unpacked.
                _packet_format (int): The packet format

            Raises:
                struct.error: If the binary data does not match the expected format.
            """
            self.vehicleIdx = self.COMPILED_PACKET_STRUCT.unpack(data[:self.PACKET_LEN])[0]

        def __str__(self):
            return f"RaceWinner(vehicleIdx={self.vehicleIdx})"

        def toJSON(self) -> Dict[str, Any]:
            """
            Convert the RaceWinner object to a JSON-compatible dictionary.

            Returns:
                Dict[str, str]: JSON-compatible dictionary representing the RaceWinner object.
            """
            return {
                "vehicle-idx": self.vehicleIdx,
            }

        def __eq__(self, other: "PacketEventData.RaceWinner") -> bool:
            """
            Checks if two RaceWinner objects are equal.

            Parameters:
                other (PacketEventData.RaceWinner): The other RaceWinner object to compare with.

            Returns:
                bool: True if the RaceWinner objects are equal, False otherwise.
            """
            return self.vehicleIdx == other.vehicleIdx

        def __ne__(self, other: "PacketEventData.RaceWinner") -> bool:
            """
            Checks if two RaceWinner objects are not equal.

            Parameters:
                other (PacketEventData.RaceWinner): The other RaceWinner object to compare with.

            Returns:
                bool: True if the RaceWinner objects are not equal, False otherwise.
            """
            return not self.__eq__(other)

    class Penalty(EventType):
        """
        The class representing the PENALTY event. This is sent when any driver receives a penalty
        Attributes:
            penaltyType (Penalty.PenaltyType) - The type of penalty. See Penalty.PenaltyType enumeration
            infrigementType (Penalty.InfringementType) - The type of infringement. See Penalty.InfringementType enumeration
            vehicleIdx (int) - The index of the vehicle receiving the penalty
            otherVehicleIndex (int) - The index of the other vehicle involved
            time (int) - Time gained or spent doing the action in seconds
            lapNum (int) - Lap number the penalty occured on
            placesGained (int) - Number of places gained by this
        """

        COMPILED_PACKET_STRUCT = struct.Struct("<BBBBBBB")
        PACKET_LEN = COMPILED_PACKET_STRUCT.size

        __slots__ = (
            "penaltyType",
            "infringementType",
            "vehicleIdx",
            "otherVehicleIndex",
            "time",
            "lapNum",
            "placesGained",
        )

        class PenaltyType(F1BaseEnum):
            """Enum class representing different penalties in motorsports."""

            DRIVE_THROUGH = 0
            STOP_GO = 1
            GRID_PENALTY = 2
            PENALTY_REMINDER = 3
            TIME_PENALTY = 4
            WARNING = 5
            DISQUALIFIED = 6
            REMOVED_FROM_FORMATION_LAP = 7
            PARKED_TOO_LONG_TIMER = 8
            TYRE_REGULATIONS = 9
            THIS_LAP_INVALIDATED = 10
            THIS_AND_NEXT_LAP_INVALIDATED = 11
            THIS_LAP_INVALIDATED_WITHOUT_REASON = 12
            THIS_AND_NEXT_LAP_INVALIDATED_WITHOUT_REASON = 13
            THIS_PREVIOUS_LAP_INVALIDATED = 14
            THIS_AND_PREVIOUS_LAP_INVALIDATED_WITHOUT_REASON = 15
            RETIRED = 16
            BLACK_FLAG_TIMER = 17

            def __str__(self) -> str:
                """Return a human-readable string representation of the penalty."""
                return self.name.replace("_", " ").title()

        class InfringementType(F1BaseEnum):
            """Enum class representing different infringements in motorsports."""

            BLOCKING_BY_SLOW_DRIVING = 0
            BLOCKING_BY_WRONG_WAY_DRIVING = 1
            REVERSING_OFF_THE_START_LINE = 2
            BIG_COLLISION = 3
            SMALL_COLLISION = 4
            COLLISION_FAILED_TO_HAND_BACK_POSITION_SINGLE = 5
            COLLISION_FAILED_TO_HAND_BACK_POSITION_MULTIPLE = 6
            CORNER_CUTTING_GAINED_TIME = 7
            CORNER_CUTTING_OVERTAKE_SINGLE = 8
            CORNER_CUTTING_OVERTAKE_MULTIPLE = 9
            CROSSED_PIT_EXIT_LANE = 10
            IGNORING_BLUE_FLAGS = 11
            IGNORING_YELLOW_FLAGS = 12
            IGNORING_DRIVE_THROUGH = 13
            TOO_MANY_DRIVE_THROUGHS = 14
            DRIVE_THROUGH_REMINDER_SERVE_WITHIN_N_LAPS = 15
            DRIVE_THROUGH_REMINDER_SERVE_THIS_LAP = 16
            PIT_LANE_SPEEDING = 17
            PARKED_FOR_TOO_LONG = 18
            IGNORING_TYRE_REGULATIONS = 19
            TOO_MANY_PENALTIES = 20
            MULTIPLE_WARNINGS = 21
            APPROACHING_DISQUALIFICATION = 22
            TYRE_REGULATIONS_SELECT_SINGLE = 23
            TYRE_REGULATIONS_SELECT_MULTIPLE = 24
            LAP_INVALIDATED_CORNER_CUTTING = 25
            LAP_INVALIDATED_RUNNING_WIDE = 26
            CORNER_CUTTING_RAN_WIDE_GAINED_TIME_MINOR = 27
            CORNER_CUTTING_RAN_WIDE_GAINED_TIME_SIGNIFICANT = 28
            CORNER_CUTTING_RAN_WIDE_GAINED_TIME_EXTREME = 29
            LAP_INVALIDATED_WALL_RIDING = 30
            LAP_INVALIDATED_FLASHBACK_USED = 31
            LAP_INVALIDATED_RESET_TO_TRACK = 32
            BLOCKING_THE_PITLANE = 33
            JUMP_START = 34
            SAFETY_CAR_TO_CAR_COLLISION = 35
            SAFETY_CAR_ILLEGAL_OVERTAKE = 36
            SAFETY_CAR_EXCEEDING_ALLOWED_PACE = 37
            VIRTUAL_SAFETY_CAR_EXCEEDING_ALLOWED_PACE = 38
            FORMATION_LAP_BELOW_ALLOWED_SPEED = 39
            FORMATION_LAP_PARKING = 40
            RETIRED_MECHANICAL_FAILURE = 41
            RETIRED_TERMINALLY_DAMAGED = 42
            SAFETY_CAR_FALLING_TOO_FAR_BACK = 43
            BLACK_FLAG_TIMER = 44
            UNSERVED_STOP_GO_PENALTY = 45
            UNSERVED_DRIVE_THROUGH_PENALTY = 46
            ENGINE_COMPONENT_CHANGE = 47
            GEARBOX_CHANGE = 48
            PARC_FERME_CHANGE = 49
            LEAGUE_GRID_PENALTY = 50
            RETRY_PENALTY = 51
            ILLEGAL_TIME_GAIN = 52
            MANDATORY_PITSTOP = 53
            ATTRIBUTE_ASSIGNED = 54

            def __str__(self) -> str:
                """Return a human-readable string representation of the infringement."""
                return self.name.replace("_", " ").title()

        def __init__(self, data: bytes, _packet_format: int):
            """Parse the penalty event packet into this object

            Args:
                data (bytes): The packet containing the event data.
                _packet_format (int): The packet format
            """

            (
                self.penaltyType,
                self.infringementType,
                self.vehicleIdx,
                self.otherVehicleIdx,
                self.time,
                self.lapNum,
                self.placesGained
            ) = self.COMPILED_PACKET_STRUCT.unpack(data[:self.PACKET_LEN])

            self.penaltyType = PacketEventData.Penalty.PenaltyType.safeCast(self.penaltyType)
            self.infringementType = PacketEventData.Penalty.InfringementType.safeCast(self.infringementType)

        def __str__(self):
            return f"Penalty(penaltyType={self.penaltyType}, infringementType={self.infringementType}, " \
                f"vehicleIdx={self.vehicleIdx}, otherVehicleIdx={self.otherVehicleIdx}, time={self.time}, " \
                f"lapNum={self.lapNum}, placesGained={self.placesGained})"

        def toJSON(self) -> Dict[str, Any]:
            """
            Convert the Penalty instance to a JSON-compatible dictionary.

            Returns:
                Dict[str, Any]: JSON-compatible dictionary representing the Penalty instance.
            """
            return {
                "penalty-type": str(self.penaltyType),
                "infringement-type": str(self.infringementType),
                "vehicle-idx": self.vehicleIdx,
                "other-vehicle-idx": self.otherVehicleIdx,
                "time": self.time,
                "lap-num": self.lapNum,
                "places-gained": self.placesGained
            }

        def __eq__(self, other: "PacketEventData.Penalty") -> bool:
            """
            Check if two Penalty objects are equal.

            Args:
                other (PacketEventData.Penalty): The other Penalty object to compare with.

            Returns:
                bool: True if the Penalty objects are equal, False otherwise.
            """
            return (
                self.penaltyType == other.penaltyType
                and self.infringementType == other.infringementType
                and self.vehicleIdx == other.vehicleIdx
                and self.otherVehicleIdx == other.otherVehicleIdx
                and self.time == other.time
                and self.lapNum == other.lapNum
                and self.placesGained == other.placesGained
            )

        def __ne__(self, other: "PacketEventData.Penalty") -> bool:
            """
            Check if two Penalty objects are not equal.

            Args:
                other (PacketEventData.Penalty): The other Penalty object to compare with.

            Returns:
                bool: True if the Penalty objects are not equal, False otherwise.
            """
            return not self.__eq__(other)

    class SpeedTrap(EventType):
        """
        The class representing the SPEED TRAP event. This is sent when a car is caught speeding by the speed trap.
        Attributes:
            vehicleIdx (int): The index of the vehicle caught speeding.
            speed (float): The speed of the vehicle in meters per second.
            isOverallFastestInSession (bool): Flag indicating if the speed is the overall fastest in the session.
            isDriverFastestInSession (bool): Flag indicating if the speed is the fastest for the driver in the session.
            fastestVehicleIdxInSession (int): The index of the vehicle with the fastest speed in the session.
            fastestSpeedInSession (float): The speed of the fastest vehicle in the session.
        """

        COMPILED_PACKET_STRUCT = struct.Struct("<BfBBBf")
        PACKET_LEN = COMPILED_PACKET_STRUCT.size

        __slots__ = (
            "vehicleIdx",
            "speed",
            "isOverallFastestInSession",
            "isDriverFastestInSession",
            "fastestVehicleIdxInSession",
            "fastestSpeedInSession"
        )

        def __init__(self, data: bytes, _packet_format: int) -> None:
            """
            Initializes a SpeedTrap object by unpacking the provided binary data.

            Parameters:
                data (bytes): Binary data to be unpacked.
                _packet_format (int): The packet format

            Raises:
                struct.error: If the binary data does not match the expected format.
            """
            (
                self.vehicleIdx,
                self.speed,
                self.isOverallFastestInSession,
                self.isDriverFastestInSession,
                self.fastestVehicleIdxInSession,
                self.fastestSpeedInSession
            ) = self.COMPILED_PACKET_STRUCT.unpack(data[:self.PACKET_LEN])
            self.isOverallFastestInSession = bool(self.isOverallFastestInSession)
            self.isDriverFastestInSession = bool(self.isDriverFastestInSession)

        def __str__(self) -> str:
            """
            Returns a string representation of the SpeedTrap object.

            Returns:
                str: String representation of the object.
            """

            return (
                f"SpeedTrap(vehicleIdx={self.vehicleIdx}, speed={self.speed}, "
                f"isOverallFastestInSession={self.isOverallFastestInSession}, "
                f"isDriverFastestInSession={self.isDriverFastestInSession}, "
                f"fastestVehicleIdxInSession={self.fastestVehicleIdxInSession}, "
                f"fastestSpeedInSession={self.fastestSpeedInSession})"
            )

        def toJSON(self) -> Dict[str, Any]:
            """
            Convert the SpeedTrap instance to a JSON-compatible dictionary.

            Returns:
                Dict[str, Any]: JSON-compatible dictionary representing the SpeedTrap instance.
            """

            return {
                "vehicle-idx": self.vehicleIdx,
                "speed": self.speed,
                "is-overall-fastest-in-session": self.isOverallFastestInSession,
                "is-driver-fastest-in-session": self.isDriverFastestInSession,
                "fastest-vehicle-idx-in-session": self.fastestVehicleIdxInSession,
                "fastest-speed-in-session": self.fastestSpeedInSession
            }

        def __eq__(self, other: "PacketEventData.SpeedTrap") -> bool:
            """
            Check if two SpeedTrap objects are equal.

            Args:
                other (PacketEventData.SpeedTrap): The other SpeedTrap object to compare with.

            Returns:
                bool: True if the SpeedTrap objects are equal, False otherwise.
            """

            return (
                self.vehicleIdx == other.vehicleIdx
                and self.speed == other.speed
                and self.isOverallFastestInSession == other.isOverallFastestInSession
                and self.isDriverFastestInSession == other.isDriverFastestInSession
                and self.fastestVehicleIdxInSession == other.fastestVehicleIdxInSession
                and self.fastestSpeedInSession == other.fastestSpeedInSession
            )

        def __ne__(self, other: "PacketEventData.SpeedTrap") -> bool:
            """
            Check if two SpeedTrap objects are not equal.

            Args:
                other (PacketEventData.SpeedTrap): The other SpeedTrap object to compare with.

            Returns:
                bool: True if the SpeedTrap objects are not equal, False otherwise.
            """

            return not self.__eq__(other)

    class StartLights(EventType):
        """
        The class representing the START LIGHTS event. This is sent when the start lights sequence begins.
        Attributes:
            numLights (int): The number of lights in the start lights sequence.
        """

        COMPILED_PACKET_STRUCT = struct.Struct("<B")
        PACKET_LEN = COMPILED_PACKET_STRUCT.size

        __slots__ = (
            "numLights",
        )

        def __init__(self, data: bytes, _packet_format: int) -> None:
            """
            Initializes a StartLights object by unpacking the provided binary data.

            Parameters:
                data (bytes): Binary data to be unpacked.
                _packet_format (int): The packet format

            Raises:
                struct.error: If the binary data does not match the expected format.
            """

            self.numLights = self.COMPILED_PACKET_STRUCT.unpack(data[:self.PACKET_LEN])[0]

        def __str__(self) -> str:
            """
            Returns a string representation of the StartLights object.

            Returns:
                str: String representation of the object.
            """

            return f"StartLights(numLights={self.numLights})"

        def toJSON(self) -> Dict[str, Any]:
            """
            Convert the StartLights instance to a JSON-compatible dictionary.

            Returns:
                Dict[str, Any]: JSON-compatible dictionary representing the StartLights instance.
            """

            return {"num-lights": self.numLights}

        def __eq__(self, other: "PacketEventData.StartLights") -> bool:
            """
            Check if two StartLights objects are equal.

            Args:
                other (PacketEventData.StartLights): The other StartLights object to compare with.

            Returns:
                bool: True if the StartLights objects are equal, False otherwise.
            """

            return self.numLights == other.numLights

    class DriveThroughPenaltyServed(EventType):
        """
        The class representing the DRIVE THROUGH PENALTY SERVED event.
        This is sent when a driver serves a drive-through penalty.

        Attributes:
            vehicleIdx (int): The index of the vehicle serving the drive-through penalty.
        """

        COMPILED_PACKET_STRUCT = struct.Struct("<B")
        PACKET_LEN = COMPILED_PACKET_STRUCT.size

        __slots__ = (
            "vehicleIdx",
        )

        def __init__(self, data: bytes, _packet_format: int) -> None:
            """
            Initializes a DriveThroughPenaltyServed object by unpacking the provided binary data.

            Parameters:
                data (bytes): Binary data to be unpacked.
                _packet_format (int): The packet format

            Raises:
                struct.error: If the binary data does not match the expected format.
            """

            self.vehicleIdx = self.COMPILED_PACKET_STRUCT.unpack(data[:self.PACKET_LEN])

        def __str__(self) -> str:
            """
            Returns a string representation of the DriveThroughPenaltyServed object.

            Returns:
                str: String representation of the object.
            """

            return f"DriveThroughPenaltyServed(vehicleIdx={self.vehicleIdx})"

        def toJSON(self) -> Dict[str, Any]:
            """
            Convert the DriveThroughPenaltyServed instance to a JSON-compatible dictionary.

            Returns:
                Dict[str, Any]: JSON-compatible dictionary representing the DriveThroughPenaltyServed instance.
            """

            return {
                "vehicle-idx": self.vehicleIdx
            }

        def __eq__(self, other: "PacketEventData.DriveThroughPenaltyServed") -> bool:
            """
            Check if two DriveThroughPenaltyServed objects are equal.

            Args:
                other (PacketEventData.DriveThroughPenaltyServed): The other DriveThroughPenaltyServed object to compare with.

            Returns:
                bool: True if the DriveThroughPenaltyServed objects are equal, False otherwise.
            """
            return self.vehicleIdx == other.vehicleIdx

        def __ne__(self, other: "PacketEventData.DriveThroughPenaltyServed") -> bool:
            """
            Check if two DriveThroughPenaltyServed objects are not equal.

            Args:
                other (PacketEventData.DriveThroughPenaltyServed): The other DriveThroughPenaltyServed object to compare with.

            Returns:
                bool: True if the DriveThroughPenaltyServed objects are not equal, False otherwise.
            """
            return not self.__eq__(other)

    class StopGoPenaltyServed(EventType):
        """
        The class representing the STOP-GO PENALTY SERVED event.
        This is sent when a driver serves a stop-go penalty.

        Attributes:
            vehicleIdx (int): The index of the vehicle serving the stop-go penalty.
        """

        COMPILED_PACKET_STRUCT_23_24 = struct.Struct("<B")
        PACKET_LEN_23_24 = COMPILED_PACKET_STRUCT_23_24.size

        COMPILED_PACKET_STRUCT_25 = struct.Struct("<Bf")
        PACKET_LEN_25 = COMPILED_PACKET_STRUCT_25.size

        __slots__ = (
            "vehicleIdx",
            "stopTime",
        )

        def __init__(self, data: bytes, packet_format: int) -> None:
            """
            Initializes a StopGoPenaltyServed object by unpacking the provided binary data.

            Parameters:
                data (bytes): Binary data to be unpacked.
                packet_format (int): The packet format

            Raises:
                struct.error: If the binary data does not match the expected format.
            """

            if packet_format <= 2025:
                self.vehicleIdx = self.COMPILED_PACKET_STRUCT_23_24.unpack(data[:self.PACKET_LEN_23_24])
                self.stopTime = 0.0
            else:
                self.vehicleIdx, self.stopTime = self.COMPILED_PACKET_STRUCT_25.unpack(data[:self.PACKET_LEN_25])

        def __str__(self) -> str:
            """
            Returns a string representation of the StopGoPenaltyServed object.

            Returns:
                str: String representation of the object.
            """

            return f"StopGoPenaltyServed(vehicleIdx={self.vehicleIdx} stopTime={self.stopTime})"

        def toJSON(self) -> Dict[str, Any]:
            """
            Convert the StopGoPenaltyServed instance to a JSON-compatible dictionary.

            Returns:
                Dict[str, Any]: JSON-compatible dictionary representing the StopGoPenaltyServed instance.
            """

            return {
                "vehicle-idx": self.vehicleIdx,
                "stop-time": self.stopTime
            }

        def __eq__(self, other: "PacketEventData.StopGoPenaltyServed") -> bool:
            """
            Check if two StopGoPenaltyServed objects are equal.

            Args:
                other (PacketEventData.StopGoPenaltyServed): The other StopGoPenaltyServed object to compare with.

            Returns:
                bool: True if the StopGoPenaltyServed objects are equal, False otherwise.
            """
            return self.vehicleIdx == other.vehicleIdx

        def __ne__(self, other: "PacketEventData.StopGoPenaltyServed") -> bool:
            """
            Check if two StopGoPenaltyServed objects are not equal.

            Args:
                other (PacketEventData.StopGoPenaltyServed): The other StopGoPenaltyServed object to compare with.

            Returns:
                bool: True if the StopGoPenaltyServed objects are not equal, False otherwise.
            """
            return not self.__eq__(other)

    class Flashback(EventType):
        """
        The class representing the FLASHBACK event. This is sent when the player initiates a flashback.

        Attributes:
            flashbackFrameIdentifier (int): Identifier for the flashback frame.
            flashbackSessionTime (float): Session time when the flashback was initiated, in seconds.
        """

        COMPILED_PACKET_STRUCT = struct.Struct("<If")
        PACKET_LEN = COMPILED_PACKET_STRUCT.size

        __slots__ = (
            "flashbackFrameIdentifier",
            "flashbackSessionTime",
        )

        def __init__(self, data: bytes, _packet_format: int) -> None:
            """
            Initializes a Flashback object by unpacking the provided binary data.

            Parameters:
                data (bytes): Binary data to be unpacked.
                _packet_format (int): The packet format

            Raises:
                struct.error: If the binary data does not match the expected format.
            """

            self.flashbackFrameIdentifier, self.flashbackSessionTime = \
                self.COMPILED_PACKET_STRUCT.unpack(data[:self.PACKET_LEN])

        def __str__(self) -> str:
            """
            Returns a string representation of the Flashback object.

            Returns:
                str: String representation of the object.
            """

            return f"Flashback(flashbackFrameIdentifier={self.flashbackFrameIdentifier}, " \
                f"flashbackSessionTime={self.flashbackSessionTime})"

        def toJSON(self) -> Dict[str, Any]:
            """
            Convert the Flashback instance to a JSON-compatible dictionary.

            Returns:
                Dict[str, Any]: JSON-compatible dictionary representing the Flashback instance.
            """

            return {
                "flashback-frame-identifier": self.flashbackFrameIdentifier,
                "flashback-session-time": self.flashbackSessionTime
            }

        def __eq__(self, other: "PacketEventData.Flashback") -> bool:
            """
            Check if two Flashback objects are equal.

            Args:
                other (PacketEventData.Flashback): The other Flashback object to compare with.

            Returns:
                bool: True if the Flashback objects are equal, False otherwise.
            """
            return self.flashbackFrameIdentifier == other.flashbackFrameIdentifier and \
                self.flashbackSessionTime == other.flashbackSessionTime

        def __ne__(self, other: "PacketEventData.Flashback") -> bool:
            """
            Check if two Flashback objects are not equal.

            Args:
                other (PacketEventData.Flashback): The other Flashback object to compare with.

            Returns:
                bool: True if the Flashback objects are not equal, False otherwise.
            """
            return not self.__eq__(other)

    class Buttons(EventType):
        """
        Represents a packet containing button press information.
        """

        COMPILED_PACKET_STRUCT = struct.Struct("<I")
        PACKET_LEN = COMPILED_PACKET_STRUCT.size

        # Bit mappings
        CROSS_A = 0x00000001
        TRIANGLE_Y = 0x00000002
        CIRCLE_B = 0x00000004
        SQUARE_X = 0x00000008
        DPAD_LEFT = 0x00000010
        DPAD_RIGHT = 0x00000020
        DPAD_UP = 0x00000040
        DPAD_DOWN = 0x00000080
        OPTIONS_MENU = 0x00000100
        L1_LB = 0x00000200
        R1_RB = 0x00000400
        L2_LT = 0x00000800
        R2_RT = 0x00001000
        LEFT_STICK_CLICK = 0x00002000
        RIGHT_STICK_CLICK = 0x00004000
        RIGHT_STICK_LEFT = 0x00008000
        RIGHT_STICK_RIGHT = 0x00010000
        RIGHT_STICK_UP = 0x00020000
        RIGHT_STICK_DOWN = 0x00040000
        SPECIAL = 0x00080000
        UDP_ACTION_1 = 0x00100000
        UDP_ACTION_2 = 0x00200000
        UDP_ACTION_3 = 0x00400000
        UDP_ACTION_4 = 0x00800000
        UDP_ACTION_5 = 0x01000000
        UDP_ACTION_6 = 0x02000000
        UDP_ACTION_7 = 0x04000000
        UDP_ACTION_8 = 0x08000000
        UDP_ACTION_9 = 0x10000000
        UDP_ACTION_10 = 0x20000000
        UDP_ACTION_11 = 0x40000000
        UDP_ACTION_12 = 0x80000000

        __slots__ = (
            "buttonStatus",
        )

        def __init__(self, data: bytes, _packet_format: int) -> None:
            """
            Initializes a Buttons object by unpacking the provided binary data.

            Parameters:
                data (bytes): Binary data to be unpacked.
                _packet_format (int): The packet format

            Raises:
                struct.error: If the binary data does not match the expected format.
            """
            self.buttonStatus = self.COMPILED_PACKET_STRUCT.unpack(data[:self.PACKET_LEN])[0]

        def isButtonPressed(self, button_flag: int) -> bool:
            """
            Checks if a specific button is pressed based on the given button flag.

            Args:
                button_flag (int): The button flag representing the button to check.

            Returns:
                bool: True if the button is pressed, False otherwise.

            Example:
                is_cross_pressed = button_packet.isButtonPressed(Buttons.CROSS_A)
            """
            return (self.buttonStatus & button_flag) != 0

        def isUDPActionPressed(self, udp_action_code: int) -> bool:
            """
            Checks if a specific UDP custom action code is pressed.

            Args:
                udp_action_code (int): The UDP custom action code to check (from 1 to 12).

            Returns:
                bool: True if the UDP custom action code is pressed, False otherwise.

            Example:
                is_udp_action_pressed = button_packet.isUDPActionPressed(5)
            """

            if 1 <= udp_action_code <= 12:
                # Calculate the UDP custom action code flag position in buttonStatus
                # UDP action codes start from the 19th bit, so we add 19 to the action code
                udp_flag = 1 << (udp_action_code + 19)
                return self.isButtonPressed(udp_flag)
            raise ValueError("UDP action code must be in the range 1 to 12.")

        def __str__(self) -> str:
            """
            Returns a string representation of the buttons pressed in the packet.
            """

            pressed_buttons = [
                name
                for name, value in vars(self.__class__).items()
                if name.isupper() and isinstance(value, int) and self.isButtonPressed(value)
            ]

            # 32-bit output: 0x + 8 hex digits
            return f"Pressed Buttons: [{', '.join(pressed_buttons)}] Raw = (0x{self.buttonStatus:08X})"

        def toJSON(self) -> Dict[str, Any]:
            """
            Convert the Buttons instance to a JSON-compatible dictionary.

            Returns:
                Dict[str, Any]: JSON-compatible dictionary representing the Buttons instance.
            """

            return {
                "button-status": self.buttonStatus
            }

        def __eq__(self, other: "PacketEventData.Buttons") -> bool:
            """
            Check if two Buttons objects are equal.

            Args:
                other (PacketEventData.Buttons): The other Buttons object to compare with.

            Returns:
                bool: True if the Buttons objects are equal, False otherwise.
            """

            return self.buttonStatus == other.buttonStatus

        def __ne__(self, other: "PacketEventData.Buttons") -> bool:
            """
            Check if two Buttons objects are not equal.

            Args:
                other (PacketEventData.Buttons): The other Buttons object to compare with.

            Returns:
                bool: True if the Buttons objects are not equal, False otherwise.
            """

            return self.buttonStatus != other.buttonStatus

        @classmethod
        def from_status(cls, button_status: int) -> "PacketEventData.Buttons":
            obj = cls.__new__(cls)
            obj.buttonStatus = button_status
            return obj

        @classmethod
        def udp_action_flag(cls, action_code: int) -> int:
            """
            Convert UDP action code (1-12) into the corresponding button flag.
            """
            if not 1 <= action_code <= 12:
                raise ValueError("UDP action code must be in range 1-12")
            return 1 << (action_code + 19)

        def to_bytes(self, _packet_format: int) -> bytes:
            return self.COMPILED_PACKET_STRUCT.pack(self.buttonStatus)

    class Overtake(EventType):
        """
        The class representing the OVERTAKE event. This is sent when one vehicle overtakes another.

        Attributes:
            overtakingVehicleIdx (int): The index of the overtaking vehicle.
            beingOvertakenVehicleIdx (int): The index of the vehicle being overtaken.
        """

        COMPILED_PACKET_STRUCT = struct.Struct("<BB")
        PACKET_LEN = COMPILED_PACKET_STRUCT.size

        __slots__ = (
            "overtakingVehicleIdx",
            "beingOvertakenVehicleIdx",
        )

        def __init__(self, data: bytes, _packet_format: int) -> None:
            """
            Initializes an Overtake object by unpacking the provided binary data.

            Parameters:
                data (bytes): Binary data to be unpacked.
                _packet_format (int): The packet format

            Raises:
                struct.error: If the binary data does not match the expected format.
            """
            self.overtakingVehicleIdx, self.beingOvertakenVehicleIdx = \
                self.COMPILED_PACKET_STRUCT.unpack(data[:self.PACKET_LEN])

        def __str__(self) -> str:
            """
            Returns a string representation of the Overtake object.

            Returns:
                str: String representation of the object.
            """
            return f"Overtake(overtakingVehicleIdx={self.overtakingVehicleIdx}, " \
                f"beingOvertakenVehicleIdx={self.beingOvertakenVehicleIdx})"

        def toJSON(self) -> Dict[str, Any]:
            """
            Convert the Overtake instance to a JSON-compatible dictionary.

            Returns:
                Dict[str, Any]: JSON-compatible dictionary representing the Overtake instance.
            """
            return {
                "overtaking-vehicle-idx": self.overtakingVehicleIdx,
                "being-overtaken-vehicle-idx": self.beingOvertakenVehicleIdx
            }

        def __eq__(self, other: "PacketEventData.Overtake") -> bool:
            """
            Check if two Overtake objects are equal.

            Args:
                other (PacketEventData.Overtake): The other Overtake object to compare with.

            Returns:
                bool: True if the Overtake objects are equal, False otherwise.
            """

            return self.overtakingVehicleIdx == other.overtakingVehicleIdx and \
                self.beingOvertakenVehicleIdx == other.beingOvertakenVehicleIdx

        def __ne__(self, other: "PacketEventData.Overtake") -> bool:
            """
            Check if two Overtake objects are not equal.

            Args:
                other (PacketEventData.Overtake): The other Overtake object to compare with.

            Returns:
                bool: True if the Overtake objects are not equal, False otherwise.
            """

            return self.overtakingVehicleIdx != other.overtakingVehicleIdx or \
                self.beingOvertakenVehicleIdx != other.beingOvertakenVehicleIdx

    class SafetyCarEvent(EventType):
        """
        The class representing the safety car event. Refer to the various safety car event types.

        Attributes:
            m_safety_car_type (SafetyCarType): Refer SafetyCarType enumeration
            m_event_type (SafetyCarEventType): Refer SafetyCarEventType enumeration
        """

        COMPILED_PACKET_STRUCT = struct.Struct("<BB")
        PACKET_LEN = COMPILED_PACKET_STRUCT.size

        __slots__ = (
            "m_safety_car_type",
            "m_event_type",
        )

        def __init__(self, data: bytes, _packet_format: int) -> None:
            """
            Initializes an Overtake object by unpacking the provided binary data.

            Parameters:
                data (bytes): Binary data to be unpacked.
                _packet_format (int): The packet format

            Raises:
                struct.error: If the binary data does not match the expected format.
            """
            self.m_safety_car_type, self.m_event_type = self.COMPILED_PACKET_STRUCT.unpack(data[:self.PACKET_LEN])
            self.m_safety_car_type = SafetyCarType.safeCast(self.m_safety_car_type)
            self.m_event_type = SafetyCarEventType.safeCast(self.m_event_type)

        def __str__(self) -> str:
            """
            Returns a string representation of the SafetyCar object.

            Returns:
                str: String representation of the object.
            """
            return f"SafetyCarEvent(safety_car_type={str(self.m_safety_car_type)}, " \
                f"event_type={str(self.m_event_type)})"

        def toJSON(self) -> Dict[str, Any]:
            """
            Convert the Overtake instance to a JSON-compatible dictionary.

            Returns:
                Dict[str, Any]: JSON-compatible dictionary representing the Overtake instance.
            """
            return {
                "safety-car-type" : str(self.m_safety_car_type),
                "safety-car-event-type" : str(self.m_event_type)
            }

        def __eq__(self, other: "PacketEventData.SafetyCarEvent") -> bool:
            """
            Check if two SafetyCarEvent objects are equal.

            Args:
                other (PacketEventData.SafetyCarEvent): The other SafetyCarEvent object to compare with.

            Returns:
                bool: True if the SafetyCarEvent objects are equal, False otherwise.
            """

            return self.m_safety_car_type == other.m_safety_car_type and \
                self.m_event_type == other.m_event_type

        def __ne__(self, other: "PacketEventData.SafetyCarEvent") -> bool:
            """
            Check if two SafetyCarEvent objects are not equal.

            Args:
                other (PacketEventData.SafetyCarEvent): The other SafetyCarEvent object to compare with.

            Returns:
                bool: True if the SafetyCarEvent objects are not equal, False otherwise.
            """

            return self.m_safety_car_type != other.m_safety_car_type or \
                self.m_event_type != other.m_event_type

    class Collision(EventType):
        """
        The class representing the COLLISION event. This is sent when one vehicle overtakes another.

        Attributes:
            m_vehicle_1_index (int): The index of the overtaking vehicle.
            m_vehicle_2_index (int): The index of the vehicle being overtaken.
        """

        COMPILED_PACKET_STRUCT = struct.Struct("<BB")
        PACKET_LEN = COMPILED_PACKET_STRUCT.size

        __slots__ = (
            "m_vehicle_1_index",
            "m_vehicle_2_index",
        )

        def __init__(self, data: bytes, _packet_format: int) -> None:
            """
            Initializes a Collision object by unpacking the provided binary data.

            Parameters:
                data (bytes): Binary data to be unpacked.
                _packet_format (int): The packet format

            Raises:
                struct.error: If the binary data does not match the expected format.
            """
            self.m_vehicle_1_index, self.m_vehicle_2_index = self.COMPILED_PACKET_STRUCT.unpack(data[:self.PACKET_LEN])

        def __str__(self) -> str:
            """
            Returns a string representation of the Collision object.

            Returns:
                str: String representation of the object.
            """
            return f"Collision(m_vehicle_1_index={str(self.m_vehicle_1_index)}, " \
                f"m_vehicle_2_index={str(self.m_vehicle_2_index)})"

        def toJSON(self) -> Dict[str, Any]:
            """
            Convert the Collision instance to a JSON-compatible dictionary.

            Returns:
                Dict[str, Any]: JSON-compatible dictionary representing the Collision instance.
            """
            return {
                "vehicle-1-index": self.m_vehicle_1_index,
                "vehicle-2-index": self.m_vehicle_2_index
            }

        def __eq__(self, other: "PacketEventData.Collision") -> bool:
            """
            Check if two Collision objects are equal.

            Args:
                other (PacketEventData.Collision): The other Collision object to compare with.

            Returns:
                bool: True if the Collision objects are equal, False otherwise.
            """

            return self.m_vehicle_1_index == other.m_vehicle_1_index and \
                self.m_vehicle_2_index == other.m_vehicle_2_index

        def __ne__(self, other: "PacketEventData.Collision") -> bool:
            """
            Check if two Collision objects are not equal.

            Args:
                other (PacketEventData.Collision): The other Collision object to compare with.

            Returns:
                bool: True if the Collision objects are not equal, False otherwise.
            """

            return not self.__eq__(other)

    # Mappings between the event type and the type of object to parse into
    event_type_map: Dict[EventPacketType, Optional[EventType]] = {
        EventPacketType.SESSION_STARTED: None,
        EventPacketType.SESSION_ENDED: None,
        EventPacketType.FASTEST_LAP: FastestLap,
        EventPacketType.RETIREMENT: Retirement,
        EventPacketType.DRS_ENABLED: None,
        EventPacketType.DRS_DISABLED: DrsDisabled,
        EventPacketType.TEAM_MATE_IN_PITS: TeamMateInPits,
        EventPacketType.CHEQUERED_FLAG: None,
        EventPacketType.RACE_WINNER: RaceWinner,
        EventPacketType.PENALTY_ISSUED: Penalty,
        EventPacketType.SPEED_TRAP_TRIGGERED: SpeedTrap,
        EventPacketType.START_LIGHTS: StartLights,
        EventPacketType.LIGHTS_OUT: None,
        EventPacketType.DRIVE_THROUGH_SERVED: DriveThroughPenaltyServed,
        EventPacketType.STOP_GO_SERVED: StopGoPenaltyServed,
        EventPacketType.FLASHBACK: Flashback,
        EventPacketType.BUTTON_STATUS: Buttons,
        EventPacketType.RED_FLAG: None,
        EventPacketType.OVERTAKE: Overtake,
        EventPacketType.SAFETY_CAR: SafetyCarEvent,
        EventPacketType.COLLISION: Collision
    }

    COMPILED_PACKET_STRUCT = struct.Struct("4s")
    PACKET_LEN = COMPILED_PACKET_STRUCT.size

    __slots__ = (
        'm_eventStringCode',
        'm_eventCode',
        'mEventDetails',
    )

    def __init__(self, header: PacketHeader, packet: bytes) -> None:
        """Construct the PacketEventData object from the incoming raw packet

        Args:
            header (PacketHeader): The parsed header object
            packet (bytes): The incoming raw bytes

        Raises:
            TypeError: Unsupported event type
        """

        super().__init__(header)

        # Parse the event string and prep the enum
        self.m_eventStringCode = self.COMPILED_PACKET_STRUCT.unpack(packet[:self.PACKET_LEN])[0].decode('utf-8')
        if PacketEventData.EventPacketType.isValid(self.m_eventStringCode):
            self.m_eventCode = PacketEventData.EventPacketType(self.m_eventStringCode)
        else:
            self.m_eventCode = PacketEventData.EventPacketType.NONE
            raise TypeError(f"Unsupported Event Type {self.m_eventCode}")

        # Parse the optional data, if any
        if PacketEventData.event_type_map.get(self.m_eventCode):
            self.mEventDetails = PacketEventData.event_type_map[self.m_eventCode](packet[4:], header.m_packetFormat)
        else:
            self.mEventDetails = None

    def __str__(self) -> str:
        """Convert this object contents into a readable/printable/loggable string

        Returns:
            str: The string version
        """

        event_str = (f"Event: {str(self.mEventDetails)}") if self.mEventDetails else ""
        return f"PacketEventData(Header: {str(self.m_header)}, Event String Code: {self.m_eventCode}, {event_str})"

    def toJSON(self, include_header: bool=False) -> Dict[str, Any]:
        """Convert this PacketEventData object into a JSON friendly dict

        Arguments:
            - include_header - Whether the header dump must be included in the JSON

        Returns:
            Dict[str, Any]: JSON dict containing all the attributes
        """

        json_data = {
            "event-string-code" : self.m_eventStringCode,
            "event-details" : self.mEventDetails.toJSON() if self.mEventDetails else None
        }
        if include_header:
            json_data["header"] = self.m_header.toJSON()
        return json_data

    def __eq__(self, other: "PacketEventData") -> bool:
        """
        Check if two PacketEventData objects are equal.

        Args:
            other (PacketEventData): The other PacketEventData object to compare with.

        Returns:
            bool: True if the PacketEventData objects are equal, False otherwise.
        """

        return self.m_eventCode == other.m_eventCode and \
            self.mEventDetails == other.mEventDetails

    def __ne__(self, other: "PacketEventData") -> bool:
        """
        Check if two PacketEventData objects are not equal.

        Args:
            other (PacketEventData): The other PacketEventData object to compare with.

        Returns:
            bool: True if the PacketEventData objects are not equal, False otherwise.
        """

        return not self.__eq__(other)

    def to_bytes(self, include_header: bool=False) -> bytes:
        data = bytearray()

        # 1. Header
        if include_header:
            data += self.m_header.to_bytes()

        # 2. Event string code (4 bytes, ASCII per spec)
        data += self.COMPILED_PACKET_STRUCT.pack(
            self.m_eventStringCode.encode("utf-8")
        )

        # 3. Optional event payload
        if self.mEventDetails:
            data += self.mEventDetails.to_bytes(self.m_header.m_packetFormat)

        return bytes(data)



    @classmethod
    def from_values(
        cls,
        header: PacketHeader,
        event_type: EventPacketType,
        event_details: Optional[EventType]
    ) -> "PacketEventData":

        obj = cls.__new__(cls)
        super(PacketEventData, obj).__init__(header)

        obj.m_eventCode = event_type
        obj.m_eventStringCode = event_type.value
        obj.mEventDetails = event_details

        return obj

