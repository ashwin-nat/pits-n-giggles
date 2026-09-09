# MIT License
#
# Copyright (c) [2024] [Ashwin Natarajan]
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

"""yappi profiling for a subsystem run, kept out of the lifecycle class.

A subsystem opts in with PROFILE = True and the base calls these around the run. Profiling is a
dev aid rather than part of the subsystem contract, so it lives here and PngSubsystem keeps two
call sites instead of fifty lines of pstats and HTML.
"""

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

import pstats
from types import ModuleType
from typing import Optional

from lib.logger import PngLogger

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def start_profiler(enabled: bool) -> Optional[ModuleType]:  # pragma: no cover - dev tool, never on
    """Start yappi if this subsystem asked for it. Wall clock, so I/O waits show up.

    yappi is imported inside the branch, so a normal boot neither imports it nor pays for it -
    which is what lets the call sit in the constructor of every subsystem.

    Args:
        enabled (bool): The subsystem's PROFILE class variable

    Returns:
        Optional[ModuleType]: The yappi module while profiling, else None
    """

    if not enabled:
        return None

    import yappi  # pylint: disable=import-outside-toplevel
    yappi.set_clock_type("wall")  # Use "cpu" for CPU-bound tasks
    yappi.start()
    return yappi

def stop_profiler(profiler: Optional[ModuleType],
                  name: str,
                  logger: PngLogger) -> None:  # pragma: no cover - dev tool, never on in prod
    """Write the profile out. Called after teardown, so it covers the whole process.

    Files are named after the subsystem: profiling two at once would otherwise have them
    overwrite each other.

    Args:
        profiler (Optional[ModuleType]): Whatever start_profiler() returned. None is a no-op.
        name (str): Subsystem name, used for the output file names
        logger (PngLogger): Logger to report the written files through
    """

    if profiler is None:
        return

    profiler.stop()

    # Function-level stats for SnakeViz
    prof_path = f"{name}_yappi.prof"
    profiler.get_func_stats().save(prof_path, type="pstat")

    # Don't strip directories, so full paths are included
    # If you want the paths to be fully visible, just skip strip_dirs()
    stats = pstats.Stats(prof_path)
    stats.sort_stats("cumulative")

    # Save as HTML
    with open(f"{name}_yappi.html", "w", encoding="utf-8") as f:
        f.write("<html><head><title>Yappi Profile</title></head><body><pre>")
        stats.stream = f
        stats.print_stats()
        f.write("</pre></body></html>")

    # Save as TXT
    with open(f"{name}_yappi.txt", "w", encoding="utf-8") as f:
        stats.stream = f
        stats.print_stats()

    # Not print(): stdout is the launcher's JSONL channel, and MCP's stdio transport.
    logger.info("Wrote profile: %s_yappi.{prof,txt,html}", name)
