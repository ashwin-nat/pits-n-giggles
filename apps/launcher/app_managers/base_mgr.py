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

import subprocess
import sys
import threading
import tkinter as tk
from abc import ABC, abstractmethod
from tkinter import messagebox, ttk
from typing import Callable, Optional

import psutil

from lib.config import PngSettings
from lib.error_status import PNG_ERROR_CODE_PORT_IN_USE, PNG_ERROR_CODE_UNKNOWN
from lib.ipc import IpcParent, get_free_tcp_port
from lib.pid_report import extract_pid_from_line

from ..console_interface import ConsoleInterface

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def get_executable_extension() -> str:
    """Get the executable file extension based on the operating system"""
    if sys.platform == "win32":
        return ".exe"
    if sys.platform == "darwin":
        return ".app"
    return "" if sys.platform.startswith("linux") else ""

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
    }
    DEFAULT_EXIT = EXIT_ERRORS[PNG_ERROR_CODE_UNKNOWN]

    def __init__(self,
                 port_conflict_settings_field: str,
                 module_path: str,
                 exe_name_without_ext: str,
                 display_name: str,
                 start_by_default: bool,
                 console_app: ConsoleInterface,
                 args: list[str] = None):
        """Initialize the sub-application
        :param port_conflict_settings_field: Settings field to check for port conflicts
        :param module_path: Path to the sub-application module
        :param exe_name_without_ext: Executable name without extension
        :param display_name: Display name for the sub-application
        :param start_by_default: Whether to start this app by default
        :param console_app: Reference to a console interface for logging
        """
        self.port_conflict_settings_field = port_conflict_settings_field
        self.module_path = module_path
        self.display_name = display_name
        self.exec_name = exe_name_without_ext + get_executable_extension()
        self.console_app = console_app
        self.args = args or []  # Store CLI args
        self.process: Optional[subprocess.Popen] = None
        self._process_lock = threading.Lock()
        self.status_var = tk.StringVar(value="Stopped")
        self.is_running = False
        self._is_restarting = threading.Event()
        self.start_by_default = start_by_default
        self.child_pid = None
        self._post_start_hook: Optional[Callable[[], None]] = None
        self._post_stop_hook: Optional[Callable[[], None]] = None
        self.ipc_port = None

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
                self.console_app.log(f"{self.display_name} is already running.")
                return

            # Start the subprocess and update all related state variables atomically
            # so no other thread sees a partially updated state.
            launch_command = self.get_launch_command(self.module_path, self.args)
            self.console_app.log(f"Starting {self.display_name}...")

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
            self.status_var.set("Running")

        # Start output capture and monitor threads outside the lock to avoid deadlocks
        threading.Thread(target=self._capture_output, daemon=True).start()
        threading.Thread(target=self._monitor_process_exit, daemon=True).start()
        threading.Thread(target=self._ipc_manager_thread, daemon=True).start()

        self.console_app.log(f"{self.display_name} started successfully. PID = {self.child_pid}")

        if self._post_start_hook:
            try:
                self._post_start_hook()
            except Exception as e: # pylint: disable=broad-exception-caught
                self.console_app.log(f"{self.display_name}: Error in post-start hook: {e}")

    def stop(self):
        with self._process_lock:
            if not self.is_running:
                self.console_app.log(f"{self.display_name} is not running.")
                return

            self.console_app.log(f"Stopping {self.display_name}...")

            reported_pid = self.child_pid
            popen_pid = self.process.pid if self.process else None
            used_pid = reported_pid or popen_pid

            # Terminate actual child process or subprocess as appropriate
            # All state updates below are done while holding the lock to ensure
            # consistent visibility across threads.
            if reported_pid and reported_pid != popen_pid:
                self.console_app.log(f"Terminating actual child PID {reported_pid} (launched by PyInstaller stub)")
                try:
                    psutil.Process(reported_pid).terminate()
                    psutil.Process(reported_pid).wait(timeout=5)
                except psutil.NoSuchProcess:
                    self.console_app.log(f"Child PID {reported_pid} already exited.")
                except psutil.TimeoutExpired:
                    self.console_app.log(f"Child PID {reported_pid} did not exit in time. Killing it.")
                    psutil.Process(reported_pid).kill()
            elif self.process:
                # Otherwise, just terminate the subprocess
                self.console_app.log(f"Terminating subprocess PID {popen_pid}")
                try:
                    self.process.terminate()
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.console_app.log(f"{self.display_name} did not exit in time. Killing it.")
                    self.process.kill()
                    self.process.wait()

            # Clear process-related state atomically to avoid race conditions
            self.process = None
            self.child_pid = None
            self.is_running = False
            self.status_var.set("Stopped")
        self.console_app.log(f"{self.display_name} stopped successfully. Terminated PID = {used_pid}")

        if self._post_stop_hook:
            try:
                self._post_stop_hook()
            # pylint: disable=broad-exception-caught
            except Exception as e:
                self.console_app.log(f"{self.display_name}: Error in post-stop hook: {e}")

    def start_stop(self):
        """Start or stop the sub-application process based on its current state"""
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
                self.console_app.log(f"{self.display_name} PID update: {pid} changed = {changed}")
            else:
                self.console_app.log(line, is_child_message=True)

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

            # Skip expected exit during restart
            # Exit code 15 occurs when the process is terminated during a restart (e.g., via .terminate()).
            # It's expected in this case, so we ignore it to avoid falsely showing a crash.
            if self._is_restart_exit_expected(ret_code):
                return

            if self.is_running:
                self._handle_unexpected_exit(ret_code)

        finally:
            if self.process is this_process:
                self.process = None

    def _ipc_manager_thread(self):

        import time
        time.sleep(5)
        client = IpcParent(self.ipc_port)
        self.console_app.log(f"{self.display_name} IPC port: {self.ipc_port} Ping {client.ping()}")


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
        self.console_app.log(f"{self.display_name} exited unexpectedly with code {ret_code}")
        self.is_running = False
        self.child_pid = None
        self.process = None

        info = self.EXIT_ERRORS.get(ret_code, self.DEFAULT_EXIT)
        err_msg = f"{self.display_name} {info['message']}"

        if info["status"] == "Port Conflict":
            err_msg += f". Please fix the following field in the settings: {self.port_conflict_settings_field}"
        self.console_app.log(err_msg)
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
            self.console_app.log(
                f"{self.display_name}: Error in post-stop hook after crash: {e}"
            )
