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
import tkinter as tk
from abc import ABC, abstractmethod
from typing import Optional

from ..console_interface import ConsoleInterface

# -------------------------------------- CLASS  DEFINITIONS ------------------------------------------------------------

class PngAppMgrBase(ABC):
    """Class to manage a sub-application process"""
    def __init__(self, name: str, module_path: str, display_name: str,
                start_by_default: bool, console_app: ConsoleInterface,
                args: list[str] = None):
        """Initialize the sub-application
        :param name: Unique name for the sub-application
        :param module_path: Path to the sub-application module
        :param display_name: Display name for the sub-application
        :param start_by_default: Whether to start this app by default
        :param console_app: Reference to a console interface for logging
        """
        self.name = name
        self.module_path = module_path
        self.display_name = display_name
        self.console_app = console_app
        self.args = args or []  # Store CLI args
        self.process: Optional[subprocess.Popen] = None
        self.status_var = tk.StringVar(value="Stopped")
        self.is_running = False
        self.start_by_default = start_by_default

    @abstractmethod
    def get_buttons(self) -> list[dict]:
        """Return a list of button definitions for this app."""
        pass

    @abstractmethod
    def start(self):
        """Start the sub-application process"""
        pass

    @abstractmethod
    def stop(self):
        """Stop the sub-application process"""
        pass

    def _capture_output(self):
        """Capture and log the subprocess output line by line"""
        if self.process and self.process.stdout:
            for line in self.process.stdout:
                if not line:
                    break
                self.console_app.log(line)

    def make_text_var(self, text: str) -> tk.StringVar:
        """Wrap a static label into a StringVar for consistency with dynamic ones."""
        var = tk.StringVar()
        var.set(text)
        return var

