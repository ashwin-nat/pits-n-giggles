# pid_report.py

import os
import re

_PID_TAG_PREFIX = "<<PNG_LAUNCHER_CHILD_PID:"
_PID_TAG_REGEX = re.compile(r"<<PNG_LAUNCHER_CHILD_PID:(\d+)>>")

def report_pid_from_child():
    """Call this in the child process to print its actual PID to stdout."""
    print(f"{_PID_TAG_PREFIX}{os.getpid()}>>", flush=True)

def extract_pid_from_line(line: str) -> int | None:
    """
    Call this in the parent process to parse a PID from a line of stdout.

    Args:
        line: A line of text from the child process's stdout.

    Returns:
        The PID as an int if found, otherwise None.
    """
    match = _PID_TAG_REGEX.search(line)
    return int(match.group(1)) if match else None
