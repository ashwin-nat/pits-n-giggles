
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

import os
import sys
from typing import Tuple

from lib.packet_cap import F1PacketCapture

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def convert_file(src: str, dst: str) -> Tuple[int, int, int]:
    """Rewrite src in the current default compression, then check dst holds the same packets.

    Returns:
        (packet count, src size in bytes, dst size in bytes)

    Raises:
        ValueError: If dst does not read back identical to src. dst is left on disk for inspection.
    """
    assert os.path.normcase(os.path.abspath(src)) != os.path.normcase(os.path.abspath(dst)), "src and dst must differ"
    source = F1PacketCapture(file_name=src)
    source.set_compressed(True)
    source.dumpToFile(dst)

    # Compare loaded packets, not header counts: a source header can be stale, and dumpToFile rewrites it
    written = F1PacketCapture(file_name=dst)
    num_packets = len(source.m_packet_history)
    if num_packets != len(written.m_packet_history):
        raise ValueError(f"Packet count mismatch: {num_packets} vs {len(written.m_packet_history)}")
    for idx, (before, after) in enumerate(zip(source.getPackets(), written.getPackets())):
        if before != after:
            raise ValueError(f"Packet {idx} differs after conversion")
    return num_packets, os.path.getsize(src), os.path.getsize(dst)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python -m apps.dev_tools.compress_pcap <input_file> <output_file>")
        sys.exit(1)

    packet_count, old_size, new_size = convert_file(sys.argv[1], sys.argv[2])
    print(f"{packet_count} packets, {old_size / 1e6:.1f} MB -> {new_size / 1e6:.1f} MB")
