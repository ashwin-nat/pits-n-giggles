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

from f1_types import *
from udp_listener import UDPListener
from typing import Callable

# ------------------------- CLASSES --------------------------------------------

class F12023TelemetryManager:
    """
    This class is used to act as the interface between the raw parsers and the user application layer.
    This class handles the following tasks
        1 - manage the socket and receive the data
        2 - identify the packet type and parse the packet accordingly
        3 - identify the callback function that the user has registered and invoke it for the incoming packet type
    """

    packet_type_map = {
        F1PacketType.MOTION : PacketMotionData,
        F1PacketType.SESSION : PacketSessionData,
        F1PacketType.LAP_DATA : PacketLapData,
        F1PacketType.EVENT : PacketEventData,
        F1PacketType.PARTICIPANTS : PacketParticipantsData,
        F1PacketType.CAR_SETUPS : PacketCarSetupData,
        F1PacketType.CAR_TELEMETRY : PacketCarTelemetryData,
        F1PacketType.CAR_STATUS : PacketCarStatusData,
        F1PacketType.FINAL_CLASSIFICATION : PacketFinalClassificationData,
        F1PacketType.LOBBY_INFO : PacketLobbyInfoData,
        F1PacketType.CAR_DAMAGE : PacketCarDamageData,
        F1PacketType.SESSION_HISTORY : PacketSessionHistoryData,
        F1PacketType.TYRE_SETS : PacketTyreSetsData,
        F1PacketType.MOTION_EX : PacketMotionExData,
    }


    def __init__(self, port_number: int):
        """Init the telemetry manager app and all its sub components

        Args:
            port_number (int): The port number to listen in on
        """

        self.m_udp_listener = UDPListener(port_number, "0.0.0.0")
        self.m_callbacks = {
            F1PacketType.MOTION : None,
            F1PacketType.SESSION : None,
            F1PacketType.LAP_DATA : None,
            F1PacketType.EVENT : None,
            F1PacketType.PARTICIPANTS : None,
            F1PacketType.CAR_SETUPS : None,
            F1PacketType.CAR_TELEMETRY : None,
            F1PacketType.CAR_STATUS : None,
            F1PacketType.FINAL_CLASSIFICATION : None,
            F1PacketType.LOBBY_INFO : None,
            F1PacketType.CAR_DAMAGE : None,
            F1PacketType.SESSION_HISTORY : None,
            F1PacketType.TYRE_SETS : None,
            F1PacketType.MOTION_EX : None,
        }

    def registerCallback(self, packet_type: F1PacketType, callback: Callable) -> None:
        """
        Registers a callback function for a specific F1 packet type.

        Args:
            packet_type (F1PacketType): The type of F1 packet for which the callback is registered.
            callback (Callable): The callback function to be executed when a packet of the specified type is received.
                It should be a function that takes one argument of the corresponding packet type.
                    e.g. if registering for F1PacketType.MOTION event, the arg passed will be PacketMotionData
                    Refer to the the below table for all mappings
                        # Packet Type Mappings:
                        +-------------------------------------+-------------------------------------------+
                        | F1PacketType                        | Corresponding Packet Class                |
                        +-------------------------------------+-------------------------------------------+
                        | F1PacketType.MOTION                 | PacketMotionData                          |
                        | F1PacketType.SESSION                | PacketSessionData                         |
                        | F1PacketType.LAP_DATA               | PacketLapData                             |
                        | F1PacketType.EVENT                  | PacketEventData                           |
                        | F1PacketType.PARTICIPANTS           | PacketParticipantsData                    |
                        | F1PacketType.CAR_SETUPS             | PacketCarSetupData                        |
                        | F1PacketType.CAR_TELEMETRY          | PacketCarTelemetryData                    |
                        | F1PacketType.CAR_STATUS             | PacketCarStatusData                       |
                        | F1PacketType.FINAL_CLASSIFICATION   | PacketFinalClassificationData             |
                        | F1PacketType.LOBBY_INFO             | PacketLobbyInfoData                       |
                        | F1PacketType.CAR_DAMAGE             | PacketCarDamageData                       |
                        | F1PacketType.SESSION_HISTORY        | PacketSessionHistoryData                  |
                        | F1PacketType.TYRE_SETS              | PacketTyreSetsData                        |
                        | F1PacketType.MOTION_EX              | PacketMotionExData                        |
                        +-------------------------------------+-------------------------------------------+

        Raises:
            ValueError: If the provided packet_type is not a valid F1PacketType.
        """
        if not F1PacketType.isValid(packet_type):
            raise ValueError('Invalid packet type in registering callback')
        self.m_callbacks[packet_type] = callback

    def run(self) -> None:
        """Run the telemetry client
        """

        # Run the client indefinitely
        while True:

            # Get next UDP message
            data = self.m_udp_listener.getNextMessage()
            if len(data) < F1_23_PACKET_HEADER_LEN:
                # skip incomplete packet
                continue

            # Parse the header
            header_raw = data[:F1_23_PACKET_HEADER_LEN]
            header = PacketHeader(header_raw)
            if not header.isPacketTypeSupported():
                # Unsupported packet type, skip
                continue

            # Parse the payload and call the registered callback
            payload_raw = data[F1_23_PACKET_HEADER_LEN:]
            try:
                packet = F12023TelemetryManager.packet_type_map[header.m_packetId](header, payload_raw)
            except InvalidPacketLengthError as e:
                print("Cannot parse packet of type " + header.m_packetId + ". Error = " + e)
            callback = self.m_callbacks.get(header.m_packetId, None)
            if callback:
                callback(packet)
