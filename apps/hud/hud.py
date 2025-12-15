# MIT License
#
# Copyright (c) [2024] [Ashwin Natarajan]
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
import logging
import sys

from lib.child_proc_mgmt import report_pid_from_child
from lib.config import PngSettings, load_config_from_json
from lib.error_status import PNG_ERROR_CODE_UNSUPPORTED_OS
from lib.logger import get_logger
from meta.meta import APP_NAME

from .ipc import run_ipc_task
from .listener.task import run_hud_update_threads
from .ui.infra import OverlaysMgr

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def parseArgs() -> argparse.Namespace:
    """Parse the command line args and perform validation

    Returns:
        argparse.Namespace: The parsed args namespace
    """

    # Initialize the ArgumentParser
    parser = argparse.ArgumentParser(description=f"{APP_NAME} HUD")

    # Add command-line arguments with default values
    parser.add_argument("--config-file", nargs="?", default="png_config.ini", help="Configuration file name (optional)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument('--run-ipc-server', action='store_true', help="Run IPC server on OS assigned port")
    parser.add_argument('--xpub-port', type=int, default=None, help="IPC xpub port") # unused
    parser.add_argument('--xsub-port', type=int, default=None, help="IPC xsub port") # unused

    # Parse the command-line arguments
    return parser.parse_args()

def main(logger: logging.Logger, config: PngSettings, debug_mode: bool, xpub_port: int) -> None:
    """Main function

    Args:
        logger (logging.Logger): Logger
        config (PngSettings): Configurations
        debug_mode (bool): Debug mode
        xpub_port (int): IPC xpub port
    """

    overlays_mgr = OverlaysMgr(logger, config, debug=debug_mode)

    socketio_client, ipc_sub = run_hud_update_threads(
        logger=logger,
        overlays_mgr=overlays_mgr,
        port=config.Network.server_port,
        low_freq_update_interval_ms=config.Display.refresh_interval,
        xpub_port=xpub_port)

    run_ipc_task(
        logger=logger,
        overlays_mgr=overlays_mgr,
        socketio_client=socketio_client,
        ipc_sub=ipc_sub)

    overlays_mgr.run()
# -------------------------------------- ENTRY POINT -------------------------------------------------------------------

def entry_point():
    """Entry point"""
    if sys.platform != 'win32':
        sys.exit(PNG_ERROR_CODE_UNSUPPORTED_OS)

    report_pid_from_child()
    args = parseArgs()
    png_logger = get_logger("hud", args.debug, jsonl=True)
    configs = load_config_from_json(args.config_file, png_logger)
    try:
        main(
            logger=png_logger,
            config=configs,
            debug_mode=args.debug,
            xpub_port=args.xpub_port)
    except KeyboardInterrupt:
        png_logger.info("Program interrupted by user.")
    except Exception as e: # pylint: disable=broad-except
        png_logger.exception("Error in main: %s", e)
        sys.exit(1)

    png_logger.info("HUD application exiting normally.")

# ---------------------------------------- PROFILER MODE ---------------------------------------------------------------

# import yappi
# import pstats

# def save_pstats_report(html_filename, txt_filename):
#     stats = pstats.Stats("hud_profile.prof")

#     # Don't strip directories, so full paths are included
#     # If you want the paths to be fully visible, just skip strip_dirs()
#     stats.sort_stats("cumulative")

#     # Save as HTML
#     with open(html_filename, "w") as f:
#         f.write("<html><head><title>Yappi Profile</title></head><body><pre>")
#         stats.stream = f
#         stats.print_stats()
#         f.write("</pre></body></html>")

#     # Save as TXT
#     with open(txt_filename, "w") as f:
#         stats.stream = f
#         stats.print_stats()

# def save_thread_report(filename):
#     ts = yappi.get_thread_stats()
#     with open(filename, "w") as f:
#         for t in ts:
#             f.write(
#                 f"Thread {t.name} (id={t.id})\n"
#                 f"  Total time : {t.ttot}\n"
#                 f"  Scheduled  : {t.sched_count} times\n"
#                 f"  Avg time   : {t.ttot / max(t.sched_count,1)}\n"
#                 "\n"
#             )

# def entry_point():
#     """Entry point"""

#     # ---- PROFILING START ----------------------------------------------------
#     yappi.set_clock_type("wall")     # or "cpu"
#     yappi.start()
#     # -------------------------------------------------------------------------

#     report_pid_from_child()
#     args = parseArgs()
#     png_logger = get_logger("hud", args.debug, jsonl=True)
#     configs = load_config_from_json(args.config_file, png_logger)

#     try:
#         main(
#             logger=png_logger,
#             config=configs,
#             ipc_port=args.ipc_port,
#             debug_mode=args.debug
#         )
#     except KeyboardInterrupt:
#         png_logger.info("Program interrupted by user.")
#     except Exception as e:
#         png_logger.exception("Error in main: %s", e)
#         sys.exit(1)
#     finally:
#         yappi.stop()

#         # Save global function stats
#         yappi.get_func_stats().save("hud_profile.prof", type="pstat")

#         # Save function stats PER THREAD
#         for t in yappi.get_thread_stats():
#             yappi.get_func_stats(filter={'thread_id': t.id}).save(
#                 f"hud_thread_{t.id}.prof",
#                 type="pstat"
#             )

#         # Save HTML/TXT summary (your existing code)
#         save_pstats_report("hud_profile.html", "hud_profile.txt")

#         # Optional thread report
#         save_thread_report("hud_threads.txt")
#         # ----------------------------------------------------------------------

#     png_logger.info("HUD application exiting normally.")
