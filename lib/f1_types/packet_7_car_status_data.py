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
from typing import Any, Dict, List, Union

from .base_pkt import F1BaseEnum, F1PacketBase, F1SubPacketBase
from .common import (ActualTyreCompound, TractionControlAssistMode,
                     VisualTyreCompound, _validate_parse_fixed_segments)
from .header import PacketHeader

# --------------------- CLASS DEFINITIONS --------------------------------------

class CarStatusData(F1SubPacketBase):
    """
    Class representing car status data.

    Attributes:
        - m_tractionControl (uint8): Traction control - 0 = off, 1 = medium, 2 = full
        - m_antiLockBrakes (uint8): Anti-lock brakes - 0 (off) - 1 (on)
        - m_fuelMix (uint8): Fuel mix - 0 = lean, 1 = standard, 2 = rich, 3 = max
        - m_frontBrakeBias (uint8): Front brake bias (percentage)
        - m_pitLimiterStatus (uint8): Pit limiter status - 0 = off, 1 = on
        - m_fuelInTank (float): Current fuel mass
        - m_fuelCapacity (float): Fuel capacity
        - m_fuelRemainingLaps (float): Fuel remaining in terms of laps (value on MFD)
        - m_maxRPM (uint16): Cars max RPM, point of rev limiter
        - m_idleRPM (uint16): Cars idle RPM
        - m_maxGears (uint8): Maximum number of gears
        - m_drsAllowed (uint8): DRS allowed - 0 = not allowed, 1 = allowed
        - m_drsActivationDistance (uint16): DRS activation distance -
                                          0 = DRS not available, non-zero - DRS will be available in [X] metres
        - m_actualTyreCompound (ActualTyreCompound): Actual tyre compound (enum)
        - m_visualTyreCompound (VisualTyreCompound): Visual tyre compound (enum)
        - m_tyresAgeLaps (uint8): Age in laps of the current set of tyres
        - m_vehicleFiaFlags (VehicleFIAFlags): Vehicle FIA flags (enum)
        - m_enginePowerICE (float): Engine power output of ICE (W)
        - m_enginePowerMGUK (float): Engine power output of MGU-K (W)
        - m_ersStoreEnergy (float): ERS energy store in Joules
        - m_ersDeployMode (ERSDeployMode): ERS deployment mode (enum)
        - m_ersHarvestedThisLapMGUK (float): ERS energy harvested this lap by MGU-K
        - m_ersHarvestedThisLapMGUH (float): ERS energy harvested this lap by MGU-H
        - m_ersDeployedThisLap (float): ERS energy deployed this lap
        - m_networkPaused (uint8): Whether the car is paused in a network game

    Note:
        The class uses enum classes for certain attributes for better readability and type safety.
    """

    MIN_FUEL_KG = 0.2 # Source: Trust me bro
    MAX_ERS_STORE_ENERGY = 4000000.0 # Source: https://www.mercedes-amg-hpp.com/formula-1-engine-facts/#
    COMPILED_PACKET_STRUCT = struct.Struct("<"
        "B" # uint8       m_tractionControl;          // Traction control - 0 = off, 1 = medium, 2 = full
        "B" # uint8       m_antiLockBrakes;           // 0 (off) - 1 (on)
        "B" # uint8       m_fuelMix;                  // Fuel mix - 0 = lean, 1 = standard, 2 = rich, 3 = max
        "B" # uint8       m_frontBrakeBias;           // Front brake bias (percentage)
        "B" # uint8       m_pitLimiterStatus;         // Pit limiter status - 0 = off, 1 = on
        "f" # float       m_fuelInTank;               // Current fuel mass
        "f" # float       m_fuelCapacity;             // Fuel capacity
        "f" # float       m_fuelRemainingLaps;        // Fuel remaining in terms of laps (value on MFD)
        "H" # uint16      m_maxRPM;                   // Cars max RPM, point of rev limiter
        "H" # uint16      m_idleRPM;                  // Cars idle RPM
        "B" # uint8       m_maxGears;                 // Maximum number of gears
        "B" # uint8       m_drsAllowed;               // 0 = not allowed, 1 = allowed
        "H" # uint16      m_drsActivationDistance;    // 0 = DRS not available, non-zero - DRS will be available
                                                # // in [X] metres
        "B" # uint8       m_actualTyreCompound;       // F1 Modern - 16 = C5, 17 = C4, 18 = C3, 19 = C2, 20 = C1
                            #   // 21 = C0, 7 = inter, 8 = wet
                            #   // F1 Classic - 9 = dry, 10 = wet
                            #   // F2 – 11 = super soft, 12 = soft, 13 = medium, 14 = hard
                            #   // 15 = wet
        "B" # uint8       m_visualTyreCompound;       // F1 visual (can be different from actual compound)
                                                # // 16 = soft, 17 = medium, 18 = hard, 7 = inter, 8 = wet
                                                # // F1 Classic – same as above
                                                # // F2 ‘19, 15 = wet, 19 – super soft, 20 = soft
                                                # // 21 = medium , 22 = hard
        "B" # uint8       m_tyresAgeLaps;             // Age in laps of the current set of tyres
        "b" # int8        m_vehicleFiaFlags;       // -1 = invalid/unknown, 0 = none, 1 = green
                                                # // 2 = blue, 3 = yellow
        "f" # float       m_enginePowerICE;           // Engine power output of ICE (W)
        "f" # float       m_enginePowerMGUK;          // Engine power output of MGU-K (W)
        "f" # float       m_ersStoreEnergy;           // ERS energy store in Joules
        "B" # uint8       m_ersDeployMode;            // ERS deployment mode, 0 = none, 1 = medium
                            #   // 2 = hotlap, 3 = overtake
        "f" # float       m_ersHarvestedThisLapMGUK;  // ERS energy harvested this lap by MGU-K
        "f" # float       m_ersHarvestedThisLapMGUH;  // ERS energy harvested this lap by MGU-H
        "f" # float       m_ersDeployedThisLap;       // ERS energy deployed this lap
        "B" # uint8       m_networkPaused;            // Whether the car is paused in a network game
    )
    PACKET_LEN = COMPILED_PACKET_STRUCT.size

    # Type hint declarations
    m_tractionControl: Union[TractionControlAssistMode, int]
    m_antiLockBrakes: bool
    m_fuelMix: Union["CarStatusData.FuelMix", int]
    m_frontBrakeBias: int
    m_pitLimiterStatus: bool
    m_fuelInTank: float
    m_fuelCapacity: float
    m_fuelRemainingLaps: float
    m_maxRPM: int
    m_idleRPM: int
    m_maxGears: int
    m_drsAllowed: int
    m_drsActivationDistance: int
    m_actualTyreCompound: Union[ActualTyreCompound, int]
    m_visualTyreCompound: Union[VisualTyreCompound, int]
    m_tyresAgeLaps: int
    m_vehicleFiaFlags: Union["CarStatusData.VehicleFIAFlags", int]
    m_enginePowerICE: float
    m_enginePowerMGUK: float
    m_ersStoreEnergy: float
    m_ersDeployMode: Union["CarStatusData.ERSDeployMode", int]
    m_ersHarvestedThisLapMGUK: float
    m_ersHarvestedThisLapMGUH: float
    m_ersDeployedThisLap: float
    m_networkPaused: bool

    class VehicleFIAFlags(F1BaseEnum):
        """
        Enumeration representing different FIA flags related to vehicles.

        Attributes:
            INVALID_UNKNOWN (int): Invalid or unknown FIA flag (-1)
            NONE (int): No FIA flag (0)
            GREEN (int): Green flag (1)
            BLUE (int): Blue flag (2)
            YELLOW (int): Yellow flag (3)

            Note:
                Each attribute represents a unique FIA flag identified by an integer value.
        """

        INVALID_UNKNOWN = -1
        NONE = 0
        GREEN = 1
        BLUE = 2
        YELLOW = 3

        def __str__(self) -> str:
            """
            Returns a human-readable string representation of the FIA flag.

            Returns:
                str: String representation of the FIA flag.
            """
            return {
                CarStatusData.VehicleFIAFlags.INVALID_UNKNOWN: "Invalid/Unknown",
                CarStatusData.VehicleFIAFlags.NONE: "None",
                CarStatusData.VehicleFIAFlags.GREEN: "Green",
                CarStatusData.VehicleFIAFlags.BLUE: "Blue",
                CarStatusData.VehicleFIAFlags.YELLOW: "Yellow",
            }[self]

    class ERSDeployMode(F1BaseEnum):
        """
        Enumeration representing different ERS deployment modes.

        Attributes:
            NONE (int): No ERS deployment (0)
            MEDIUM (int): Medium ERS deployment (1)
            HOPLAP (int): Hotlap ERS deployment (2)
            OVERTAKE (int): Overtake ERS deployment (3)

            Note:
                Each attribute represents a unique ERS deployment mode identified by an integer value.
        """

        NONE = 0
        MEDIUM = 1
        HOTLAP = 2
        OVERTAKE = 3

        def __str__(self) -> str:
            """
            Returns a human-readable string representation of the ERS deployment mode.

            Returns:
                str: String representation of the ERS deployment mode.
            """
            return self.name.title()

    class FuelMix(F1BaseEnum):
        """
        Enumeration representing different ERS deployment modes.

        Attributes:
            LEAN (int) - (0)
            STANDARD (int) - (1)
            RICH (int) - (2)
            MAX (int) - (3)

            Note:
                Each attribute represents a unique fuel mix mode identified by an integer value.
        """

        LEAN = 0
        STANDARD = 1
        RICH = 2
        MAX = 3

        def __str__(self) -> str:
            """Return the string representation of this object

            Returns:
                str: string representation
            """
            return self.name.title()

    def __init__(self, data) -> None:
        """
        Initializes CarStatusData with raw data.

        Args:
            data (bytes): Raw data representing car status.
        """

        # Unpack data in a single step
        unpacked = self.COMPILED_PACKET_STRUCT.unpack(data)

        # Set attributes using __dict__.update() to reduce overhead
        self.__dict__.update(zip([
            "m_tractionControl", "m_antiLockBrakes", "m_fuelMix", "m_frontBrakeBias",
            "m_pitLimiterStatus", "m_fuelInTank", "m_fuelCapacity", "m_fuelRemainingLaps",
            "m_maxRPM", "m_idleRPM", "m_maxGears", "m_drsAllowed", "m_drsActivationDistance",
            "m_actualTyreCompound", "m_visualTyreCompound", "m_tyresAgeLaps", "m_vehicleFiaFlags",
            "m_enginePowerICE", "m_enginePowerMGUK", "m_ersStoreEnergy", "m_ersDeployMode",
            "m_ersHarvestedThisLapMGUK", "m_ersHarvestedThisLapMGUH", "m_ersDeployedThisLap",
            "m_networkPaused"
        ], unpacked))

        # Convert boolean fields using bitwise AND
        self.m_antiLockBrakes = unpacked[1] & 1
        self.m_pitLimiterStatus = unpacked[4] & 1
        self.m_networkPaused = unpacked[24] & 1

        # Convert Enums with error handling
        def try_enum(enum_class, value):
            try:
                return enum_class(value)
            except ValueError:
                return value  # Store raw value if conversion fails

        self.m_actualTyreCompound = try_enum(ActualTyreCompound, unpacked[13])
        self.m_visualTyreCompound = try_enum(VisualTyreCompound, unpacked[14])
        self.m_vehicleFiaFlags = try_enum(CarStatusData.VehicleFIAFlags, unpacked[16])
        self.m_ersDeployMode = try_enum(CarStatusData.ERSDeployMode, unpacked[20])
        self.m_tractionControl = try_enum(TractionControlAssistMode, unpacked[0])
        self.m_fuelMix = try_enum(CarStatusData.FuelMix, unpacked[2])

        self.m_antiLockBrakes = bool(self.m_antiLockBrakes)
        self.m_pitLimiterStatus = bool(self.m_pitLimiterStatus)
        self.m_networkPaused = bool(self.m_networkPaused)

    def __str__(self):
        """
        Returns a string representation of CarStatusData.

        Returns:
            str: String representation of CarStatusData.
        """
        return (
            f"CarStatusData("
            f"m_tractionControl={self.m_tractionControl}, "
            f"m_antiLockBrakes={self.m_antiLockBrakes}, "
            f"m_fuelMix={str(self.m_fuelMix)}, "
            f"m_frontBrakeBias={self.m_frontBrakeBias}, "
            f"m_pitLimiterStatus={self.m_pitLimiterStatus}, "
            f"m_fuelInTank={self.m_fuelInTank}, "
            f"m_fuelCapacity={self.m_fuelCapacity}, "
            f"m_fuelRemainingLaps={self.m_fuelRemainingLaps}, "
            f"m_maxRPM={self.m_maxRPM}, "
            f"m_idleRPM={self.m_idleRPM}, "
            f"m_maxGears={self.m_maxGears}, "
            f"m_drsAllowed={self.m_drsAllowed}, "
            f"m_drsActivationDistance={self.m_drsActivationDistance}, "
            f"m_actualTyreCompound={self.m_actualTyreCompound}, "
            f"m_visualTyreCompound={self.m_visualTyreCompound}, "
            f"m_tyresAgeLaps={self.m_tyresAgeLaps}, "
            f"m_vehicleFiaFlags={self.m_vehicleFiaFlags}, "
            f"m_enginePowerICE={self.m_enginePowerICE}, "
            f"m_enginePowerMGUK={self.m_enginePowerMGUK}, "
            f"m_ersStoreEnergy={self.m_ersStoreEnergy}, "
            f"m_ersDeployMode={self.m_ersDeployMode}, "
            f"m_ersHarvestedThisLapMGUK={self.m_ersHarvestedThisLapMGUK}, "
            f"m_ersHarvestedThisLapMGUH={self.m_ersHarvestedThisLapMGUH}, "
            f"m_ersDeployedThisLap={self.m_ersDeployedThisLap}, "
            f"m_networkPaused={self.m_networkPaused})"
        )

    def toJSON(self) -> Dict[str, Any]:
        """
        Convert the CarStatusData instance to a JSON-compatible dictionary.

        Returns:
            Dict[str, Any]: JSON-compatible dictionary representing the CarStatusData instance.
        """

        return {
            "traction-control": str(self.m_tractionControl),
            "anti-lock-brakes": self.m_antiLockBrakes,
            "fuel-mix": str(self.m_fuelMix),
            "front-brake-bias": self.m_frontBrakeBias,
            "pit-limiter-status": self.m_pitLimiterStatus,
            "fuel-in-tank": self.m_fuelInTank,
            "fuel-capacity": self.m_fuelCapacity,
            "fuel-remaining-laps": self.m_fuelRemainingLaps,
            "max-rpm": self.m_maxRPM,
            "idle-rpm": self.m_idleRPM,
            "max-gears": self.m_maxGears,
            "drs-allowed": self.m_drsAllowed,
            "drs-activation-distance": self.m_drsActivationDistance,
            "actual-tyre-compound": str(self.m_actualTyreCompound),
            "visual-tyre-compound": str(self.m_visualTyreCompound),
            "tyres-age-laps": self.m_tyresAgeLaps,
            "vehicle-fia-flags": str(self.m_vehicleFiaFlags),
            "engine-power-ice": self.m_enginePowerICE,
            "engine-power-mguk": self.m_enginePowerMGUK,
            "ers-store-energy": self.m_ersStoreEnergy,
            "ers-deploy-mode": str(self.m_ersDeployMode),
            "ers-harvested-this-lap-mguk": self.m_ersHarvestedThisLapMGUK,
            "ers-harvested-this-lap-mguh": self.m_ersHarvestedThisLapMGUH,
            "ers-deployed-this-lap": self.m_ersDeployedThisLap,
            "ers-max-capacity" : self.MAX_ERS_STORE_ENERGY,
            "network-paused": self.m_networkPaused,
        }

    def __eq__(self, other: "CarStatusData") -> bool:
        """
        Check if two CarStatusData instances are equal.

        Args:
            other (CarStatusData): The other CarStatusData instance.

        Returns:
            bool: True if the two CarStatusData instances are equal, False otherwise.
        """

        return (
            self.m_tractionControl == other.m_tractionControl and
            self.m_antiLockBrakes == other.m_antiLockBrakes and
            self.m_fuelMix == other.m_fuelMix and
            self.m_frontBrakeBias == other.m_frontBrakeBias and
            self.m_pitLimiterStatus == other.m_pitLimiterStatus and
            self.m_fuelInTank == other.m_fuelInTank and
            self.m_fuelCapacity == other.m_fuelCapacity and
            self.m_fuelRemainingLaps == other.m_fuelRemainingLaps and
            self.m_maxRPM == other.m_maxRPM and
            self.m_idleRPM == other.m_idleRPM and
            self.m_maxGears == other.m_maxGears and
            self.m_drsAllowed == other.m_drsAllowed and
            self.m_drsActivationDistance == other.m_drsActivationDistance and
            self.m_actualTyreCompound == other.m_actualTyreCompound and
            self.m_visualTyreCompound == other.m_visualTyreCompound and
            self.m_tyresAgeLaps == other.m_tyresAgeLaps and
            self.m_vehicleFiaFlags == other.m_vehicleFiaFlags and
            self.m_enginePowerICE == other.m_enginePowerICE and
            self.m_enginePowerMGUK == other.m_enginePowerMGUK and
            self.m_ersStoreEnergy == other.m_ersStoreEnergy and
            self.m_ersDeployMode == other.m_ersDeployMode and
            self.m_ersHarvestedThisLapMGUK == other.m_ersHarvestedThisLapMGUK and
            self.m_ersHarvestedThisLapMGUH == other.m_ersHarvestedThisLapMGUH and
            self.m_ersDeployedThisLap == other.m_ersDeployedThisLap and
            self.m_networkPaused == other.m_networkPaused
        )

    def __ne__(self, other: "CarStatusData") -> bool:
        """
        Check if two CarStatusData instances are not equal.

        Args:
            other (CarStatusData): The other CarStatusData instance.

        Returns:
            bool: True if the two CarStatusData instances are not equal, False otherwise.
        """

        return not self.__eq__(other)

    def to_bytes(self) -> bytes:
        """Serialize the CarStatusData object to bytes based on PACKET_FORMAT.

        Returns:
            bytes: The serialized bytes.
        """

        return self.COMPILED_PACKET_STRUCT.pack(
            self.m_tractionControl.value,
            self.m_antiLockBrakes,
            self.m_fuelMix.value,
            self.m_frontBrakeBias,
            self.m_pitLimiterStatus,
            self.m_fuelInTank,
            self.m_fuelCapacity,
            self.m_fuelRemainingLaps,
            self.m_maxRPM,
            self.m_idleRPM,
            self.m_maxGears,
            self.m_drsAllowed,
            self.m_drsActivationDistance,
            self.m_actualTyreCompound.value,
            self.m_visualTyreCompound.value,
            self.m_tyresAgeLaps,
            self. m_vehicleFiaFlags.value,
            self.m_enginePowerICE,
            self.m_enginePowerMGUK,
            self.m_ersStoreEnergy,
            self.m_ersDeployMode.value,
            self.m_ersHarvestedThisLapMGUK,
            self.m_ersHarvestedThisLapMGUH,
            self.m_ersDeployedThisLap,
            self.m_networkPaused
        )

    @classmethod
    def from_values(cls,
        traction_control: TractionControlAssistMode,
        anti_lock_brakes: bool,
        fuel_mix: FuelMix,
        front_brake_bias: int,
        pit_limiter_status: bool,
        fuel_in_tank: float,
        fuel_capacity: float,
        fuel_remaining_laps: float,
        max_rpm: int,
        idle_rpm: int,
        max_gears: int,
        drs_allowed: int,
        drs_activation_distance: int,
        actual_tyre_compound: ActualTyreCompound,
        visual_tyre_compound: VisualTyreCompound,
        tyres_age_laps: int,
        m_vehicle_fia_flags: VehicleFIAFlags,
        engine_power_ice: float,
        engine_power_mguk: float,
        ers_store_energy: float,
        ers_deploy_mode: ERSDeployMode,
        ers_harvested_this_lap_mguk: float,
        ers_harvested_this_lap_mguh: float,
        ers_deployed_this_lap: float,
        network_paused) -> "CarStatusData":
        """
        Create a new CarStatusData object from the provided values.

        Args:
            Too many arguments to document for a test method

        Returns:
            CarStatusData: The created CarStatusData object.
        """

        return cls(cls.COMPILED_PACKET_STRUCT.pack(
            traction_control.value,
            anti_lock_brakes,
            fuel_mix.value,
            front_brake_bias,
            pit_limiter_status,
            fuel_in_tank,
            fuel_capacity,
            fuel_remaining_laps,
            max_rpm,
            idle_rpm,
            max_gears,
            drs_allowed,
            drs_activation_distance,
            actual_tyre_compound.value,
            visual_tyre_compound.value,
            tyres_age_laps,
            m_vehicle_fia_flags.value,
            engine_power_ice,
            engine_power_mguk,
            ers_store_energy,
            ers_deploy_mode.value,
            ers_harvested_this_lap_mguk,
            ers_harvested_this_lap_mguh,
            ers_deployed_this_lap,
            network_paused)
        )

