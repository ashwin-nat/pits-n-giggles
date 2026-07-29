#!/usr/bin/env python3
"""
Simple integration test for Pits n Giggles App
"""

import asyncio
import os
import platform
import signal
import ssl
import subprocess
import sys
import threading
import json
import time
import webbrowser
from pathlib import Path
from typing import Optional

import gdown
from aiohttp import ClientSession, TCPConnector

# Add the parent directory to the Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from lib.config import load_config_from_json
from lib.f1_types import MAX_DRIVERS
from lib.ipc import IpcClientSync, get_free_tcp_port
from lib.save_invariants import checkSaveFile
from tests.integration_test.log import create_logger, TestLogger
from apps.dev_tools.telemetry_replayer import send_telemetry_data

# Constants
DRIVE_FOLDER_URL = "https://drive.google.com/drive/folders/13tIadKMvi3kuItkovT6GUTTHOL3YM6n_?usp=drive_link"
CACHE_DIR = Path("test_data")
IS_WINDOWS = platform.system() == "Windows"

# Global state for signal handling
app_process: Optional[subprocess.Popen] = None
exit_event: Optional[threading.Event] = None
ipc_port: Optional[int] = None

# Test statistics
test_stats = {
    "files_processed": 0,
    "telemetry_sent": 0,
    "telemetry_failed": 0,
    "endpoints_passed": 0,
    "endpoints_failed": 0,
    "saves_checked": 0,
    "saves_unreadable": 0,
    "invariant_violations": 0,
}

logger = create_logger()


def get_cached_files() -> list[str]:
    """Get list of cached test files."""
    return sorted(str(p) for p in CACHE_DIR.glob("*.f1pcap"))


def send_ipc_shutdown(port: int) -> bool:
    """Send shutdown command to the child process via IPC."""
    try:
        rsp = IpcClientSync(port).shutdown_child("Integration test complete")
        return rsp.get("status") == "success"
    except Exception as e:
        logger.test_log(f"IPC shutdown failed: {e}")
        return False


def kill_app(process: subprocess.Popen) -> None:
    """Force kill the application process."""
    if IS_WINDOWS:
        if process.poll() is None:
            try:
                subprocess.call(["taskkill", "/F", "/T", "/PID", str(process.pid)])
            except Exception as e:
                logger.test_log(f"[WARN] Could not terminate app: {e}")
        else:
            logger.test_log(f"App already exited (PID={process.pid})")
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            logger.test_log("[WARN] App already exited")


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
                logger.test_log(f"Integration test: Heartbeat response: {rsp}")
            else:
                logger.test_log(f"Integration test: Heartbeat failed with response: {rsp}")
                failed_heartbeat_count += 1

        except Exception as e:
            logger.test_log(f"Integration test: Error sending heartbeat: {e}")
            failed_heartbeat_count += 1

        if failed_heartbeat_count > num_missable_heartbeats:
            logger.test_log(f"Integration test: Missed {failed_heartbeat_count} consecutive heartbeats. Stopping.")
            break

        time.sleep(interval)

    stop_event.clear()
    logger.test_log("Integration test: Heartbeat job stopped")


async def _check_endpoints_async(urls: list[str]) -> list[tuple[str, bool]]:
    """Check if HTTP endpoints are responding."""
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    connector = TCPConnector(ssl=ssl_context)

    async def fetch(url: str) -> tuple[str, bool]:
        try:
            async with session.get(url, timeout=5) as response:
                success = response.status in {200, 404}
                status_str = "OK" if success else "FAIL"
                logger.test_log(f"  [{status_str}] Endpoint check: {url} ({response.status})")
                return (url, success)
        except Exception as e:
            logger.test_log(f"  [FAIL] Endpoint check: {url} - {e}")
            return (url, False)

    async with ClientSession(connector=connector) as session:
        tasks = [fetch(url) for url in urls]
        return await asyncio.gather(*tasks)


def check_endpoints_blocking(urls: list[str]) -> list[tuple[str, bool]]:
    """Blocking wrapper for endpoint checks."""
    return asyncio.run(_check_endpoints_async(urls))


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
            output=str(CACHE_DIR),
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


