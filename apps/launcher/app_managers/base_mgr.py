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

import copy
import random
import subprocess
import sys
import threading
import time
import tkinter as tk
from abc import ABC, abstractmethod
from tkinter import messagebox, ttk
from typing import Callable, Optional

import psutil

from lib.child_proc_mgmt import extract_pid_from_line, is_init_complete
from lib.config import PngSettings
from lib.error_status import (PNG_ERROR_CODE_PORT_IN_USE,
                              PNG_ERROR_CODE_UNKNOWN, PNG_LOST_CONN_TO_PARENT)
from lib.ipc import IpcParent, get_free_tcp_port

from ..console_interface import ConsoleInterface

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

# -------------------------------------- CLASS  DEFINITIONS ------------------------------------------------------------

class PngAppMgrBase(ABC):
    """Class to manage a sub-application process"""

    EXIT_ERRORS = {
        PNG_ERROR_CODE_PORT_IN_USE: {
            "title": "Port In Use",
            "message": (
                "failed to start because the required port is already in use.\n"
                "Please close the conflicting app or change the port in settings."
            ),
            "status": "Port Conflict",
        },
        PNG_ERROR_CODE_UNKNOWN: {
            "title": "Unknown Error",
            "message": (
                "failed to start due to an unknown error.\n"
                "Please check the logs for more details."
            ),
            "status": "Crashed",
        },
        PNG_LOST_CONN_TO_PARENT: {
            "title": "Lost Connection to Parent",
            "message": (
                "lost connection to the parent process.\n"
                "Please check the logs for more details."
            ),
            "status": "Timed out",
        }
    }
    DEFAULT_EXIT = EXIT_ERRORS[PNG_ERROR_CODE_UNKNOWN]

    def __init__(self,
                 port_conflict_settings_field: str,
                 module_path: str,
                 display_name: str,
                 start_by_default: bool,
                 console_app: ConsoleInterface,
                 settings: PngSettings,
                 args: list[str],
                 debug_mode: bool):
        """Initialize the sub-application
        :param port_conflict_settings_field: Settings field to check for port conflicts
        :param module_path: Path to the sub-application module
        :param display_name: Display name for the sub-application
        :param start_by_default: Whether to start this app by default
        :param console_app: Reference to a console interface for logging
        :param settings: Settings object
        :param args: Additional Command line arguments to pass to the sub-application
        :param debug_mode: Whether to run the sub-application in debug mode
        """
        self.port_conflict_settings_field = port_conflict_settings_field
        self.module_path = module_path
        self.display_name = display_name
        self.console_app = console_app
        self.args = args or []  # Store CLI args
        self.process: Optional[subprocess.Popen] = None
        self._process_lock = threading.Lock()
        self.status_var = tk.StringVar(value="Stopped")
        self.is_running = False
        self._is_restarting = threading.Event()
        self._is_stopping = threading.Event()
        self.curr_settings = copy.deepcopy(settings)
        self.heartbeat_interval: float = settings.SubSysCtrlCfg__.heartbeat_interval
        self.num_missable_heartbeats: int = settings.SubSysCtrlCfg__.num_missable_heartbeats
        self._stop_heartbeat = threading.Event()
        self._heartbeat_stopped = threading.Event()
        self.start_by_default = start_by_default
        self.child_pid = None
        self._post_start_hook: Optional[Callable[[], None]] = None
        self._post_stop_hook: Optional[Callable[[], None]] = None
        self.ipc_port = None
        self._debug_mode = debug_mode

    @abstractmethod
    def get_buttons(self, frame: ttk.Frame) -> list[dict]:
        """Return a list of button definitions for this app."""
        pass

    @abstractmethod
    def on_settings_change(self, new_settings: PngSettings) -> bool:
        """Handle changes in settings for the sub-application

        :param new_settings: New settings

        :return: True if the app needs to be restarted
        """
        pass

    def get_launch_command(self, module_path: str, args: list[str]):
        """
        Returns the subprocess launch command for a given module.
        In frozen (PyInstaller) builds, use `runpy.run_module()` to avoid `-m` issues.
        """
        if getattr(sys, "frozen", False):
            return [sys.executable, "--module", module_path, *args]
        return [sys.executable, "-m", module_path, *args]


    def register_post_start(self, func: Callable[[], None]):
        """Register a post-start callback."""
        self._post_start_hook = func
        return func

    def register_post_stop(self, func: Callable[[], None]):
        """Register a post-stop callback."""
        self._post_stop_hook = func
        return func

    def start(self):
        """Start the sub-application process"""
        with self._process_lock:
            if self.is_running:
                self.console_app.debug_log(f"{self.display_name} is already running.")
                return

            # Start the subprocess and update all related state variables atomically
            # so no other thread sees a partially updated state.
            launch_command = self.get_launch_command(self.module_path, self.args)
            self.console_app.info_log(f"Starting {self.display_name}...")

            self.ipc_port = get_free_tcp_port()
            launch_command.extend(["--ipc-port", f"{self.ipc_port}"])

            # pylint: disable=consider-using-with
            self.process = subprocess.Popen(
                launch_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                stdin=subprocess.PIPE
            )
            self.is_running = True
            self.child_pid = self.process.pid
            self.status_var.set("Starting...")

        # Start output capture and monitor threads outside the lock to avoid deadlocks
        threading.Thread(target=self._capture_output, daemon=True, name=f"{self.display_name} output capture").start()
        threading.Thread(target=self._monitor_process_exit, daemon=True, name=f"{self.display_name} exit monitor").start()
        threading.Thread(target=self._send_heartbeat, args=(self.ipc_port,), daemon=True,
                         name=f"{self.display_name} heartbeat").start()

        self.console_app.debug_log(f"{self.display_name} started successfully. PID = {self.child_pid}")

    def stop(self):
        """Stop the sub-application process"""
        with self._process_lock:
            if not self.is_running:
                self.console_app.debug_log(f"{self.display_name} is not running.")
                return

            self.console_app.info_log(f"Stopping {self.display_name}...")
            self._is_stopping.set()
            self.status_var.set("Stopping...")
            if self._send_ipc_shutdown():
                try:
                    self.process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.console_app.debug_log(f"{self.display_name} did not exit in time after IPC shutdown. Killing it.")
                    self._terminate_process()
            else:
                self.console_app.debug_log(f"Failed to send shutdown signal to {self.display_name}.")
                self._terminate_process()

            # Wait for heartbeat thread to stop
            self.console_app.debug_log(f"{self.display_name} - Waiting for heartbeat thread to stop...")
            if self._heartbeat_stopped.wait(timeout=self.heartbeat_interval + 1.0):
                self.console_app.debug_log(f"{self.display_name} - Heartbeat thread stopped.")
            else:
                self.console_app.debug_log(f"{self.display_name} - Timed out waiting for heartbeat thread to stop.")
            self._heartbeat_stopped.clear()

            # Clear process-related state atomically to avoid race conditions
            self.process = None
            self.child_pid = None
            self.is_running = False
            self.status_var.set("Stopped")
            self._is_stopping.clear()

        if self._post_stop_hook:
            try:
                self._post_stop_hook()
            # pylint: disable=broad-exception-caught
            except Exception as e:
                self.console_app.debug_log(f"{self.display_name}: Error in post-stop hook: {e}")

    def start_stop(self):
        """Start or stop the sub-application process (non-blocking for GUI)."""
        def worker():
            # Call the original start_stop logic
            try:
                self._start_stop_blocking()
            except Exception as e:  # pylint: disable=broad-exception-caught
                self.console_app.debug_log(f"{self.display_name}: Error during start/stop: {e}")

        threading.Thread(target=worker, daemon=True, name=f"{self.display_name} start/stop").start()

    def _start_stop_blocking(self):
        """Actual start/stop logic that may block (called in worker thread)."""
        if self.is_running:
            self.stop()
        else:
            self.start()

    def restart(self):
        """Restart the sub-application process"""
        self._is_restarting.set()
        if self.is_running:
            self.stop()
        self.start()
        self._is_restarting.clear()

    def _capture_output(self):
        """Capture and log the subprocess output line by line, safely synchronized.

        This method:
        - Takes a snapshot of the subprocess and its stdout once under the lock to avoid race conditions.
        - Iterates over the stdout file-like iterator to read lines until EOF (pipe closed).
        - Updates shared state with locking only when needed.
        - Exits cleanly when the process stdout closes (process ends or is terminated).
        """

        # Snapshot process and stdout once under the lock
        with self._process_lock:
            process = self.process
            # If process or its stdout isn't available, exit immediately.
            if not process or not process.stdout:
                return
            stdout = process.stdout

        # Read lines until EOF (when pipe closes)
        for line in stdout:
            if not line:
                # EOF reached
                break

            if pid := extract_pid_from_line(line):
                with self._process_lock:
                    # Check current PID safely in case process changed meanwhile
                    current_pid = self.process.pid if self.process else None
                    changed = current_pid is not None and current_pid != pid
                    self.child_pid = pid
                self.console_app.debug_log(f"{self.display_name} PID update: {pid} changed = {changed}")
            elif is_init_complete(line):
                self.console_app.debug_log(f"{self.display_name} initialization complete")
                with self._process_lock:
                    self.status_var.set("Running")
                if self._post_start_hook:
                    try:
                        self._post_start_hook()
                    except Exception as e: # pylint: disable=broad-exception-caught
                        self.console_app.debug_log(f"{self.display_name}: Error in post-start hook: {e}")

            else:
                self.console_app.info_log(line, is_child_message=True)

    def _monitor_process_exit(self):
        """subprocess monitoring thread to handle unexpected exits"""
        this_process = self.process  # Store reference to the process this thread is watching
        try:
            if not this_process:
                return
            ret_code = this_process.wait()

            # Skip if a new process has been started after this thread began
            if self.process is not this_process:
                return

            # Skip expected exit during restart or if stopping
            # Exit code 15 occurs when the process is terminated during a restart (e.g., via .terminate()).
            # It's expected in this case, so we ignore it to avoid falsely showing a crash.
            if self._is_restart_exit_expected(ret_code) or self._is_stopping.is_set():
                return

            if self.is_running:
                self._handle_unexpected_exit(ret_code)

        finally:
            if self.process is this_process:
                self.process = None
            self._stop_heartbeat.set()

    def _send_heartbeat(self, port_num: int) -> None:
        """Send heartbeat messages to the child process periodically

        Args:
            port_num (int): IPC port number
        """
        # Initial delay to avoid bursts
        initial_delay = random.uniform(0, 5.0)
        time.sleep(initial_delay)
        failed_heartbeat_count = 0
        timeout_ms = (int(self.heartbeat_interval) - 2) * 1000
        assert timeout_ms > 0

        self.console_app.debug_log(f"{self.display_name}: Starting heartbeat on port {port_num}...")
        self._heartbeat_stopped.clear()

        while not self._stop_heartbeat.is_set():
            try:
                rsp = IpcParent(port_num, timeout_ms).heartbeat()

                if rsp.get("status") == "success":
                    failed_heartbeat_count = 0
                    self.console_app.debug_log(f"{self.display_name}: Heartbeat success response: {rsp} on port {port_num}")
                else:
                    self.console_app.debug_log(
                        f"{self.display_name}: Heartbeat failed with response: {rsp} on port {port_num}"
                    )
                    failed_heartbeat_count += 1

            except Exception as e:  # pylint: disable=broad-exception-caught
                self.console_app.debug_log(f"{self.display_name}: Error sending heartbeat: {e} on port {port_num}")
                failed_heartbeat_count += 1

            # Check if we've exceeded the maximum allowed missed heartbeats
            if (failed_heartbeat_count > self.num_missable_heartbeats) and not self._debug_mode:
                self.stop()
                self.console_app.info_log(
                    f"{self.display_name}: Missed {failed_heartbeat_count} consecutive heartbeats on port {port_num}. "
                    "Stopping")
                break

            self._stop_heartbeat.wait(self.heartbeat_interval)

        self._stop_heartbeat.clear()
        self._heartbeat_stopped.set()
        self.console_app.debug_log(f"{self.display_name}: Heartbeat job stopped on port {port_num}")

    def _is_restart_exit_expected(self, ret_code: int) -> bool:
        """
        Check if the process was restarted intentionally with code 15.

        :param ret_code: Exit code of the process
        """
        return self._is_restarting.is_set() and ret_code == 15

    def _handle_unexpected_exit(self, ret_code: int) -> None:
        """
        Handle unexpected process exit: logging, UI update, error dialog.

        :param ret_code: Exit code of the process
        """
        self.console_app.info_log(f"{self.display_name} exited unexpectedly with code {ret_code}")
        self.is_running = False
        self.child_pid = None
        self.process = None

        info = self.EXIT_ERRORS.get(ret_code, self.DEFAULT_EXIT)
        err_msg = f"{self.display_name} {info['message']}"

        if info["status"] == "Port Conflict":
            err_msg += f". Please fix the following field in the settings: {self.port_conflict_settings_field}"
        self.console_app.info_log(err_msg)
        messagebox.showerror(
            title=f"{self.display_name} - {info['title']}",
            message=err_msg,
        )
        self.status_var.set(info["status"])

        if self._post_stop_hook:
            self._run_post_stop_hook()

    def _run_post_stop_hook(self) -> None:
        """
        Safely execute the post-stop hook with error logging.
        """
        try:
            self._post_stop_hook()
        except Exception as e:  # pylint: disable=broad-exception-caught
            # suppressing linter warning here since this is dependent on the child process
            # out of scope of the launcher code.
            self.console_app.debug_log(
                f"{self.display_name}: Error in post-stop hook after crash: {e}"
            )

    def _send_ipc_shutdown(self) -> bool:
        """Sends a shutdown command to the child process.

        Returns:
            True if the shutdown was successful, False otherwise.
        """
        try:
            rsp = IpcParent(self.ipc_port).shutdown_child("Stop requested")
            return rsp.get("status") == "success"
        except Exception as e: # pylint: disable=broad-exception-caught
            self.console_app.debug_log(f"IPC shutdown failed: {e}")
            return False

    def _terminate_process(self) -> None:
        """Terminates the child process or subprocess. (Assumes the lock is held.)"""
        reported_pid = self.child_pid
        popen_pid = self.process.pid if self.process else None
        used_pid = reported_pid or popen_pid

        # Terminate actual child process or subprocess as appropriate
        # All state updates below are done while holding the lock to ensure
        # consistent visibility across threads.
        if reported_pid and reported_pid != popen_pid:
            self.console_app.debug_log(f"Killing actual child PID {reported_pid} (launched by PyInstaller stub)")
            try:
                psutil.Process(reported_pid).kill()
            except psutil.NoSuchProcess:
                self.console_app.debug_log(f"Child PID {reported_pid} already exited.")
        elif self.process:
            # Otherwise, just kill the subprocess
            self.console_app.debug_log(f"Killing subprocess PID {popen_pid}")
            self.process.kill()
            self.process.wait() # Wait for the process to fully terminate after killing
        self.console_app.debug_log(f"{self.display_name} stopped successfully. Killed PID = {used_pid}")
