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
import logging
from datetime import datetime
from typing import Dict


def _ensureDirectoryExists(directory: str, logger: logging.Logger) -> None:
    """
    Ensure that the specified directory exists. If it doesn't, create it along with any missing parent directories.

    Parameters:
    - directory (str): The path of the directory to be checked or created.
    """

    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        logger.info("Directory '%s' created.", directory)

def initDirectories(logger: logging.Logger) -> Dict[str, str]:
    """
    Initialize the necessary directories for storing race information
    This function creates a directory structure based on the current date if it does not already exist.
    The directory structure is as follows:
    - data/
        - YYYY_MM_DD/
            - race-info/

    Parameters:
    - logger (logging.Logger): Logger instance to log directory creation events.
    """

    ts_prefix = datetime.now().strftime("%Y_%m_%d")
    dir_map = {
        'race-info': f"data/{ts_prefix}/race-info/",
    }

    for directory in dir_map.values():
        _ensureDirectoryExists(directory, logger)

    return dir_map
