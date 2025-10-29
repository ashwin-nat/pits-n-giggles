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
import time
import webbrowser
from pathlib import Path

import gdown
from aiohttp import ClientSession, TCPConnector

# Add the parent directory to the Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from lib.config import load_config_from_ini
from lib.ipc import IpcParent, get_free_tcp_port
from tests.integration_test.log import create_logger, TestLogger

# Google Drive folder URL
DRIVE_FOLDER_URL = "https://drive.google.com/drive/folders/13tIadKMvi3kuItkovT6GUTTHOL3YM6n_?usp=drive_link"
CACHE_DIR = Path("test_data")
logger = create_logger()

def get_cached_files() -> list[str]:
    return sorted(str(p) for p in CACHE_DIR.glob("*.f1pcap"))

def check_endpoints_blocking(urls):
    return asyncio.run(_check_endpoints_async(urls))

def send_ipc_shutdown(ipc_port) -> bool:
    """Sends a shutdown command to the child process.

    Returns:
        True if the shutdown was successful, False otherwise.
    """
    try:
        rsp = IpcParent(ipc_port).shutdown_child("Integration test complete")
        return rsp.get("status") == "success"
    except Exception as e: # pylint: disable=broad-exception-caught
        logger.test_log(f"IPC shutdown failed: {e}")
        return False

def kill_app(is_windows: bool, app_process: subprocess.Popen):

    if is_windows:
        if app_process.poll() is None:
            try:
                subprocess.call(["taskkill", "/F", "/T", "/PID", str(app_process.pid)])
            except Exception as e:
                logger.test_log(f"[WARN] Could not terminate app: {e}")
        else:
            logger.test_log(f"App already exited (PID={app_process.pid})")
    else:
        try:
            os.killpg(app_process.pid, signal.SIGKILL)
        except ProcessLookupError:
            logger.test_log("[WARN] App already exited")

def send_heartbeat(
        stop_event: threading.Event,
        ipc_port: int,
        num_missable_heartbeats: int = 3,
        interval: float = 5.0) -> None:
    failed_heartbeat_count = 0

    while not stop_event.is_set():
        try:
            rsp = IpcParent(ipc_port).heartbeat()

            if rsp.get("status") == "success":
                failed_heartbeat_count = 0
                logger.test_log(f"Backend process: Heartbeat response: {rsp}")
            else:
                logger.test_log(f"Backend process: Heartbeat failed with response: {rsp}")
                failed_heartbeat_count += 1

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.test_log(f"Backend process: Error sending heartbeat: {e}")
            failed_heartbeat_count += 1

        # Check if we've exceeded the maximum allowed missed heartbeats
        if failed_heartbeat_count > num_missable_heartbeats:
            logger.test_log(f"Backend process: Missed {failed_heartbeat_count} consecutive heartbeats. Stopping.")
            break

        time.sleep(interval)

    stop_event.clear()
    logger.test_log(f"Backend process: Heartbeat job stopped")

async def _check_endpoints_async(urls):
    results = []

    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    connector = TCPConnector(ssl=ssl_context)

    async with ClientSession(connector=connector) as session:
        async def fetch(url):
            try:
                async with session.get(url, timeout=5) as response:
                    if response.status in {200, 404}:
                        logger.test_log(f"  [OK] Endpoint check PASSED: {url}")
                        return (url, True)
                    else:
                        logger.test_log(f"  [FAIL] Endpoint check FAILED ({response.status}): {url}")
                        return (url, False)
            except Exception as e:
                logger.test_log(f"  [FAIL] Endpoint check FAILED (exception): {url} - {e}")
                return (url, False)

        tasks = [fetch(url) for url in urls]
        results = await asyncio.gather(*tasks)

    return results