def start_app(config_file: str, port: int, coverage_enabled: bool) -> subprocess.Popen:
    """Start the application process."""
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

    logger.test_log(f"Starting app with command: {' '.join(app_cmd)}")

    if IS_WINDOWS:
        return subprocess.Popen(
            app_cmd,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
    else:
        return subprocess.Popen(
            app_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            preexec_fn=os.setsid
        )

def snapshot_saves(session_dir: Path) -> set:
    """List the save files currently on disk.

    Args:
        session_dir (Path): Directory the app writes sessions into

    Returns:
        set: Every save file found under it
    """

    return set(session_dir.rglob("*.json")) if session_dir.is_dir() else set()


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


def check_new_saves(session_dir: Path, seen: set) -> set:
    """Check any save files the app has written since the last sweep.

    The app writes these itself - post-session autosave, plus just-in-case autosave when a
    new session starts before the previous one finished, which is exactly what a
    back-to-back replay looks like. So there is nothing to trigger; we just pick up what
    appeared. Attribution to a specific recording is approximate for that reason, hence the
    file name in the log line.

    Args:
        session_dir (Path): Directory the app writes sessions into
        seen (set): Save files already accounted for

    Returns:
        set: The updated set of accounted-for files
    """

    current = snapshot_saves(session_dir)
    for save_path in sorted(current - seen):
        violations = check_save_invariants(save_path)
        if violations is None:
            test_stats["saves_unreadable"] += 1
            continue
        test_stats["saves_checked"] += 1
        test_stats["invariant_violations"] += violations
    return current


def process_test_file(file: str, telemetry_port: int, http_port: int, proto: str) -> dict:
    """Process a single test file and check endpoints."""
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

    # Check endpoints
    endpoint_results = check_endpoints_blocking(http_endpoints)
    for _, success in endpoint_results:
        if success:
            results["endpoints_passed"] += 1
        else:
            results["endpoints_failed"] += 1

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
    logger.test_log(f"Saves unreadable:       {test_stats['saves_unreadable']}")
    logger.test_log(f"Invariant violations:   {test_stats['invariant_violations']}")

    total_telemetry = test_stats['telemetry_sent'] + test_stats['telemetry_failed']
    total_endpoints = test_stats['endpoints_passed'] + test_stats['endpoints_failed']

    if total_telemetry > 0:
        telemetry_success_rate = (test_stats['telemetry_sent'] / total_telemetry) * 100
        logger.test_log(f"Telemetry success rate: {telemetry_success_rate:.1f}%")

    if total_endpoints > 0:
        endpoint_success_rate = (test_stats['endpoints_passed'] / total_endpoints) * 100
        logger.test_log(f"Endpoint success rate:  {endpoint_success_rate:.1f}%")

    logger.test_log("=" * 80)

def main(config_file: str, telemetry_port: int, http_port: int, proto: str, coverage_enabled: bool,
         session_dir: Path = Path("data")) -> bool:
    """Main test execution function.

    Returns:
        bool: True only if every file replayed and every endpoint check passed.
    """
    global app_process, exit_event, ipc_port

    files = fetch_test_files()
    logger.test_log(f"Number of Test files: {len(files)}")

    # Only saves written from here on belong to this run
    seen_saves = snapshot_saves(session_dir)
    logger.test_log(f"Existing saves in {session_dir}: {len(seen_saves)} (ignored)")

    exit_event = threading.Event()

    # Start the app
    ipc_port = get_free_tcp_port()
    app_process = start_app(config_file, ipc_port, coverage_enabled)
    logger.test_log(f"Started app with IPC port: {ipc_port}")

    # Start heartbeat thread
    heartbeat_thread = threading.Thread(
        target=send_heartbeat,
        args=(exit_event, ipc_port),
        daemon=True
    )
    heartbeat_thread.start()
    logger.test_log(f"Heartbeat thread started (TID: {heartbeat_thread.ident})")

    time.sleep(5)

    # Launch browser views. These are not decoration - they put the web server routes,
    # Socket.IO and the frontend JS through the run as well.
    logger.test_log("Launching driver view, engineer view and overlay clients")
    webbrowser.open(f'{proto}://localhost:{http_port}/', new=2)
    webbrowser.open(f'{proto}://localhost:{http_port}/eng-view', new=2)
    webbrowser.open(f'{proto}://localhost:{http_port}/player-stream-overlay', new=2)

    try:
        # Process each test file
        for index, file in enumerate(files):
            logger.test_log("=" * 80)
            logger.test_log(f">>> Test {index + 1}/{len(files)}: {Path(file).name} <<<")
            logger.test_log("=" * 80)

            results = process_test_file(file, telemetry_port, http_port, proto)

            # Update statistics
            test_stats["files_processed"] += 1
            if results["telemetry_success"]:
                test_stats["telemetry_sent"] += 1
            else:
                test_stats["telemetry_failed"] += 1
            test_stats["endpoints_passed"] += results["endpoints_passed"]
            test_stats["endpoints_failed"] += results["endpoints_failed"]

            # Print file statistics
            logger.test_log(f"\nFile Results:")
            logger.test_log(f"  Telemetry: {'Sent' if results['telemetry_success'] else 'Failed'}")
            logger.test_log(f"  Endpoints: {results['endpoints_passed']} passed, {results['endpoints_failed']} failed")

            time.sleep(2)
            seen_saves = check_new_saves(session_dir, seen_saves)

        time.sleep(5)

    except KeyboardInterrupt:
        raise
    finally:
        # Normal cleanup
        logger.test_log("\nShutting down...")
        exit_event.set()

        if not send_ipc_shutdown(ipc_port):
            kill_app(app_process)

        # The last session's save is only written on shutdown, and just-in-case autosave
        # lags a session behind, so sweep once more after the app has gone.
        time.sleep(2)
        check_new_saves(session_dir, seen_saves)

        # Print final statistics
        print_test_statistics()

    # Report honestly. Previously this returned True unconditionally, so the process always
    # exited 0 and the runner could never gate anything.
    return (
        test_stats["files_processed"] == len(files) and
        test_stats["telemetry_failed"] == 0 and
        test_stats["endpoints_failed"] == 0 and
        test_stats["saves_checked"] > 0 and
        test_stats["saves_unreadable"] == 0 and
        test_stats["invariant_violations"] == 0
    )


if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, cleanup_and_exit)
    if not IS_WINDOWS:
        signal.signal(signal.SIGTERM, cleanup_and_exit)

    config_file = "integration_test_cfg.json"
    settings = load_config_from_json(config_file)
    coverage_enabled = "--coverage" in sys.argv

    start_time = time.perf_counter()

    try:
        success = main(
            config_file=config_file,
            telemetry_port=settings.Network.telemetry_port,
            http_port=settings.Network.server_port,
            proto=settings.HTTPS.proto,
            coverage_enabled=coverage_enabled,
            session_dir=Path(settings.Capture.session_dir)
        )
    except KeyboardInterrupt:
        logger.test_log("\n[MAIN] KeyboardInterrupt caught")
        cleanup_and_exit()

    end_time = time.perf_counter()
    elapsed = end_time - start_time
    mm, ss = divmod(int(elapsed), 60)
    ms = int((elapsed - int(elapsed)) * 1000)
    logger.test_log(f"\nTotal execution time: {mm:02d}:{ss:02d}.{ms:03d}")

    sys.exit(0 if success else 1)
