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
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiofiles

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

async def save_json_to_file(
    data: dict,
    filename: str,
    base_dir: Optional[Path] = None
) -> Path:
    """
    Saves the given dictionary as a JSON file in data/<date>/race-info/.

    Args:
        data (dict): The data to save.
        filename (str): Name of the file (e.g., "race.json").
        base_dir (Path, optional): Custom base directory for saving.
                                   If not provided, uses current date (YYYY_MM_DD) under 'data'.

    Returns:
        Path: The full path to the saved JSON file.
    """
    if base_dir is None:
        date_str = datetime.now().strftime("%Y_%m_%d")
        base_dir = Path("data") / date_str
    else:
        base_dir = Path(base_dir) / "data"

    dir_path = base_dir / "race-info"
    dir_path.mkdir(parents=True, exist_ok=True)

    file_path = dir_path / filename
    json_str = json.dumps(data, separators=(",", ":"))
    async with aiofiles.open(file_path, mode='w', encoding='utf-8') as json_file:
        await json_file.write(json_str)

    return file_path
