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

import os
import sys
import runpy
import traceback

def _prod_pre_checks():
    # Allowed modules for dispatch
    ALLOWED_MODULES = {
        "apps.backend",
        "apps.save_viewer",
    }

    # --------------------------------------------------------------------------------------------------
    # [Block 1] Frozen mode setup (PyInstaller bootstrapping)
    # --------------------------------------------------------------------------------------------------
    # If running from a PyInstaller-built EXE, sys._MEIPASS points to the unpacked temp dir.
    # We add this to sys.path so that imports like 'apps.*' work as expected.

    idx = sys.argv.index('--module')
    module = sys.argv[idx + 1]
    args = sys.argv[idx + 2:]

    if module not in ALLOWED_MODULES:
        print(f"[dispatcher] ERROR: Attempted to run unauthorized module: {module}")
        sys.exit(1)

    sys.path.insert(0, os.path.join(sys._MEIPASS))
    sys.argv = [module] + args

    try:
        runpy.run_module(module, run_name="__main__")
    except Exception as e: # pylint: disable=broad-exception-caught
        print(f"[dispatcher] ERROR: Exception during run_module: {e}")
        traceback.print_exc()
        sys.exit(1)

    # --------------------------------------------------------------------------------------------------
    # [Block 2] Submodule dispatcher (run subsystems via --module)
    # --------------------------------------------------------------------------------------------------
    # Enables running subsystems like:
    #   pits_n_giggles.exe --module apps.backend
    #   pits_n_giggles.exe --module apps.save_viewer
    #
    # We rewrite sys.argv and use runpy to launch the target module.

    idx = sys.argv.index('--module')
    module = sys.argv[idx + 1]
    args = sys.argv[idx + 2:]

    sys.path.insert(0, os.path.join(sys._MEIPASS))
    sys.argv = [module] + args

    try:
        runpy.run_module(module, run_name="__main__")
    # pylint: disable=broad-exception-caught
    except Exception as e:
        print(f"[__main__.py] Error launching module {module}: {e}")
        traceback.print_exc()
    sys.exit(0)


    # --------------------------------------------------------------------------------------------------
    # [Block 3] Force PyInstaller to include subsystem __main__.py files
    # --------------------------------------------------------------------------------------------------
    # PyInstaller won't include these unless we explicitly reference them.
    # This block is never executed, but it's scanned by PyInstaller's static analysis.
    # pylint: disable=using-constant-test
    # pylint: disable=unused-import
    if False: # pylint: disable=unreachable
        import apps.backend.__main__ # pylint: disable=import-outside-toplevel
        import apps.save_viewer.__main__ # pylint: disable=import-outside-toplevel

if getattr(sys, 'frozen', False) and '--module' in sys.argv:
    _prod_pre_checks()


# --------------------------------------------------------------------------------------------------
# Main launcher entry point (only runs if not in --module mode)
# --------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        from apps.launcher.launcher import entry_point
    # pylint: disable=broad-exception-caught
    except Exception as e:
        print(f"[__main__.py] Failed to import launcher: {e}")
        traceback.print_exc()
        sys.exit(1)

    entry_point()
