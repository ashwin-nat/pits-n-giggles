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

def sendBytesUDP(data: bytes, udp_ip: str, udp_port: int) -> int:
    """Send the given list of bytes to the specified destination over UDP

    Args:
        data (bytes): List of raw bytes to be sent
        udp_ip (str): The destination IP address
        udp_port (int): The destination UDP port

    Returns:
        int: Number of bytes sent
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        return udp_socket.sendto(data, (udp_ip, udp_port))

def formatFileSize(num_bytes:int) -> str:
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

def main():

    # Parse the command line args
    parser = argparse.ArgumentParser(description="Send captured F1 packets over TCP")
    parser.add_argument("--file-name", help="Name of the capture file")
    parser.add_argument("--ip-addr", default="127.0.0.1", help="Server IP address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=20777, help="Server port number (default: 20777)")
    parser.add_argument("--packet-loss", type=int, default=None, help="The packet loss percentage to simulate")
    parser.add_argument('--no-nagle',  action='store_true', help="Disable Nagle's Algorithm in TCP mode")
    parser.add_argument('--udp-mode',  action='store_true',
                            help="Send telemetry over UDP considering timestamps as well")
    parser.add_argument('--speed-multiplier', type=float, default=1.0, help="Speed multiplier for the replay speed "
                                                                            "Applicable only for UDP mode.")

    args = parser.parse_args()
    client_socket = None

    if not args.file_name:
        print("Error: Please provide the --file-name argument.")
        return

    if args.udp_mode and args.no_nagle:
        print("--no-nagle and --udp-mode are mutually exclusive")
        return

    try:
        # Read and parse the file
        captured_packets = F1PacketCapture(args.file_name)
        total_bytes = 0
        dropped_packets = 0
        if args.udp_mode:
            total_packets = captured_packets.getNumPackets()
            prev_timestamp = None

            progress_bar = tqdm(
                total=total_packets,
                desc='Sending Packets',
                unit='packet',
                mininterval=0.1
            )
            for timestamp, packet in captured_packets.getPackets():
                progress_bar.update(1)
                if prev_timestamp is not None:
                    sleep_duration = timestamp - prev_timestamp
                    if sleep_duration == 0:
                        sleep_duration = 0.01667 # 16.67ms is time interval on 60 Hz telemetry rate.
                    time.sleep(sleep_duration/args.speed_multiplier)

                if args.packet_loss and should_drop(args.packet_loss):
                    dropped_packets += 1
                    continue

                total_bytes += sendBytesUDP(packet, args.ip_addr, args.port)
                prev_timestamp = timestamp
        else:
            # TCP mode
            total_packets = captured_packets.getNumPackets()
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((args.ip_addr, args.port))

            # Disable Nagle's algorithm if specified
            if args.no_nagle:
                client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

            progress_bar = tqdm(
                total=total_packets,
                desc='Sending Packets',
                unit='packet',
                mininterval=0.1,
                miniters=1
            )

            # Send each packet one by one and update the progress bar
            for _, packet in captured_packets.getPackets():
                progress_bar.update(1)
                if args.packet_loss and should_drop(args.packet_loss):
                    dropped_packets += 1
                    continue
                # Prefix each message with its length (as a 4-byte integer)
                message_length = len(packet)
                message_length_bytes = struct.pack('!I', message_length)

                # Send the message length followed by the actual message
                client_socket.sendall(message_length_bytes + packet)
                total_bytes += message_length


            print('\nSent ' + str(total_packets) + ' packets.')
            print(f'Sent {str(total_bytes)} bytes.')
            if args.packet_loss:
                dropped_rate = (dropped_packets / total_packets) * 100.0
                print(f'Dropped {dropped_packets} packets ({dropped_rate:.3f}% loss).')

    except KeyboardInterrupt:
        print("Client terminated by user.")
    except FileNotFoundError:
        print(f"Error: File '{args.file_name}' not found.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Close the socket in the finally block to ensure cleanup
        if client_socket:
            client_socket.close()

if __name__ == "__main__":
    main()
