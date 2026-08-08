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
_PID_TAG_REGEX = re.compile(fr"{_PID_TAG_PREFIX}(\d+)>>")
_INIT_COMPLETE_STR = "<<__PNG_SUBSYSTEM_INIT_COMPLETE__>>"
_IPC_PORT_TAG_PREFIX = "<<PNG_LAUNCHER_IPC_PORT:"
_IPC_PORT_TAG_REGEX = re.compile(fr"{_IPC_PORT_TAG_PREFIX}(\d+)>>")
_SESSION_SAVED_TAG_PREFIX = "<<PNG_SESSION_SAVED:"
_SESSION_SAVED_TAG_REGEX = re.compile(fr"{_SESSION_SAVED_TAG_PREFIX}(.+?)>>")
_SESSION_SAVE_SKIPPED_TAG_PREFIX = "<<PNG_SESSION_SAVE_SKIPPED:"
_SESSION_SAVE_SKIPPED_TAG_REGEX = re.compile(fr"{_SESSION_SAVE_SKIPPED_TAG_PREFIX}(.+?)>>")

# The save tokens exist only for the integration runner, which always runs from source. The
# launcher has no use for them, so in a packaged build they would only land in its log as
# noise. Set in builds to turn them off; unset everywhere else.
_NO_SAVE_TOKENS_ENV_VAR = "PNG_NO_SAVE_TOKENS"

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def report_pid_from_child():
    """Call this in the child process to print its actual PID to stdout."""
    print(f"{_PID_TAG_PREFIX}{os.getpid()}>>", flush=True)

def extract_pid_from_line(line: str) -> Optional[int]:
    """
    Call this in the parent process to parse a PID from a line of stdout.

    Args:
        line: A line of text from the child process's stdout.

    Returns:
        The PID as an int if found, otherwise None.
    """
    match = _PID_TAG_REGEX.search(line)
    return int(match.group(1)) if match else None

def report_ipc_port_from_child(port: int) -> None:
    """
    Call this in the child process to report the IPC port it is listening on.

    Args:
        port: The IPC port number to report.
    """
    print(f"{_IPC_PORT_TAG_PREFIX}{port}>>", flush=True)

def extract_ipc_port_from_line(line: str) -> Optional[int]:
    """
    Parse IPC port from a line of stdout.
    """
    match = _IPC_PORT_TAG_REGEX.search(line)
    return int(match.group(1)) if match else None

def notify_parent_init_complete() -> None:
    """Call this in the child process to notify the parent that initialization is complete."""
    print(_INIT_COMPLETE_STR, flush=True)

def is_init_complete(line: str) -> bool:
    """Call this in the parent process to check if the child process has completed initialization."""
    return _INIT_COMPLETE_STR in line

def disable_save_tokens() -> None:
    """Call this once at startup in a packaged build to silence the session save tokens.

    Sets an env var rather than flipping a module global, so the child processes the
    launcher spawns inherit the setting without having to be told.
    """
    os.environ[_NO_SAVE_TOKENS_ENV_VAR] = "1"

def _save_tokens_disabled() -> bool:
    """Whether session save tokens should be suppressed in this process."""
    return bool(os.environ.get(_NO_SAVE_TOKENS_ENV_VAR))

def report_session_saved_from_child(file_path: str) -> None:
    """Call this in the child process after writing a session save to disk.

    Emitted as a token rather than left to the log message, so consumers do not have to
    match on prose that could be reworded. No-op when the tokens are disabled.

    Args:
        file_path (str): Path the session was written to
    """
    if _save_tokens_disabled():
        return
    print(f"{_SESSION_SAVED_TAG_PREFIX}{file_path}>>", flush=True)

def extract_saved_path_from_line(line: str) -> Optional[str]:
    """Parse a written session save path from a line of stdout.

    Args:
        line (str): A line of text from the child process's stdout

    Returns:
        Optional[str]: The path if the line carries the token, else None
    """
    match = _SESSION_SAVED_TAG_REGEX.search(line)
    return match.group(1) if match else None

def report_session_save_skipped_from_child(reason: str) -> None:
    """Call this in the child process when a session save is deliberately not written.

    Lets a consumer tell "nothing was saved because this session does not qualify" apart
    from "the save failed", instead of inferring it from an absence. No-op when the tokens
    are disabled.

    Args:
        reason (str): Why the save was skipped
    """
    if _save_tokens_disabled():
        return
    print(f"{_SESSION_SAVE_SKIPPED_TAG_PREFIX}{reason}>>", flush=True)

def extract_save_skipped_from_line(line: str) -> Optional[str]:
    """Parse a skipped-save reason from a line of stdout.

    Args:
        line (str): A line of text from the child process's stdout

    Returns:
        Optional[str]: The reason if the line carries the token, else None
    """
    match = _SESSION_SAVE_SKIPPED_TAG_REGEX.search(line)
    return match.group(1) if match else None
