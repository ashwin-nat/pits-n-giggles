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
    log_file: str = "png_launcher.log", # TODO: Use a more appropriate path
    max_bytes: int = 3 * 1024 * 1024,
    backup_count: int = 3
) -> logging.Logger:
    """
    Sets up and returns a thread-safe logger with a conditional timestamp formatter
    and a rotating file handler.

    Args:
        name (str): Logger name.
        log_file (str): Path to the log file.
        max_bytes (int): Max file size before rotation.
        backup_count (int): Number of backup log files to keep.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count)
        handler.setFormatter(ConditionalTimestampFormatter())
        logger.addHandler(handler)

    return logger
