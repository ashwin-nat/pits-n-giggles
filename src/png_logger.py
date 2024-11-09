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

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

import logging
import threading
import sys
import io
import os

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def initLogger(file_name: str = None, debug_mode: bool = False) -> logging.Logger:
    """Initialize and configure the logger.

    Args:
        file_name (str, optional): The name of the log file. Defaults to None.
        debug_mode (bool, optional): Whether to enable debug mode. Defaults to False.

    Returns:
        logging.Logger: The configured logger.
    """
    # Create a formatter with a time-based format
    format_str = '%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d] - %(message)s' if debug_mode else \
                 '%(asctime)s [%(levelname)s] - %(message)s'
    formatter = logging.Formatter(format_str)

    # Create a lock to make the logger thread-safe
    lock = threading.Lock()

    # Create the logger
    png_logger = logging.getLogger('png')
    png_logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)

    # Create console handler with UTF-8 encoding
    console_handler = logging.StreamHandler(stream=io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8'))
    console_handler.setFormatter(formatter)
    png_logger.addHandler(console_handler)

    # Add file handler if a file name is provided
    if file_name:
        _clearFileIfRequired(file_name)
        file_handler = logging.FileHandler(file_name, encoding='utf-8')
        file_handler.setFormatter(formatter)
        png_logger.addHandler(file_handler)

    # Add lock to the logger to make it thread-safe
    png_logger.addHandler(logging.NullHandler())
    png_logger._lock = lock

    return png_logger

def getLogger() -> logging.Logger:
    """Get the PNG logger

    Returns:
        logging.Logger: The logger object
    """
    return logging.getLogger('png')

def _clearFileIfRequired(file_name: str) -> None:
    """Clear the file if it is larger than 1 MB."""

    if os.path.exists(file_name):
        file_size = os.path.getsize(file_name)
        if file_size > 1000000:
            os.remove(file_name)
            print(f"File {file_name} cleared.")
