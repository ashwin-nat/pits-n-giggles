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
from typing import Dict, Any, List
from .common import _validate_parse_fixed_segments
from .header import PacketHeader
from .base_pkt import F1PacketBase, F1SubPacketBase

# --------------------- CLASS DEFINITIONS --------------------------------------

class CarTelemetryData(F1SubPacketBase):
    """
    A class representing telemetry data for a single car in a racing simulation.

    Attributes:
        m_speed (int): Speed of the car in kilometers per hour.
        m_throttle (float): Amount of throttle applied (0.0 to 1.0).
        m_steer (float): Steering value (-1.0 (full lock left) to 1.0 (full lock right)).
        m_brake (float): Amount of brake applied (0.0 to 1.0).
        m_clutch (int): Amount of clutch applied (0 to 100).
        m_gear (int): Gear selected (1-8, N=0, R=-1).
        m_engineRPM (int): Engine RPM.
        m_drs (int): DRS (Drag Reduction System) state (0 = off, 1 = on).
        m_revLightsPercent (int): Rev lights indicator (percentage).
        m_revLightsBitValue (int): Rev lights represented as a bitfield.
        m_brakesTemperature (List[int]): List of brake temperatures (celsius) for each wheel.
        m_tyresSurfaceTemperature (List[int]): List of surface temperatures (celsius) for each tyre.
        m_tyresInnerTemperature (List[int]): List of inner temperatures (celsius) for each tyre.
        m_engineTemperature (int): Engine temperature (celsius).
        m_tyresPressure (List[float]): List of tyre pressures (PSI) for each tyre.
        m_surfaceType (List[int]): List of surface types for each wheel, see appendices.

            Note:
                The length of each list attribute should be 4, corresponding to the four wheels of the car.
    """

    COMPILED_PACKET_STRUCT = struct.Struct("<"
        "H" # uint16    m_speed;                    // Speed of car in kilometres per hour
        "f" # float     m_throttle;                 // Amount of throttle applied (0.0 to 1.0)
        "f" # float     m_steer;                    // Steering (-1.0 (full lock left) to 1.0 (full lock right))
        "f" # float     m_brake;                    // Amount of brake applied (0.0 to 1.0)
        "B" # uint8     m_clutch;                   // Amount of clutch applied (0 to 100)
        "b" # int8      m_gear;                     // Gear selected (1-8, N=0, R=-1)
        "H" # uint16    m_engineRPM;                // Engine RPM
        "B" # uint8     m_drs;                      // 0 = off, 1 = on
        "B" # uint8     m_revLightsPercent;         // Rev lights indicator (percentage)
        "H" # uint16    m_revLightsBitValue;        // Rev lights (bit 0 = leftmost LED, bit 14 = rightmost LED)
        "4H" # uint16    m_brakesTemperature[4];     // Brakes temperature (celsius)
        "4B" # uint8     m_tyresSurfaceTemperature[4]; // Tyres surface temperature (celsius)
        "4B" # uint8     m_tyresInnerTemperature[4]; // Tyres inner temperature (celsius)
        "H" # uint16    m_engineTemperature;        // Engine temperature (celsius)
        "4f" # float     m_tyresPressure[4];         // Tyres pressure (PSI)
        "4B" # uint8     m_surfaceType[4];           // Driving surface, see appendices
    )
    PACKET_LEN = COMPILED_PACKET_STRUCT.size

    __slots__ = (
        "m_speed",
        "m_throttle",
        "m_steer",
        "m_brake",
        "m_clutch",
        "m_gear",
        "m_engineRPM",
        "m_drs",
        "m_revLightsPercent",
        "m_revLightsBitValue",
        "m_brakesTemperature",
        "m_tyresSurfaceTemperature",
        "m_tyresInnerTemperature",
        "m_engineTemperature",
        "m_tyresPressure",
        "m_surfaceType",
    )

    def __init__(self, data) -> None:
        """
        Initializes a CarTelemetryData object by unpacking the provided binary data.

        Parameters:
            data (bytes): Binary data to be unpacked.

        Raises:
            struct.error: If the binary data does not match the expected format.
        """
        self.m_brakesTemperature = [0] * 4
        self.m_tyresSurfaceTemperature = [0] * 4
        self.m_tyresInnerTemperature = [0] * 4
        self.m_tyresPressure = [0] * 4
        self.m_surfaceType = [0] * 4

        (
            self.m_speed,
            self.m_throttle,
            self.m_steer,
            self.m_brake,
            self.m_clutch,
            self.m_gear,
            self.m_engineRPM,
            self.m_drs,
            self.m_revLightsPercent,
            self.m_revLightsBitValue,
            self.m_brakesTemperature[0],
            self.m_brakesTemperature[1],
            self.m_brakesTemperature[2],
            self.m_brakesTemperature[3],
            self.m_tyresSurfaceTemperature[0],
            self.m_tyresSurfaceTemperature[1],
            self.m_tyresSurfaceTemperature[2],
            self.m_tyresSurfaceTemperature[3],
            self.m_tyresInnerTemperature[0],
            self.m_tyresInnerTemperature[1],
            self.m_tyresInnerTemperature[2],
            self.m_tyresInnerTemperature[3],
            self.m_engineTemperature,
            self.m_tyresPressure[0],
            self.m_tyresPressure[1],
            self.m_tyresPressure[2],
            self.m_tyresPressure[3],
            self.m_surfaceType[0],
            self.m_surfaceType[1],
            self.m_surfaceType[2],
            self.m_surfaceType[3],
        ) = self.COMPILED_PACKET_STRUCT.unpack(data)

        self.m_drs = bool(self.m_drs)

    def __str__(self) -> str:
        """
        Returns a string representation of the CarTelemetryData object.

        Returns:
            str: String representation of the object.
        """
        return (
            f"CarTelemetryData("
            f"Speed: {self.m_speed}, "
            f"Throttle: {self.m_throttle}, "
            f"Steer: {self.m_steer}, "
            f"Brake: {self.m_brake}, "
            f"Clutch: {self.m_clutch}, "
            f"Gear: {self.m_gear}, "
            f"Engine RPM: {self.m_engineRPM}, "
            f"DRS: {self.m_drs}, "
            f"Rev Lights Percent: {self.m_revLightsPercent}, "
            f"Brakes Temperature: {str(self.m_brakesTemperature)}, "
            f"Tyres Surface Temperature: {str(self.m_tyresSurfaceTemperature)}, "
            f"Tyres Inner Temperature: {str(self.m_tyresInnerTemperature)}, "
            f"Engine Temperature: {str(self.m_engineTemperature)}, "
            f"Tyres Pressure: {str(self.m_tyresPressure)})"
        )

    def toJSON(self) -> Dict[str, Any]:
        """
        Convert the CarTelemetryData instance to a JSON-compatible dictionary.

        Returns:
            Dict[str, Any]: JSON-compatible dictionary representing the CarTelemetryData instance.
        """

        return {
            "speed": self.m_speed,
            "throttle": self.m_throttle,
            "steer": self.m_steer,
            "brake": self.m_brake,
            "clutch": self.m_clutch,
            "gear": self.m_gear,
            "engine-rpm": self.m_engineRPM,
            "drs": self.m_drs,
            "rev-lights-percent": self.m_revLightsPercent,
            "brakes-temperature": self.m_brakesTemperature,
            "tyres-surface-temperature": self.m_tyresSurfaceTemperature,
            "tyres-inner-temperature": self.m_tyresInnerTemperature,
            "engine-temperature": self.m_engineTemperature,
            "tyres-pressure": self.m_tyresPressure,
            "surface-type": self.m_surfaceType,
        }

    def __eq__(self, other: "CarTelemetryData") -> bool:
        """
        Checks if two CarTelemetryData objects are equal.

        Args:
            other (CarTelemetryData): The other CarTelemetryData object to compare with.

        Returns:
            bool: True if the objects are equal, False otherwise.
        """

        if not isinstance(other, CarTelemetryData):
            return False
        return (
            self.m_speed == other.m_speed
            and self.m_throttle == other.m_throttle
            and self.m_steer == other.m_steer
            and self.m_brake == other.m_brake
            and self.m_clutch == other.m_clutch
            and self.m_gear == other.m_gear
            and self.m_engineRPM == other.m_engineRPM
            and self.m_drs == other.m_drs
            and self.m_revLightsPercent == other.m_revLightsPercent
            and self.m_revLightsBitValue == other.m_revLightsBitValue
            and self.m_brakesTemperature == other.m_brakesTemperature
            and self.m_tyresSurfaceTemperature == other.m_tyresSurfaceTemperature
            and self.m_tyresInnerTemperature == other.m_tyresInnerTemperature
            and self.m_engineTemperature == other.m_engineTemperature
            and self.m_tyresPressure == other.m_tyresPressure
            and self.m_surfaceType == other.m_surfaceType
        )

    def __ne__(self, other: "CarTelemetryData") -> bool:
        """
        Checks if two CarTelemetryData objects are not equal.

        Args:
            other (CarTelemetryData): The other CarTelemetryData object to compare with.

        Returns:
            bool: True if the objects are not equal, False otherwise.
        """
        return not self.__eq__(other)

    def to_bytes(self) -> bytes:
        """
        Convert the CarTelemetryData object to bytes.

        Returns:
            bytes: Bytes representation of the CarTelemetryData object.
        """
        return self.COMPILED_PACKET_STRUCT.pack(
            self.m_speed,
            self.m_throttle,
            self.m_steer,
            self.m_brake,
            self.m_clutch,
            self.m_gear,
            self.m_engineRPM,
            self.m_drs,
            self.m_revLightsPercent,
            self.m_revLightsBitValue,
            self.m_brakesTemperature[0],
            self.m_brakesTemperature[1],
            self.m_brakesTemperature[2],
            self.m_brakesTemperature[3],
            self.m_tyresSurfaceTemperature[0],
            self.m_tyresSurfaceTemperature[1],
            self.m_tyresSurfaceTemperature[2],
            self.m_tyresSurfaceTemperature[3],
            self.m_tyresInnerTemperature[0],
            self.m_tyresInnerTemperature[1],
            self.m_tyresInnerTemperature[2],
            self.m_tyresInnerTemperature[3],
            self.m_engineTemperature,
            self.m_tyresPressure[0],
            self.m_tyresPressure[1],
            self.m_tyresPressure[2],
            self.m_tyresPressure[3],
            self.m_surfaceType[0],
            self.m_surfaceType[1],
            self.m_surfaceType[2],
            self.m_surfaceType[3]
        )

    @classmethod
    def from_values(cls,
        speed: int,
        throttle: int,
        steer: int,
        brake: int,
        clutch: int,
        gear: int,
        engine_rpm: int,
        drs: bool,
        rev_lights_percent: int,
        rev_lights_bit_value: int,
        brakes_temperature_0: int,
        brakes_temperature_1: int,
        brakes_temperature_2: int,
        brakes_temperature_3: int,
        tyres_surface_temperature_0: int,
        tyres_surface_temperature_1: int,
        tyres_surface_temperature_2: int,
        tyres_surface_temperature_3: int,
        tyres_inner_temperature_0: int,
        tyres_inner_temperature_1: int,
        tyres_inner_temperature_2: int,
        tyres_inner_temperature_3: int,
        engine_temperature: int,
        tyres_pressure_0: float,
        tyres_pressure_1: float,
        tyres_pressure_2: float,
        tyres_pressure_3: float,
        surface_type_0: int,
        surface_type_1: int,
        surface_type_2: int,
        surface_type_3: int) -> "CarTelemetryData":
        """
        Create a new CarTelemetryData object from the provided values.

        Args:
            Too many to document for a test method

        Returns:
            CarTelemetryData: A new CarTelemetryData object with the provided values.
        """
        return cls(cls.COMPILED_PACKET_STRUCT.pack(
            speed,
            throttle,
            steer,
            brake,
            clutch,
            gear,
            engine_rpm,
            drs,
            rev_lights_percent,
            rev_lights_bit_value,
            brakes_temperature_0,
            brakes_temperature_1,
            brakes_temperature_2,
            brakes_temperature_3,
            tyres_surface_temperature_0,
            tyres_surface_temperature_1,
            tyres_surface_temperature_2,
            tyres_surface_temperature_3,
            tyres_inner_temperature_0,
            tyres_inner_temperature_1,
            tyres_inner_temperature_2,
            tyres_inner_temperature_3,
            engine_temperature,
            tyres_pressure_0,
            tyres_pressure_1,
            tyres_pressure_2,
            tyres_pressure_3,
            surface_type_0,
            surface_type_1,
            surface_type_2,
            surface_type_3
        ))

