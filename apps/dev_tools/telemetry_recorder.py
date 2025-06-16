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

import asyncio
import sys
import os
import time
import tkinter as tk
from tkinter import messagebox, filedialog
from typing import List

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.packet_cap import F1PacketCapture
from lib.telemetry_manager import AsyncF1TelemetryManager
from lib.packet_forwarder import UDPForwarder
from threading import Thread, Lock, Condition
import queue

# Condition variable for signaling when the port is set
g_start_condition = Condition()
g_port_num = None
g_queue = queue.Queue()

class PacketCaptureTable:
    """Thread safe container for F1PacketCapture instance.
    """

    def __init__(self) -> None:
        """
        Initialize the object by creating a new F1PacketCapture instance and a Lock instance.
        """
        self.m_packet_capture = F1PacketCapture(compressed=True)
        self.m_lock = Lock()

    def add(self, packet: List[bytes]) -> None:
        """
        Add a packet to the packet list while acquiring a lock to ensure thread safety.

        Parameters:
            packet (List[bytes]): The packet to be added to the table.
        """
        with self.m_lock:
            self.m_packet_capture.add(packet)

    def clear(self) -> int:
        """
        Clear the packet history table and reset the number of packets.

        Returns:
            int: The number of packets cleared.
        """
        with self.m_lock:
            ret = self.m_packet_capture.getNumPackets()
            self.m_packet_capture.clear()
            return ret

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

        # Port Number Entry
        self.port_label = tk.Label(root, text="Port:")
        self.port_label.pack(pady=(10, 0))

        self.port_entry = tk.Entry(root)
        self.port_entry.insert(0, "20777")  # Default port
        self.port_entry.pack(pady=5)

        # Start Button
        self.start_button = tk.Button(root, text="Start!", command=self.start_capture)
        self.start_button.pack(pady=10)

        # Clear Memory Button (Initially Disabled)
        self.clear_button = tk.Button(root, text="Clear Memory", command=self.clear_memory, state="disabled")
        self.clear_button.pack(pady=10)

        # Save to File Button (Initially Disabled)
        self.save_button = tk.Button(root, text="Save to File", command=self.save_to_file, state="disabled")
        self.save_button.pack(pady=10)

    def start_capture(self):
        port = self.port_entry.get()
        if port.isdigit():
            print(f"Starting capture on port {port}")
            self.port_entry.config(state="disabled")  # Grey out/lock the text box
            self.start_button.config(state="disabled")  # Disable the Start button

            # Enable the other two buttons
            self.clear_button.config(state="normal")
            self.save_button.config(state="normal")

            global g_port_num
            g_port_num = int(port)
            with g_start_condition:
                g_start_condition.notify_all()

            # Signal the condition variable
            with g_start_condition:
                g_start_condition.notify_all()
        else:
            messagebox.showerror("Error", "Invalid port number. Please enter a valid number.")

    def clear_memory(self):
        global g_capture_table
        count = g_capture_table.clear()
        self.memory_data = ""
        messagebox.showinfo("Info", f"Memory cleared! Number of packets cleared: {count}")

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

async def async_telemetry_main():
    """Main function for async telemetry. This runs its own asyncio event loop"""
    global g_port_num
    global g_start_condition

    # Wait until start signal is received
    def wait_for_port():
        with g_start_condition:
            g_start_condition.wait()
        return g_port_num

    loop = asyncio.get_running_loop()
    port = await loop.run_in_executor(None, wait_for_port)

    print(f"[async telemetry] Starting server on port {port}")
    telemetry_manager = AsyncF1TelemetryManager(port_number=port)
    @telemetry_manager.on_raw_packet()
    async def handleRawPacket(packet: List[bytes]) -> None:
        """
        Handle raw telemetry packet.
        Parameters:
            packet (List[bytes]): The raw telemetry packet.
        """
        global g_capture_table
        g_capture_table.add(packet)
    await telemetry_manager.run()

if __name__ == "__main__":

    f1_telemetry_thread = Thread(
        target=lambda: asyncio.run(async_telemetry_main()),
        daemon=True
    )
    f1_telemetry_thread.start()

    time.sleep(1)
    root = tk.Tk()
    app = SimpleApp(root)
    root.mainloop()
