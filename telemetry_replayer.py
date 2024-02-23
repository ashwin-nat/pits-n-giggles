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
    args = parser.parse_args()

    if not args.file_name:
        print("Error: Please provide the --file-name argument.")
        return

    try:
        # Read and parse the file
        captured_packets = F1PacketCapture(args.file_name)
        total_bytes = 0
        total_packets = captured_packets.getNumPackets()
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((args.ip_addr, args.port))

        # Disable Nagle's algorithm
        client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        # Send each packet one by one and update the progress bar
        for _, message in tqdm(
            captured_packets.getPackets(),
            desc='Sending Packets',
            unit='packet',
            total=total_packets):

            # Prefix each message with its length (as a 4-byte integer)
            message_length = len(message)
            message_length_bytes = struct.pack('!I', message_length)

            # Send the message length followed by the actual message
            client_socket.sendall(message_length_bytes + message)
            total_bytes += message_length

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
