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
from typing import Dict, Any
from .common import PacketHeader

# --------------------- CLASS DEFINITIONS --------------------------------------

class PacketMotionExData:
    """
    Represents extended motion data for a player's car.

    Attributes:
        m_header (PacketHeader): Header information for the packet.
        m_suspensionPosition (List[float]): Suspension position for each wheel.
        m_suspensionVelocity (List[float]): Suspension velocity for each wheel.
        m_suspensionAcceleration (List[float]): Suspension acceleration for each wheel.
        m_wheelSpeed (List[float]): Speed of each wheel.
        m_wheelSlipRatio (List[float]): Slip ratio for each wheel.
        m_wheelSlipAngle (List[float]): Slip angles for each wheel.
        m_wheelLatForce (List[float]): Lateral forces for each wheel.
        m_wheelLongForce (List[float]): Longitudinal forces for each wheel.
        m_heightOfCOGAboveGround (float): Height of the center of gravity above ground.
        m_localVelocityX (float): Velocity in local space along the X-axis.
        m_localVelocityY (float): Velocity in local space along the Y-axis.
        m_localVelocityZ (float): Velocity in local space along the Z-axis.
        m_angularVelocityX (float): Angular velocity around the X-axis.
        m_angularVelocityY (float): Angular velocity around the Y-axis.
        m_angularVelocityZ (float): Angular velocity around the Z-axis.
        m_angularAccelerationX (float): Angular acceleration around the X-axis.
        m_angularAccelerationY (float): Angular acceleration around the Y-axis.
        m_angularAccelerationZ (float): Angular acceleration around the Z-axis.
        m_frontWheelsAngle (float): Current front wheels angle in radians.
        m_wheelVertForce (List[float]): Vertical forces for each wheel.
        m_frontAeroHeight (float): Front plank edge height above road surface
        m_rearAeroHeight (float): Rear plank edge height above road surface
        m_frontRollAngle (float): Roll angle of the front suspension
        m_rearRollAngle (float): Roll angle of the rear suspension
        m_chassisYaw (float): Yaw angle of the chassis relative to the direction of motion - radians
    """

    COMPILED_PACKET_STRUCT_23 = struct.Struct("<"
        # // Extra player car ONLY data
        "4f" # float         m_suspensionPosition[4];       // Note: All wheel arrays have the following order:
        "4f" # float         m_suspensionVelocity[4];       // RL, RR, FL, FR
        "4f" # float         m_suspensionAcceleration[4];	// RL, RR, FL, FR
        "4f" # float         m_wheelSpeed[4];           	// Speed of each wheel
        "4f" # float         m_wheelSlipRatio[4];           // Slip ratio for each wheel
        "4f" # float         m_wheelSlipAngle[4];           // Slip angles for each wheel
        "4f" # float         m_wheelLatForce[4];            // Lateral forces for each wheel
        "4f" # float         m_wheelLongForce[4];           // Longitudinal forces for each wheel
        "f" # float         m_heightOfCOGAboveGround;      // Height of centre of gravity above ground
        "f" # float         m_localVelocityX;         	// Velocity in local space – metres/s
        "f" # float         m_localVelocityY;         	// Velocity in local space
        "f" # float         m_localVelocityZ;         	// Velocity in local space
        "f" # float         m_angularVelocityX;		// Angular velocity x-component – radians/s
        "f" # float         m_angularVelocityY;            // Angular velocity y-component
        "f" # float         m_angularVelocityZ;            // Angular velocity z-component
        "f" # float         m_angularAccelerationX;        // Angular acceleration x-component – radians/s/s
        "f" # float         m_angularAccelerationY;	// Angular acceleration y-component
        "f" # float         m_angularAccelerationZ;        // Angular acceleration z-component
        "f" # float         m_frontWheelsAngle;            // Current front wheels angle in radians
        "4f" # float        m_wheelVertForce[4];           // Vertical forces for each wheel
    )
    PACKET_LEN_23 = COMPILED_PACKET_STRUCT_23.size

    COMPILED_PACKET_STRUCT_24_EXTRA = struct.Struct("<"
        "f" # float         m_frontAeroHeight;             // Front plank edge height above road surface
        "f" # float         m_rearAeroHeight;              // Rear plank edge height above road surface
        "f" # float         m_frontRollAngle;              // Roll angle of the front suspension
        "f" # float         m_rearRollAngle;               // Roll angle of the rear suspension
        "f" # float         m_chassisYaw;                  // Yaw angle of the chassis relative to the direction
                                                        #  // of motion - radians)
    )
    PACKET_LEN_EXTRA_24 = COMPILED_PACKET_STRUCT_24_EXTRA.size
    PACKET_LEN_24 = PACKET_LEN_23 + PACKET_LEN_EXTRA_24

    COMPILED_PACKET_STRUCT_25_EXTRA = struct.Struct("<"
        "f" # float         m_chassisPitch                 // Chassis pitch relative to the dir of motion in radians
        "4f" # float        m_wheelCamber[4]               // Camber angle for each wheel in radians
        "4f" # float        m_wheelCamberGain[4];          // Camber gain for each wheel in radians, difference
                                                        #  // between active camber and dynamic camber
    )
    PACKET_LEN_EXTRA_25 = COMPILED_PACKET_STRUCT_25_EXTRA.size
    PACKET_LEN_25 = PACKET_LEN_23 + PACKET_LEN_EXTRA_24 + PACKET_LEN_EXTRA_25

    def __init__(self, header: PacketHeader, data: bytes) -> None:
        """
        Initializes PacketMotionExData with raw data.

        Args:
            header (PacketHeader): Header information for the packet.
            data (bytes): Raw data representing extended motion information for a player's car.
        """

        self.m_header = header

        self.m_suspensionPosition = [0.0] * 4
        self.m_suspensionVelocity = [0.0] * 4
        self.m_suspensionAcceleration = [0.0] * 4
        self.m_wheelSpeed = [0.0] * 4
        self.m_wheelSlipRatio = [0.0] * 4
        self.m_wheelSlipAngle = [0.0] * 4
        self.m_wheelLatForce = [0.0] * 4
        self.m_wheelLongForce = [0.0] * 4
        self.m_wheelVertForce = [0.0] * 4
        self.m_frontAeroHeight: float = 0.0
        self.m_rearAeroHeight: float = 0.0
        self.m_frontRollAngle: float = 0.0
        self.m_rearRollAngle: float = 0.0
        self.m_chassisYaw: float = 0.0
        self.m_chassisPitch: float = 0.0
        self.m_wheelCamber: float = [0.0] * 4
        self.m_wheelCamberGain: float = [0.0] * 4

        # Common stuff
        (
            self.m_suspensionPosition[0],           # array of floats
            self.m_suspensionPosition[1],           # array of floats
            self.m_suspensionPosition[2],           # array of floats
            self.m_suspensionPosition[3],           # array of floats
            self.m_suspensionVelocity[0],           # array of floats
            self.m_suspensionVelocity[1],           # array of floats
            self.m_suspensionVelocity[2],           # array of floats
            self.m_suspensionVelocity[3],           # array of floats
            self.m_suspensionAcceleration[0],       # array of floats
            self.m_suspensionAcceleration[1],       # array of floats
            self.m_suspensionAcceleration[2],       # array of floats
            self.m_suspensionAcceleration[3],       # array of floats
            self.m_wheelSpeed[0],                   # array of floats
            self.m_wheelSpeed[1],                   # array of floats
            self.m_wheelSpeed[2],                   # array of floats
            self.m_wheelSpeed[3],                   # array of floats
            self.m_wheelSlipRatio[0],               # array of floats
            self.m_wheelSlipRatio[1],               # array of floats
            self.m_wheelSlipRatio[2],               # array of floats
            self.m_wheelSlipRatio[3],               # array of floats
            self.m_wheelSlipAngle[0],               # array of floats
            self.m_wheelSlipAngle[1],               # array of floats
            self.m_wheelSlipAngle[2],               # array of floats
            self.m_wheelSlipAngle[3],               # array of floats
            self.m_wheelLatForce[0],                # array of floats
            self.m_wheelLatForce[1],                # array of floats
            self.m_wheelLatForce[2],                # array of floats
            self.m_wheelLatForce[3],                # array of floats
            self.m_wheelLongForce[0],               # array of floats
            self.m_wheelLongForce[1],               # array of floats
            self.m_wheelLongForce[2],               # array of floats
            self.m_wheelLongForce[3],               # array of floats
            self.m_heightOfCOGAboveGround,       # float
            self.m_localVelocityX,               # float
            self.m_localVelocityY,               # float
            self.m_localVelocityZ,               # float
            self.m_angularVelocityX,             # float
            self.m_angularVelocityY,             # float
            self.m_angularVelocityZ,             # float
            self.m_angularAccelerationX,         # float
            self.m_angularAccelerationY,         # float
            self.m_angularAccelerationZ,         # float
            self.m_frontWheelsAngle,             # float
            self.m_wheelVertForce[0],               # array of floats
            self.m_wheelVertForce[1],               # array of floats
            self.m_wheelVertForce[2],               # array of floats
            self.m_wheelVertForce[3],               # array of floats

        ) = self.COMPILED_PACKET_STRUCT_23.unpack(data[:self.PACKET_LEN_23])

        if header.m_packetFormat > 2023:
            curr_offset = self.PACKET_LEN_23
            if header.m_packetFormat >= 2024:
                (
                    self.m_frontAeroHeight,             # float
                    self.m_rearAeroHeight,              # float
                    self.m_frontRollAngle,              # float
                    self.m_rearRollAngle,               # float
                    self.m_chassisYaw,                  # float
                ) = self.COMPILED_PACKET_STRUCT_24_EXTRA.unpack(
                                    data[curr_offset:curr_offset + self.PACKET_LEN_EXTRA_24])
                curr_offset += self.PACKET_LEN_EXTRA_24
            if header.m_packetFormat >= 2025:
                (
                    self.m_chassisPitch,                # float
                    self.m_wheelCamber[0],             # array of floats
                    self.m_wheelCamber[1],             # array of floats
                    self.m_wheelCamber[2],             # array of floats
                    self.m_wheelCamber[3],             # array of floats
                    self.m_wheelCamberGain[0],         # array of floats
                    self.m_wheelCamberGain[1],         # array of floats
                    self.m_wheelCamberGain[2],         # array of floats
                    self.m_wheelCamberGain[3],         # array of floats
                ) = self.COMPILED_PACKET_STRUCT_25_EXTRA.unpack(
                                    data[curr_offset:curr_offset + self.PACKET_LEN_EXTRA_25])
                curr_offset += self.PACKET_LEN_EXTRA_25

    def __str__(self) -> str:
        """
        Returns a string representation of PacketMotionExData.

        Returns:
            str: String representation of PacketMotionExData.
        """

        return (
            f"Header: {str(self.m_header)}, "
            f"Suspension Position: {str(self.m_suspensionPosition)}, "
            f"Suspension Velocity: {str(self.m_suspensionVelocity)}, "
            f"Suspension Acceleration: {str(self.m_suspensionAcceleration)}, "
            f"Wheel Speed: {str(self.m_wheelSpeed)}, "
            f"Wheel Slip Ratio: {str(self.m_wheelSlipRatio)}, "
            f"Wheel Slip Angle: {str(self.m_wheelSlipAngle)}, "
            f"Wheel Lat Force: {str(self.m_wheelLatForce)}, "
            f"Wheel Long Force: {str(self.m_wheelLongForce)}, "
            f"Height of COG Above Ground: {self.m_heightOfCOGAboveGround}, "
            f"Local Velocity (X, Y, Z): ({self.m_localVelocityX}, {self.m_localVelocityY}, {self.m_localVelocityZ}), "
            f"Angular Velocity (X, Y, Z): ({self.m_angularVelocityX}, {self.m_angularVelocityY}, {self.m_angularVelocityZ}), "
            f"Angular Acceleration (X, Y, Z): ({self.m_angularAccelerationX}, {self.m_angularAccelerationY}, {self.m_angularAccelerationZ}), "
            f"Front Wheels Angle: {self.m_frontWheelsAngle}, "
            f"Wheel Vertical Force: {str(self.m_wheelVertForce)}, "
            f"Front AERO Height: {self.m_frontAeroHeight}, "
            f"Rear AERO Height: {self.m_rearAeroHeight}, "
            f"Front Roll Angle: {self.m_frontRollAngle}, "
            f"Rear Roll Angle: {self.m_rearRollAngle}, "
            f"Chassis Yaw: {self.m_chassisYaw}, "
            f"Chassis Pitch: {self.m_chassisPitch}, "
            f"Wheel Camber: {str(self.m_wheelCamber)}, "
            f"Wheel Camber Gain: {str(self.m_wheelCamberGain)}"
        )

    def toJSON(self, include_header: bool=False) -> Dict[str, Any]:
        """
        Convert the PacketMotionExData instance to a JSON-compatible dictionary with the specified structure.

        Arguments:
            - include_header - Whether the header dump must be included in the JSON

        Returns:
            Dict[str, Any]: JSON-compatible dictionary representing the PacketMotionExData instance.
        """

        # Helper function to create sub-dictionaries for x, y, z components
        def xyz_dict(x, y, z):
            return {"x": x, "y": y, "z": z}

        json_data = {
            "suspension-position": self.m_suspensionPosition,
            "suspension-velocity": self.m_suspensionVelocity,
            "suspension-acceleration": self.m_suspensionAcceleration,
            "wheel-speed": self.m_wheelSpeed,
            "wheel-slip-ratio": self.m_wheelSlipRatio,
            "wheel-slip-angle": self.m_wheelSlipAngle,
            "wheel-lat-force": self.m_wheelLatForce,
            "wheel-long-force": self.m_wheelLongForce,
            "height-of-cog-above-ground": self.m_heightOfCOGAboveGround,
            "local-velocity": xyz_dict(self.m_localVelocityX, self.m_localVelocityY, self.m_localVelocityZ),
            "angular-velocity": xyz_dict(self.m_angularVelocityX, self.m_angularVelocityY, self.m_angularVelocityZ),
            "angular-acceleration": xyz_dict(
                self.m_angularAccelerationX, self.m_angularAccelerationY, self.m_angularAccelerationZ
            ),
            "front-wheels-angle": self.m_frontWheelsAngle,
            "wheel-vert-force": self.m_wheelVertForce,
            "front-aero-height": self.m_frontAeroHeight,
            "rear-aero-height": self.m_rearAeroHeight,
            "front-roll-angle": self.m_frontRollAngle,
            "rear-roll-angle": self.m_rearRollAngle,
            "chassis-yaw": self.m_chassisYaw,
            "chassis-pitch": self.m_chassisPitch,
            "wheel-camber": self.m_wheelCamber,
            "wheel-camber-gain": self.m_wheelCamberGain
        }
        if include_header:
            json_data["header"] = self.m_header.toJSON()

        return json_data

    def __eq__(self, other: "PacketMotionExData") -> bool:
        """
        Compare two PacketMotionExData instances for equality.

        Arguments:
            - other (PacketMotionExData): The other PacketMotionExData instance to compare with.

        Returns:
            bool: True if the two PacketMotionExData instances are equal, False otherwise.
        """

        if not isinstance(other, PacketMotionExData):
            return False

        return (
            self.m_header == other.m_header and
            self.m_suspensionPosition == other.m_suspensionPosition and
            self.m_suspensionVelocity == other.m_suspensionVelocity and
            self.m_suspensionAcceleration == other.m_suspensionAcceleration and
            self.m_wheelSpeed == other.m_wheelSpeed and
            self.m_wheelSlipRatio == other.m_wheelSlipRatio and
            self.m_wheelSlipAngle == other.m_wheelSlipAngle and
            self.m_wheelLatForce == other.m_wheelLatForce and
            self.m_wheelLongForce == other.m_wheelLongForce and
            self.m_heightOfCOGAboveGround == other.m_heightOfCOGAboveGround and
            self.m_localVelocityX == other.m_localVelocityX and
            self.m_localVelocityY == other.m_localVelocityY and
            self.m_localVelocityZ == other.m_localVelocityZ and
            self.m_angularVelocityX == other.m_angularVelocityX and
            self.m_angularVelocityY == other.m_angularVelocityY and
            self.m_angularVelocityZ == other.m_angularVelocityZ and
            self.m_angularAccelerationX == other.m_angularAccelerationX and
            self.m_angularAccelerationY == other.m_angularAccelerationY and
            self.m_angularAccelerationZ == other.m_angularAccelerationZ and
            self.m_frontWheelsAngle == other.m_frontWheelsAngle and
            self.m_wheelVertForce == other.m_wheelVertForce and
            self.m_frontAeroHeight == other.m_frontAeroHeight and
            self.m_rearAeroHeight == other.m_rearAeroHeight and
            self.m_frontRollAngle == other.m_frontRollAngle and
            self.m_rearRollAngle == other.m_rearRollAngle and
            self.m_chassisYaw == other.m_chassisYaw
        )

    def __ne__(self, other: "PacketMotionExData") -> bool:
        """
        Compare two PacketMotionExData instances for inequality.

        Arguments:
            - other (PacketMotionExData): The other PacketMotionExData instance to compare with.

        Returns:
            bool: True if the two PacketMotionExData instances are not equal, False otherwise.
        """

        return not self.__eq__(other)
