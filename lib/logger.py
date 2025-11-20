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

import os
import logging
import json
from datetime import datetime
from typing import Optional

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def get_logger(
    name: str,
    debug_mode: bool = False,
    jsonl: bool = False,
    file_path: Optional[str] = None,
) -> logging.Logger:
    """Initialize and configure the logger.

    Args:
        name (str): The name of the logger.
        debug_mode (bool, optional): Whether to enable debug mode. Defaults to False.
        jsonl (bool, optional): Whether to use JSONL format. Defaults to False.
        file_path (Optional[str], optional): The path to the log file. Defaults to None.

    Returns:
        logging.Logger: The configured logger.
    """

    png_logger = logging.getLogger(name)
    png_logger.propagate = False

    # Optionally enforce "create once" rule
    assert not png_logger.handlers, f"Logger '{name}' already initialized"

    png_logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)

    # Choose formatters
    if jsonl:
        ts_fmt = "%Y-%m-%d %H:%M:%S.%f"
        console_formatter = JsonlFormatter(datefmt=ts_fmt)
        file_formatter    = JsonlFormatter(datefmt=ts_fmt)
    else:
        text_fmt = "%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s"
        ts_fmt   = "%Y-%m-%d %H:%M:%S"
        console_formatter = logging.Formatter(text_fmt, ts_fmt)
        file_formatter    = logging.Formatter(text_fmt, ts_fmt)

    # Console handler (always)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    png_logger.addHandler(console_handler)

    # File handler (optional)
    if file_path:
        _clearFileIfRequired(file_path, max_size=1000000)
        file_handler = logging.FileHandler(
            file_path, mode="a", encoding="utf-8", delay=False
        )
        file_handler.setFormatter(file_formatter)
        png_logger.addHandler(file_handler)

    return png_logger

def _clearFileIfRequired(file_name: str, max_size: int) -> None:
    """Clear the file if it is larger than 1 MB.

    Args:
        file_name (str): The name of the file to clear.
        max_size (int): The maximum size of the file in bytes.
    """

    if os.path.exists(file_name):
        file_size = os.path.getsize(file_name)
        if file_size > max_size:
            os.remove(file_name)
            print(f"File {file_name} cleared.")


# -------------------------------------- CLASSES -----------------------------------------------------------------------

class JsonlFormatter(logging.Formatter):
    def format(self, record):

        return json.dumps(
            {
                "time": datetime.fromtimestamp(record.created).isoformat(timespec="milliseconds"),
                "level": record.levelname,
                "logger": record.name,
                "filename": record.filename,
                "lineno": record.lineno,
                "func": record.funcName,
                "message": record.getMessage(),
            }, ensure_ascii=False)
