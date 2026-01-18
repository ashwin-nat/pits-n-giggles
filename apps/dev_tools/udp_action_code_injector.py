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

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

import argparse
import socket
import struct

from lib.f1_types import F1PacketType, PacketEventData, PacketHeader

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def get_button_event_obj(button_code: int) -> PacketEventData:
    return PacketEventData.from_values(
        header=PacketHeader.from_values(
            packet_format=2025,
            game_year=25,
            game_major_version=1,
            game_minor_version=1,
            packet_version=1,
            packet_type=F1PacketType.EVENT,
            session_uid=1,
            session_time=1.0,
            frame_identifier=1,
            overall_frame_identifier=1,
            player_car_index=19,
            secondary_player_car_index=255
        ),
        event_type=PacketEventData.EventPacketType.BUTTON_STATUS,
        event_details=PacketEventData.Buttons.from_status(
            button_status=button_code
        ))

def get_udp_action_code_obj(udp_action_code: int) -> PacketEventData:
    return get_button_event_obj(button_code=PacketEventData.Buttons.udp_action_flag(udp_action_code))

def send_bytes_udp(data: bytes, udp_ip: str, udp_port: int) -> int:
    """Send the given list of bytes to the specified destination over UDP

    Args:
        data (bytes): List of raw bytes to be sent
        udp_ip (str): The destination IP address
        udp_port (int): The destination UDP port

    Returns:
        int: Number of bytes sent
    """
    print(f"Sending {len(data)} bytes to UDP {udp_ip}:{udp_port}")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        return udp_socket.sendto(data, (udp_ip, udp_port))

def send_bytes_tcp(
    data: bytes,
    tcp_ip: str,
    tcp_port: int,
    no_nagle: bool = False
) -> int:
    """
    Send a single F1 UDP-format packet over TCP using
    4-byte big-endian length prefix framing.
    """

    message_length = len(data)
    message_length_bytes = struct.pack("!I", message_length)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_socket:
        tcp_socket.connect((tcp_ip, tcp_port))

        if no_nagle:
            tcp_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        tcp_socket.sendall(message_length_bytes + data)

    return message_length

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send UDP action code packet over TCP/UDP")
    parser.add_argument("--action-code", required=True, type=int, help="UDP action code number")
    parser.add_argument("--ip-addr", default="127.0.0.1", help="Server IP address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=20777, help="Server port number (default: 20777)")
    parser.add_argument('--udp-mode', action='store_true', default=False,
                        help="Send telemetry over UDP considering timestamps as well")
    args = parser.parse_args()

    pkt_obj = get_udp_action_code_obj(args.action_code)
    test_obj = PacketEventData(pkt_obj.m_header, pkt_obj.to_bytes(include_header=False))
    assert test_obj == pkt_obj

    raw_pkt = pkt_obj.to_bytes(include_header=True)
    if args.udp_mode:
        ret = send_bytes_udp(raw_pkt, args.ip_addr, args.port)
        print(f"Sent {ret} bytes")
    else:
        raise NotImplementedError
