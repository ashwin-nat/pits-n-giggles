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
import re
from typing import Optional
# -------------------------------------- CONSTANTS -----------------------------------------------------------------------

_PID_TAG_PREFIX = "<<PNG_LAUNCHER_CHILD_PID:"
_PID_TAG_REGEX = re.compile(r"<<PNG_LAUNCHER_CHILD_PID:(\d+)>>")
_INIT_COMPLETE_STR = "<<__PNG_SUBSYSTEM_INIT_COMPLETE__>>"

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def report_pid_from_child():
    """Call this in the child process to print its actual PID to stdout."""
    print(f"{_PID_TAG_PREFIX}{os.getpid()}>>", flush=True)

def extract_pid_from_line(line: str) ->  Optional[int]:
    """
    Call this in the parent process to parse a PID from a line of stdout.

    Args:
        line: A line of text from the child process's stdout.

    Returns:
        The PID as an int if found, otherwise None.
    """
    match = _PID_TAG_REGEX.search(line)
    return int(match.group(1)) if match else None

def is_init_complete(line: str) -> bool:
    """Call this in the parent process to check if the child process has completed initialization."""
    return _INIT_COMPLETE_STR in line
