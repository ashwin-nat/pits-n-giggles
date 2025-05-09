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

from ..console_interface import ConsoleInterface
from .base_mgr import PngAppMgrBase

# -------------------------------------- CLASS  DEFINITIONS ------------------------------------------------------------

class BackendAppMgr(PngAppMgrBase):
    """Implementation of PngApp for backend services"""
    def __init__(self, console_app: ConsoleInterface, args: list[str] = None):
        super().__init__(
            name="server",
            module_path="apps.backend.pits_n_giggles",
            display_name="Server",
            start_by_default=True,
            console_app=console_app,
            args=args
        )

    def get_buttons(self) -> list[dict]:
        return [
            {"text": "Start", "command": self.start},
            {"text": "Stop", "command": self.stop}
        ]

    def start(self):
        """Start the sub-application process"""
        if self.is_running:
            self.console_app.log(f"{self.display_name} is already running.")
            return

        try:
            self.console_app.log(f"Starting {self.display_name}...")

            self.process = subprocess.Popen(
                [sys.executable, '-m', self.module_path, *self.args],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            self.is_running = True
            self.status_var.set("Running")

            threading.Thread(target=self._capture_output, daemon=True).start()

            self.console_app.log(f"{self.display_name} started successfully.")
        except Exception as e:
            self.console_app.log(f"Error starting {self.display_name}: {e}")
            self.status_var.set("Error")

    def stop(self):
        if not self.is_running:
            self.console_app.log(f"{self.display_name} is not running.")
            return

        try:
            self.console_app.log(f"Stopping {self.display_name}...")

            if self.process:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.console_app.log(f"{self.display_name} did not exit in time. Killing it.")
                    self.process.kill()
                    self.process.wait()

            self.process = None
            self.is_running = False
            self.status_var.set("Stopped")
            self.console_app.log(f"{self.display_name} stopped successfully.")
        except Exception as e:
            self.console_app.log(f"Error stopping {self.display_name}: {e}")
            self.status_var.set("Error")