class PacketCarStatusData(F1PacketBase):
    """
    Class containing details on car statuses for all the cars in the race.

    Attributes:
        - m_header(PacketHeader) - packet header info
        - m_carStatusData(List[CarStatusData]) - List of statuses of every car
    """

    MAX_CARS = 22

    def __init__(self, header: PacketHeader, packet: bytes) -> None:
        """Initialize the object from raw bytes.

        Args:
            header (PacketHeader): Object containing header info.
            packet (bytes): Bytes representing the packet payload.
        """
        super().__init__(header)
        self.m_carStatusData: List[CarStatusData]

        self.m_carStatusData, _ = _validate_parse_fixed_segments(
            data=packet,
            offset=0,
            item_cls=CarStatusData,
            item_len=CarStatusData.PACKET_LEN,
            count=self.MAX_CARS,
            max_count=self.MAX_CARS
        )

    def __str__(self) -> str:
        """Generate a human readable string of this object's contents

        Returns:
            str: Printable/Loggable string
        """

        status_data_str = ", ".join(str(status) for status in self.m_carStatusData)
        return f"PacketCarStatusData(Header: {str(self.m_header)}, Car Status Data: [{status_data_str}])"

    def toJSON(self, include_header: bool=False) -> Dict[str, Any]:
        """
        Convert the PacketCarStatusData instance to a JSON-compatible dictionary.

        Arguments:
            - include_header - Whether the header dump must be included in the JSON
        Returns:
            Dict[str, Any]: JSON-compatible dictionary representing the PacketCarStatusData instance.
        """

        json_data = {
            "car-status-data": [car_status_data.toJSON() for car_status_data in self.m_carStatusData],
        }
        if include_header:
            json_data["header"] = self.m_header.toJSON()

        return json_data

    def __eq__(self, other: "PacketCarStatusData") -> bool:
        """Check if two objects are equal

        Args:
            other (PacketCarStatusData): The object to compare to

        Returns:
            bool: True if the objects are equal, False otherwise
        """

        return self.m_header == other.m_header and self.m_carStatusData == other.m_carStatusData

    def __ne__(self, other: "PacketCarStatusData") -> bool:
        """Check if two objects are not equal

        Args:
            other (PacketCarStatusData): The object to compare to

        Returns:
            bool: True if the objects are not equal, False otherwise
        """

        return not self.__eq__(other)

    def to_bytes(self) -> bytes:
        """Convert the PacketCarStatusData instance to raw bytes

        Returns:
            bytes: Raw bytes representing the PacketCarStatusData instance
        """

        return self.m_header.to_bytes() + b"".join([car_status_data.to_bytes() for car_status_data in self.m_carStatusData])

    @classmethod
    def from_values(cls, header: PacketHeader, car_status_data: List[CarStatusData]) -> "PacketCarStatusData":
        """Create a PacketCarStatusData object from individual values.

        Args:
            header (PacketHeader): The header of the telemetry packet.
            car_status_data (List[CarStatusData]): List of CarStatusData objects containing data for all cars on track.

        Returns:
            PacketCarStatusData: A PacketCarStatusData object initialized with the provided values.
        """
        return cls(header, b''.join([car.to_bytes() for car in car_status_data]))
