from udp_listener import UDPListener
from f1_types import *
import struct
import logging
import binascii

logging.basicConfig(filename='f1-telemetry.log',
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

class F12023TelemetryManager:

    def __init__(self, port_number):

        self.m_udp_listener = UDPListener(port_number, "localhost")
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
        self.m_packet_type_map = {
            F1PacketType.MOTION : PacketMotionData,
            # F1PacketType.SESSION : PacketSessionData,
            # F1PacketType.LAP_DATA : PacketLapData,
            # F1PacketType.EVENT : PacketEventData,
            # F1PacketType.PARTICIPANTS : PacketParticipantsData,
            # F1PacketType.CAR_SETUPS : PacketCarSetupData,
            # F1PacketType.CAR_TELEMETRY : PacketCarTelemetryData,
            # F1PacketType.CAR_STATUS : PacketCarStatusData,
            # F1PacketType.FINAL_CLASSIFICATION : PacketFinalClassificationData,
            # F1PacketType.LOBBY_INFO : PacketLobbyInfoData,
            # F1PacketType.CAR_DAMAGE : PacketCarDamageData,
            # F1PacketType.SESSION_HISTORY : PacketSessionHistoryData,
            # F1PacketType.TYRE_SETS : PacketTyreSetsData,
            # F1PacketType.MOTION_EX : PacketMotionExData,
        }

    def registerCallback(self, packet_type, callback):

        if not F1PacketType.isValid(packet_type):
            raise ValueError('Invalid packet type in registering callback')

        self.m_callbacks[packet_type] = callback

    def run(self):

        while True:
            data = self.m_udp_listener.getNextMessage()
            if len(data) < F1_23_PACKET_HEADER_LEN:
                logging.debug('skipping incomplete packet')
            header_raw = data[:F1_23_PACKET_HEADER_LEN]
            payload_raw = data[F1_23_PACKET_HEADER_LEN:]
            logging.debug('received %d bytes packet. header dump =\n%s' %(len(data), self.__packetDump(header_raw)))
            header = PacketHeader(header_raw)
            logging.debug('received header. parsed contents is ' + str(header))

            if not header.isPacketTypeSupported():
                logging.debug('unsupported header')
                continue
            is_packet_parser_available = (header.m_packetId in self.m_packet_type_map)
            if is_packet_parser_available:
                try:
                    packet = self.m_packet_type_map[header.m_packetId](header, payload_raw)
                except InvalidPacketLengthError as e:
                    logging.error("Cannot parse packet of type " + header.m_packetId + ". Error = " + e)
            else:
                continue
            callback = self.m_callbacks.get(header.m_packetId, None)
            if callback:
                callback(packet)

    def __packetDump(self, data):

        # Convert the raw bytes to a string of hex values in upper case with a space between each byte
        hex_string = binascii.hexlify(data).decode('utf-8').upper()

        # Add a space between each pair of characters and format as 8 bytes per line
        formatted_hex_string = ''
        i=0
        for char in hex_string:
            formatted_hex_string += char
            if i%32 == 0:
                formatted_hex_string += '\n'
            elif i%16 == 0:
                formatted_hex_string +='    '
            elif i%2 == 0:
                formatted_hex_string += ' '
            i += 1

        return formatted_hex_string






