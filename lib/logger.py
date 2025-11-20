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

import logging
import json
from datetime import datetime

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def get_logger(
    name: str,
    debug_mode: bool = False,
    jsonl: bool = False
) -> logging.Logger:

    png_logger = logging.getLogger(name)
    png_logger.propagate = False
    png_logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)

    handler = logging.StreamHandler()

    if jsonl:
        # timestamp with milliseconds
        ts_format = "%Y-%m-%d %H:%M:%S.%f"
        formatter = JsonlFormatter(datefmt=ts_format)
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    handler.setFormatter(formatter)

    if not png_logger.handlers:
        png_logger.addHandler(handler)

    return png_logger

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
