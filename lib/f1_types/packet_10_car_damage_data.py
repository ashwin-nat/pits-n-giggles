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
from typing import List, Dict, Any
from .common import PacketHeader

# --------------------- CLASS DEFINITIONS --------------------------------------

class CarDamageData:
    """
    Class representing the packet for car damage data.

    Attributes:
        m_tyresWear (List[float]): List of tyre wear percentages for each tyre.
        m_tyresDamage (List[int]): List of tyre damage percentages for each tyre.
        m_brakesDamage (List[int]): List of brake damage percentages for each brake.
        m_tyresBlisters (List[int]): List of tyre blister percentages for each tyre.
        m_frontLeftWingDamage (int): Front left wing damage percentage.
        m_frontRightWingDamage (int): Front right wing damage percentage.
        m_rearWingDamage (int): Rear wing damage percentage.
        m_floorDamage (int): Floor damage percentage.
        m_diffuserDamage (int): Diffuser damage percentage.
        m_sidepodDamage (int): Sidepod damage percentage.
        m_drsFault (bool): Indicator for DRS fault
        m_ersFault (bool): Indicator for ERS fault
        m_gearBoxDamage (int): Gearbox damage percentage.
        m_engineDamage (int): Engine damage percentage.
        m_engineMGUHWear (int): Engine wear MGU-H percentage.
        m_engineESWear (int): Engine wear ES percentage.
        m_engineCEWear (int): Engine wear CE percentage.
        m_engineICEWear (int): Engine wear ICE percentage.
        m_engineMGUKWear (int): Engine wear MGU-K percentage.
        m_engineTCWear (int): Engine wear TC percentage.
        m_engineBlown (bool): Engine blown, 0 = OK, 1 = fault.
        m_engineSeized (bool): Engine seized, 0 = OK, 1 = fault.

    Note:
        The class is designed to parse and represent the car damage data packet.
    """

    PACKET_FORMAT = ("<"
        "4f" # float     m_tyresWear[4];                     // Tyre wear (percentage)
        "4B" # uint8     m_tyresDamage[4];                   // Tyre damage (percentage)
        "4B" # uint8     m_brakesDamage[4];                  // Brakes damage (percentage)
        "B" # uint8     m_frontLeftWingDamage;              // Front left wing damage (percentage)
        "B" # uint8     m_frontRightWingDamage;             // Front right wing damage (percentage)
        "B" # uint8     m_rearWingDamage;                   // Rear wing damage (percentage)
        "B" # uint8     m_floorDamage;                      // Floor damage (percentage)
        "B" # uint8     m_diffuserDamage;                   // Diffuser damage (percentage)
        "B" # uint8     m_sidepodDamage;                    // Sidepod damage (percentage)
        "B" # uint8     m_drsFault;                         // Indicator for DRS fault, 0 = OK, 1 = fault
        "B" # uint8     m_ersFault;                         // Indicator for ERS fault, 0 = OK, 1 = fault
        "B" # uint8     m_gearBoxDamage;                    // Gear box damage (percentage)
        "B" # uint8     m_engineDamage;                     // Engine damage (percentage)
        "B" # uint8     m_engineMGUHWear;                   // Engine wear MGU-H (percentage)
        "B" # uint8     m_engineESWear;                     // Engine wear ES (percentage)
        "B" # uint8     m_engineCEWear;                     // Engine wear CE (percentage)
        "B" # uint8     m_engineICEWear;                    // Engine wear ICE (percentage)
        "B" # uint8     m_engineMGUKWear;                   // Engine wear MGU-K (percentage)
        "B" # uint8     m_engineTCWear;                     // Engine wear TC (percentage)
        "B" # uint8     m_engineBlown;                      // Engine blown, 0 = OK, 1 = fault
        "B" # uint8     m_engineSeized;                     // Engine seized, 0 = OK, 1 = fault
    )
    PACKET_LEN = struct.calcsize(PACKET_FORMAT)

    PACKET_FORMAT_25 = ("<"
        "4f" # float     m_tyresWear[4];                     // Tyre wear (percentage)
        "4B" # uint8     m_tyresDamage[4];                   // Tyre damage (percentage)
        "4B" # uint8     m_brakesDamage[4];                  // Brakes damage (percentage)
        "4B" # uint8     m_tyreBlisters[4];                  // Tyre Blisters (percentage)
        "B" # uint8     m_frontLeftWingDamage;              // Front left wing damage (percentage)
        "B" # uint8     m_frontRightWingDamage;             // Front right wing damage (percentage)
        "B" # uint8     m_rearWingDamage;                   // Rear wing damage (percentage)
        "B" # uint8     m_floorDamage;                      // Floor damage (percentage)
        "B" # uint8     m_diffuserDamage;                   // Diffuser damage (percentage)
        "B" # uint8     m_sidepodDamage;                    // Sidepod damage (percentage)
        "B" # uint8     m_drsFault;                         // Indicator for DRS fault, 0 = OK, 1 = fault
        "B" # uint8     m_ersFault;                         // Indicator for ERS fault, 0 = OK, 1 = fault
        "B" # uint8     m_gearBoxDamage;                    // Gear box damage (percentage)
        "B" # uint8     m_engineDamage;                     // Engine damage (percentage)
        "B" # uint8     m_engineMGUHWear;                   // Engine wear MGU-H (percentage)
        "B" # uint8     m_engineESWear;                     // Engine wear ES (percentage)
        "B" # uint8     m_engineCEWear;                     // Engine wear CE (percentage)
        "B" # uint8     m_engineICEWear;                    // Engine wear ICE (percentage)
        "B" # uint8     m_engineMGUKWear;                   // Engine wear MGU-K (percentage)
        "B" # uint8     m_engineTCWear;                     // Engine wear TC (percentage)
        "B" # uint8     m_engineBlown;                      // Engine blown, 0 = OK, 1 = fault
        "B" # uint8     m_engineSeized;                     // Engine seized, 0 = OK, 1 = fault
    )
    PACKET_LEN_25 = struct.calcsize(PACKET_FORMAT_25)

    def __init__(self, data, game_year) -> None:
        """
        Initializes CarDamageData with raw data.

        Args:
            data (bytes): Raw data representing the packet for car damage data.
        """
        self.m_tyresWear = [0.0] * 4
        self.m_tyresDamage = [0] * 4
        self.m_brakesDamage = [0] * 4
        self.m_tyreBlisters = [0] * 4
        self.m_gameYear = game_year
        if game_year >= 25:
            (
                self.m_tyresWear[0],
                self.m_tyresWear[1],
                self.m_tyresWear[2],
                self.m_tyresWear[3],
                self.m_tyresDamage[0],
                self.m_tyresDamage[1],
                self.m_tyresDamage[2],
                self.m_tyresDamage[3],
                self.m_brakesDamage[0],
                self.m_brakesDamage[1],
                self.m_brakesDamage[2],
                self.m_brakesDamage[3],
                self.m_tyreBlisters[0],
                self.m_tyreBlisters[1],
                self.m_tyreBlisters[2],
                self.m_tyreBlisters[3],
                self.m_frontLeftWingDamage,
                self.m_frontRightWingDamage,
                self.m_rearWingDamage,
                self.m_floorDamage,
                self.m_diffuserDamage,
                self.m_sidepodDamage,
                self.m_drsFault,
                self.m_ersFault,
                self.m_gearBoxDamage,
                self.m_engineDamage,
                self.m_engineMGUHWear,
                self.m_engineESWear,
                self.m_engineCEWear,
                self.m_engineICEWear,
                self.m_engineMGUKWear,
                self.m_engineTCWear,
                self.m_engineBlown,
                self.m_engineSeized,
            ) = struct.unpack(self.PACKET_FORMAT_25, data)
        else:
            (
                self.m_tyresWear[0],
                self.m_tyresWear[1],
                self.m_tyresWear[2],
                self.m_tyresWear[3],
                self.m_tyresDamage[0],
                self.m_tyresDamage[1],
                self.m_tyresDamage[2],
                self.m_tyresDamage[3],
                self.m_brakesDamage[0],
                self.m_brakesDamage[1],
                self.m_brakesDamage[2],
                self.m_brakesDamage[3],
                self.m_frontLeftWingDamage,
                self.m_frontRightWingDamage,
                self.m_rearWingDamage,
                self.m_floorDamage,
                self.m_diffuserDamage,
                self.m_sidepodDamage,
                self.m_drsFault,
                self.m_ersFault,
                self.m_gearBoxDamage,
                self.m_engineDamage,
                self.m_engineMGUHWear,
                self.m_engineESWear,
                self.m_engineCEWear,
                self.m_engineICEWear,
                self.m_engineMGUKWear,
                self.m_engineTCWear,
                self.m_engineBlown,
                self.m_engineSeized,
            ) = struct.unpack(self.PACKET_FORMAT, data)

        self.m_drsFault = bool(self.m_drsFault)
        self.m_ersFault = bool(self.m_ersFault)
        self.m_engineBlown = bool(self.m_engineBlown)
        self.m_engineSeized = bool(self.m_engineSeized)

    def __str__(self) -> str:
        """
        Returns a string representation of CarDamageData.

        Returns:
            str: String representation of CarDamageData.
        """

        return (
            f"Tyres Wear: {str(self.m_tyresWear)}, Tyres Damage: {str(self.m_tyresDamage)}, "
            f"Brakes Damage: {str(self.m_brakesDamage)}, Front Left Wing Damage: {self.m_frontLeftWingDamage}, "
            f"Front Right Wing Damage: {self.m_frontRightWingDamage}, Rear Wing Damage: {self.m_rearWingDamage}, "
            f"Floor Damage: {self.m_floorDamage}, Diffuser Damage: {self.m_diffuserDamage}, "
            f"Sidepod Damage: {self.m_sidepodDamage}, DRS Fault: {self.m_drsFault}, ERS Fault: {self.m_ersFault}, "
            f"Gear Box Damage: {self.m_gearBoxDamage}, Engine Damage: {self.m_engineDamage}, "
            f"Engine MGU-H Wear: {self.m_engineMGUHWear}, Engine ES Wear: {self.m_engineESWear}, "
            f"Engine CE Wear: {self.m_engineCEWear}, Engine ICE Wear: {self.m_engineICEWear}, "
            f"Engine MGU-K Wear: {self.m_engineMGUKWear}, Engine TC Wear: {self.m_engineTCWear}, "
            f"Engine Blown: {self.m_engineBlown}, Engine Seized: {self.m_engineSeized}"
        )

    def toJSON(self) -> Dict[str, Any]:
        """
        Convert the CarDamageData instance to a JSON-compatible dictionary with kebab-case keys.

        Returns:
            Dict[str, Any]: JSON-compatible dictionary with kebab-case keys representing the CarDamageData instance.
        """

        return {
            "tyres-wear": self.m_tyresWear,
            "tyres-damage": self.m_tyresDamage,
            "brakes-damage": self.m_brakesDamage,
            "front-left-wing-damage": self.m_frontLeftWingDamage,
            "front-right-wing-damage": self.m_frontRightWingDamage,
            "rear-wing-damage": self.m_rearWingDamage,
            "floor-damage": self.m_floorDamage,
            "diffuser-damage": self.m_diffuserDamage,
            "sidepod-damage": self.m_sidepodDamage,
            "drs-fault": self.m_drsFault,
            "ers-fault": self.m_ersFault,
            "gear-box-damage": self.m_gearBoxDamage,
            "engine-damage": self.m_engineDamage,
            "engine-mguh-wear": self.m_engineMGUHWear,
            "engine-es-wear": self.m_engineESWear,
            "engine-ce-wear": self.m_engineCEWear,
            "engine-ice-wear": self.m_engineICEWear,
            "engine-mguk-wear": self.m_engineMGUKWear,
            "engine-tc-wear": self.m_engineTCWear,
            "engine-blown": self.m_engineBlown,
            "engine-seized": self.m_engineSeized,
        }

    def __eq__(self, other: "CarDamageData") -> bool:
        """
        Check if two CarDamageData instances are equal.

        Args:
            other (CarDamageData): The other CarDamageData instance to compare with.

        Returns:
            bool: True if the CarDamageData instances are equal, False otherwise.
        """

        return (
            self.m_tyresWear == other.m_tyresWear and
            self.m_tyresDamage == other.m_tyresDamage and
            self.m_brakesDamage == other.m_brakesDamage and
            self.m_frontLeftWingDamage == other.m_frontLeftWingDamage and
            self.m_frontRightWingDamage == other.m_frontRightWingDamage and
            self.m_rearWingDamage == other.m_rearWingDamage and
            self.m_floorDamage == other.m_floorDamage and
            self.m_diffuserDamage == other.m_diffuserDamage and
            self.m_sidepodDamage == other.m_sidepodDamage and
            self.m_drsFault == other.m_drsFault and
            self.m_ersFault == other.m_ersFault and
            self.m_gearBoxDamage == other.m_gearBoxDamage and
            self.m_engineDamage == other.m_engineDamage and
            self.m_engineMGUHWear == other.m_engineMGUHWear and
            self.m_engineESWear == other.m_engineESWear and
            self.m_engineCEWear == other.m_engineCEWear and
            self.m_engineICEWear == other.m_engineICEWear and
            self.m_engineMGUKWear == other.m_engineMGUKWear and
            self.m_engineTCWear == other.m_engineTCWear and
            self.m_engineBlown == other.m_engineBlown and
            self.m_engineSeized == other.m_engineSeized
        )

    def __ne__(self, other: "CarDamageData") -> bool:
        """
        Check if two CarDamageData instances are not equal.

        Args:
            other (CarDamageData): The other CarDamageData instance to compare with.

        Returns:
            bool: True if the CarDamageData instances are not equal, False otherwise.
        """
        return not self.__eq__(other)

    def to_bytes(self) -> bytes:
        """
        Convert the CarDamageData instance to bytes.

        Returns:
            bytes: Bytes representing the CarDamageData instance.
        """

        if self.m_gameYear < 25:
            return struct.pack(self.PACKET_FORMAT,
                self.m_tyresWear[0],
                self.m_tyresWear[1],
                self.m_tyresWear[2],
                self.m_tyresWear[3],
                self.m_tyresDamage[0],
                self.m_tyresDamage[1],
                self.m_tyresDamage[2],
                self.m_tyresDamage[3],
                self.m_brakesDamage[0],
                self.m_brakesDamage[1],
                self.m_brakesDamage[2],
                self.m_brakesDamage[3],
                self.m_frontLeftWingDamage,
                self.m_frontRightWingDamage,
                self.m_rearWingDamage,
                self.m_floorDamage,
                self.m_diffuserDamage,
                self.m_sidepodDamage,
                self.m_drsFault,
                self.m_ersFault,
                self.m_gearBoxDamage,
                self.m_engineDamage,
                self.m_engineMGUHWear,
                self.m_engineESWear,
                self.m_engineCEWear,
                self.m_engineICEWear,
                self.m_engineMGUKWear,
                self.m_engineTCWear,
                self.m_engineBlown,
                self.m_engineSeized,
            )
        else:
            return struct.pack(self.PACKET_FORMAT_25,
                self.m_tyresWear[0],
                self.m_tyresWear[1],
                self.m_tyresWear[2],
                self.m_tyresWear[3],
                self.m_tyresDamage[0],
                self.m_tyresDamage[1],
                self.m_tyresDamage[2],
                self.m_tyresDamage[3],
                self.m_brakesDamage[0],
                self.m_brakesDamage[1],
                self.m_brakesDamage[2],
                self.m_brakesDamage[3],
                self.m_tyreBlisters[0],
                self.m_tyreBlisters[1],
                self.m_tyreBlisters[2],
                self.m_tyreBlisters[3],
                self.m_frontLeftWingDamage,
                self.m_frontRightWingDamage,
                self.m_rearWingDamage,
                self.m_floorDamage,
                self.m_diffuserDamage,
                self.m_sidepodDamage,
                self.m_drsFault,
                self.m_ersFault,
                self.m_gearBoxDamage,
                self.m_engineDamage,
                self.m_engineMGUHWear,
                self.m_engineESWear,
                self.m_engineCEWear,
                self.m_engineICEWear,
                self.m_engineMGUKWear,
                self.m_engineTCWear,
                self.m_engineBlown,
                self.m_engineSeized,
            )

    @classmethod
    def from_values(cls,
        game_year: int,
        tyres_wear: List[float],
        tyres_damage: List[int],
        brakes_damage: List[int],
        tyre_blisters: List[int],
        fl_wing_damage: int,
        fr_wing_damage: int,
        rear_wing_damage: int,
        floor_damage: int,
        diffuser_damage: int,
        sidepod_damage: int,
        drs_fault: bool,
        ers_fault: bool,
        gear_box_damage: int,
        engine_damage: int,
        engine_mguh_wear: int,
        engine_es_wear: int,
        engine_ce_wear: int,
        engine_ice_wear: int,
        engine_mguk_wear: int,
        engine_tc_wear: int,
        engine_blown: bool,
        engine_seized: bool) -> "CarDamageData":

        """
        Create a CarDamageData object from individual values.

        Args:
            Too many to document for a test method

        Returns:
            CarDamageData: A new CarDamageData object with the provided values.
        """

        if game_year < 25:
            return cls(struct.pack(cls.PACKET_FORMAT,
                tyres_wear[0],
                tyres_wear[1],
                tyres_wear[2],
                tyres_wear[3],
                tyres_damage[0],
                tyres_damage[1],
                tyres_damage[2],
                tyres_damage[3],
                brakes_damage[0],
                brakes_damage[1],
                brakes_damage[2],
                brakes_damage[3],
                fl_wing_damage,
                fr_wing_damage,
                rear_wing_damage,
                floor_damage,
                diffuser_damage,
                sidepod_damage,
                drs_fault,
                ers_fault,
                gear_box_damage,
                engine_damage,
                engine_mguh_wear,
                engine_es_wear,
                engine_ce_wear,
                engine_ice_wear,
                engine_mguk_wear,
                engine_tc_wear,
                engine_blown,
                engine_seized,
            ), game_year)
        else:
            return cls(struct.pack(cls.PACKET_FORMAT_25,
                tyres_wear[0],
                tyres_wear[1],
                tyres_wear[2],
                tyres_wear[3],
                tyres_damage[0],
                tyres_damage[1],
                tyres_damage[2],
                tyres_damage[3],
                brakes_damage[0],
                brakes_damage[1],
                brakes_damage[2],
                brakes_damage[3],
                tyre_blisters[0],
                tyre_blisters[1],
                tyre_blisters[2],
                tyre_blisters[3],
                fl_wing_damage,
                fr_wing_damage,
                rear_wing_damage,
                floor_damage,
                diffuser_damage,
                sidepod_damage,
                drs_fault,
                ers_fault,
                gear_box_damage,
                engine_damage,
                engine_mguh_wear,
                engine_es_wear,
                engine_ce_wear,
                engine_ice_wear,
                engine_mguk_wear,
                engine_tc_wear,
                engine_blown,
                engine_seized,
            ), game_year)


