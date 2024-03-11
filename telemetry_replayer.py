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

import socket
from packet_cap import F1PacketCapture
import argparse
from tqdm import tqdm
import struct
import time

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
    parser.add_argument('--no-nagle',  action='store_true', help="Disable Nagle's Algorithm in TCP mode")
    parser.add_argument('--udp-mode',  action='store_true',
                            help="Send telemetry over UDP considering timestamps as well")

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
        if args.udp_mode:
            total_bytes = 0
            total_packets = captured_packets.getNumPackets()
            prev_timestamp = captured_packets.getFirstTimestamp()

            progress_bar = tqdm(
                total=total_packets,
                desc='Sending Packets',
                unit='packet',
                mininterval=0.1
            )
            for timestamp, packet in captured_packets.getPackets():

                total_bytes += sendBytesUDP(packet, args.ip_addr, args.port)
                sleep_duration = timestamp - prev_timestamp
                prev_timestamp = timestamp
                assert (sleep_duration > 0)
                progress_bar.update(1)
                time.sleep(sleep_duration)
        else:
            # TCP mode
            total_bytes = 0
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

                # Prefix each message with its length (as a 4-byte integer)
                message_length = len(packet)
                message_length_bytes = struct.pack('!I', message_length)

                # Send the message length followed by the actual message
                client_socket.sendall(message_length_bytes + packet)
                total_bytes += message_length

                progress_bar.update(1)

            print('\nSent ' + str(total_packets) + ' packets.')
            print('Sent ' + str(total_bytes) + ' bytes.')

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
