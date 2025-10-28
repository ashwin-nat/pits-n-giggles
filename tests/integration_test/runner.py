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

# Google Drive folder URL
DRIVE_FOLDER_URL = "https://drive.google.com/drive/folders/13tIadKMvi3kuItkovT6GUTTHOL3YM6n_?usp=drive_link"
CACHE_DIR = Path("test_data")


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
        print(f"IPC shutdown failed: {e}")
        return False

def kill_app(is_windows: bool, app_process: subprocess.Popen):

    if is_windows:
        if app_process.poll() is None:
            try:
                subprocess.call(["taskkill", "/F", "/T", "/PID", str(app_process.pid)])
            except Exception as e:
                print(f"[WARN] Could not terminate app: {e}")
        else:
            print(f"App already exited (PID={app_process.pid})")
    else:
        try:
            os.killpg(app_process.pid, signal.SIGKILL)
        except ProcessLookupError:
            print("[WARN] App already exited")

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
                print(f"Backend process: Heartbeat response: {rsp}")
            else:
                print(f"Backend process: Heartbeat failed with response: {rsp}")
                failed_heartbeat_count += 1

        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"Backend process: Error sending heartbeat: {e}")
            failed_heartbeat_count += 1

        # Check if we've exceeded the maximum allowed missed heartbeats
        if failed_heartbeat_count > num_missable_heartbeats:
            print(f"Backend process: Missed {failed_heartbeat_count} consecutive heartbeats. Stopping.")
            break

        time.sleep(interval)

    stop_event.clear()
    print(f"Backend process: Heartbeat job stopped")

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
                        print(f"  [OK] Endpoint check PASSED: {url}")
                        return (url, True)
                    else:
                        print(f"  [FAIL] Endpoint check FAILED ({response.status}): {url}")
                        return (url, False)
            except Exception as e:
                print(f"  [FAIL] Endpoint check FAILED (exception): {url} - {e}")
                return (url, False)

        tasks = [fetch(url) for url in urls]
        results = await asyncio.gather(*tasks)

    return results

def main(telemetry_port, http_port, proto):
    CACHE_DIR.mkdir(exist_ok=True)
    is_windows = platform.system() == "Windows"

    print("Checking for cached test files...")
    if cached_files := get_cached_files():
        print(f"Found {len(cached_files)} cached files - skipping download")
        files = cached_files
    else:
        print("No cached files found. Downloading test files from Google Drive...")
        try:
            files = gdown.download_folder(
                DRIVE_FOLDER_URL,
                output=str(CACHE_DIR),
                quiet=False,
                remaining_ok=True
            )
            if not files:
                print("No files were downloaded from Google Drive!")
                sys.exit(1)
            print(f"Downloaded {len(files)} test files")
        except Exception as e:
            print(f"Error occurred while downloading test files from Google Drive: {e}")
            files = get_cached_files()
            if files:
                print(f"Using {len(files)} cached files")
            else:
                print("No test files available to run.")
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

    print("\nStarting app in replay server mode...")
    app_cmd = [
        sys.executable, "-m", "coverage", "run",
        "--parallel-mode", "--rcfile", "scripts/.coveragerc_integration", "-m", "apps.backend",
            "--replay-server", "--debug", "--ipc-port", str(ipc_port)
    ]


    os.environ["COVERAGE_PROCESS_START"] = str(Path("scripts/.coveragerc_integration").resolve())
    if is_windows:
        app_process = subprocess.Popen(app_cmd, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    else:
        app_process = subprocess.Popen(app_cmd, start_new_session=True)

    exit_event = threading.Event()
    threading.Thread(target=send_heartbeat, args=(exit_event, ipc_port), daemon=True).start()
    print("Waiting for app to start...")
    time.sleep(5)

    print("Launching driver view, engineer view and overlay clients")
    webbrowser.open(f'{proto}://localhost:{http_port}/', new=2)
    webbrowser.open(f'{proto}://localhost:{http_port}/eng-view', new=2)
    webbrowser.open(f'{proto}://localhost:{http_port}/player-stream-overlay', new=2)

    results = []
    try:
        for index, file_path in enumerate(files):
            # If app is already dead, don't even try to replay
            if app_process.poll() is not None:
                print(f"\n[FAIL] App crashed or exited unexpectedly (code={app_process.returncode}) - aborting remaining tests")
                break

            file_name = os.path.basename(file_path)
            print("=" * 40)
            print(f"\nRunning test {index + 1} of {len(files)}: {file_name}")

            # Build replayer command
            replayer_cmd = [
                "poetry", "run", "python", "-m", "apps.dev_tools.telemetry_replayer",
                "--file-name", str(file_path),
                "--port", str(telemetry_port)
            ]

            replay_success = False
            endpoint_status = []

            # Launch the replayer — will cause file decompression
            try:
                result = subprocess.run(replayer_cmd, timeout=120)
                replay_success = (result.returncode == 0)
            except subprocess.TimeoutExpired:
                print(f"[FAIL] Test FAILED: {file_name} timed out after 120 seconds")

            # Abort early if replay failed and app has crashed
            if not replay_success:
                print(f"[FAIL] App crashed during replay (code={app_process.returncode}) - aborting remaining tests")
                results.append((file_name, False, replay_success, []))
                break

            # If app crashed during replay
            if app_process.poll() is not None:
                print(f"[FAIL] App crashed during replay (code={app_process.returncode}) - skipping endpoint checks")
                results.append((file_name, False, replay_success, []))
                break

            # Only run endpoint checks if replay succeeded and app is still alive
            endpoint_status = check_endpoints_blocking(http_endpoints)

            overall_success = replay_success and all(ok for _, ok in endpoint_status)
            results.append((file_name, overall_success, replay_success, endpoint_status))

            status = "PASSED" if overall_success else "FAILED"
            print(f"Test {index + 1} of {len(files)} {status}: {file_name}")

    finally:
        print(f"\nStopping app... PID={app_process.pid}")
        exit_event.set()
        if not send_ipc_shutdown(ipc_port):
            kill_app(is_windows, app_process)
        time.sleep(5)

    print("\n===== TEST RESULTS =====")
    success_count = sum(overall for _, overall, _, _ in results)
    print(f"Passed: {success_count}/{len(results)}\n")

    for file_name, overall, replay_success, endpoint_status in results:
        status = "PASS" if overall else "FAIL"
        print(f"{status}: {file_name}")

        if not replay_success:
            print("  [FAIL] Replayer failed")
        for url, ok in endpoint_status:
            if not ok:
                print(f"  [FAIL] Endpoint failed: {url}")

    return success_count == len(results)

if __name__ == "__main__":
    settings = load_config_from_ini("png_config.ini")

    start_time = time.perf_counter()
    success = main(
        telemetry_port=settings.Network.telemetry_port,
        http_port=settings.Network.server_port,
        proto=settings.HTTPS.proto
    )
    end_time = time.perf_counter()
    mm, ss = divmod(int(end_time - start_time), 60)
    ms = int((end_time - start_time - mm * 60 - ss) * 1000)
    print(f"Total time: {mm:02d}:{ss:02d}.{ms:03d}")

    sys.exit(0 if success else 1)
