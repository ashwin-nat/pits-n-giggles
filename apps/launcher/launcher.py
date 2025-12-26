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

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

import argparse
import atexit
import ctypes
import os
import shutil
import sys
import tempfile

from apps.launcher.gui import PngLauncherWindow
from lib.file_path import resolve_user_file
from lib.ipc import IpcServerSync
from lib.version import get_version
from meta.meta import APP_NAME, APP_NAME_SNAKE

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

_temp_icon_file = None

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments for the application.

    Returns:
        argparse.Namespace: Parsed command-line arguments containing:
            - smoke_test (Optional[str]): Name or mode for smoke testing, if provided.
            - debug (bool): True if debug mode is enabled, False otherwise.
    """
    parser = argparse.ArgumentParser(description=f"Launch {APP_NAME}")

    # Smoke test requires an argument if provided
    parser.add_argument(
        "--smoke-test",
        required=False,
        help="Run smoke test with a required mode or test name",
        metavar="TEST_NAME"
    )

    # Debug mode is an optional boolean flag
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )

    # Optional config file
    parser.add_argument(
        "--config-file",
        nargs="?",
        default="png_config.json",
        help="Configuration file name (optional)"
    )

    # Replay server is an optional boolean flag
    parser.add_argument(
        "--replay-server",
        action="store_true",
        help="Enable replay mode"
    )

    # If integration test IPC port is specified, start an IPC server
    parser.add_argument(
        "--ipc-port",
        type=int,
        default=None,
        help="Port to enable synchronous IPC server for integration testing."
    )

    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Enable coverage mode"
    )

    return parser.parse_args()

def resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller.
    """
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, relative_path)
    # Base path is project root (2 levels up from this file)
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    return os.path.join(base_path, relative_path)

def load_icon_safely(icon_relative_path):
    """
    Workaround for tkinter.iconbitmap() failing to load .ico from _MEIPASS.
    """
    global _temp_icon_file
    icon_path = resource_path(icon_relative_path)

    if getattr(sys, 'frozen', False):
        # Copy .ico file to a real temp file so tkinter can access it
        tmp_fd, tmp_icon_path = tempfile.mkstemp(suffix=".ico")
        os.close(tmp_fd)
        shutil.copyfile(icon_path, tmp_icon_path)
        _temp_icon_file = tmp_icon_path
        return tmp_icon_path
    return icon_path

def _cleanup_temp_icon():
    """
    Cleanup temp icon file.
    """
    global _temp_icon_file
    if _temp_icon_file and os.path.exists(_temp_icon_file):
        try:
            os.remove(_temp_icon_file)
        except Exception: # pylint: disable=broad-except
            pass
        _temp_icon_file = None

def smoke_test(file_content: str) -> None:
    """Create a test file at the log file path. (CWD for windows, ~/Library/Application Support/pits_n_giggles for mac)
        Parent process is responsible to test if the file exists.

        Args:
            file_content (str): The content to write to the file.
    """
    path = resolve_user_file("png_smoke_test.txt")
    with open(path, "w", encoding='utf-8') as f:
        f.write(file_content)

atexit.register(_cleanup_temp_icon)

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

APP_ICON_PATH = str(resource_path("assets/logo.png"))

# -------------------------------------- ENTRY POINT -------------------------------------------------------------------

def entry_point() -> None:
    """
    Main entry point for the Pits n' Giggles application.

    Handles:
        - Running smoke tests if the --smoke-test flag is provided.
        - Launching the main Tkinter application otherwise.
    """
    args: argparse.Namespace = parse_args()

    # Handle smoke test
    if args.smoke_test is not None:
        smoke_test(args.smoke_test)
        sys.exit(0)

    # Set AppUserModelID to ensure correct taskbar icon in dev mode
    if os.name == "nt":  # Only on Windows
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_NAME_SNAKE)
        except Exception: # pylint: disable=broad-except
            pass

    app = PngLauncherWindow(
        ver_str=get_version(),
        config_file=args.config_file,
        logo_path=APP_ICON_PATH,
        debug_mode=args.debug,
        replay_mode=args.replay_server,
        integration_test_mode=args.ipc_port is not None,
        coverage_enabled=args.coverage
    )

    ipc = None
    if args.ipc_port is not None:
        ipc = IpcServerSync(
            port=args.ipc_port,
            name="launcher_ipc",
            max_missed_heartbeats=3,
            heartbeat_timeout=5.0,
        )

        def ipc_shutdown_callback(_args: dict) -> dict:
            app.request_shutdown()
            return {"status": "success"}

        # shutdown handler (__shutdown__)
        ipc.register_shutdown_callback(ipc_shutdown_callback)

        # heartbeat missed callback
        ipc.register_heartbeat_missed_callback(ipc_shutdown_callback)

        # minimal generic handler
        def launcher_handler(request: dict) -> dict:
            return {
                "status": "error",
                "message": f"Launcher does not support IPC requests. Unknown command {request['cmd']}",
            }

        ipc.serve_in_thread(handler_fn=launcher_handler, timeout=0.25)

    # main loop
    try:
        app.run()
    finally:
        if ipc:
            ipc.close()
