#!/usr/bin/env python3
"""
Simple integration test for Pits n Giggles App
"""

import argparse
import asyncio
import os
import platform
import signal
import ssl
import subprocess
import sys
import threading
import json
import queue
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import gdown
from aiohttp import ClientSession, TCPConnector

# Add the parent directory to the Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from lib.child_proc_mgmt import (enable_integration_test_mode,
                                 extract_integration_fail_from_line,
                                 extract_save_skipped_from_line,
                                 extract_saved_path_from_line)
from lib.config import load_config_from_json
from lib.f1_types import MAX_DRIVERS
from lib.ipc import IpcClientSync, get_free_tcp_port
from lib.save_invariants import checkSaveFile
from tests.integration_test.diff_utils import (create_worktree, diff_captures,
                                               normalize_for_diff, remove_worktree,
                                               resolve_commit)
from tests.integration_test.log import create_logger, TestLogger
from apps.dev_tools.telemetry_replayer import send_telemetry_data

# Constants
DRIVE_FOLDER_URL = "https://drive.google.com/drive/folders/13tIadKMvi3kuItkovT6GUTTHOL3YM6n_?usp=drive_link"
IS_WINDOWS = platform.system() == "Windows"
TEST_DATA_DIR = PROJECT_ROOT / "test_data"

# Base-commit endpoint captures, keyed by base commit. Not golden files: nothing here is
# committed or reviewed, it is a throwaway cache that regenerates on demand - see
# state-mgmt-simplification.md's "Regression harness" section for why.
DIFF_CACHE_DIR = TEST_DATA_DIR / ".diff_cache"

# Global state for signal handling
app_process: Optional[subprocess.Popen] = None
exit_event: Optional[threading.Event] = None
ipc_port: Optional[int] = None
app_died_reported: bool = False  # so an app death is announced once, not per heartbeat

# Test statistics
test_stats = {
    "files_processed": 0,
    "telemetry_sent": 0,
    "telemetry_failed": 0,
    "endpoints_passed": 0,
    "endpoints_failed": 0,
    "saves_checked": 0,
    "saves_skipped": 0,
    "saves_unreadable": 0,
    "invariant_violations": 0,
    "diff_violations": 0,
}

logger = create_logger()


def get_cached_files() -> list[str]:
    """Get list of cached test files."""
    return sorted(str(p) for p in TEST_DATA_DIR.glob("*.f1pcap"))


def send_ipc_shutdown(port: int) -> bool:
    """Send shutdown command to the child process via IPC."""
    try:
        rsp = IpcClientSync(port).shutdown_child("Integration test complete")
        return rsp.get("status") == "success"
    except Exception as e:
        logger.test_log(f"IPC shutdown failed: {e}")
        return False


# Windows reports a fatal exception as the raw NTSTATUS value, so an app that dies this way
# leaves nothing on stderr and nothing in its own log - the exit code is the only evidence
# there is. Worth decoding rather than printing a bare 10-digit number nobody recognises.
_WINDOWS_FATAL_STATUS = {
    0xC0000005: "STATUS_ACCESS_VIOLATION",
    0xC0000017: "STATUS_NO_MEMORY",
    0xC00000FD: "STATUS_STACK_OVERFLOW",
    0xC0000135: "STATUS_DLL_NOT_FOUND",
    0xC000013A: "STATUS_CONTROL_C_EXIT",
    0xC0000142: "STATUS_DLL_INIT_FAILED",
    0xC0000409: "STATUS_STACK_BUFFER_OVERRUN",
}


def describe_exit_code(code: Optional[int]) -> str:
    """Render a process exit code alongside what it most likely means.

    Args:
        code: Popen.returncode, or None if the process is still running.

    Returns:
        str: Human-readable description, e.g. "3221225477 (0xC0000005 STATUS_ACCESS_VIOLATION)".
    """
    if code is None:
        return "still running"
    if code == 0:
        return "0 (clean exit)"
    if code < 0:
        # POSIX: negative means terminated by signal.
        return f"{code} (killed by signal {-code})"
    if name := _WINDOWS_FATAL_STATUS.get(code):
        return f"{code} (0x{code:08X} {name})"
    return f"{code} (0x{code:08X})"


