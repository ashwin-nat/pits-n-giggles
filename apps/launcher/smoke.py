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

"""In-app smoke-test driver.

Spawns every launcher-managed subsystem with ``--smoke-test``, so each one runs its full
constructor (parse argv, pre_boot, logger, config load, mgmt IPC bind, pub/sub/dealer, route
and task registration) and then exits 0 without entering its run loop. The launcher aggregates
the child exit codes into a JSON report and exits 0/1.

This ships inside the frozen exe: it is the only piece that runs *inside* the app and spawns
the subsystems. Everything outside the app (locate the artifact, run it, render, propagate the
code) lives in ``scripts/build.py``.
"""

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from collections import Counter
from typing import NoReturn, Optional

from apps.launcher.subsystems import (BackendAppMgr, BrokerAppMgr, HudAppMgr,
                                      McpAppMgr, WebAppMgr)
from apps.launcher.subsystems.base_mgr import build_launch_command
from lib.config import PngSettings, save_config_to_json
from lib.file_path import resolve_user_file
from lib.version import get_version

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

# Per-child wall-clock ceiling. A construct-only run is sub-second in practice; this only trips
# if a constructor hangs (a socket bind that never returns, say). Tighten once real timings land.
_TIMEOUT_SEC = 60

# Tail of the child's combined stdout+stderr kept in the report on a non-PASS result.
_OUTPUT_TAIL_CHARS = 4000

# display name, module path, extra args, runs on this platform?
SUBSYSTEMS = [
    ("Core",     BackendAppMgr.MODULE_PATH, [],            True),
    ("Web",      WebAppMgr.MODULE_PATH,     [],            True),
    ("HUD",      HudAppMgr.MODULE_PATH,     [],            sys.platform == "win32"),
    ("Pit Wall", BrokerAppMgr.MODULE_PATH,  [],            True),
    ("MCP",      McpAppMgr.MODULE_PATH,     ["--managed"], True),
]

# The set that *must* run on this platform. Checked against what actually ran so that "HUD
# silently stopped being covered on Windows" cannot hide inside a green build - a renamed
# manager, a dropped table row or a flipped predicate would all trip this.
EXPECTED = {
    "win32": {"Core", "Web", "HUD", "Pit Wall", "MCP"},
}.get(sys.platform, {"Core", "Web", "Pit Wall", "MCP"})

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def _write_throwaway_config(tmpdir: str) -> str:
    """Write a full-defaults config with every feature on into ``tmpdir``.

    Defaults already satisfy every construct-only requirement except the MCP HTTP server, which
    is off by default - forced on here so ``McpSubsystem`` builds its HTTP transport. ``HUD.enabled``
    is left alone: it already defaults True on every platform, and the schema has no OS-specific
    rule that would rewrite the file on the mac runner.

    Args:
        tmpdir: Directory to write ``png_config.json`` into.

    Returns:
        str: Absolute path to the written config file.
    """
    settings = PngSettings()
    settings.MCP.mcp_http_server_enable = True
    path = os.path.join(tmpdir, "png_config.json")
    save_config_to_json(settings, path)
    return path


def _run_one(name: str, module: str, extra: list, supported: bool, config_file: str) -> dict:
    """Spawn one subsystem in smoke mode and return its ``results`` entry.

    Every entry carries the same keys - ``exit_code`` / ``duration_sec`` are None for a
    SKIPPED row, ``output`` is empty on anything but FAIL / TIMEOUT - so the renderer and the
    report never have to special-case a shape.
    """
    row = {"name": name, "module": module, "exit_code": None,
           "duration_sec": None, "output": ""}

    if not supported:
        return {**row, "status": "SKIPPED", "reason": f"not supported on {sys.platform}"}

    cmd = build_launch_command(module, ["--config-file", config_file, "--smoke-test", *extra])
    started = time.monotonic()
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              text=True, timeout=_TIMEOUT_SEC, check=False)
        code, output = proc.returncode, proc.stdout
    except subprocess.TimeoutExpired as e:
        code, output = None, e.output or ""

    ok = code == 0
    return {**row,
            "status": "PASS" if ok else "TIMEOUT" if code is None else "FAIL",
            "exit_code": code,
            "duration_sec": round(time.monotonic() - started, 2),
            "output": "" if ok else output[-_OUTPUT_TAIL_CHARS:]}


def _fmt(value: object, unit: str = "") -> str:
    """Blank for None, else ``value`` with an optional unit suffix - for the table cells."""
    return "" if value is None else f"{value}{unit}"


def _render_text(report: dict) -> str:
    """Render the report as a plain-text table for stdout."""
    rows = report["results"]
    counts = Counter(r["status"] for r in rows)
    skips = [f"{r['name']}: {r['reason']}" for r in rows if r["status"] == "SKIPPED"]

    summary = f"{counts['PASS']} passed, {counts['FAIL'] + counts['TIMEOUT']} failed"
    if skips:
        summary += f", {len(skips)} skipped ({'; '.join(skips)})"

    lines = [
        f"Smoke test - {report['version']} - {report['platform']}"
        f"{' (frozen)' if report['frozen'] else ''}",
        "",
        f"  {'Subsystem':<10} {'Status':<8} {'Exit':>5} {'Time':>7}",
        f"  {'-' * 10} {'-' * 8} {'-' * 5} {'-' * 7}",
        *(f"  {r['name']:<10} {r['status']:<8} {_fmt(r['exit_code']):>5} "
          f"{_fmt(r['duration_sec'], 's'):>7}" for r in rows),
        "",
        summary,
        *(f"\n--- {r['name']} ({r['module']}) output ---\n{r['output']}"
          for r in rows if r["output"]),
    ]
    return "\n".join(lines)


def run_smoke_test(report_path: Optional[str] = None) -> NoReturn:
    """Construct every subsystem, run none, write the report, exit 0/1.

    Args:
        report_path: Where to write the JSON report. Defaults to
            ``resolve_user_file("png_smoke_report.json")`` so a bare ``--smoke-test`` works by hand.
    """
    report_path = report_path or resolve_user_file("png_smoke_report.json")
    tmpdir = tempfile.mkdtemp(prefix="png_smoke_")
    try:
        config_file = _write_throwaway_config(tmpdir)
        results = [_run_one(*entry, config_file) for entry in SUBSYSTEMS]
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    ran = {r["name"] for r in results if r["status"] != "SKIPPED"}
    passed = ran == EXPECTED and all(r["status"] == "PASS"
                                    for r in results if r["status"] != "SKIPPED")

    report = {
        "version": get_version(),
        "platform": sys.platform,
        "frozen": bool(getattr(sys, "frozen", False)),
        "passed": passed,
        "results": results,
    }
    if ran != EXPECTED:
        report["coverage_error"] = {
            "expected": sorted(EXPECTED), "ran": sorted(ran),
            "missing": sorted(EXPECTED - ran), "unexpected": sorted(ran - EXPECTED),
        }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(_render_text(report))
    if "coverage_error" in report:
        print(f"\nCOVERAGE ERROR: ran {sorted(ran)}, expected {sorted(EXPECTED)}")
    print(f"\nReport: {report_path}")

    sys.exit(0 if passed else 1)
