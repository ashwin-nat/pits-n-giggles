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

    """

    PACKET_FORMAT = ("<"
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
        "4f" # float         m_wheelVertForce[4];           // Vertical forces for each wheel
    )
    PACKET_LEN = struct.calcsize(PACKET_FORMAT)

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
        ) = struct.unpack(self.PACKET_FORMAT, data)

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
            f"Wheel Vertical Force: {str(self.m_wheelVertForce)}"
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
        }
        if include_header:
            json_data["header"] = self.m_header.toJSON()

        return json_data