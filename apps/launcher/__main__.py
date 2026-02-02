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

def _rewrite_mcp_flag():
    if "--mcp" in sys.argv:
        # Remove --mcp
        sys.argv.remove("--mcp")

        # Inject the internal module dispatch
        sys.argv.insert(1, "--module")
        sys.argv.insert(2, "apps.mcp_server")

def _maybe_detach_console():
    """
    Detach the Windows console when running in GUI mode.
    Keep the console when running MCP or internal modules.
    """
    if os.name != "nt":
        return

    # Keep console if MCP or submodule mode is active
    if "--mcp" in sys.argv:
        return

    try:
        import ctypes
        ctypes.windll.kernel32.FreeConsole()
    except Exception: # pylint: disable=broad-except
        pass

def _dispatch_submodule():
    """
    Dispatcher for running specific submodules when the app is packaged with PyInstaller.

    This function is triggered when:
      1. The app is running as a PyInstaller-built executable (`sys.frozen` is True), AND
      2. The command line contains the `--module` flag.

    Purpose:
    --------
    PyInstaller bundles the entire application into a single executable.
    The launcher runs the subsystems individually as subprocesses. The subsystems are run as python modules
    with their own entry points.

    Example invocations:
        pits_n_giggles.exe --module apps.backend <...>
        pits_n_giggles.exe --module apps.save_viewer <...>
    """

    ALLOWED_MODULES = {
        "apps.backend",
        "apps.save_viewer",
        "apps.hud",
        "apps.broker",
        "apps.mcp_server",
    }

    _rewrite_mcp_flag()

    # Locate the module name and its args
    idx = sys.argv.index('--module')
    module = sys.argv[idx + 1]
    args = sys.argv[idx + 2:]

    # Validate module
    if module not in ALLOWED_MODULES:
        print(f"[dispatcher] ERROR: Attempted to run unauthorized module: {module}")
        sys.exit(2)

    # ---- CRITICAL PATH FIXUP ----
    if getattr(sys, "frozen", False):
        # PyInstaller: all packages live directly under _MEIPASS
        sys.path.insert(0, sys._MEIPASS)
    else:
        # Dev mode: project root
        project_root = os.path.abspath(os.path.dirname(__file__))
        sys.path.insert(0, project_root)

    # Rewrite argv so the submodule behaves like a real entrypoint
    sys.argv = [module] + args

    try:
        runpy.run_module(module, run_name="__main__")
        sys.exit(0)
    except Exception as e:
        print(f"[dispatcher] ERROR running {module}: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(3)

# ------------------------------------------------------------------------------------
# Main launcher entry point (only runs if not in `--module` mode)
# ------------------------------------------------------------------------------------

if __name__ == "__main__":
    _maybe_detach_console()
    if "--module" in sys.argv or "--mcp" in sys.argv:
        _dispatch_submodule()

    from apps.launcher.launcher import entry_point
    entry_point()
