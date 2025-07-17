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

import aiofiles
import json
from pathlib import Path
from typing import Optional

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

async def save_race_info(data: dict, filename: str, date_str: str, base_dir: Optional[Path] = None) -> None:
    """
    Saves the given dictionary as a JSON file in data/<date>/race-info/.

    Args:
        data (dict): The data to save.
        filename (str): Name of the file (e.g., "race.json").
        date_str (str): Date string for directory structure (e.g., "2025-07-17").
        base_dir (Path, optional): Custom base directory for saving. Defaults to current directory.
    """
    if base_dir is None:
        base_dir = Path("data")
    else:
        base_dir = Path(base_dir) / "data"

    dir_path = base_dir / date_str / "race-info"
    dir_path.mkdir(parents=True, exist_ok=True)

    file_path = dir_path / filename
    async with aiofiles.open(file_path, mode='w', encoding='utf-8') as f:
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        await f.write(json_str)
