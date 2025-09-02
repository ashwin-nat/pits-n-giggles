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

import logging
from logging.handlers import RotatingFileHandler
from typing import Tuple

from lib.file_path import resolve_user_file

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

DEFAULT_LOG_FILE = "png.log"

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

class ConditionalTimestampFormatter(logging.Formatter):
    """
    A custom logging formatter that conditionally includes a timestamp in log messages.

    Attributes:
        format_with_ts (logging.Formatter): Formatter with timestamp.
        format_without_ts (logging.Formatter): Formatter without timestamp.
    """
    def __init__(self) -> None:
        """
        Initializes the ConditionalTimestampFormatter with two formatters:
        one with a timestamp and one without.
        """
        super().__init__()
        self.format_with_ts = logging.Formatter('%(asctime)s [%(filename)s:%(lineno)d] - %(message)s')
        self.format_without_ts = logging.Formatter('%(message)s')

    def format(self, record: logging.LogRecord) -> str:
        """
        Formats the log record based on the presence of the 'with_timestamp' attribute.

        Args:
            record (logging.LogRecord): The log record to format.

        Returns:
            str: The formatted log message.
        """
        use_ts = getattr(record, 'with_timestamp', False)
        formatter = self.format_with_ts if use_ts else self.format_without_ts
        return formatter.format(record)

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def get_rotating_logger(
    name: str = "png_logger",
    log_file_path: str = DEFAULT_LOG_FILE,
    max_bytes: int = 3 * 1024 * 1024,
    backup_count: int = 3,
    debug_mode: bool = False
) -> Tuple[logging.Logger, str]:
    """
    Get a logger with a rotating file handler.

    Args:
        name (str, optional): The name of the logger. Defaults to "png_logger".
        log_file_path (str, optional): The name of the log file. Defaults to "png.log".
        max_bytes (int, optional): The maximum size of the log file in bytes. Defaults to 3MB.
        backup_count (int, optional): The number of backup log files to keep. Defaults to 3.
        debug_mode (bool, optional): Whether to enable debug mode. Defaults to False.

    Returns:
        logging.Logger: The logger with a rotating file handler.
        log_file_path (str): The path to the log file.
    """
    if log_file_path == DEFAULT_LOG_FILE:
        log_file_path = resolve_user_file(DEFAULT_LOG_FILE)

    logger = logging.getLogger(name)
    logger.propagate = False
    logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)

    if not logger.handlers:
        handler = RotatingFileHandler(log_file_path, maxBytes=max_bytes, backupCount=backup_count)
        handler.setFormatter(ConditionalTimestampFormatter())
        logger.addHandler(handler)

    return logger, log_file_path
