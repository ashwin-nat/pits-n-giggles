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

# ------------------------- IMPORTS ------------------------------------------------------------------------------------

from dataclasses import dataclass

from lib.config import PngSettings
from lib.logger import PngLogger
from lib.subsystem import AsyncSubsystem

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

@dataclass(frozen=True)
class AppCtx:
    """Bundles the handles that every backend layer's init function and top-level class need:
    the logger, settings and the owning subsystem (for add_task/fire_and_forget, its version
    string, and its IPC surfaces). Built once in BackendSubsystem.__init__ and threaded down
    instead of passing the same args individually through each layer.
    """

    logger: PngLogger
    settings: PngSettings
    subsystem: AsyncSubsystem