def _report_if_app_died() -> bool:
    """Log loudly, once, if the app process has exited underneath us.

    A dead app turns every subsequent check into a failure, which buries the one fact that
    matters - when it died and with what code - under hundreds of connection-refused lines.
    Reported at the first failed heartbeat, which is the earliest the runner can notice.

    Returns:
        bool: True if the app has exited.
    """
    global app_died_reported

    if app_process is None or app_process.poll() is None:
        return False

    if not app_died_reported:
        app_died_reported = True
        logger.test_log("=" * 80)
        logger.test_log(
            f"[FATAL] App process (PID={app_process.pid}) has exited. "
            f"Exit code: {describe_exit_code(app_process.returncode)}"
        )
        logger.test_log("[FATAL] Everything reported as failing from here is a cascade.")
        logger.test_log("=" * 80)
    return True


def kill_app(process: subprocess.Popen) -> None:
    """Force kill the application process."""
    if IS_WINDOWS:
        if process.poll() is None:
            try:
                subprocess.call(["taskkill", "/F", "/T", "/PID", str(process.pid)])
            except Exception as e:
                logger.test_log(f"[WARN] Could not terminate app: {e}")
        else:
            logger.test_log(
                f"App already exited (PID={process.pid}) exit code: "
                f"{describe_exit_code(process.returncode)}"
            )
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            process.poll()
            logger.test_log(
                f"[WARN] App already exited, exit code: {describe_exit_code(process.returncode)}"
            )


def cleanup_and_exit(signum=None, frame=None) -> None:
    """Handle cleanup on Ctrl+C or other termination signals."""
    global app_process, exit_event, ipc_port

    logger.test_log("\n[SIGNAL] Received interrupt signal, cleaning up...")

    if exit_event:
        exit_event.set()

    if app_process and app_process.poll() is None:
        if ipc_port:
            logger.test_log("[SIGNAL] Attempting graceful shutdown via IPC...")
            if not send_ipc_shutdown(ipc_port):
                logger.test_log("[SIGNAL] Graceful shutdown failed, forcing termination...")
                kill_app(app_process)
        else:
            logger.test_log("[SIGNAL] Forcing app termination...")
            kill_app(app_process)

    print_test_statistics()
    logger.test_log("[SIGNAL] Cleanup complete, exiting...")
    sys.exit(130)


def send_heartbeat(
        stop_event: threading.Event,
        port: int,
        num_missable_heartbeats: int = 3,
        interval: float = 5.0) -> None:
    """Send periodic heartbeat to the main app."""
    failed_heartbeat_count = 0

    while not stop_event.is_set():
        try:
            rsp = IpcClientSync(port).heartbeat()

            if rsp.get("status") == "success":
                failed_heartbeat_count = 0
            else:
                logger.test_log(f"Integration test: Heartbeat failed with response: {rsp}")
                _report_if_app_died()
                failed_heartbeat_count += 1

        except Exception as e:
            logger.test_log(f"Integration test: Error sending heartbeat: {e}")
            _report_if_app_died()
            failed_heartbeat_count += 1

        if failed_heartbeat_count > num_missable_heartbeats:
            logger.test_log(f"Integration test: Missed {failed_heartbeat_count} consecutive heartbeats. Stopping.")
            break

        time.sleep(interval)

    stop_event.clear()
    logger.test_log("Integration test: Heartbeat job stopped")


async def _check_endpoints_async(urls: list[str], capture_body: bool) -> list[Tuple[str, bool, Any]]:
    """Check if HTTP endpoints are responding, optionally capturing their JSON body.

    Args:
        urls (list[str]): Endpoints to check.
        capture_body (bool): If True, also parse and return each response's JSON body -
            used for --base diffing. Left False for a normal run since parsing bodies we
            never look at is wasted work.
    """
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    connector = TCPConnector(ssl=ssl_context)

    async def fetch(url: str) -> Tuple[str, bool, Any]:
        try:
            async with session.get(url, timeout=5) as response:
                success = response.status in {200, 404}
                status_str = "OK" if success else "FAIL"
                logger.test_log(f"  [{status_str}] Endpoint check: {url} ({response.status})")
                body = None
                if capture_body and success:
                    try:
                        body = await response.json(content_type=None)
                    except ValueError:
                        body = None
                return (url, success, body)
        except Exception as e:
            logger.test_log(f"  [FAIL] Endpoint check: {url} - {e}")
            return (url, False, None)

    async with ClientSession(connector=connector) as session:
        tasks = [fetch(url) for url in urls]
        return await asyncio.gather(*tasks)


