# MIT License
#
# Copyright (c) [2025] [Ashwin Natarajan]
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
from typing import Any, Dict, List

from .base_pkt import F1PacketBase, F1SubPacketBase
from .header import PacketHeader

# --------------------- CLASS DEFINITIONS --------------------------------------

class CarTelemetry2Data(F1SubPacketBase):
    """
    Per-car active aero and overtake telemetry, introduced in F1 2026.

    Attributes:
        m_activeAeroMode (int): 0 = Corner mode, 1 = Straight mode.
        m_activeAeroAvailable (int): 0 = not available, 1 = available.
        m_activeAeroActivationDistance (int): metres until active aero becomes available (0 = N/A).
        m_overtakeAvailable (int): 0 = not available, 1 = available.
        m_overtakeActive (int): 0 = not active, 1 = active.
        m_overtakeActivationDistance (int): metres until Overtake Mode becomes available (0 = N/A).
        m_2026Regulations (int): 0 = pre-2026 vehicle, 1 = 2026 regulations applicable.
        m_drivingWrongWay (int): 0 = correct direction, 1 = wrong way.
    """

    COMPILED_PACKET_STRUCT = struct.Struct("<"
        "B"  # uint8  m_activeAeroMode
        "B"  # uint8  m_activeAeroAvailable
        "H"  # uint16 m_activeAeroActivationDistance
        "B"  # uint8  m_overtakeAvailable
        "B"  # uint8  m_overtakeActive
        "H"  # uint16 m_overtakeActivationDistance
        "B"  # uint8  m_2026Regulations
        "B"  # uint8  m_drivingWrongWay
    )
    PACKET_LEN = COMPILED_PACKET_STRUCT.size  # 10 bytes

    __slots__ = (
        "m_activeAeroMode",
        "m_activeAeroAvailable",
        "m_activeAeroActivationDistance",
        "m_overtakeAvailable",
        "m_overtakeActive",
        "m_overtakeActivationDistance",
        "m_2026Regulations",
        "m_drivingWrongWay",
    )

    def __init__(self, data: bytes) -> None:
        self._parse(data)

    def _parse(self, data: bytes) -> None:
        (
            self.m_activeAeroMode,
            self.m_activeAeroAvailable,
            self.m_activeAeroActivationDistance,
            self.m_overtakeAvailable,
            self.m_overtakeActive,
            self.m_overtakeActivationDistance,
            self.m_2026Regulations,
            self.m_drivingWrongWay,
        ) = self.COMPILED_PACKET_STRUCT.unpack(data)

    def __str__(self) -> str:
        return (
            f"CarTelemetry2Data("
            f"ActiveAeroMode: {self.m_activeAeroMode}, "
            f"ActiveAeroAvailable: {self.m_activeAeroAvailable}, "
            f"ActiveAeroActivationDistance: {self.m_activeAeroActivationDistance}, "
            f"OvertakeAvailable: {self.m_overtakeAvailable}, "
            f"OvertakeActive: {self.m_overtakeActive}, "
            f"OvertakeActivationDistance: {self.m_overtakeActivationDistance}, "
            f"2026Regulations: {self.m_2026Regulations}, "
            f"DrivingWrongWay: {self.m_drivingWrongWay})"
        )

    def toJSON(self) -> Dict[str, Any]:
        return {
            "active-aero-mode": self.m_activeAeroMode,
            "active-aero-available": self.m_activeAeroAvailable,
            "active-aero-activation-distance": self.m_activeAeroActivationDistance,
            "overtake-available": self.m_overtakeAvailable,
            "overtake-active": self.m_overtakeActive,
            "overtake-activation-distance": self.m_overtakeActivationDistance,
            "2026-regulations": self.m_2026Regulations,
            "driving-wrong-way": self.m_drivingWrongWay,
        }

    def __eq__(self, other: "CarTelemetry2Data") -> bool:
        if not isinstance(other, CarTelemetry2Data):
            return False
        return (
            self.m_activeAeroMode == other.m_activeAeroMode
            and self.m_activeAeroAvailable == other.m_activeAeroAvailable
            and self.m_activeAeroActivationDistance == other.m_activeAeroActivationDistance
            and self.m_overtakeAvailable == other.m_overtakeAvailable
            and self.m_overtakeActive == other.m_overtakeActive
            and self.m_overtakeActivationDistance == other.m_overtakeActivationDistance
            and self.m_2026Regulations == other.m_2026Regulations
            and self.m_drivingWrongWay == other.m_drivingWrongWay
        )

    def __ne__(self, other: "CarTelemetry2Data") -> bool:
        return not self.__eq__(other)

    def to_bytes(self) -> bytes:
        return self.COMPILED_PACKET_STRUCT.pack(
            self.m_activeAeroMode,
            self.m_activeAeroAvailable,
            self.m_activeAeroActivationDistance,
            self.m_overtakeAvailable,
            self.m_overtakeActive,
            self.m_overtakeActivationDistance,
            self.m_2026Regulations,
            self.m_drivingWrongWay,
        )

    @classmethod
    def from_values(cls,
        active_aero_mode: int,
        active_aero_available: int,
        active_aero_activation_distance: int,
        overtake_available: int,
        overtake_active: int,
        overtake_activation_distance: int,
        regulations_2026: int,
        driving_wrong_way: int) -> "CarTelemetry2Data":
        return cls(cls.COMPILED_PACKET_STRUCT.pack(
            active_aero_mode,
            active_aero_available,
            active_aero_activation_distance,
            overtake_available,
            overtake_active,
            overtake_activation_distance,
            regulations_2026,
            driving_wrong_way,
        ))


