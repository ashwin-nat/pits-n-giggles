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
# pylint: skip-file

import socket
import argparse
from tqdm import tqdm
import struct
import time
import sys
import os
import random
from typing import Callable, Optional, Tuple, Iterator

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now perform the import
from lib.packet_cap import F1PacketCapture

def should_drop(probability_percentage: int) -> bool:
    """
    Returns True with the given probability percentage.

    Args:
        probability_percentage (int): A value between 0 and 100 representing the probability.

    Returns:
        bool: True if should drop this packet
    """
    if not (0 <= probability_percentage <= 100):
        raise ValueError("Probability percentage must be between 0 and 100.")
    return random.uniform(0, 100) < probability_percentage

def send_bytes_udp(data: bytes, udp_ip: str, udp_port: int) -> int:
    """Send the given list of bytes to the specified destination over UDP

    Args:
        data (bytes): List of raw bytes to be sent
        udp_ip (str): The destination IP address
        udp_port (int): The destination UDP port

    Returns:
        int: Number of bytes sent
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        return udp_socket.sendto(data, (udp_ip, udp_port))

def format_file_size(num_bytes: int) -> str:
    """Get human readable string containing file size

    Args:
        num_bytes (int): The number of bytes in integer form

    Returns:
        str: The formatted size string
    """
    sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
    if num_bytes == 0:
        return '0 Byte'

    i = 0
    while num_bytes >= 1024 and i < len(sizes) - 1:
        num_bytes /= 1024.0
        i += 1

    return f"{round(num_bytes, 2)} {sizes[i]}"

def send_telemetry_data(
    file_name: str,
    ip_addr: str = "127.0.0.1",
    port: int = 20777,
    udp_mode: bool = False,
    speed_multiplier: float = 1.0,
    packet_loss: Optional[int] = None,
    no_nagle: bool = False,
    printer: Optional[Callable[[str], None]] = None,
    show_progress: bool = True
) -> Tuple[int, int, int]:
    """
    Send captured F1 telemetry packets to a specified destination.

    Args:
        file_name (str): Name of the capture file
        ip_addr (str): Destination IP address (default: "127.0.0.1")
        port (int): Destination port number (default: 20777)
        udp_mode (bool): Send telemetry over UDP with timestamps (default: False, uses TCP)
        speed_multiplier (float): Speed multiplier for replay (UDP mode only, default: 1.0)
        packet_loss (Optional[int]): Packet loss percentage to simulate (0-100)
        no_nagle (bool): Disable Nagle's Algorithm in TCP mode (default: False)
        printer (Optional[Callable[[str], None]]): Custom print function (default: print)
        show_progress (bool): Show progress bar (default: True)

    Returns:
        Tuple[int, int, int]: (total_packets_sent, total_bytes_sent, dropped_packets)

    Raises:
        ValueError: If arguments are invalid
        FileNotFoundError: If capture file not found
        ConnectionError: If connection to destination fails
    """
    if printer is None:
        printer = print

    if udp_mode and no_nagle:
        raise ValueError("--no-nagle and --udp-mode are mutually exclusive")

    # Read and parse the file
    captured_packets = F1PacketCapture(file_name=file_name)
    printer(f'Loaded {file_name} with {captured_packets.getNumPackets()} packets.')
    printer(f'File format ver: {captured_packets.m_header._major_version}.{captured_packets.m_header._minor_version}')
    printer(f'Compressed: {captured_packets.m_header.is_compressed}')

    total_packets = captured_packets.getNumPackets()
    total_bytes = 0
    dropped_packets = 0
    client_socket = None

    try:
        if udp_mode:
            total_bytes, dropped_packets = _send_udp_mode(
                captured_packets=captured_packets,
                total_packets=total_packets,
                ip_addr=ip_addr,
                port=port,
                speed_multiplier=speed_multiplier,
                packet_loss=packet_loss,
                show_progress=show_progress
            )
        else:
            client_socket, total_bytes, dropped_packets = _send_tcp_mode(
                captured_packets=captured_packets,
                total_packets=total_packets,
                ip_addr=ip_addr,
                port=port,
                no_nagle=no_nagle,
                packet_loss=packet_loss,
                show_progress=show_progress
            )

        packets_sent = total_packets - dropped_packets
        printer(f'\nSent {packets_sent} packets.')
        printer(f'Sent {total_bytes} bytes ({format_file_size(total_bytes)}).')
        if packet_loss:
            dropped_rate = (dropped_packets / total_packets) * 100.0
            printer(f'Dropped {dropped_packets} packets ({dropped_rate:.3f}% loss).')

        return packets_sent, total_bytes, dropped_packets

    finally:
        if client_socket:
            client_socket.close()


def _send_udp_mode(
    captured_packets: F1PacketCapture,
    total_packets: int,
    ip_addr: str,
    port: int,
    speed_multiplier: float,
    packet_loss: Optional[int],
    show_progress: bool
) -> Tuple[int, int]:
    """Send packets in UDP mode with timing."""
    total_bytes = 0
    dropped_packets = 0
    prev_timestamp = None

    progress_bar = tqdm(
        total=total_packets,
        desc='Sending Packets',
        unit='packet',
        mininterval=2,
        disable=not show_progress
    )

    for timestamp, packet in captured_packets.getPackets():
        progress_bar.update(1)

        if prev_timestamp is not None:
            sleep_duration = timestamp - prev_timestamp
            if sleep_duration == 0:
                sleep_duration = 0.01667  # 16.67ms is time interval on 60 Hz telemetry rate.
            time.sleep(sleep_duration / speed_multiplier)

        if packet_loss and should_drop(packet_loss):
            dropped_packets += 1
            prev_timestamp = timestamp
            continue

        try:
            total_bytes += send_bytes_udp(packet, ip_addr, port)
        except Exception as e:
            progress_bar.close()
            raise ConnectionError(f"Failed to send to {ip_addr}:{port} — {e}")

        prev_timestamp = timestamp

    progress_bar.close()
    return total_bytes, dropped_packets


def _send_tcp_mode(
    captured_packets: F1PacketCapture,
    total_packets: int,
    ip_addr: str,
    port: int,
    no_nagle: bool,
    packet_loss: Optional[int],
    show_progress: bool
) -> Tuple[socket.socket, int, int]:
    """Send packets in TCP mode."""
    total_bytes = 0
    dropped_packets = 0

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((ip_addr, port))
    except Exception as e:
        raise ConnectionError(f"Failed to connect to {ip_addr}:{port} — {e}")

    # Disable Nagle's algorithm if specified
    if no_nagle:
        client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    progress_bar = tqdm(
        total=total_packets,
        desc='Sending Packets',
        unit='packet',
        mininterval=2,
        disable=not show_progress
    )

    # Send each packet one by one and update the progress bar
    for _, packet in captured_packets.getPackets():
        progress_bar.update(1)

        if packet_loss and should_drop(packet_loss):
            dropped_packets += 1
            continue

        # Prefix each message with its length (as a 4-byte integer)
        message_length = len(packet)
        message_length_bytes = struct.pack('!I', message_length)

        # Send the message length followed by the actual message
        try:
            client_socket.sendall(message_length_bytes + packet)
        except Exception as e:
            progress_bar.close()
            raise ConnectionError(f"Failed to send to {ip_addr}:{port} — {e}")

        total_bytes += message_length

    progress_bar.close()
    return client_socket, total_bytes, dropped_packets


def main():
    """Main entry point for command-line execution."""
    # Parse the command line args
    parser = argparse.ArgumentParser(description="Send captured F1 packets over TCP/UDP")
    parser.add_argument("--file-name", required=True, help="Name of the capture file")
    parser.add_argument("--ip-addr", default="127.0.0.1", help="Server IP address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=20777, help="Server port number (default: 20777)")
    parser.add_argument("--packet-loss", type=int, default=None, help="The packet loss percentage to simulate")
    parser.add_argument('--no-nagle', action='store_true', help="Disable Nagle's Algorithm in TCP mode")
    parser.add_argument('--udp-mode', action='store_true',
                        help="Send telemetry over UDP considering timestamps as well")
    parser.add_argument('--speed-multiplier', type=float, default=1.0,
                        help="Speed multiplier for the replay speed (UDP mode only)")

    args = parser.parse_args()

    try:
        send_telemetry_data(
            file_name=args.file_name,
            ip_addr=args.ip_addr,
            port=args.port,
            udp_mode=args.udp_mode,
            speed_multiplier=args.speed_multiplier,
            packet_loss=args.packet_loss,
            no_nagle=args.no_nagle
        )
    except KeyboardInterrupt:
        print("\nClient terminated by user.")
        sys.exit(0)
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: Invalid argument - {e}")
        sys.exit(1)
    except ConnectionError as e:
        print(f"Error: Connection failed - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
