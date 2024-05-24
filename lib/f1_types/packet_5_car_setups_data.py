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
from .common import _split_list, PacketHeader

# --------------------- CLASS DEFINITIONS --------------------------------------

class PacketCarSetupData:
    """
    A class representing the setup data for all cars in a racing simulation.

    Attributes:
        m_header (PacketHeader): Header containing general information about the packet.
        m_carSetups (List[CarSetupData]): List of CarSetupData objects representing the setup information
            for each car in the race.

            Note:
                The length of m_carSetups should not exceed the maximum number of participants.
    """

    def __init__(self, header: PacketHeader, packet: bytes) -> None:
        """
        Initializes a PacketCarSetupData object by unpacking the provided binary data.

        Parameters:
            header (PacketHeader): Header containing general information about the packet.
            packet (bytes): Binary data to be unpacked.

        Raises:
            struct.error: If the binary data does not match the expected format.
        """

        self.m_header: PacketHeader = header
        self.m_carSetups: List[CarSetupData] = []

        for setup_per_car_raw_data in _split_list(packet, CarSetupData.PACKET_LEN):
            self.m_carSetups.append(CarSetupData(setup_per_car_raw_data))

    def __str__(self) -> str:
        """
        Returns a string representation of the PacketCarSetupData object.

        Returns:
            str: String representation of the object.
        """

        setups_str = ", ".join(str(setup) for setup in self.m_carSetups)
        return f"PacketCarSetupData(Header: {str(self.m_header)}, Car Setups: [{setups_str}])"

    def toJSON(self, include_header: bool=False) -> Dict[str, Any]:
        """
        Convert the PacketCarSetupData instance to a JSON-compatible dictionary.

        Arguments:
            - include_header - Whether the header dump must be included in the JSON

        Returns:
            Dict[str, Any]: JSON-compatible dictionary representing the PacketCarSetupData instance.
        """

        json_data = {
            "car-setups": [car_setup.toJSON() for car_setup in self.m_carSetups]
        }
        if include_header:
            json_data["header"] = self.m_header.toJSON()
        return json_data

