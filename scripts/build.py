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
import subprocess
import sys
import os
import shutil
import time
from pathlib import Path

# Run as `python scripts/build.py`, so sys.path[0] is scripts/ and the project root needs adding
# before meta.meta can be imported.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from meta.meta import APP_VERSION  # pylint: disable=wrong-import-position

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
        "--ci",
        action="store_true",
        help="Mark this as a non-dev build: the splash screen shows meta.meta.APP_VERSION "
             "instead of the git-derived dev string. Passed by the CI workflows.",
    )
    return parser.parse_args()

def main():
    args = parse_args()
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
    if args.debug:
        # PyInstaller splits its command line on `--` and hands the rest to the spec
        # file as sys.argv[1:]. png.spec looks for --force-debug there.
        pyinstaller_cmd += ["--", "--force-debug"]
        print("build.py: --debug given; the packaged app will always run with --debug.")

    # png.spec renders the splash image, which reads its version through lib/version.py. That
    # returns $PNG_VERSION when set and otherwise a git-derived `dev_<branch>_<sha>_<state>`
    # string, so an ad-hoc local build is visibly marked as one. --ci opts out of that
    # marking; the CI workflows pass it. Without it a tagged CI build would read
    # `dev_HEAD_<sha>_clean`, since Actions checks out a detached HEAD.
    #
    # This only affects the splash. The app's own version always comes from the runtime hook
    # png.spec generates, which bakes in APP_VERSION regardless of this flag.
    pyinstaller_env = dict(os.environ)
    if args.ci:
        pyinstaller_env["PNG_VERSION"] = APP_VERSION
        print(f"build.py: --ci given; splash version stamped as {APP_VERSION}.")

    subprocess.run(pyinstaller_cmd, check=True, env=pyinstaller_env)

    # 3. Cleanup the custom COLLECT dir
    remove_dir_if_exists(collect_dir)

    end_time = time.time()
    elapsed = end_time - start_time
    print(f"\n Build completed in {elapsed:.2f} seconds.")

if __name__ == "__main__":
    main()
