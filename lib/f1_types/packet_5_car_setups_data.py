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
from typing import Dict, Any, List, Optional
from .common import _split_list, PacketHeader, _extract_sublist

# --------------------- CLASS DEFINITIONS --------------------------------------

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

    PACKET_FORMAT_23 = ("<"
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
        "B" # uint8     m_ballast;                  // Ballast
        "f" # float     m_fuelLoad;                 // Fuel load
    )
    PACKET_LEN_23 = struct.calcsize(PACKET_FORMAT_23)

    PACKET_FORMAT_24 = ("<"
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
        "B" # uint8     m_engineBraking;            // Engine braking (percentage)
        "f" # float     m_rearLeftTyrePressure;     // Rear left tyre pressure (PSI)
        "f" # float     m_rearRightTyrePressure;    // Rear right tyre pressure (PSI)
        "f" # float     m_frontLeftTyrePressure;    // Front left tyre pressure (PSI)
        "f" # float     m_frontRightTyrePressure;   // Front right tyre pressure (PSI)
        "B" # uint8     m_ballast;                  // Ballast
        "f" # float     m_fuelLoad;                 // Fuel load
    )
    PACKET_LEN_24 = struct.calcsize(PACKET_FORMAT_24)

    def __init__(self, data: bytes, game_year: int) -> None:
        """
        Initializes a CarSetupData object by unpacking the provided binary data.

        Parameters:
            data (bytes): Binary data to be unpacked.

        Raises:
            struct.error: If the binary data does not match the expected format.
        """

        self.m_gameYear = game_year
        if game_year == 23:
            unpacked_data = struct.unpack(self.PACKET_FORMAT_23, data)
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
            self.m_engineBraking = 0
        else:
            unpacked_data = struct.unpack(self.PACKET_FORMAT_24, data)
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
                self.m_engineBraking,
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
            "engine-braking": self.m_engineBraking,
            "rear-left-tyre-pressure": self.m_rearLeftTyrePressure,
            "rear-right-tyre-pressure": self.m_rearRightTyrePressure,
            "front-left-tyre-pressure": self.m_frontLeftTyrePressure,
            "front-right-tyre-pressure": self.m_frontRightTyrePressure,
            "ballast": self.m_ballast,
            "fuel-load": self.m_fuelLoad
        }

    def __eq__(self, other: "CarSetupData") -> bool:
        """
        Check if two CarSetupData objects are equal.

        Args:
            other (CarSetupData): The other CarSetupData object to compare with.

        Returns:
            bool: True if the objects are equal, False otherwise.
        """

        return (
            self.m_gameYear == other.m_gameYear and
            self.m_frontWing == other.m_frontWing and
            self.m_rearWing == other.m_rearWing and
            self.m_onThrottle == other.m_onThrottle and
            self.m_offThrottle == other.m_offThrottle and
            self.m_frontCamber == other.m_frontCamber and
            self.m_rearCamber == other.m_rearCamber and
            self.m_frontToe == other.m_frontToe and
            self.m_rearToe == other.m_rearToe and
            self.m_frontSuspension == other.m_frontSuspension and
            self.m_rearSuspension == other.m_rearSuspension and
            self.m_frontAntiRollBar == other.m_frontAntiRollBar and
            self.m_rearAntiRollBar == other.m_rearAntiRollBar and
            self.m_frontSuspensionHeight == other.m_frontSuspensionHeight and
            self.m_rearSuspensionHeight == other.m_rearSuspensionHeight and
            self.m_brakePressure == other.m_brakePressure and
            self.m_brakeBias == other.m_brakeBias and
            self.m_rearLeftTyrePressure == other.m_rearLeftTyrePressure and
            self.m_rearRightTyrePressure == other.m_rearRightTyrePressure and
            self.m_frontLeftTyrePressure == other.m_frontLeftTyrePressure and
            self.m_frontRightTyrePressure == other.m_frontRightTyrePressure and
            self.m_ballast == other.m_ballast and
            self.m_fuelLoad == other.m_fuelLoad
        )

    def __ne__(self, other: "CarSetupData") -> bool:
        """
        Check if two CarSetupData objects are not equal.

        Args:
            other (CarSetupData): The other CarSetupData object to compare with.

        Returns:
            bool: True if the objects are not equal, False otherwise.
        """

        return not self.__eq__(other)

    def to_bytes(self) -> bytes:
        """
        Convert the CarSetupData object to bytes.

        Returns:
            bytes: Bytes representation of the CarSetupData object.
        """

        if self.m_gameYear == 23:
            return struct.pack(self.PACKET_FORMAT_23,
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
                self.m_fuelLoad
            )
        if self.m_gameYear == 24:
            return struct.pack(self.PACKET_FORMAT_24,
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
                self.m_engineBraking,
                self.m_rearLeftTyrePressure,
                self.m_rearRightTyrePressure,
                self.m_frontLeftTyrePressure,
                self.m_frontRightTyrePressure,
                self.m_ballast,
                self.m_fuelLoad
            )

        raise NotImplementedError(f"Invalid game year: {self.m_gameYear}")

    @classmethod
    def from_values(cls, game_year: int,
                    front_wing: int,
                    rear_wing: int,
                    on_throttle: int,
                    off_throttle: int,
                    front_camber: float,
                    rear_camber: float,
                    front_toe: float,
                    rear_toe: float,
                    front_suspension: int,
                    rear_suspension: int,
                    front_anti_roll_bar: int,
                    rear_anti_roll_bar: int,
                    front_suspension_height: int,
                    rear_suspension_height: int,
                    brake_pressure: int,
                    brake_bias: int,
                    rear_left_tyre_pressure: float,
                    rear_right_tyre_pressure: float,
                    front_left_tyre_pressure: float,
                    front_right_tyre_pressure: float,
                    ballast: int,
                    fuel_load: float,
                    engine_braking: Optional[int] = 0) -> "CarSetupData":
        """
        Create a CarSetupData object from values.

        Args:
            Too many to document for a test method

        Returns:
            CarSetupData: The created CarSetupData object.
        """

        if game_year == 23:
            raw_packet = struct.pack(cls.PACKET_FORMAT_23,
                front_wing,
                rear_wing,
                on_throttle,
                off_throttle,
                front_camber,
                rear_camber,
                front_toe,
                rear_toe,
                front_suspension,
                rear_suspension,
                front_anti_roll_bar,
                rear_anti_roll_bar,
                front_suspension_height,
                rear_suspension_height,
                brake_pressure,
                brake_bias,
                rear_left_tyre_pressure,
                rear_right_tyre_pressure,
                front_left_tyre_pressure,
                front_right_tyre_pressure,
                ballast,
                fuel_load
            )
            return cls(raw_packet, game_year)

        if game_year == 24:
            raw_packet = struct.pack(cls.PACKET_FORMAT_24,
                front_wing,
                rear_wing,
                on_throttle,
                off_throttle,
                front_camber,
                rear_camber,
                front_toe,
                rear_toe,
                front_suspension,
                rear_suspension,
                front_anti_roll_bar,
                rear_anti_roll_bar,
                front_suspension_height,
                rear_suspension_height,
                brake_pressure,
                brake_bias,
                engine_braking,
                rear_left_tyre_pressure,
                rear_right_tyre_pressure,
                front_left_tyre_pressure,
                front_right_tyre_pressure,
                ballast,
                fuel_load
            )
            return cls(raw_packet, game_year)
        raise NotImplementedError(f"Invalid game year: {game_year}")

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

        packet_len = CarSetupData.PACKET_LEN_23 if (header.m_gameYear == 23) else CarSetupData.PACKET_LEN_24
        if header.m_gameYear == 23:
            packet_len = CarSetupData.PACKET_LEN_23
            car_setups_raw_data = _split_list(packet, packet_len)
            self.m_nextFrontWingValue: float = 0.0
        else: # 24
            packet_len = CarSetupData.PACKET_LEN_24
            car_setups_raw_data = _extract_sublist(packet, 0, packet_len*22)
            car_setups_raw_data = _split_list(car_setups_raw_data, packet_len)
            self.m_nextFrontWingValue: float = struct.unpack("<f", packet[packet_len*22:])[0]
        for setup_per_car_raw_data in car_setups_raw_data:
            self.m_carSetups.append(CarSetupData(setup_per_car_raw_data, header.m_gameYear))

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

    def __eq__(self, other: Any) -> bool:
        """
        Checks if two PacketCarSetupData objects are equal.

        Arguments:
            other (Any): The object to compare with.

        Returns:
            bool: True if the objects are equal, False otherwise.
        """

        if not isinstance(other, PacketCarSetupData):
            return False

        return (
            self.m_header == other.m_header and
            self.m_carSetups == other.m_carSetups and
            self.m_nextFrontWingValue == other.m_nextFrontWingValue
        )

    def __ne__(self, other: Any) -> bool:
        """
        Checks if two PacketCarSetupData objects are not equal.

        Arguments:
            other (Any): The object to compare with.

        Returns:
            bool: True if the objects are not equal, False otherwise.
        """

        return not self.__eq__(other)

    def to_bytes(self) -> bytes:
        """
        Convert the PacketCarSetupData object to bytes.

        Returns:
            bytes: Bytes representation of the object.
        """

        raw_packet = self.m_header.to_bytes() + b''.join(setup.to_bytes() for setup in self.m_carSetups)
        if self.m_header.m_gameYear != 23:
            raw_packet += struct.pack("<f", self.m_nextFrontWingValue)
        return raw_packet

    @classmethod
    def from_values(cls,
                    header: PacketHeader,
                    car_setups: List[CarSetupData],
                    next_front_wing_value: Optional[float] = 0.0) -> "PacketCarSetupData":
        """
        Create a PacketCarSetupData object from values.

        Args:
            header (PacketHeader): The header of the telemetry packet.
            car_setups (List[CarSetupData]): List of CarSetupData objects containing data for all cars on track.
            next_front_wing_value (float, optional): The next front wing value. Defaults to 0.0.

        Returns:
            PacketCarSetupData: A PacketCarSetupData object initialized with the provided values.
        """

        if header.m_gameYear == 23:
            raw_bytes = b''.join([setup.to_bytes() for setup in car_setups])
            return cls(header, raw_bytes)
        if header.m_gameYear == 24:
            raw_bytes = b''.join([setup.to_bytes() for setup in car_setups])
            raw_bytes += struct.pack("<f", next_front_wing_value)
            return cls(header, raw_bytes)
        raise NotImplementedError(f"Unsupported game year: {header.m_gameYear}")
