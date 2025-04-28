import sys

import lib.packet_cap as pcap

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python compress_pcap.py <input_file> <output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    capture = pcap.F1PacketCapture(file_name=input_file)
    capture.set_compressed(True)
    capture.dumpToFile(output_file)