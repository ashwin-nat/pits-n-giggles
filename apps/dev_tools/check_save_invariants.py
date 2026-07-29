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

"""Check saved session JSON files against the state-layer invariants.

Run from the repo root:

    # one specific file
    poetry run python -m apps.dev_tools.check_save_invariants data/2026_07_29/race-info/Race_Melbourne_*.json

    # everything produced by an integration run
    poetry run python -m apps.dev_tools.check_save_invariants "data/**/*.json"

    # only show the failures
    poetry run python -m apps.dev_tools.check_save_invariants -q "data/**/*.json"

Exits 1 if any file has a violation, so it can gate a script.
"""

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

import argparse
import glob
import json
import sys
from pathlib import Path
from typing import List

from lib.save_invariants import checkSaveFile

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def expandPaths(patterns: List[str]) -> List[Path]:
    """Expand the given paths or globs into concrete JSON files.

    Args:
        patterns (List[str]): Paths or glob patterns

    Returns:
        List[Path]: Sorted, de-duplicated list of matching files
    """

    paths = set()
    for pattern in patterns:
        candidate = Path(pattern)
        if candidate.is_file():
            paths.add(candidate)
        elif candidate.is_dir():
            paths.update(candidate.rglob("*.json"))
        else:
            paths.update(Path(p) for p in glob.glob(pattern, recursive=True))
    return sorted(paths)

def main() -> int:
    """Entry point.

    Returns:
        int: 0 if every file passed, else 1
    """

    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("paths", nargs="+", help="Save file(s), directory, or glob pattern")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="Only print files that have violations")
    parser.add_argument("--max-violations", type=int, default=10,
                        help="Cap violations printed per file (default: 10, 0 for all)")
    args = parser.parse_args()

    files = expandPaths(args.paths)
    if not files:
        print(f"No JSON files matched: {' '.join(args.paths)}", file=sys.stderr)
        return 1

    failed = 0
    for path in files:
        try:
            with open(path, "r", encoding="utf-8") as f:
                save = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"[ERROR] {path}: {e}")
            failed += 1
            continue

        report = checkSaveFile(save)
        if report.ok:
            if not args.quiet:
                print(f"[PASS] {path.name}  ({report.summary()})")
            continue

        failed += 1
        print(f"[FAIL] {path.name}  ({report.summary()})")
        shown = report.violations if args.max_violations == 0 else report.violations[:args.max_violations]
        for violation in shown:
            print(f"         {violation}")
        if len(report.violations) > len(shown):
            print(f"         ... and {len(report.violations) - len(shown)} more")

    print(f"\n{len(files) - failed}/{len(files)} files passed")
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(main())
