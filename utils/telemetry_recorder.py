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

import sys
import os
import tkinter as tk
from tkinter import messagebox, filedialog
from typing import List

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.f1_types import F1Utils, LapData, ResultStatus
from lib.packet_cap import F1PacketCapture
import lib.overtake_analyzer as OvertakeAnalyzer
from flask import Flask, render_template, request, jsonify
from src.telemetry_manager import F1TelemetryManager
from threading import Thread, Lock


class PacketCaptureTable:
    """Thread safe container for F1PacketCapture instance.
    """

    def __init__(self) -> None:
        """
        Initialize the object by creating a new F1PacketCapture instance and a Lock instance.
        """
        self.m_packet_capture = F1PacketCapture()
        self.m_lock = Lock()

    def add(self, packet: List[bytes]) -> None:
        """
        Add a packet to the packet list while acquiring a lock to ensure thread safety.

        Parameters:
            packet (List[bytes]): The packet to be added to the table.
        """
        with self.m_lock:
            self.m_packet_capture.add(packet)

    def clear(self) -> None:
        """
        Clear the packet history table and reset the number of packets.
        """
        with self.m_lock:
            self.m_packet_capture.clear()

    def getNumPackets(self) -> int:
        """
        Returns the number of packets captured by the packet capture object.
        """
        with self.m_lock:
            return self.m_packet_capture.getNumPackets()

g_capture_table = PacketCaptureTable()

class SimpleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("F1 Telemetry Recorder")

        # Set the default window size
        self.root.geometry("400x300")

        self.clear_button = tk.Button(root, text="Clear Memory", command=self.clear_memory)
        self.clear_button.pack(pady=10)

        self.save_button = tk.Button(root, text="Save to File", command=self.save_to_file)
        self.save_button.pack(pady=10)

    def clear_memory(self):
        global g_capture_table
        g_capture_table.clear()
        self.memory_data = ""
        messagebox.showinfo("Info", "Memory cleared!")

    def save_to_file(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".f1pcap",
                                                 filetypes=[("Custom files", "*.f1pcap"), ("All files", "*.*")])
        if file_path:
            global g_capture_table
            _, num_packets, _ = g_capture_table.m_packet_capture.dumpToFile(file_path)
            g_capture_table.clear()
            if num_packets == 0:
                messagebox.showinfo("Info", "No data to save!")
            else:
                messagebox.showinfo("Info", f"Data has been successfully written to file {file_path}. "
                                    f"Number of packets is {num_packets}")

def raw_packet_callback(raw_packet: bytes):
    global g_capture_table
    g_capture_table.add(raw_packet)

def telemetry_manager_thread():
    telemetry_manager = F1TelemetryManager(port_number=20777)
    telemetry_manager.registerRawPacketCallback(raw_packet_callback)
    telemetry_manager.run()

if __name__ == "__main__":

    f1_telemetry_thread = Thread(target=telemetry_manager_thread)
    f1_telemetry_thread.daemon = True
    f1_telemetry_thread.start()
    root = tk.Tk()
    app = SimpleApp(root)
    root.mainloop()