class CarSetupData:
    """
    A class representing the setup data for a car in a racing simulation.

    Attributes:
        m_frontWing (int): Front wing aero.
        m_rearWing (int): Rear wing aero.
        m_onThrottle (int): Differential adjustment on throttle (percentage).
        m_offThrottle (int): Differential adjustment off throttle (percentage).
        m_frontCamber (float): Front camber angle (suspension geometry).
        m_rearCamber (float): Rear camber angle (suspension geometry).
        m_frontToe (float): Front toe angle (suspension geometry).
        m_rearToe (float): Rear toe angle (suspension geometry).
        m_frontSuspension (int): Front suspension.
        m_rearSuspension (int): Rear suspension.
        m_frontAntiRollBar (int): Front anti-roll bar.
        m_rearAntiRollBar (int): Rear anti-roll bar.
        m_frontSuspensionHeight (int): Front ride height.
        m_rearSuspensionHeight (int): Rear ride height.
        m_brakePressure (int): Brake pressure (percentage).
        m_brakeBias (int): Brake bias (percentage).
        m_rearLeftTyrePressure (float): Rear left tyre pressure (PSI).
        m_rearRightTyrePressure (float): Rear right tyre pressure (PSI).
        m_frontLeftTyrePressure (float): Front left tyre pressure (PSI).
        m_frontRightTyrePressure (float): Front right tyre pressure (PSI).
        m_ballast (int): Ballast.
        m_fuelLoad (float): Fuel load.
    """

    PACKET_FORMAT = ("<"
        "B" # uint8     m_frontWing;                // Front wing aero
        "B" # uint8     m_rearWing;                 // Rear wing aero
        "B" # uint8     m_onThrottle;               // Differential adjustment on throttle (percentage)
        "B" # uint8     m_offThrottle;              // Differential adjustment off throttle (percentage)
        "f" # float     m_frontCamber;              // Front camber angle (suspension geometry)
        "f" # float     m_rearCamber;               // Rear camber angle (suspension geometry)
        "f" # float     m_frontToe;                 // Front toe angle (suspension geometry)
        "f" # float     m_rearToe;                  // Rear toe angle (suspension geometry)
        "B" # uint8     m_frontSuspension;          // Front suspension
        "B" # uint8     m_rearSuspension;           // Rear suspension
        "B" # uint8     m_frontAntiRollBar;         // Front anti-roll bar
        "B" # uint8     m_rearAntiRollBar;          // Front anti-roll bar
        "B" # uint8     m_frontSuspensionHeight;    // Front ride height
        "B" # uint8     m_rearSuspensionHeight;     // Rear ride height
        "B" # uint8     m_brakePressure;            // Brake pressure (percentage)
        "B" # uint8     m_brakeBias;                // Brake bias (percentage)
        "f" # float     m_rearLeftTyrePressure;     // Rear left tyre pressure (PSI)
        "f" # float     m_rearRightTyrePressure;    // Rear right tyre pressure (PSI)
        "f" # float     m_frontLeftTyrePressure;    // Front left tyre pressure (PSI)
        "f" # float     m_frontRightTyrePressure;   // Front right tyre pressure (PSI)
        "f" # uint8     m_ballast;                  // Ballast
        "B" # float     m_fuelLoad;                 // Fuel load
    )
    PACKET_LEN = struct.calcsize(PACKET_FORMAT)

    def __init__(self, data: bytes) -> None:
        """
        Initializes a CarSetupData object by unpacking the provided binary data.

        Parameters:
            data (bytes): Binary data to be unpacked.

        Raises:
            struct.error: If the binary data does not match the expected format.
        """
        unpacked_data = struct.unpack(self.PACKET_FORMAT, data)

        (
            self.m_frontWing,
            self.m_rearWing,
            self.m_onThrottle,
            self.m_offThrottle,
            self.m_frontCamber,
            self.m_rearCamber,
            self.m_frontToe,
            self.m_rearToe,
            self.m_frontSuspension,
            self.m_rearSuspension,
            self.m_frontAntiRollBar,
            self.m_rearAntiRollBar,
            self.m_frontSuspensionHeight,
            self.m_rearSuspensionHeight,
            self.m_brakePressure,
            self.m_brakeBias,
            self.m_rearLeftTyrePressure,
            self.m_rearRightTyrePressure,
            self.m_frontLeftTyrePressure,
            self.m_frontRightTyrePressure,
            self.m_ballast,
            self.m_fuelLoad,
        ) = unpacked_data

    def __str__(self) -> str:
        """
        Returns a string representation of the CarSetupData object.

        Returns:
            str: String representation of the object.
        """

        return (
            f"CarSetupData(\n"
            f"  Front Wing: {self.m_frontWing}\n"
            f"  Rear Wing: {self.m_rearWing}\n"
            f"  On Throttle: {self.m_onThrottle}\n"
            f"  Off Throttle: {self.m_offThrottle}\n"
            f"  Front Camber: {self.m_frontCamber}\n"
            f"  Rear Camber: {self.m_rearCamber}\n"
            f"  Front Toe: {self.m_frontToe}\n"
            f"  Rear Toe: {self.m_rearToe}\n"
            f"  Front Suspension: {self.m_frontSuspension}\n"
            f"  Rear Suspension: {self.m_rearSuspension}\n"
            f"  Front Anti-Roll Bar: {self.m_frontAntiRollBar}\n"
            f"  Rear Anti-Roll Bar: {self.m_rearAntiRollBar}\n"
            f"  Front Suspension Height: {self.m_frontSuspensionHeight}\n"
            f"  Rear Suspension Height: {self.m_rearSuspensionHeight}\n"
            f"  Brake Pressure: {self.m_brakePressure}\n"
            f"  Brake Bias: {self.m_brakeBias}\n"
            f"  Rear Left Tyre Pressure: {self.m_rearLeftTyrePressure}\n"
            f"  Rear Right Tyre Pressure: {self.m_rearRightTyrePressure}\n"
            f"  Front Left Tyre Pressure: {self.m_frontLeftTyrePressure}\n"
            f"  Front Right Tyre Pressure: {self.m_frontRightTyrePressure}\n"
            f"  Ballast: {self.m_ballast}\n"
            f"  Fuel Load: {self.m_fuelLoad}\n"
            f")"
        )

    def toJSON(self) -> Dict[str, Any]:
        """
        Convert the CarSetupData instance to a JSON-compatible dictionary.

        Returns:
            Dict[str, Any]: JSON-compatible dictionary representing the CarSetupData instance.
        """

        return {
            "front-wing": self.m_frontWing,
            "rear-wing": self.m_rearWing,
            "on-throttle": self.m_onThrottle,
            "off-throttle": self.m_offThrottle,
            "front-camber": self.m_frontCamber,
            "rear-camber": self.m_rearCamber,
            "front-toe": self.m_frontToe,
            "rear-toe": self.m_rearToe,
            "front-suspension": self.m_frontSuspension,
            "rear-suspension": self.m_rearSuspension,
            "front-anti-roll-bar": self.m_frontAntiRollBar,
            "rear-anti-roll-bar": self.m_rearAntiRollBar,
            "front-suspension-height": self.m_frontSuspensionHeight,
            "rear-suspension-height": self.m_rearSuspensionHeight,
            "brake-pressure": self.m_brakePressure,
            "brake-bias": self.m_brakeBias,
            "rear-left-tyre-pressure": self.m_rearLeftTyrePressure,
            "rear-right-tyre-pressure": self.m_rearRightTyrePressure,
            "front-left-tyre-pressure": self.m_frontLeftTyrePressure,
            "front-right-tyre-pressure": self.m_frontRightTyrePressure,
            "ballast": self.m_ballast,
            "fuel-load": self.m_fuelLoad
        }
