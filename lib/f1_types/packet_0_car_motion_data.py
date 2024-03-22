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

class CarMotionData:
    """
    A class for parsing the Car Motion Data of a telemetry packet in a racing game.
    The car motion data structure is as follows:

    Attributes:
        - m_worldPositionX (float): World space X position - metres
        - m_worldPositionY (float): World space Y position - metres
        - m_worldPositionZ (float): World space Z position - metres
        - m_worldVelocityX (float): Velocity in world space X - metres/s
        - m_worldVelocityY (float): Velocity in world space Y - metres/s
        - m_worldVelocityZ (float): Velocity in world space Z - metres/s
        - m_worldForwardDirX (int): World space forward X direction (normalised)
        - m_worldForwardDirY (int): World space forward Y direction (normalised)
        - m_worldForwardDirZ (int): World space forward X direction (normalised)
        - m_worldRightDirX (int): World space right X direction (normalised)
        - m_worldRightDirY (int): World space right Y direction (normalised)
        - m_worldRightDirZ (int): World space right Z direction (normalised)
        - m_gForceLateral (float): Lateral G-Force component
        - m_gForceLongitudinal (float): Longitudinal G-Force component
        - m_gForceVertical (float): Vertical G-Force component
        - m_yaw (float): Yaw angle in radians
        - m_pitch (float): Pitch angle in radians
        - m_roll (float): Roll angle in radians
    """

    PACKET_FORMAT = ("<"
        "f" # float - World space X position - metres
        "f" # float - World space Y position
        "f" # float - World space Z position
        "f" # float - Velocity in world space X – metres/s
        "f" # float - Velocity in world space Y
        "f" # float - Velocity in world space Z
        "h" # int16 - World space forward X direction (normalised)
        "h" # int16 - World space forward Y direction (normalised)
        "h" # int16 - World space forward Z direction (normalised)
        "h" # int16 - World space right X direction (normalised)
        "h" # int16 - World space right Y direction (normalised)
        "h" # int16 - World space right Z direction (normalised)
        "f" # float - Lateral G-Force component
        "f" # float - Longitudinal G-Force component
        "f" # float - Vertical G-Force component
        "f" # float - Yaw angle in radians
        "f" # float - Pitch angle in radians
        "f" # float - Roll angle in radians
    )
    PACKET_LEN: int = struct.calcsize(PACKET_FORMAT)

    def __init__(self, data: bytes) -> None:
        """A class for parsing the data related to the motion of the F1 car

        Args:
            data (List[bytes]): list containing the raw bytes for this packet
        """

        # Declare the data type hints
        self.m_worldPositionX: float
        self.m_worldPositionY: float
        self.m_worldPositionZ: float
        self.m_worldVelocityX: float
        self.m_worldVelocityY: float
        self.m_worldVelocityZ: float
        self.m_worldForwardDirX: int
        self.m_worldForwardDirY: int
        self.m_worldForwardDirZ: int
        self.m_worldRightDirX: int
        self.m_worldRightDirY: int
        self.m_worldRightDirZ: int
        self.m_gForceLateral: float
        self.m_gForceLongitudinal: float
        self.m_gForceVertical: float
        self.m_yaw: float
        self.m_pitch: float
        self.m_roll: float

        # Now, unpack the data and populate the members
        self.m_worldPositionX, self.m_worldPositionY, self.m_worldPositionZ, \
        self.m_worldVelocityX, self.m_worldVelocityY, self.m_worldVelocityZ, \
        self.m_worldForwardDirX, self.m_worldForwardDirY, self.m_worldForwardDirZ, \
        self.m_worldRightDirX, self.m_worldRightDirY, self.m_worldRightDirZ, \
        self.m_gForceLateral, self.m_gForceLongitudinal, self.m_gForceVertical, \
        self.m_yaw, self.m_pitch, self.m_roll = struct.unpack(self.PACKET_FORMAT, data)

    def __str__(self) -> str:
        """Return a formatted string representing the CarMotionData object

        Returns:
            str - string representation of this object
        """
        return (
            f"CarMotionData("
            f"World Position: ({self.m_worldPositionX}, {self.m_worldPositionY}, {self.m_worldPositionZ}), "
            f"World Velocity: ({self.m_worldVelocityX}, {self.m_worldVelocityY}, {self.m_worldVelocityZ}), "
            f"World Forward Dir: ({self.m_worldForwardDirX}, {self.m_worldForwardDirY}, {self.m_worldForwardDirZ}), "
            f"World Right Dir: ({self.m_worldRightDirX}, {self.m_worldRightDirY}, {self.m_worldRightDirZ}), "
            f"G-Force Lateral: {self.m_gForceLateral}, "
            f"G-Force Longitudinal: {self.m_gForceLongitudinal}, "
            f"G-Force Vertical: {self.m_gForceVertical}, "
            f"Yaw: {self.m_yaw}, "
            f"Pitch: {self.m_pitch}, "
            f"Roll: {self.m_roll})"
        )

    def toJSON(self) -> Dict[str, Any]:
        """Converts the CarMotionData object to a dictionary suitable for JSON serialization.

        Returns:
            Dict[str, Any]: A dictionary representing the JSON-compatible data.
        """
        return {
            "world-position": {
                "x": self.m_worldPositionX,
                "y": self.m_worldPositionY,
                "z": self.m_worldPositionZ
            },
            "world-velocity": {
                "x": self.m_worldVelocityX,
                "y": self.m_worldVelocityY,
                "z": self.m_worldVelocityZ
            },
            "world-forward-dir": {
                "x": self.m_worldForwardDirX,
                "y": self.m_worldForwardDirY,
                "z": self.m_worldForwardDirZ
            },
            "world-right-dir": {
                "x": self.m_worldRightDirX,
                "y": self.m_worldRightDirY,
                "z": self.m_worldRightDirZ
            },
            "g-force": {
                "lateral": self.m_gForceLateral,
                "longitudinal": self.m_gForceLongitudinal,
                "vertical": self.m_gForceVertical
            },
            "orientation": {
                "yaw": self.m_yaw,
                "pitch": self.m_pitch,
                "roll": self.m_roll
            }
        }