def check_endpoints_blocking(urls: list[str], capture_body: bool = False) -> list[Tuple[str, bool, Any]]:
    """Blocking wrapper for endpoint checks."""
    return asyncio.run(_check_endpoints_async(urls, capture_body))


def fetch_test_files() -> list[str]:
    """Download or retrieve cached test files."""
    logger.test_log("Checking for cached test files...")

    if cached_files := get_cached_files():
        logger.test_log(f"Found {len(cached_files)} cached files - skipping download")
        return cached_files

    logger.test_log("No cached files found. Downloading from Google Drive...")
    try:
        files = gdown.download_folder(
            DRIVE_FOLDER_URL,
            output=str(TEST_DATA_DIR),
            quiet=False,
            remaining_ok=True
        )
        if not files:
            logger.test_log("No files were downloaded from Google Drive!")
            sys.exit(1)
        logger.test_log(f"Downloaded {len(files)} test files")
        return files

    except Exception as e:
        logger.test_log(f"Error downloading from Google Drive: {e}")
        if files := get_cached_files():
            logger.test_log(f"Using {len(files)} cached files")
            return files
        logger.test_log("No test files available to run.")
        sys.exit(1)


def start_app(config_file: str, port: int, coverage_enabled: bool, cwd: Optional[Path] = None) -> subprocess.Popen:
    """Start the application process.

    Args:
        config_file (str): Path to the config file. Pass an absolute path when cwd is set to
            something other than the repo root, since the launcher resolves it relative to cwd.
        port (int): IPC port for the launcher to listen on.
        coverage_enabled (bool): Whether to wrap the launch in coverage.py.
        cwd (Optional[Path]): Working directory to launch from - a git worktree checkout of a
            base commit, when driving a --base diff capture, or the repo root otherwise.
    """
    # The app writes nothing to stdout by default. Opt in here, so the launcher forwards its
    # children's output and the save tokens get emitted - both of which this runner parses.
    # Inherited by the launcher and everything it spawns.
    enable_integration_test_mode()

    app_cmd_base = [
        "-m", "apps.launcher",
        "--ipc-port", str(port),
        "--debug",
        "--replay-server",
        "--config-file", config_file
    ]
    if coverage_enabled:
        app_cmd = [
            sys.executable, "-m", "coverage", "run",
            "--parallel-mode", "--rcfile", "scripts/.coveragerc_integration", *app_cmd_base, "--coverage"
        ]
        os.environ["COVERAGE_PROCESS_START"] = str(Path("scripts/.coveragerc_integration").resolve())
    else:
        app_cmd = [sys.executable, *app_cmd_base]

    logger.test_log(f"Starting app with command: {' '.join(app_cmd)}" + (f" (cwd={cwd})" if cwd else ""))

    if IS_WINDOWS:
        return subprocess.Popen(
            app_cmd,
            cwd=cwd,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
    else:
        return subprocess.Popen(
            app_cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            preexec_fn=os.setsid
        )

def pump_app_output(process: subprocess.Popen, saved_paths: queue.Queue) -> None:
    """Drain the launcher's stdout, logging it and picking out the save tokens.

    The launcher forwards everything its subsystems print, and keeps writing its own log
    file as before. We drop all of it except the save tokens.

    Draining is required regardless: the pipe is created with subprocess.PIPE, and an
    unread pipe fills its OS buffer and then blocks the child mid-write. base_mgr makes
    the same point about its own children.

    Args:
        process (subprocess.Popen): The launcher process
        saved_paths (queue.Queue): Receives the path of each session save as it is written
    """

    if not process.stdout:
        return

    for raw_line in process.stdout:
        line = raw_line.rstrip()
        if not line:
            continue

        if saved_path := extract_saved_path_from_line(line):
            saved_paths.put(saved_path)
            logger.test_log(f"  [SAVE] Session written to {saved_path}")
        elif skip_reason := extract_save_skipped_from_line(line):
            test_stats["saves_skipped"] += 1
            logger.test_log(f"  [SKIP] Session not saved: {skip_reason}")
        elif fail_reason := extract_integration_fail_from_line(line):
            # The launcher's dying breath. It hard-exits straight after emitting this, so its
            # own log file never receives it - this is the only place the reason survives.
            logger.test_log(f"  [APP FAIL] {fail_reason}")
        # Anything else is discarded. The launcher already writes the consolidated
        # subsystem log to its own file; duplicating it here would just double it up.


def check_save_invariants(save_path: Path) -> Optional[int]:
    """Run the state-layer invariants over a written save file.

    Args:
        save_path (Path): The save file to check

    Returns:
        Optional[int]: Number of violations, or None if the file could not be read
    """

    try:
        with open(save_path, "r", encoding="utf-8") as f:
            save = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        logger.test_log(f"  [FAIL] Could not read save file {save_path}: {e}")
        return None

    report = checkSaveFile(save)
    status = "OK" if report.ok else "FAIL"
    logger.test_log(f"  [{status}] Invariants {save_path.name}: {report.summary()}")
    for violation in report.violations:
        logger.test_log(f"           {violation}")
    return len(report.violations)


def drain_saved_queue(saved_paths: queue.Queue) -> None:
    """Check every session save announced since the last drain.

    The app tells us what it wrote via a stdout token, so each save is picked up as it
    happens rather than inferred from a directory diff.

    Args:
        saved_paths (queue.Queue): Paths announced by the output pump
    """

    while True:
        try:
            save_path = Path(saved_paths.get_nowait())
        except queue.Empty:
            return

        violations = check_save_invariants(save_path)
        if violations is None:
            test_stats["saves_unreadable"] += 1
            continue
        test_stats["saves_checked"] += 1
        test_stats["invariant_violations"] += violations


def process_test_file(file: str, telemetry_port: int, http_port: int, proto: str,
                       capture_bodies: bool = False) -> dict:
    """Process a single test file and check endpoints.

    Args:
        file (str): Path to the .f1pcap recording to replay.
        telemetry_port (int): UDP port the app is listening for telemetry on.
        http_port (int): Port the app's web server is listening on.
        proto (str): "http" or "https".
        capture_bodies (bool): If True, also collect each endpoint's normalized JSON body
            under results["endpoint_bodies"], for --base diffing.
    """
    http_endpoints = [
        f"{proto}://localhost:{http_port}/telemetry-info",
        f"{proto}://localhost:{http_port}/race-info",
        f"{proto}://localhost:{http_port}/stream-overlay-info",
        *[f"{proto}://localhost:{http_port}/driver-info?index={i}" for i in range(MAX_DRIVERS)]
    ]

    results = {
        "telemetry_success": False,
        "endpoints_passed": 0,
        "endpoints_failed": 0,
    }

    # Send telemetry data
    try:
        send_telemetry_data(
            file,
            ip_addr="127.0.0.1",
            port=telemetry_port,
            printer=logger.test_log,
            show_progress=False
        )
        results["telemetry_success"] = True
        logger.test_log(f"  [OK] Telemetry data sent successfully")
    except Exception as e:
        logger.test_log(f"  [FAIL] Error sending telemetry data: {e}")

    # send_telemetry_data returns once the bytes are on the wire, not once the backend has
    # finished processing them - give it a moment to settle before checking endpoints, or the
    # last packet or two (e.g. FINAL_CLASSIFICATION) can still be mid-flight.
    time.sleep(5)

    # Check endpoints
    endpoint_results = check_endpoints_blocking(http_endpoints, capture_body=capture_bodies)
    endpoint_bodies: Dict[str, Any] = {}
    for url, success, body in endpoint_results:
        if success:
            results["endpoints_passed"] += 1
        else:
            results["endpoints_failed"] += 1
        if capture_bodies:
            endpoint_bodies[url] = normalize_for_diff(body)

    if capture_bodies:
        results["endpoint_bodies"] = endpoint_bodies

    return results


def print_test_statistics() -> None:
    """Print summary statistics of test execution."""
    logger.test_log("\n" + "=" * 80)
    logger.test_log("TEST STATISTICS")
    logger.test_log("=" * 80)
    logger.test_log(f"Files processed:        {test_stats['files_processed']}")
    logger.test_log(f"Telemetry sent:         {test_stats['telemetry_sent']}")
    logger.test_log(f"Telemetry failed:       {test_stats['telemetry_failed']}")
    logger.test_log(f"Endpoint checks passed: {test_stats['endpoints_passed']}")
    logger.test_log(f"Endpoint checks failed: {test_stats['endpoints_failed']}")
    logger.test_log(f"Saves checked:          {test_stats['saves_checked']}")
    logger.test_log(f"Saves skipped by app:   {test_stats['saves_skipped']}")
    logger.test_log(f"Saves unreadable:       {test_stats['saves_unreadable']}")
    logger.test_log(f"Invariant violations:   {test_stats['invariant_violations']}")
    if test_stats["diff_violations"]:
        logger.test_log(f"Diff violations:        {test_stats['diff_violations']}")

    total_telemetry = test_stats['telemetry_sent'] + test_stats['telemetry_failed']
    total_endpoints = test_stats['endpoints_passed'] + test_stats['endpoints_failed']

    if total_telemetry > 0:
        telemetry_success_rate = (test_stats['telemetry_sent'] / total_telemetry) * 100
        logger.test_log(f"Telemetry success rate: {telemetry_success_rate:.1f}%")

    if total_endpoints > 0:
        endpoint_success_rate = (test_stats['endpoints_passed'] / total_endpoints) * 100
        logger.test_log(f"Endpoint success rate:  {endpoint_success_rate:.1f}%")

    # Called after shutdown, so the app has normally exited by now. A non-zero code here means
    # the run's failures are wreckage from the app dying rather than genuine check failures -
    # the distinction is invisible in the rates above, which just count everything sent at a
    # dead port.
    if app_process is not None:
        app_process.poll()
        code = app_process.returncode
        logger.test_log(f"App exit code:          {describe_exit_code(code)}")
        if code not in (0, None):
            logger.test_log(
                "  ^ app did not exit cleanly - failures above may be a cascade, not real"
            )

    logger.test_log("=" * 80)


def reset_stats() -> None:
    """Zero out the module-level stats dict.

    main() is called more than once in the same process in --base mode (once to drive the
    base-commit app for the capture, once for the real working-tree run) - without this the
    two runs' numbers would accumulate into one another.
    """
    global app_died_reported

    for key in test_stats:
        test_stats[key] = 0

    # Each run gets its own app process, so a death in the second must still be announced.
    app_died_reported = False


def main(config_file: str, telemetry_port: int, http_port: int, proto: str, coverage_enabled: bool,
          capture_bodies: bool = False, open_browser: bool = True,
          app_cwd: Optional[Path] = None) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """Main test execution function.

    Args:
        config_file (str): Path to the config file to launch the app with.
        telemetry_port (int): UDP port the app is listening for telemetry on.
        http_port (int): Port the app's web server is listening on.
        proto (str): "http" or "https".
        coverage_enabled (bool): Whether to wrap the launch in coverage.py.
        capture_bodies (bool): If True, collect normalized endpoint bodies for --base diffing.
        open_browser (bool): If False, skip opening the browser views - used for the
            invisible base-commit capture run, which nothing looks at. The user-facing run
            (base diff's "current" side, and the plain no-diff mode) always opens them; see
            state-mgmt-simplification.md's ground rule against a general --no-browser flag.
        app_cwd (Optional[Path]): Working directory to launch the app from - a worktree
            checkout of a base commit, or None for the repo root.

    Returns:
        Tuple[bool, Optional[Dict[str, Any]]]: (True only if every file replayed and every
            endpoint check passed, {file_stem: {url: normalized_body}} if capture_bodies else None)
    """
    global app_process, exit_event, ipc_port

    reset_stats()
    endpoint_capture: Dict[str, Any] = {}

    files = fetch_test_files()
    logger.test_log(f"Number of Test files: {len(files)}")

    exit_event = threading.Event()

    # Start the app
    ipc_port = get_free_tcp_port()
    app_process = start_app(config_file, ipc_port, coverage_enabled, cwd=app_cwd)
    logger.test_log(f"Started app with IPC port: {ipc_port}")

    # Drain the launcher's stdout. Required regardless of the tokens: an unread pipe fills
    # and blocks the child mid-write.
    saved_paths: queue.Queue = queue.Queue()
    output_thread = threading.Thread(
        target=pump_app_output,
        args=(app_process, saved_paths),
        daemon=True
    )
    output_thread.start()
    logger.test_log(f"Output pump thread started (TID: {output_thread.ident})")

    # Start heartbeat thread
    heartbeat_thread = threading.Thread(
        target=send_heartbeat,
        args=(exit_event, ipc_port),
        daemon=True
    )
    heartbeat_thread.start()
    logger.test_log(f"Heartbeat thread started (TID: {heartbeat_thread.ident})")

    time.sleep(5)

    if open_browser:
        # Launch browser views. These are not decoration - they put the web server routes,
        # Socket.IO and the frontend JS through the run as well.
        logger.test_log("Launching driver view, engineer view and overlay clients")
        webbrowser.open(f'{proto}://localhost:{http_port}/live', new=2)
        webbrowser.open(f'{proto}://localhost:{http_port}/eng-view', new=2)
        webbrowser.open(f'{proto}://localhost:{http_port}/player-stream-overlay', new=2)

    try:
        # Process each test file
        for index, file in enumerate(files):
            logger.test_log("=" * 80)
            logger.test_log(f">>> Test {index + 1}/{len(files)}: {Path(file).name} <<<")
            logger.test_log("=" * 80)

            results = process_test_file(file, telemetry_port, http_port, proto, capture_bodies=capture_bodies)

            # Update statistics
            test_stats["files_processed"] += 1
            if results["telemetry_success"]:
                test_stats["telemetry_sent"] += 1
            else:
                test_stats["telemetry_failed"] += 1
            test_stats["endpoints_passed"] += results["endpoints_passed"]
            test_stats["endpoints_failed"] += results["endpoints_failed"]
            if capture_bodies:
                endpoint_capture[Path(file).stem] = results["endpoint_bodies"]

            # Print file statistics
            logger.test_log(f"\nFile Results:")
            logger.test_log(f"  Telemetry: {'Sent' if results['telemetry_success'] else 'Failed'}")
            logger.test_log(f"  Endpoints: {results['endpoints_passed']} passed, {results['endpoints_failed']} failed")

            time.sleep(2)
            drain_saved_queue(saved_paths)

        time.sleep(5)

    except KeyboardInterrupt:
        raise
    finally:
        # Normal cleanup
        logger.test_log("\nShutting down...")
        exit_event.set()

        if not send_ipc_shutdown(ipc_port):
            kill_app(app_process)

        # The last session's save is written during shutdown, so give the pump a moment to
        # see it before draining a final time.
        output_thread.join(timeout=10)
        drain_saved_queue(saved_paths)

        # Print final statistics
        print_test_statistics()

    # Report honestly. Previously this returned True unconditionally, so the process always
    # exited 0 and the runner could never gate anything.
    success = (
        test_stats["files_processed"] == len(files) and
        test_stats["telemetry_failed"] == 0 and
        test_stats["endpoints_failed"] == 0 and
        test_stats["saves_checked"] > 0 and
        test_stats["saves_unreadable"] == 0 and
        test_stats["invariant_violations"] == 0
    )
    return success, (endpoint_capture if capture_bodies else None)


def base_cache_path(base_sha: str) -> Path:
    """Cache file for a given base commit's capture.

    Args:
        base_sha (str): Full commit sha the capture was taken against.
    """
    return DIFF_CACHE_DIR / f"{base_sha}.json"


def diff_report_path(base_sha: str) -> Path:
    """Standalone, commit-tagged report file for a --base run - see run_diff for why this
    exists separately from integration_test.log.

    Args:
        base_sha (str): Full commit sha the diff was run against.
    """
    return DIFF_CACHE_DIR / f"{base_sha}.report.txt"


def run_base_capture(base_sha: str, config_file: str, telemetry_port: int, http_port: int, proto: str,
                      coverage_enabled: bool) -> Dict[str, Any]:
    """Get the base commit's endpoint capture, from cache or by replaying it in a worktree.

    Args:
        base_sha (str): Full commit sha to capture against.
        config_file (str): Absolute path to the config file to launch the app with - must be
            absolute since it is resolved relative to the worktree's cwd, not the repo root.
        telemetry_port (int): UDP port the app is listening for telemetry on.
        http_port (int): Port the app's web server is listening on.
        proto (str): "http" or "https".
        coverage_enabled (bool): Whether to wrap the launch in coverage.py.

    Returns:
        Dict[str, Any]: {file_stem: {url: normalized_body}}
    """
    cache_path = base_cache_path(base_sha)
    if cache_path.exists():
        logger.test_log(f"Using cached base capture: {cache_path}")
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)

    logger.test_log(f"No cached base capture for {base_sha[:12]} - replaying against a worktree checkout")
    worktree = create_worktree(base_sha, PROJECT_ROOT)
    try:
        success, capture = main(
            config_file=config_file,
            telemetry_port=telemetry_port,
            http_port=http_port,
            proto=proto,
            coverage_enabled=coverage_enabled,
            capture_bodies=True,
            open_browser=False,
            app_cwd=worktree,
        )
        if not success:
            logger.test_log("[WARN] Base commit run did not pass its own checks - "
                             "the capture is still used for diffing, but treat any diff with suspicion.")
    finally:
        remove_worktree(worktree, PROJECT_ROOT)

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(capture, f)
    logger.test_log(f"Cached base capture: {cache_path}")
    return capture


