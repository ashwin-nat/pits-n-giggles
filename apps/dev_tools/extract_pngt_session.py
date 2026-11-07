# MIT License
#
# Copyright (c) [2026] [Ashwin Natarajan]
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

import argparse
import sys
import zipfile
from pathlib import Path
from typing import Optional, Sequence

from lib.pngt import PngtError, read_contents

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def main(argv: Optional[Sequence[str]] = None) -> int:
    """Save the raw session JSON bytes of a .pngt file as <pngt name>.json in cwd, or at -o if given.

    Returns:
        0 on success, 2 if the file has no session data section, 1 on any other error.
    """
    parser = argparse.ArgumentParser(description="Extract the session JSON from a .pngt file")
    parser.add_argument("file", help="Path to the .pngt file")
    parser.add_argument("-o", "--output", help="Output path (default: <pngt name>.json in cwd)")
    args = parser.parse_args(argv)

    try:
        entry = read_contents(args.file).session_data_entry
        if entry is None:
            print(f"{args.file} has no session data", file=sys.stderr)
            return 2
        with zipfile.ZipFile(args.file) as zf:
            data = zf.read(entry)
    except (PngtError, OSError, KeyError, zipfile.BadZipFile) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    out_path = Path(args.output) if args.output else Path.cwd() / f"{Path(args.file).stem}.json"
    try:
        out_path.write_bytes(data)
    except OSError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Saved {out_path}")
    return 0

if __name__ == '__main__':
    sys.exit(main())
