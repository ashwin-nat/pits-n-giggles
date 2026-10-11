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

"""Per-sensor size statistics for .pngt recordings, used to calibrate the entropy classes.

Run from the repo root:

    # one recording
    poetry run python -m apps.dev_tools.pngt_sensor_stats --file data/2026_09_25/telemetry/x.pngt

    # every .pngt under a directory (recursive), aggregated into one table
    poetry run python -m apps.dev_tools.pngt_sensor_stats --dir data

    # machine-readable
    poetry run python -m apps.dev_tools.pngt_sensor_stats --dir data --json

Exits 1 if no readable recordings were found.
"""

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

import argparse
import json
import math
import re
import sys
import zipfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from tabulate import tabulate

from lib.config.schema.lap_analyzer import ENTROPY_BYTES_PER_SAMPLE
from lib.pngt.dto import MANDATORY_TELEMETRY_KEYS, SensorConfig
from lib.pngt.exceptions import PngtError
from lib.pngt.reader import read_session

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

_LAP_ENTRY_RE = re.compile(r"^drivers/\d+/lap_\d+\.npz$")
_ROW_KEY = "lap_distance"  # present in every lap, so its sample count is the row count

# -------------------------------------- CLASSES -----------------------------------------------------------------------

@dataclass
class _Acc:
    """Running totals for one sensor key across all files"""
    samples: int = 0
    raw_bytes: int = 0
    compressed_bytes: int = 0
    min_val: Optional[float] = None
    max_val: Optional[float] = None

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def _find_files(args: argparse.Namespace) -> List[Path]:
    if args.file:
        return [Path(args.file)]
    return sorted(Path(args.dir).rglob("*.pngt"))


def _accumulate_lap(accs: Dict[str, _Acc], npz_bytes: bytes) -> None:
    """Add one lap's .npz to the per-key totals. Sizes come from the inner .npy entries
    of the npz, so they are the real on-disk cost of each array."""
    with zipfile.ZipFile(BytesIO(npz_bytes)) as inner:
        sizes = {Path(i.filename).stem: i for i in inner.infolist()}
    with np.load(BytesIO(npz_bytes)) as npz:
        for key in npz.files:
            arr = npz[key]
            acc = accs.setdefault(key, _Acc())
            acc.samples += int(arr.size)
            info = sizes.get(key)
            if info is not None:
                acc.raw_bytes += info.file_size
                acc.compressed_bytes += info.compress_size
            if arr.size and not np.all(np.isnan(arr)):
                lo, hi = float(np.nanmin(arr)), float(np.nanmax(arr))
                acc.min_val = lo if acc.min_val is None else min(acc.min_val, lo)
                acc.max_val = hi if acc.max_val is None else max(acc.max_val, hi)


def _scan_file(path: Path, accs: Dict[str, _Acc], manifest: Dict[str, SensorConfig],
               conflicts: set) -> int:
    """Fold one recording into the totals. Returns its size on disk."""
    for sensor in read_session(path).sensors:
        seen = manifest.setdefault(sensor.key, sensor)
        if seen != sensor:
            conflicts.add(sensor.key)
    with zipfile.ZipFile(path) as zf:
        for name in zf.namelist():
            if _LAP_ENTRY_RE.match(name):
                _accumulate_lap(accs, zf.read(name))
    return path.stat().st_size


def _entropy_class(bytes_per_sample: float) -> Optional[str]:
    """Nearest ENTROPY_BYTES_PER_SAMPLE class in log space"""
    if bytes_per_sample <= 0:
        return None
    return min(ENTROPY_BYTES_PER_SAMPLE,
               key=lambda c: abs(math.log(ENTROPY_BYTES_PER_SAMPLE[c]) - math.log(bytes_per_sample))).value


def _build_report(paths: List[Path]) -> Dict[str, Any]:
    accs: Dict[str, _Acc] = {}
    manifest: Dict[str, SensorConfig] = {}
    conflicts: set = set()
    total_bytes = 0
    files = 0
    for path in paths:
        try:
            total_bytes += _scan_file(path, accs, manifest, conflicts)
            files += 1
        except (PngtError, zipfile.BadZipFile, OSError, ValueError) as exc:
            print(f"skipped {path}: {exc}", file=sys.stderr)

    rows = accs[_ROW_KEY].samples if _ROW_KEY in accs else 0
    sensors = []
    for key in sorted(accs, key=lambda k: (k not in MANDATORY_TELEMETRY_KEYS, k)):
        acc = accs[key]
        cfg = manifest.get(key)
        bps = acc.compressed_bytes / acc.samples if acc.samples else 0.0
        sensors.append({
            "key": key,
            "label": cfg.label if cfg else None,
            "unit": cfg.unit if cfg else None,
            "type": cfg.type.value if cfg else None,
            "declared_range": list(cfg.range) if cfg and cfg.range else None,
            "mandatory": key in MANDATORY_TELEMETRY_KEYS,
            "manifest_differs": key in conflicts,
            "num_samples": acc.samples,
            "observed_range": [acc.min_val, acc.max_val] if acc.min_val is not None else None,
            "raw_bytes": acc.raw_bytes,
            "compressed_bytes": acc.compressed_bytes,
            "ratio": acc.raw_bytes / acc.compressed_bytes if acc.compressed_bytes else None,
            "bytes_per_sample": bps,
            "entropy_class": _entropy_class(bps),
        })
    return {
        "files": files,
        "rows": rows,
        "bytes_per_row": total_bytes / rows if rows else None,
        "sensors": sensors,
    }


def _fmt_range(rng: Optional[List[float]]) -> str:
    return "-" if rng is None else f"{rng[0]:g}..{rng[1]:g}"


def _print_table(report: Dict[str, Any]) -> None:
    bpr = report["bytes_per_row"]
    print(f"files: {report['files']}  rows: {report['rows']}  "
          f"bytes/row (whole file): {'-' if bpr is None else f'{bpr:.3f}'}")
    header = ["key", "type", "samples", "declared", "observed", "raw B", "comp B", "ratio", "B/sample", "class"]
    table = []
    for s in report["sensors"]:
        table.append([
            s["key"] + (" *" if s["manifest_differs"] else ""),
            s["type"] or "-",
            str(s["num_samples"]),
            _fmt_range(s["declared_range"]),
            _fmt_range(s["observed_range"]),
            str(s["raw_bytes"]),
            str(s["compressed_bytes"]),
            "-" if s["ratio"] is None else f"{s['ratio']:.1f}",
            f"{s['bytes_per_sample']:.3f}",
            s["entropy_class"] or "-",
        ])
    print(tabulate(table, headers=header, tablefmt="simple",
                   colalign=("left", "left") + ("right",) * 7 + ("left",)))
    if any(s["manifest_differs"] for s in report["sensors"]):
        print("* manifest entry differs between files; the first one seen is shown")


def main() -> int:
    parser = argparse.ArgumentParser(description="Per-sensor size statistics for .pngt recordings")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", help="a single .pngt file")
    group.add_argument("--dir", help="a directory, searched recursively for *.pngt")
    parser.add_argument("--json", action="store_true", help="print JSON instead of a table")
    args = parser.parse_args()

    report = _build_report(_find_files(args))
    if report["files"] == 0:
        print("no readable .pngt files found", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        _print_table(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
