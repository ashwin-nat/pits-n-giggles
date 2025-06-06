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
import subprocess
import sys
import threading
import tkinter as tk
from abc import ABC, abstractmethod
from tkinter import ttk
from typing import Callable, Optional

import psutil

from lib.config import PngSettings
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
    def __init__(self,
                 name: str,
                 module_path: str,
                 exe_name_without_ext: str,
                 display_name: str,
                 start_by_default: bool,
                 console_app: ConsoleInterface,
                 args: list[str] = None):
        """Initialize the sub-application
        :param name: Unique name for the sub-application
        :param module_path: Path to the sub-application module
        :param exe_name_without_ext: Executable name without extension
        :param display_name: Display name for the sub-application
        :param start_by_default: Whether to start this app by default
        :param console_app: Reference to a console interface for logging
        """
        self.name = name
        self.module_path = module_path
        self.display_name = display_name
        self.exec_name = exe_name_without_ext + get_executable_extension()
        self.console_app = console_app
        self.args = args or []  # Store CLI args
        self.process: Optional[subprocess.Popen] = None
        self.status_var = tk.StringVar(value="Stopped")
        self.is_running = False
        self.start_by_default = start_by_default
        self.child_pid = None
        self._post_start_hook: Optional[Callable[[], None]] = None
        self._post_stop_hook: Optional[Callable[[], None]] = None


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
        """Get the command to launch the backend application"""

        # In dev environment, run python with the module path
        if not getattr(sys, 'frozen', False):
            return [sys.executable, "-m", module_path, *args]
        # In PyInstaller frozen mode, the executable is in sys._MEIPASS in embedded_exes dir
        exe_path = os.path.join(sys._MEIPASS, 'embedded_exes', self.exec_name)
        return [exe_path, *args]

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
        if self.is_running:
            self.console_app.log(f"{self.display_name} is already running.")
            return

        try:
            launch_command = self.get_launch_command(self.module_path, self.args)
            self.console_app.log(f"Starting {self.display_name}...")

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
            threading.Thread(target=self._capture_output, daemon=True).start()

            self.console_app.log(f"{self.display_name} started successfully. PID = {self.child_pid}")

            if self._post_start_hook:
                try:
                    self._post_start_hook()
                # pylint: disable=broad-exception-caught
                except Exception as e:
                    self.console_app.log(f"{self.display_name}: Error in post-start hook: {e}")

        # pylint: disable=broad-exception-caught
        except Exception as e:
            self.console_app.log(f"Error starting {self.display_name}: {e}")
            self.status_var.set("Error")

    def stop(self):
        """Stop the sub-application process"""
        if not self.is_running:
            self.console_app.log(f"{self.display_name} is not running.")
            return

        try:
            self.console_app.log(f"Stopping {self.display_name}...")

            reported_pid = self.child_pid
            popen_pid = self.process.pid if self.process else None
            used_pid = reported_pid or popen_pid

            # Attempt to terminate the reported child PID directly if it's different
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

            # Cleanup state
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

        # pylint: disable=broad-exception-caught
        except Exception as e:
            self.console_app.log(f"Error stopping {self.display_name}: {e}")
            self.status_var.set("Error")

    def start_stop(self):
        """Start or stop the sub-application process based on its current state"""
        if self.is_running:
            self.stop()
        else:
            self.start()

    def restart(self):
        """Restart the sub-application process"""
        if self.is_running:
            self.stop()
            self.start()
        # No Op if not running

    def _capture_output(self):
        """Capture and log the subprocess output line by line"""
        if self.process and self.process.stdout:
            for line in self.process.stdout:
                if not line:
                    break
                if pid := extract_pid_from_line(line):
                    self.console_app.log(f"{self.display_name} PID update: {pid} changed = {self.process.pid != pid}")
                    self.child_pid = pid
                else:
                    self.console_app.log(line, is_child_message=True)