def run_diff(base_ref: str, config_file: str, telemetry_port: int, http_port: int, proto: str,
             coverage_enabled: bool) -> bool:
    """Run the --base A/B differential: capture the base commit, replay the working tree, diff.

    Args:
        base_ref (str): Anything git accepts as a commit-ish (sha, branch, tag).
        config_file (str): Absolute path to the config file to launch the app with.
        telemetry_port (int): UDP port the app is listening for telemetry on.
        http_port (int): Port the app's web server is listening on.
        proto (str): "http" or "https".
        coverage_enabled (bool): Whether to wrap the launch in coverage.py.

    Returns:
        bool: True only if the working tree's own checks pass AND nothing diffed.
    """
    base_sha = resolve_commit(base_ref, PROJECT_ROOT)
    logger.test_log(f"Diffing against base commit {base_sha} (resolved from '{base_ref}')")

    base_capture = run_base_capture(base_sha, config_file, telemetry_port, http_port, proto, coverage_enabled)

    success, current_capture = main(
        config_file=config_file,
        telemetry_port=telemetry_port,
        http_port=http_port,
        proto=proto,
        coverage_enabled=coverage_enabled,
        capture_bodies=True,
        open_browser=True,
    )

    logger.test_log("Diffing captures...")

    def _log_diff_progress(file_index: int, total_files: int, file_stem: str) -> None:
        logger.test_log(f"  [{file_index}/{total_files}] Diffing {file_stem}")

    violations, report = diff_captures(base_capture, current_capture, progress_cb=_log_diff_progress)
    test_stats["diff_violations"] = violations
    if report:
        logger.test_log("\n" + "=" * 80)
        logger.test_log(f"DIFF AGAINST {base_sha[:12]}")
        logger.test_log("=" * 80)
        for line in report:
            logger.test_log(line)
    else:
        logger.test_log(f"No differences from base commit {base_sha[:12]}")

    # integration_test.log is a fixed-name rotating file - the next run of any kind overwrites
    # it. Write a standalone report keyed by base_sha so a diff result survives long enough to
    # be looked at later, and doesn't get clobbered by the next --base run against a different
    # commit.
    report_path = diff_report_path(base_sha)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"base_commit: {base_sha}\n")
        f.write(f"generated_at: {datetime.now().isoformat(timespec='seconds')}\n")
        f.write(f"working_tree_checks_passed: {success}\n")
        f.write(f"diff_violations: {violations}\n")
        f.write("\n")
        f.write("\n".join(report) if report else "No differences.")
        f.write("\n")
    logger.test_log(f"Diff report written to {report_path}")

    return success and violations == 0