class PacketCarDamageData:
    """
    Class representing the packet for car damage data.

    Attributes:
        m_header (PacketHeader): The header of the packet.
        m_carDamageData (List[CarDamageData]): List of CarDamageData objects for each car.

    Note:
        The class is designed to parse and represent the car damage data packet.
    """

    def __init__(self, header: PacketHeader, data: bytes) -> None:
        """
        Initializes PacketCarDamageData with raw data.

        Args:
            header (PacketHeader): The header of the packet.
            data (bytes): Raw data representing the packet for car damage data.
        """

        self.m_header: PacketHeader = header
        if header.m_gameYear >= 25:
            packet_len = CarDamageData.PACKET_LEN_25
        else:
            packet_len = CarDamageData.PACKET_LEN
        # Slice the data bytes in steps of CarDamageData.PACKET_LEN to create CarDamageData objects.
        self.m_carDamageData = [
            CarDamageData(data[i:i + packet_len], header.m_gameYear)
            for i in range(0, len(data), packet_len)
        ]

    def __str__(self) -> str:
        """
        Returns a string representation of PacketCarDamageData.

        Returns:
            str: String representation of PacketCarDamageData.
        """

        return f"Header: {str(self.m_header)}, Car Damage Data: {[str(car_data) for car_data in self.m_carDamageData]}"

    def toJSON(self, include_header: bool=False) -> Dict[str, Any]:
        """
        Convert the PacketCarDamageData instance to a JSON-compatible dictionary with kebab-case keys.

        Arguments:
            - include_header - Whether the header dump must be included in the JSON

        Returns:
            Dict[str, Any]: JSON-compatible dictionary with kebab-case keys representing the object.
        """

        json_data = {
            "car-damage-data": [car_data.toJSON() for car_data in self.m_carDamageData],
        }
        if include_header:
            json_data["header"] = self.m_header.toJSON()

        return json_data

    def __eq__(self, other: "PacketCarDamageData") -> bool:
        """
        Checks if two PacketCarDamageData objects are equal.

        Arguments:
            other (Any): The object to compare with.

        Returns:
            bool: True if the objects are equal, False otherwise.
        """

        return (
            self.m_header == other.m_header and
            self.m_carDamageData == other.m_carDamageData
        )

    def __ne__(self, other: "PacketCarDamageData") -> bool:
        """
        Checks if two PacketCarDamageData objects are not equal.

        Arguments:
            other (Any): The object to compare with.

        Returns:
            bool: True if the objects are not equal, False otherwise.
        """

        return not self.__eq__(other)

    def to_bytes(self) -> bytes:
        """
        Convert the PacketCarDamageData instance to raw bytes.

        Returns:
            bytes: Raw bytes representing the packet for car damage data.
        """

        return self.m_header.to_bytes() + b"".join([car_data.to_bytes() for car_data in self.m_carDamageData])

    @classmethod
    def from_values(cls, header: PacketHeader, car_damage_data: List[CarDamageData]) -> "PacketCarDamageData":
        """Create a PacketCarDamageData object from individual values.

        Args:
            header (PacketHeader): The header of the packet.
            car_damage_data (List[CarDamageData]): List of CarDamageData objects for each car.

        Returns:
            PacketCarDamageData: A new PacketCarDamageData object.
        """

        return cls(header, b"".join([car_data.to_bytes() for car_data in car_damage_data]))
