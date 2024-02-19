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
    """_summary_

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
    parser = argparse.ArgumentParser(description="Send captured F1 packets over UDP")
    parser.add_argument("--file-name", help="Name of the capture file")
    parser.add_argument("--udp_ip", default="127.0.0.1", help="UDP IP address (default: 127.0.0.1)")
    parser.add_argument("--udp_port", type=int, default=20777, help="UDP port number (default: 20777)")
    args = parser.parse_args()

    if not args.file_name:
        print("Error: Please provide the --file-name argument.")
        return

    try:

        # Read and parse the file
        captured_packets = F1PacketCapture(args.file_name)
        counter = 0
        total_bytes = 0
        total_packets = captured_packets.getNumPackets()

        # Send each packet one by one and update the progress bar
        for _, data in tqdm(captured_packets.getPackets(), desc='Sending Packets', unit='packet', total=total_packets):
            counter += 1
            total_bytes += sendBytesUDP(data, args.udp_ip, args.udp_port)
            if (counter % 1000 == 0):
                time.sleep(0.001)

        print(f'Total bytes sent: {formatFileSize(total_bytes)}')
        print(total_bytes)

    except FileNotFoundError:
        print(f"Error: File '{args.file_name}' not found.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