class PacketCarTelemetry2Data(F1PacketBase):
    """
    F1 2026 packet containing active aero and overtake telemetry for all 24 cars.

    Attributes:
        m_header (PacketHeader): Packet header.
        m_carTelemetry2Data (List[CarTelemetry2Data]): Per-car telemetry2 data, 24 entries.
    """

    NUM_CARS = 24

    __slots__ = ("m_carTelemetry2Data",)

    def __init__(self, header: PacketHeader, packet: bytes) -> None:
        super().__init__(header)
        self.m_carTelemetry2Data: List[CarTelemetry2Data]
        self.m_carTelemetry2Data, _ = CarTelemetry2Data.parse_array(
            data=packet,
            offset=0,
            item_len=CarTelemetry2Data.PACKET_LEN,
            count=self.NUM_CARS,
            max_count=self.NUM_CARS,
        )

    def __str__(self) -> str:
        cars_str = ", ".join(str(c) for c in self.m_carTelemetry2Data)
        return f"PacketCarTelemetry2Data(Header: {self.m_header}, Cars: [{cars_str}])"

    def toJSON(self, include_header: bool = False) -> Dict[str, Any]:
        json_data = {
            "car-telemetry-2-data": [c.toJSON() for c in self.m_carTelemetry2Data],
        }
        if include_header:
            json_data["header"] = self.m_header.toJSON()
        return json_data

    def __eq__(self, other: "PacketCarTelemetry2Data") -> bool:
        if not isinstance(other, PacketCarTelemetry2Data):
            return False
        return (
            self.m_header == other.m_header
            and self.m_carTelemetry2Data == other.m_carTelemetry2Data
        )

    def __ne__(self, other: "PacketCarTelemetry2Data") -> bool:
        return not self.__eq__(other)

    def to_bytes(self) -> bytes:
        raw = self.m_header.to_bytes()
        raw += b"".join(c.to_bytes() for c in self.m_carTelemetry2Data)
        return raw

    @classmethod
    def from_values(cls,
                    header: PacketHeader,
                    car_telemetry2_data: List[CarTelemetry2Data]) -> "PacketCarTelemetry2Data":
        raw = b"".join(c.to_bytes() for c in car_telemetry2_data)
        return cls(header, raw)