def main(telemetry_port, http_port, proto, coverage_enabled):
    CACHE_DIR.mkdir(exist_ok=True)
    is_windows = platform.system() == "Windows"

    logger.test_log("Checking for cached test files...")
    if cached_files := get_cached_files():
        logger.test_log(f"Found {len(cached_files)} cached files - skipping download")
        files = cached_files
    else:
        logger.test_log("No cached files found. Downloading test files from Google Drive...")
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
        except Exception as e:
            logger.test_log(f"Error occurred while downloading test files from Google Drive: {e}")
            files = get_cached_files()
            if files:
                logger.test_log(f"Using {len(files)} cached files")
            else:
                logger.test_log("No test files available to run.")
                sys.exit(1)

    http_endpoints = [
        f"{proto}://localhost:{http_port}/telemetry-info",
        f"{proto}://localhost:{http_port}/race-info",
        f"{proto}://localhost:{http_port}/stream-overlay-info",
        *[
            f"{proto}://localhost:{http_port}/driver-info?index={i}"
            for i in range(23)
        ]
    ]

    ipc_port = get_free_tcp_port()

    logger.test_log("\nStarting app in replay server mode...")
    app_cmd_base = ["-m", "apps.backend",
                "--replay-server", "--debug", "--ipc-port", str(ipc_port)
    ]

    if coverage_enabled:
        app_cmd = [
            sys.executable, "-m", "coverage", "run",
            "--parallel-mode", "--rcfile", "scripts/.coveragerc_integration", *app_cmd_base
        ]
        os.environ["COVERAGE_PROCESS_START"] = str(Path("scripts/.coveragerc_integration").resolve())
    else:
        app_cmd = [sys.executable, *app_cmd_base]

    if is_windows:
        app_process = subprocess.Popen(
            app_cmd,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True)
    else:
        app_process = subprocess.Popen(
            app_cmd,
            start_new_session=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True)

    logger.test_log(f"App process started with PID: {app_process.pid}. Command line: {' '.join(app_cmd)}")

    # --- Threaded background jobs ---
    def log_app_output(process, log_func, stop_event):
        for line in iter(process.stdout.readline, ''):
            if stop_event.is_set():
                break
            log_func(line.strip())
        process.stdout.close()

    exit_event = threading.Event()
    app_output_stop_event = threading.Event()

    threads = []

    heartbeat_thread = threading.Thread(target=send_heartbeat, args=(exit_event, ipc_port))
    threads.append(heartbeat_thread)
    heartbeat_thread.start()
    logger.test_log(f"Heartbeat thread started. PID: {heartbeat_thread.ident}")

    app_output_thread = threading.Thread(
        target=log_app_output, args=(app_process, logger.proc_log, app_output_stop_event))
    threads.append(app_output_thread)
    app_output_thread.start()
    logger.test_log(f"App output thread started. PID: {app_output_thread.ident}")

    logger.test_log("Waiting for app to start...")
    time.sleep(5)

    logger.test_log("Launching driver view, engineer view and overlay clients")
    webbrowser.open(f'{proto}://localhost:{http_port}/', new=2)
    webbrowser.open(f'{proto}://localhost:{http_port}/eng-view', new=2)
    webbrowser.open(f'{proto}://localhost:{http_port}/player-stream-overlay', new=2)

    results = []
    try:
        for index, file_path in enumerate(files):
            file_name = os.path.basename(file_path)
            logger.test_log("=" * 40)
            logger.test_log(f"\n{'='*80}\n>>> Running test {index + 1} of {len(files)}: {file_name} <<<\n{'='*80}")

            replayer_cmd = [
                "poetry", "run", "python", "-m", "apps.dev_tools.telemetry_replayer",
                "--file-name", str(file_path),
                "--port", str(telemetry_port)
            ]

            replay_success = False
            endpoint_status = []
            replayer_process = None

            try:
                replayer_process = subprocess.Popen(
                    replayer_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                replayer_output_stop_event = threading.Event()

                logger.test_log(f"Replayer process started with PID: {replayer_process.pid}. Command line: {' '.join(replayer_cmd)}")
                start_time = time.perf_counter()

                replayer_thread = threading.Thread(
                    target=log_app_output, args=(replayer_process, logger.replayer_log, replayer_output_stop_event))
                replayer_thread.start()
                logger.test_log(f"Replayer output thread started. PID: {replayer_thread.ident}")

                replayer_process.wait(timeout=6000)
                replay_success = (replayer_process.returncode == 0)
            except subprocess.TimeoutExpired:
                logger.test_log(f"[FAIL] Test FAILED: {file_name} timed out after 120 seconds")
                if replayer_process:
                    kill_app(is_windows, replayer_process)
            finally:
                if replayer_process:
                    replayer_output_stop_event.set()

            # Endpoint checks only if replay succeeded
            if replay_success:
                endpoint_status = check_endpoints_blocking(http_endpoints)
            else:
                logger.test_log(f"[FAIL] Replay failed for {file_name}")

            overall_success = replay_success and all(ok for _, ok in endpoint_status)
            results.append((file_name, overall_success, replay_success, endpoint_status))

            end_time = time.perf_counter()
            time_elapsed = end_time - start_time
            status = "PASSED" if overall_success else "FAILED"
            logger.test_log(f"Test {index + 1} of {len(files)} {status}: {file_name} | Elapsed: {time_elapsed:.2f} s")

    finally:
        logger.test_log(f"\nStopping app... PID={app_process.pid}")
        exit_event.set()
        app_output_stop_event.set()

        # Give heartbeat a chance to exit gracefully
        time.sleep(1)

        # Give time for watchdog to expire
        time.sleep(3)

        # Try clean IPC shutdown
        if not send_ipc_shutdown(ipc_port):
            logger.test_log("[WARN] IPC shutdown failed, forcing termination")
            kill_app(is_windows, app_process)

        try:
            app_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            logger.test_log("[WARN] App did not terminate in time")

        # Join all threads
        for t in threads:
            t.join(timeout=2)

    logger.test_log("\n===== TEST RESULTS =====")
    success_count = sum(overall for _, overall, _, _ in results)
    logger.test_log(f"Passed: {success_count}/{len(results)}\n")

    for file_name, overall, replay_success, endpoint_status in results:
        status = "PASS" if overall else "FAIL"
        logger.test_log(f"{status}: {file_name}")

        if not replay_success:
            logger.test_log("  [FAIL] Replayer failed")
        for url, ok in endpoint_status:
            if not ok:
                logger.test_log(f"  [FAIL] Endpoint failed: {url}")

    return success_count == len(results)

if __name__ == "__main__":

    settings = load_config_from_ini("integration_test_cfg.ini")

    coverage_enabled = "--coverage" in sys.argv

    start_time = time.perf_counter()
    success = main(
        telemetry_port=settings.Network.telemetry_port,
        http_port=settings.Network.server_port,
        proto=settings.HTTPS.proto,
        coverage_enabled=coverage_enabled
    )
    end_time = time.perf_counter()
    mm, ss = divmod(int(end_time - start_time), 60)
    ms = int((end_time - start_time - mm * 60 - ss) * 1000)
    logger.test_log(f"Total time: {mm:02d}:{ss:02d}.{ms:03d}")

    sys.exit(0 if success else 1)
