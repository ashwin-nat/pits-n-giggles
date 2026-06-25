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
# pylint: skip-file

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

import json
import logging
import os
from datetime import datetime
from typing import Optional

from meta.meta import APP_NAME_SNAKE

# -------------------------------------- CUSTOM LOG LEVEL ---------------------------------------------------------------

SILENT_LEVEL = 15  # Between DEBUG (10) and INFO (20)

logging.addLevelName(SILENT_LEVEL, "SILENT")


# -------------------------------------- LOGGER CLASS ------------------------------------------------------------------

class PngLogger(logging.Logger):
    """Custom logger with SILENT level support."""

    def silent(self, message: str, *args, **kwargs) -> None:
        if self.isEnabledFor(SILENT_LEVEL):
            self._log(SILENT_LEVEL, message, args, **kwargs)


# Tell logging module to use our logger class
logging.setLoggerClass(PngLogger)


# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def get_logger(
    name: str,
    debug_mode: bool = False,
    jsonl: bool = False,
    file_path: Optional[str] = None,
) -> PngLogger:
    """Initialize and configure the logger.

    Args:
        name (str): The name of the logger.
        debug_mode (bool, optional): Whether to enable debug mode. Defaults to False.
        jsonl (bool, optional): Whether to use JSONL format. Defaults to False. If set to true, logs will be emitted
            via stdout in JSONL format, and file logging will be disabled. This will be parent process's responsibility
                to capture and route logs appropriately. If disabled, logs will be emitted
                    in human-readable format to a file.
        file_path (Optional[str], optional): The path to the log file. Defaults to None.

    Returns:
        PngLogger: The configured logger instance.
    """

    logger = logging.getLogger(name)
    logger.propagate = False

    assert not logger.handlers, f"Logger '{name}' already initialized"

    # DEBUG mode -> everything
    # Normal mode -> SILENT and above
    logger.setLevel(logging.DEBUG if debug_mode else SILENT_LEVEL)

    # Choose formatter
    if jsonl:
        ts_fmt = "%Y-%m-%d %H:%M:%S.%f"
        console_formatter = JsonlFormatter(datefmt=ts_fmt)
        file_formatter = JsonlFormatter(datefmt=ts_fmt)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    else:
        text_fmt = "%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s"
        ts_fmt = "%Y-%m-%d %H:%M:%S"
        file_formatter = logging.Formatter(text_fmt, ts_fmt)

    # Optional file handler
    if file_path:
        _clearFileIfRequired(file_path, max_size=1000000)
        file_handler = logging.FileHandler(
            file_path, mode="a", encoding="utf-8", delay=False
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger

def get_null_logger() -> PngLogger:
    """Return a no-op :class:`PngLogger` that discards all records.

    Use this as the default when no logger is injected into a component. A bare
    ``logging.getLogger()`` is not guaranteed to return a ``PngLogger`` (so it
    may lack ``silent()``); this always does.

    Returns:
        PngLogger: A logger whose records go nowhere.
    """
    logger = PngLogger(f"{APP_NAME_SNAKE}.null")
    logger.addHandler(logging.NullHandler())
    logger.propagate = False
    return logger

def _clearFileIfRequired(file_name: str, max_size: int) -> None:
    if os.path.exists(file_name):
        file_size = os.path.getsize(file_name)
        if file_size > max_size:
            os.remove(file_name)
            print(f"File {file_name} cleared.")


# -------------------------------------- CLASSES -----------------------------------------------------------------------

class JsonlFormatter(logging.Formatter):
    def format(self, record):
        # Base log data
        log = {
            "time": datetime.fromtimestamp(record.created).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "filename": record.filename,
            "lineno": record.lineno,
            "func": record.funcName,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log["exc_type"] = record.exc_info[0].__name__
            log["exc_message"] = str(record.exc_info[1])
            log["stack"] = self.formatException(record.exc_info)

        return json.dumps(log, ensure_ascii=True)
