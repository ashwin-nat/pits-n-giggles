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

import base64
import ctypes
import json
import logging
import os
import time
import traceback
from threading import Lock, Thread
from typing import Dict, Optional

import win32con
import win32gui

from .config import OverlaysConfig

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class WindowManager:
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def create_window(self, window_id: str, params: OverlaysConfig):
        pass # TODO

    def set_locked_state_all(self, args: Dict[str, bool]):
        pass # TODO

    def race_table_update(self, data):
        pass # TODO

    def toggle_visibility_all(self):
        pass # TODO

    def stop(self):
        pass # TODO

    def broadcast_data(self, data):
        pass # TODO

    def get_window_info(self, window_id: str) -> OverlaysConfig:
        return OverlaysConfig(x=0, y=0, width=0, height=0) # TODO