class PacketMotionData:
    """A class for parsing the Motion Data Packet of a telemetry packet in a racing game.

    Args:
        header (PacketHeader): Incoming packet header
        packet (List[bytes]): list containing the raw bytes for this packet

    Attributes:
    - m_header (PacketHeader): The header of the telemetry packet.
    - m_car_motion_data (list): List of CarMotionData objects containing data for all cars on track.

    Raises:
        InvalidPacketLengthError: If received length is not as per expectation
    """

    def __init__(self, header:PacketHeader, packet: bytes) -> None:
        """Construct the PacketMotionData object from the given packet payload

        Args:
            header (PacketHeader): the parsed header object
            packet (bytes): The packet containing only the payload (header must be stripped)

        Raises:
            InvalidPacketLengthError: If number of bytes is not as per expectation
        """

        self.m_header: PacketHeader = header       # PacketHeader

        if ((len(packet) % CarMotionData.PACKET_LEN) != 0):
            raise InvalidPacketLengthError("Received packet length " + str(len(packet)) + " is not a multiple of " +
                                            str(CarMotionData.PACKET_LEN))
        self.m_carMotionData: List[CarMotionData] = []
        motion_data_packet_per_car = _split_list(packet, CarMotionData.PACKET_LEN)
        for motion_data_packet in motion_data_packet_per_car:
            self.m_carMotionData.append(CarMotionData(motion_data_packet))

    def __str__(self) -> str:
        """
        Return a string representation of the PacketMotionData instance.

        Returns:
        - str: String representation of PacketMotionData.
        """
        car_motion_data_str = ", ".join(str(car) for car in self.m_carMotionData)
        return f"PacketMotionData(Header: {str(self.m_header)}, CarMotionData: [{car_motion_data_str}])"

    def toJSON(self, include_header: bool=False) -> Dict[str, Any]:
        """Converts the PacketMotionData object to a dictionary suitable for JSON serialization.

        Arguments:
            - include_header - Whether the header dump must be included in the JSON

        Returns:
            Dict[str, Any]: A dictionary representing the JSON-compatible data.
        """

        json_data = {
            "car-motion-data": [car.toJSON() for car in self.m_carMotionData]
        }

        if include_header:
            json_data["header"] = self.m_header.toJSON()

        return json_data