def capture_base_only(base_ref: str, config_file: str, telemetry_port: int, http_port: int, proto: str,
                       coverage_enabled: bool) -> bool:
    """Capture and cache the base commit's replay, then stop - see --base-only.

    Args:
        base_ref (str): Anything git accepts as a commit-ish (sha, branch, tag).
        config_file (str): Absolute path to the config file to launch the app with.
        telemetry_port (int): UDP port the app is listening for telemetry on.
        http_port (int): Port the app's web server is listening on.
        proto (str): "http" or "https".
        coverage_enabled (bool): Whether to wrap the launch in coverage.py.

    Returns:
        bool: True if the capture was written (or already cached).
    """
    base_sha = resolve_commit(base_ref, PROJECT_ROOT)
    run_base_capture(base_sha, config_file, telemetry_port, http_port, proto, coverage_enabled)
    logger.test_log(f"\nBase capture for {base_sha[:12]} is cached. "
                     f"Run with --base {base_sha} (no --base-only) later to diff the working tree against it.")
    return True


def parse_cli_args() -> argparse.Namespace:
    """Parse command-line arguments for the integration runner."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coverage", action="store_true", help="Run the app under coverage.py")
    parser.add_argument(
        "--base", default=None, metavar="COMMIT",
        help="Replay the same recordings against this commit (in a throwaway git worktree) "
             "and diff its endpoint responses against the working tree's. See "
             "state-mgmt-simplification.md's 'Regression harness' section for the rationale.")
    parser.add_argument(
        "--base-only", action="store_true",
        help="With --base: only capture and cache the base commit's replay, then exit - skip "
             "the working-tree run and diff. Lets the two ~30min runs be split across two "
             "sessions; a later plain --base <same commit> run picks up the cache and only "
             "pays for the working-tree side.")
    return parser.parse_args()


if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, cleanup_and_exit)
    if not IS_WINDOWS:
        signal.signal(signal.SIGTERM, cleanup_and_exit)

    args = parse_cli_args()
    if args.base_only and not args.base:
        print("--base-only requires --base <commit>", file=sys.stderr)
        sys.exit(2)

    cli_config_file = str((PROJECT_ROOT / "integration_test_cfg.json").resolve())
    settings = load_config_from_json(cli_config_file)

    start_time = time.perf_counter()

    try:
        if args.base_only:
            run_success = capture_base_only(
                base_ref=args.base,
                config_file=cli_config_file,
                telemetry_port=settings.Network.telemetry_port,
                http_port=settings.Network.server_port,
                proto=settings.HTTPS.proto,
                coverage_enabled=args.coverage,
            )
        elif args.base:
            run_success = run_diff(
                base_ref=args.base,
                config_file=cli_config_file,
                telemetry_port=settings.Network.telemetry_port,
                http_port=settings.Network.server_port,
                proto=settings.HTTPS.proto,
                coverage_enabled=args.coverage,
            )
        else:
            run_success, _ = main(
                config_file=cli_config_file,
                telemetry_port=settings.Network.telemetry_port,
                http_port=settings.Network.server_port,
                proto=settings.HTTPS.proto,
                coverage_enabled=args.coverage,
            )
    except KeyboardInterrupt:
        logger.test_log("\n[MAIN] KeyboardInterrupt caught")
        cleanup_and_exit()

    end_time = time.perf_counter()
    elapsed = end_time - start_time
    mm, ss = divmod(int(elapsed), 60)
    ms = int((elapsed - int(elapsed)) * 1000)
    logger.test_log(f"\nTotal execution time: {mm:02d}:{ss:02d}.{ms:03d}")

    sys.exit(0 if run_success else 1)
