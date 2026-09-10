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

# ----------------------------------------------------------------------------------------------------------------------

import argparse
import json
import subprocess
import sys
import os
import shutil
import tempfile
import time
from pathlib import Path

APP_NAME = "pits_n_giggles"  # or load from the spec file dynamically if needed
COLLECT_DIR_NAME = f"{APP_NAME}_build_tmp"

def remove_dir_if_exists(path: str):
    if os.path.isdir(path):
        shutil.rmtree(path)

def parse_args() -> argparse.Namespace:
    """Parse build-time options."""
    parser = argparse.ArgumentParser(description=f"Build {APP_NAME}")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Force debug logging on in the packaged app (it runs as if launched with --debug)",
    )
    parser.add_argument(
        "--release",
        action="store_true",
        help="Report the bare meta.py version. Without it the build is stamped with the "
             "commit it was made from, so non-release builds are identifiable.",
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Skip the build. Run the launcher's --smoke-test against the existing dist/ "
             "artifact (or --from-source), render the report, and exit with its status.",
    )
    parser.add_argument(
        "--from-source",
        action="store_true",
        help="With --smoke-test, run `python -m apps.launcher` instead of a built artifact.",
    )
    return parser.parse_args()

def _find_artifact_cmd() -> list:
    """Command prefix that launches the built app in dist/. Exits if there is none."""
    if sys.platform == "darwin":
        bundles = sorted(Path("dist").glob("*.app"))
        if not bundles:
            raise SystemExit("smoke test: no .app in dist/ - run build.py first")
        return [str(bundles[0] / "Contents" / "MacOS" / bundles[0].stem)]
    exes = sorted(Path("dist").glob("*.exe"))
    if not exes:
        raise SystemExit("smoke test: no .exe in dist/ - run build.py first")
    return [str(exes[0])]

def _append_step_summary(report: "dict | None", returncode: int) -> None:
    """Append a markdown table for the report to $GITHUB_STEP_SUMMARY. No-op when unset."""
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_file:
        return

    lines = ["## Smoke test", ""]
    if report is None:
        lines.append(f"No report written; launcher exited {returncode}.")
    else:
        verdict = "PASS" if report["passed"] else "FAIL"
        frozen = " (frozen)" if report["frozen"] else ""
        lines += [
            f"`{report['version']}` on `{report['platform']}`{frozen} - **{verdict}**", "",
            "| Subsystem | Status | Exit | Time |", "|---|---|---|---|",
        ]
        for r in report["results"]:
            code = "" if r.get("exit_code") is None else r["exit_code"]
            dur = "" if r.get("duration_sec") is None else f"{r['duration_sec']}s"
            lines.append(f"| {r['name']} | {r['status']} | {code} | {dur} |")
        for r in report["results"]:
            if r["status"] in ("FAIL", "TIMEOUT") and r.get("output"):
                lines += ["", f"<details><summary>{r['name']} output</summary>", "",
                          "```", r["output"].strip(), "```", "</details>"]

    with open(summary_file, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

def run_smoke_test(from_source: bool = False) -> int:
    """Run the launcher's --smoke-test, render the JSON report, return the launcher's exit code.

    The launcher already prints a plain-text table to stdout (inherited here, so it lands in
    the CI step log); this only adds the markdown summary for $GITHUB_STEP_SUMMARY, which
    survives the step exiting non-zero as long as it is written first.
    """
    app_cmd = [sys.executable, "-m", "apps.launcher"] if from_source else _find_artifact_cmd()

    source = "source" if from_source else app_cmd[0]
    print(f"Running smoke test ({source}) ...\n", flush=True)

    with tempfile.TemporaryDirectory() as tmp:
        report_path = os.path.join(tmp, "png_smoke_report.json")
        result = subprocess.run(
            [*app_cmd, "--smoke-test", "--smoke-report", report_path], check=False)
        report = None
        if os.path.exists(report_path):
            with open(report_path, encoding="utf-8") as f:
                report = json.load(f)

    _append_step_summary(report, result.returncode)
    return result.returncode

def main():
    args = parse_args()
    if args.smoke_test:
        sys.exit(run_smoke_test(from_source=args.from_source))

    script_dir = os.path.dirname(__file__)
    spec_path = os.path.join(script_dir, "png.spec")
    collect_dir = os.path.join("dist", COLLECT_DIR_NAME)

    # 0. Cleanup previous files
    remove_dir_if_exists("build")
    remove_dir_if_exists("dist")

    start_time = time.time()

    # 1. Build f1-telemetry-viewer React app (must precede PyInstaller so dist/ is bundled)
    viewer_source = Path("apps/external/f1-save-viewer")
    if not (viewer_source / "package.json").exists():
        raise RuntimeError(
            "Viewer submodule not initialized. Run: git submodule update --init"
        )
    build_env = {
        **os.environ,
        "VITE_BASE_PATH": "/save-viewer/",
        "VITE_EXTERNAL_LINK_TEMPLATE": "/legacy/{slug}",
        "VITE_EXTERNAL_LINK_LABEL": "Legacy View",
        "VITE_DISABLE_ANALYTICS": "true",
        "VITE_APP_NAME": "Pits n' Giggles",
        # Prevent MSYS2/Git Bash from converting POSIX paths (e.g. /legacy/{slug})
        # to Windows paths (e.g. C:/Program Files/Git/legacy/{slug}).
        "MSYS_NO_PATHCONV": "1",
        "MSYS2_ARG_CONV_EXCL": "*",
    }
    subprocess.run("pnpm install", cwd=viewer_source, check=True, shell=True)
    subprocess.run(
        "pnpm build --mode production",
        cwd=viewer_source,
        env=build_env,
        check=True,
        shell=True,
    )

    # 2. Run PyInstaller
    pyinstaller_cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        spec_path,
    ]
    # PyInstaller splits its command line on `--` and hands the rest to the spec file as
    # sys.argv[1:]. Renamed on the way through because PyInstaller has its own --debug.
    spec_args = []
    if args.debug:
        spec_args.append("--force-debug")
        print("build.py: --debug given; the packaged app will always run with --debug.")
    if args.release:
        spec_args.append("--release-build")
        print("build.py: --release given; the build reports the bare meta.py version.")
    if spec_args:
        pyinstaller_cmd += ["--", *spec_args]

    subprocess.run(pyinstaller_cmd, check=True)

    # 3. Cleanup the custom COLLECT dir
    remove_dir_if_exists(collect_dir)

    end_time = time.time()
    elapsed = end_time - start_time
    print(f"\n Build completed in {elapsed:.2f} seconds.")

if __name__ == "__main__":
    main()