class PacketCarTelemetryData(F1PacketBase):
    """
    A class representing telemetry data for multiple cars in a racing simulation.

    Attributes:
        m_header (PacketHeader): Header information for the telemetry data.
        m_carTelemetryData (List[CarTelemetryData]): List of CarTelemetryData objects for each car.
        m_mfdPanelIndex (int): Index of MFD (Multi-Function Display) panel open.
            - 255: MFD closed (Single player, race)
            - 0: Car setup
            - 1: Pits
            - 2: Damage
            - 3: Engine
            - 4: Temperatures
            May vary depending on the game mode.
        m_mfdPanelIndexSecondaryPlayer (int): Secondary player's MFD panel index. See m_mfdPanelIndex for details.
        m_suggestedGear (int): Suggested gear for the player (1-8), 0 if no gear is suggested.
    """

    MAX_CARS = 22
    COMPILED_PACKET_FORMAT_EXTRA = struct.Struct("<BBb")
    PACKET_LEN_EXTRA = COMPILED_PACKET_FORMAT_EXTRA.size

    __slots__ = (
        "m_carTelemetryData",
        "m_mfdPanelIndex",
        "m_mfdPanelIndexSecondaryPlayer",
        "m_suggestedGear"
    )

    def __init__(self, header:PacketHeader, packet: bytes) -> None:
        """
        Initializes a PacketCarTelemetryData object by unpacking the provided binary data.

        Parameters:
            header (PacketHeader): Header information for the telemetry data.
            packet (bytes): Binary data to be unpacked.

        Raises:
            struct.error: If the binary data does not match the expected format.
        """

        super().__init__(header)
        self.m_carTelemetryData: List[CarTelemetryData]

        self.m_carTelemetryData, offset_so_far = _validate_parse_fixed_segments(
            data=packet,
            offset=0,
            item_cls=CarTelemetryData,
            item_len=CarTelemetryData.PACKET_LEN,
            count=self.MAX_CARS,
            max_count=self.MAX_CARS
        )

        self.m_mfdPanelIndex, self.m_mfdPanelIndexSecondaryPlayer, self.m_suggestedGear = \
                self.COMPILED_PACKET_FORMAT_EXTRA.unpack(packet[offset_so_far:])

    def __str__(self) -> str:
        """
        Returns a string representation of the PacketCarTelemetryData object.

        Returns:
            str: String representation of the object.
        """

        telemetry_data_str = ", ".join(str(telemetry) for telemetry in self.m_carTelemetryData)
        mfd_panel_index_to_string_dict = {
            255: "MFD closed Single player, race",
            0: "Car setup",
            1: "Pits",
            2: "Damage",
            3: "Engine",
            4: "Temperatures",
        }
        mfd_panel_string = mfd_panel_index_to_string_dict.get(self.m_mfdPanelIndex, str(self.m_mfdPanelIndex))
        mfd_panel_string_secondary = mfd_panel_index_to_string_dict.get(self.m_mfdPanelIndexSecondaryPlayer,
                                                                        str(self.m_mfdPanelIndexSecondaryPlayer))
        return (
            f"PacketCarTelemetryData("
            f"Header: {str(self.m_header)}, "
            f"Car Telemetry Data: [{telemetry_data_str}], "
            f"MFD Panel Index: {mfd_panel_string}), "
            f"MFD Panel Index Secondary: {mfd_panel_string_secondary}), "
            f"Suggested Gear: {self.m_suggestedGear}"
        )

    def toJSON(self, include_header: bool=False) -> Dict[str, Any]:
        """
        Convert the PacketCarTelemetryData instance to a JSON-compatible dictionary.

        Arguments:
            - include_header - Whether the header dump must be included in the JSON

        Returns:
            Dict[str, Any]: JSON-compatible dictionary representing the PacketCarTelemetryData instance.
        """

        json_data = {
            "car-telemetry-data": [telemetry.toJSON() for telemetry in self.m_carTelemetryData],
            "mfd-panel-index": self.m_mfdPanelIndex,
            "mfd-panel-index-secondary": self.m_mfdPanelIndexSecondaryPlayer,
            "suggested-gear": self.m_suggestedGear
        }
        if include_header:
            json_data["header"] = self.m_header.toJSON()
        return json_data

    def __eq__(self, other: "PacketCarTelemetryData") -> bool:
        """
        Checks if two PacketCarTelemetryData objects are equal.

        Parameters:
            other (PacketCarTelemetryData): The other PacketCarTelemetryData object.

        Returns:
            bool: True if the objects are equal, False otherwise.
        """

        if not isinstance(other, PacketCarTelemetryData):
            return False

        return (
            self.m_header == other.m_header and
            self.m_carTelemetryData == other.m_carTelemetryData and
            self.m_mfdPanelIndex == other.m_mfdPanelIndex and
            self.m_mfdPanelIndexSecondaryPlayer == other.m_mfdPanelIndexSecondaryPlayer and
            self.m_suggestedGear == other.m_suggestedGear
        )

    def __ne__(self, other: "PacketCarTelemetryData") -> bool:
        """
        Checks if two PacketCarTelemetryData objects are not equal.

        Parameters:
            other (PacketCarTelemetryData): The other PacketCarTelemetryData object.

        Returns:
            bool: True if the objects are not equal, False otherwise.
        """

        return not self.__eq__(other)

    def to_bytes(self) -> bytes:
        """
        Convert the PacketCarTelemetryData instance to bytes.

        Returns:
            bytes: Bytes representation of the PacketCarTelemetryData instance.
        """

        raw_bytes = self.m_header.to_bytes()
        raw_bytes += b''.join([telemetry.to_bytes() for telemetry in self.m_carTelemetryData])
        raw_bytes += struct.pack("<BBb",
                                 self.m_mfdPanelIndex, self.m_mfdPanelIndexSecondaryPlayer, self.m_suggestedGear)
        return raw_bytes

    @classmethod
    def from_values(cls,
                     header: PacketHeader,
                     car_telemetry_data: List[CarTelemetryData],
                     mfd_panel_index: int,
                     mfd_panel_index_secondary_player: int,
                     suggested_gear: int) -> "PacketCarTelemetryData":
        """
        Create a PacketCarTelemetryData object from values.

        Args:
            header (PacketHeader): The header of the telemetry packet.
            car_telemetry_data (List[CarTelemetryData]): List of CarTelemetryData objects.
            mfd_panel_index (int): Index of the MFD panel.
            mfd_panel_index_secondary_player (int): Index of the MFD panel for the secondary player.
            suggested_gear (int): Suggested gear for the car.

        Returns:
            PacketCarTelemetryData: A new PacketCarTelemetryData object.
        """

        raw_bytes = b''.join([telemetry.to_bytes() for telemetry in car_telemetry_data])
        raw_bytes += struct.pack("<BBb",
                                 mfd_panel_index, mfd_panel_index_secondary_player, suggested_gear)
        return cls(header, raw_bytes)
