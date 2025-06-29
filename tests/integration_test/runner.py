#!/usr/bin/env python3
"""
Simple integration test for Pits n Giggles App
"""

import asyncio
import os
import platform
import signal
import subprocess
import sys
import time
from pathlib import Path

import aiohttp
import gdown

# Add the parent directory to the Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from lib.config import load_config_from_ini

# Google Drive folder URL
DRIVE_FOLDER_URL = "https://drive.google.com/drive/folders/13tIadKMvi3kuItkovT6GUTTHOL3YM6n_?usp=drive_link"
CACHE_DIR = Path("test_data")


def get_cached_files() -> list[str]:
    return sorted(str(p) for p in CACHE_DIR.glob("*.f1pcap"))

def check_endpoints_blocking(urls):
    """
    Blocking wrapper for async endpoint check.
    """
    return asyncio.run(_check_endpoints_async(urls))


async def _check_endpoints_async(urls):
    """
    Asynchronously check each URL and print the result.
    """
    results = []

    async def fetch(session, url):
        try:
            async with session.get(url, timeout=5) as response:
                if response.status in {200, 404}:
                    print(f"  ✅ Endpoint check PASSED: {url}")
                    return (url, True)
                else:
                    print(f"  ❌ Endpoint check FAILED ({response.status}): {url}")
                    return (url, False)
        except Exception as e:
            print(f"  ❌ Endpoint check FAILED (exception): {url} — {e}")
            return (url, False)

    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, url) for url in urls]
        results = await asyncio.gather(*tasks)

    return results

def main(telemetry_port, http_port):
    # Create test data directory if it doesn't exist
    CACHE_DIR.mkdir(exist_ok=True)

    is_windows = platform.system() == "Windows"

    print("Checking for cached test files...")
    cached_files = get_cached_files()
    if cached_files:
        print(f"Found {len(cached_files)} cached files — skipping download")
        files = cached_files
    else:
        print("No cached files found. Downloading test files from Google Drive...")
        try:
            files = gdown.download_folder(
                DRIVE_FOLDER_URL,
                output=str(CACHE_DIR),
                quiet=False,
                remaining_ok=True  # Skip re-downloading existing files
            )
            if not files:
                print("No files were downloaded from Google Drive!")
                sys.exit(1)
            print(f"Downloaded {len(files)} test files")
        except Exception as e:
            print(f"Error occurred while downloading test files from Google Drive: {e}")
            # Try using any cached files even if download failed
            files = get_cached_files()
            if files:
                print(f"Using {len(files)} cached files")
            else:
                print("No test files available to run.")
                sys.exit(1)

    http_endpoints = [
        f"http://localhost:{http_port}/telemetry-info",
        f"http://localhost:{http_port}/race-info",
        f"http://localhost:{http_port}/stream-overlay-info",
        *[
            f"http://localhost:{http_port}/driver-info?index={i}"
            for i in range(23) # one index too high so that 404 is sent
        ]
    ]

    # Start the app
    print("\nStarting app in replay server mode...")
    app_cmd = ["poetry", "run", "python", "-m", "apps.backend.pits_n_giggles",
               "--replay-server", "--debug"]

    if is_windows:
        app_process = subprocess.Popen(
            app_cmd,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        app_process = subprocess.Popen(
            app_cmd,
            start_new_session=True
        )

    # Wait for app to start
    print("Waiting for app to start...")
    time.sleep(5)

    # Run each test file
    results = []
    try:
        for index, file_path in enumerate(files):
            file_name = os.path.basename(file_path)
            print('=' * 40)
            print(f"\nRunning test {index + 1} of {len(files)}: {file_name}")

            replayer_cmd = ["poetry", "run", "python", "-m", "apps.dev_tools.telemetry_replayer",
                            "--file-name", str(file_path), "--port", str(telemetry_port)]

            replay_success = False
            endpoint_status = []

            try:
                result = subprocess.run(replayer_cmd, timeout=120)
                replay_success = (result.returncode == 0)
            except subprocess.TimeoutExpired:
                print(f"Test FAILED: {file_name} timed out after 120 seconds")

            if replay_success:
                endpoint_status = check_endpoints_blocking(http_endpoints)
            else:
                print("  ⚠️ Skipping endpoint checks since replayer failed")
                endpoint_status = [(url, False) for url in http_endpoints]

            overall_success = replay_success and all(ok for _, ok in endpoint_status)
            results.append((file_name, overall_success, replay_success, endpoint_status))

            status = "PASSED" if overall_success else "FAILED"
            print(f"Test {index + 1} of {len(files)} {status}: {file_name}")

        time.sleep(10)
    finally:
        print(f"\nStopping app... PID={app_process.pid}")
        if is_windows:
            subprocess.call(["taskkill", "/F", "/T", "/PID", str(app_process.pid)])
        else:
            os.killpg(app_process.pid, signal.SIGKILL)

    # Print summary
    print("\n===== TEST RESULTS =====")
    success_count = sum(overall for _, overall, _, _ in results)
    print(f"Passed: {success_count}/{len(results)}\n")

    for file_name, overall, replay_success, endpoint_status in results:
        status = "PASS" if overall else "FAIL"
        print(f"{status}: {file_name}")

        if not replay_success:
            print("  ↳ ❌ Replayer failed")
        for url, ok in endpoint_status:
            if not ok:
                print(f"  ↳ ❌ Endpoint failed: {url}")

    return success_count == len(results)

if __name__ == "__main__":
    settings = load_config_from_ini("png_config.ini")
    success = main(settings.Network.telemetry_port, settings.Network.server_port)
    sys.exit(0 if success else 1)
