import socket
import ipaddress
from packet_cap import F1PacketCapture
import argparse
from tqdm import tqdm
import sys

def send_bytes_to_udp(data: bytes, udp_ip: str, udp_port: int) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        return udp_socket.sendto(data, (udp_ip, udp_port))

def format_file_size(bytes):
    sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
    if bytes == 0:
        return '0 Byte'

    i = 0
    while bytes >= 1024 and i < len(sizes) - 1:
        bytes /= 1024.0
        i += 1

    return f"{round(bytes, 2)} {sizes[i]}"

def main():
    parser = argparse.ArgumentParser(description="Send captured F1 packets over UDP")
    parser.add_argument("--file-name", help="Name of the capture file")
    parser.add_argument("--udp_ip", default="127.0.0.1", help="UDP IP address (default: 127.0.0.1)")
    parser.add_argument("--udp_port", type=int, default=20777, help="UDP port number (default: 20777)")

    args = parser.parse_args()

    if not args.file_name:
        print("Error: Please provide the --file-name argument.")
        return

    try:
        captured_packets = F1PacketCapture(args.file_name)

        counter = 0
        total_bytes = 0
        total_packets = captured_packets.getNumPackets()

        for _, data in tqdm(captured_packets.getPackets(), desc='Sending Packets', unit='packet', total=total_packets):
            counter += 1
            total_bytes += send_bytes_to_udp(data, args.udp_ip, args.udp_port)

        print(f'Total bytes sent: {format_file_size(total_bytes)}')
        print(total_bytes)

    except FileNotFoundError:
        print(f"Error: File '{args.file_name}' not found.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
