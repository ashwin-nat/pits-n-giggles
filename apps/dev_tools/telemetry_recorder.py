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
import os
import sys
import time
import tkinter as tk
from threading import Condition, Event, Lock, Thread
from tkinter import filedialog, messagebox, ttk
from typing import Callable, Optional, Tuple

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.packet_cap import F1PacketCapture
from lib.socket_receiver import UdpTransport
from lib.wdt import WatchDogTimerSync

g_start_condition = Condition()

# Set while packets are arriving. The watchdog callbacks run on other threads, so they only flip this
# flag and the Tk thread polls it.
g_receiving = Event()

def _on_receive_status(receiving: bool) -> None:
    if receiving:
        g_receiving.set()
    else:
        g_receiving.clear()

g_receive_wdt = WatchDogTimerSync(status_callback=_on_receive_status, timeout=1.0, check_interval=0.25)
g_port_num = None

class PacketCaptureTable:
    """Thread safe container for F1PacketCapture instance.
    """

    def __init__(self) -> None:
        """
        Initialize the object by creating a new F1PacketCapture instance and a Lock instance.
        """
        self.m_packet_capture = F1PacketCapture(compressed=True)
        self.m_lock = Lock()

    def add(self, packet: bytes) -> None:
        """
        Add a packet to the packet list while acquiring a lock to ensure thread safety.
        If the lock is held (a save is in progress) the packet is dropped, so the receiver never blocks.

        Parameters:
            packet (bytes): The raw packet to be added to the table.
        """
        if not self.m_lock.acquire(blocking=False):
            return
        try:
            self.m_packet_capture.add(packet)
        finally:
            self.m_lock.release()

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

    def dumpToFile(self, path: str, progress_callback: Optional[Callable[[int, int], None]] = None,
                   clear: bool = False) -> Tuple[str, int, int]:
        """
        Dumps the packet history to a file while acquiring a lock to ensure thread safety.

        Parameters:
            path (str): The path to the file to be written to.
            progress_callback (Callable): Called with (packets written so far, total packets)
            clear (bool): If true, clear the packet history after a successful write, under the same lock

        Returns:
            Tuple[str, int, int]: A tuple containing the filename, number of packets, and number of bytes written.
        """
        with self.m_lock:
            result = self.m_packet_capture.dumpToFile(path, progress_update_callback=progress_callback)
            if clear:
                self.m_packet_capture.clear()
            return result

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

        # Save progress (shown only while saving). The worker thread writes save_progress and save_result,
        # the UI thread polls them.
        self.save_label = tk.Label(root, text="Saving...")
        self.save_bar = ttk.Progressbar(root, mode="determinate", maximum=100, length=300)
        self.save_progress = (0, 0)
        self.save_result = None

        # Live status line, driven by the watchdog flag
        self.listening = False
        self.rx_label = tk.Label(root, text="Not listening", fg="gray")
        self.rx_label.pack(side="bottom", pady=5)
        self._update_rx_status()

    def _update_rx_status(self) -> None:
        if not self.listening:
            self.rx_label.config(text="Not listening", fg="gray")
        elif g_receiving.is_set():
            self.rx_label.config(text="Receiving telemetry", fg="green")
        else:
            self.rx_label.config(text="Waiting for telemetry...", fg="gray")
        self.root.after(300, self._update_rx_status)

    def start_capture(self):
        port = self.port_entry.get()
        if port.isdigit():
            print(f"Starting capture on port {port}")
            self.port_entry.config(state="disabled")  # Grey out/lock the text box
            self.start_button.config(state="disabled")  # Disable the Start button

            # Enable the other two buttons
            self.clear_button.config(state="normal")
            self.save_button.config(state="normal")

            self.listening = True
            global g_port_num
            g_port_num = int(port)
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
                                                 filetypes=[("F1 Packet Capture", "*.f1pcap"), ("All files", "*.*")])
        if not file_path:
            return

        # Compression takes a while, so write on a worker thread and keep the window responsive
        self.save_progress = (0, 0)
        self.save_result = None
        self.clear_button.config(state="disabled")
        self.save_button.config(state="disabled")
        self.save_bar.config(value=0)
        self.save_label.pack()
        self.save_bar.pack(pady=5)
        Thread(target=self._save_worker, args=(file_path,), daemon=True).start()
        self.root.after(100, self._poll_save, file_path)

    def _on_save_progress(self, current: int, total: int) -> None:
        self.save_progress = (current + 1, total)

    def _save_worker(self, file_path: str) -> None:
        try:
            _, num_packets, _ = g_capture_table.dumpToFile(file_path, self._on_save_progress, clear=True)
            self.save_result = (num_packets, None)
        except Exception as e:  # pylint: disable=broad-except
            self.save_result = (0, e)

    def _poll_save(self, file_path: str) -> None:
        written, total = self.save_progress
        if total:
            self.save_bar.config(value=100 * written / total)
            self.save_label.config(text=f"Saving... {written}/{total} packets")

        if self.save_result is None:
            self.root.after(100, self._poll_save, file_path)
            return

        num_packets, error = self.save_result
        self.save_label.pack_forget()
        self.save_bar.pack_forget()
        self.save_label.config(text="Saving...")
        self.clear_button.config(state="normal")
        self.save_button.config(state="normal")
        if error is not None:
            messagebox.showerror("Error", f"Failed to write {file_path}: {error}. Captured data is still in memory.")
        elif num_packets == 0:
            messagebox.showinfo("Info", "No data to save!")
        else:
            messagebox.showinfo("Info", f"Data has been successfully written to file {file_path}. "
                                        f"Number of packets is {num_packets}")

async def async_telemetry_main():
    """Main function for async telemetry. This runs its own asyncio event loop"""
    def wait_for_port():
        with g_start_condition:
            g_start_condition.wait()
        return g_port_num

    loop = asyncio.get_running_loop()
    port = await loop.run_in_executor(None, wait_for_port)

    print(f"[async telemetry] Starting server on port {port}")
    transport = UdpTransport(port, "0.0.0.0", buffer_size=4096)

    @transport.on_packet
    async def handle(raw_packet: bytes) -> None:
        g_receive_wdt.kick()
        g_capture_table.add(raw_packet)

    await transport.run()

if __name__ == "__main__":

    f1_telemetry_thread = Thread(
        target=lambda: asyncio.run(async_telemetry_main()),
        daemon=True
    )
    f1_telemetry_thread.start()

    g_receive_wdt.start()
    time.sleep(1)
    root = tk.Tk()
    app = SimpleApp(root)
    root.mainloop()
