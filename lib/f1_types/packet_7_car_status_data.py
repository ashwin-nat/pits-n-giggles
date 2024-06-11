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
from typing import Dict, List, Any
from enum import Enum
from .common import _split_list, PacketHeader, ActualTyreCompound, VisualTyreCompound, TractionControlAssistMode

# --------------------- CLASS DEFINITIONS --------------------------------------

class PacketCarStatusData:
    """
    Class containing details on car statuses for all the cars in the race.

    Attributes:
        - m_header(PacketHeader) - packet header info
        - m_carStatusData(List[CarStatusData]) - List of statuses of every car
    """

    def __init__(self, header: PacketHeader, packet: bytes) -> None:
        """Initialise the object from the raw bytes list

        Args:
            header (PacketHeader): Object containing header info
            packet (bytes): List of bytes representing the packet payload
        """

        self.m_header: PacketHeader = header
        self.m_carStatusData: List[CarStatusData] = []               # CarStatusData[22]

        for status_per_car_raw_data in _split_list(packet, CarStatusData.PACKET_LEN):
            self.m_carStatusData.append(CarStatusData(status_per_car_raw_data))

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

class CarStatusData:
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

    MAX_ERS_STORE_ENERGY = 4000000.0 # Source: https://www.mercedes-amg-hpp.com/formula-1-engine-facts/#
    PACKET_FORMAT = ("<"
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
    PACKET_LEN = struct.calcsize(PACKET_FORMAT)

    class VehicleFIAFlags(Enum):
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

        @staticmethod
        def isValid(fia_flag_code: int) -> bool:
            """
            Check if the input flag code maps to a valid enum value.

            Args:
                fia_flag_code (int): The actual FIA flag status code

            Returns:
                bool: True if the event type is valid, False otherwise.
            """
            if isinstance(fia_flag_code, CarStatusData.VehicleFIAFlags):
                return True  # It's already an instance of CarStatusData.VehicleFIAFlags
            return any(fia_flag_code == member.value for member in CarStatusData.VehicleFIAFlags)

    class ERSDeployMode(Enum):
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
        HOPLAP = 2
        OVERTAKE = 3

        def __str__(self) -> str:
            """
            Returns a human-readable string representation of the ERS deployment mode.

            Returns:
                str: String representation of the ERS deployment mode.
            """
            return {
                CarStatusData.ERSDeployMode.NONE: "None",
                CarStatusData.ERSDeployMode.MEDIUM: "Medium",
                CarStatusData.ERSDeployMode.HOPLAP: "Hotlap",
                CarStatusData.ERSDeployMode.OVERTAKE: "Overtake",
            }[self]

        @staticmethod
        def isValid(ers_deploy_mode_code: int) -> bool:
            """
            Check if the ERS deploy mode code maps to a valid enum value.

            Args:
                ers_deploy_mode_code (int): The ERS deploy mode code

            Returns:
                bool: True if the event type is valid, False otherwise.
            """
            if isinstance(ers_deploy_mode_code, CarStatusData.ERSDeployMode):
                return True  # It's already an instance of CarStatusData.ERSDeployMode
            return any(ers_deploy_mode_code == member.value for member in CarStatusData.ERSDeployMode)

    def __init__(self, data) -> None:
        """
        Initializes CarStatusData with raw data.

        Args:
            data (bytes): Raw data representing car status.
        """
        (
            self.m_tractionControl,
            self.m_antiLockBrakes,
            self.m_fuelMix,
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
            self.m_actualTyreCompound,
            self.m_visualTyreCompound,
            self.m_tyresAgeLaps,
            self. m_vehicleFiaFlags,
            self.m_enginePowerICE,
            self.m_enginePowerMGUK,
            self.m_ersStoreEnergy,
            self.m_ersDeployMode,
            self.m_ersHarvestedThisLapMGUK,
            self.m_ersHarvestedThisLapMGUH,
            self.m_ersDeployedThisLap,
            self.m_networkPaused
        ) = struct.unpack(self.PACKET_FORMAT, data)

        self.m_antiLockBrakes = bool(self.m_antiLockBrakes)
        if ActualTyreCompound.isValid(self.m_actualTyreCompound):
            self.m_actualTyreCompound = ActualTyreCompound(self.m_actualTyreCompound)
        if VisualTyreCompound.isValid(self.m_visualTyreCompound):
            self.m_visualTyreCompound = VisualTyreCompound(self.m_visualTyreCompound)
        if CarStatusData.VehicleFIAFlags.isValid(self.m_vehicleFiaFlags):
            self.m_vehicleFiaFlags = CarStatusData.VehicleFIAFlags(self.m_vehicleFiaFlags)
        if CarStatusData.ERSDeployMode.isValid(self.m_ersDeployMode):
            self.m_ersDeployMode = CarStatusData.ERSDeployMode(self.m_ersDeployMode)
        if TractionControlAssistMode.isValid(self.m_tractionControl):
            self.m_tractionControl = TractionControlAssistMode(self.m_tractionControl)

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
            f"m_fuelMix={self.m_fuelMix}, "
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
            "fuel-mix": self.m_fuelMix,
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
