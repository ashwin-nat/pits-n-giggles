#!/usr/bin/env python3
"""
Simple integration test for Pits n Giggles App
"""

import os
import signal
import subprocess
import sys
import time
import platform
from pathlib import Path

import gdown

# Google Drive folder URL
DRIVE_FOLDER_URL = "https://drive.google.com/drive/folders/13tIadKMvi3kuItkovT6GUTTHOL3YM6n_?usp=drive_link"
CACHE_DIR = Path("test_data")

def main():
    # Create test data directory if it doesn't exist
    CACHE_DIR.mkdir(exist_ok=True)

    is_windows = platform.system() == "Windows"


    # Download test files using gdown
    print("Downloading test files from Google Drive...")
    try:
        files = gdown.download_folder(DRIVE_FOLDER_URL, output=str(CACHE_DIR), quiet=False)
        if not files or len(files) == 0:
            print("No files were downloaded from Google Drive!")
            sys.exit(1)
        print(f"Downloaded {len(files)} test files")
    except Exception as e:
        print(f"Error occurred while downloading test files from Google Drive: {e}")
        sys.exit(1)
    print(f"Downloaded {len(files)} test files")

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
        for file_path in files:
            file_name = os.path.basename(file_path)
            print('=' * 40)
            print(f"\nRunning test: {file_name}")

            # Run telemetry replayer and show output in real-time
            replayer_cmd = ["poetry", "run", "python", "-m", "apps.dev_tools.telemetry_replayer",
                          "--file-name", file_path]

            try:
                result = subprocess.run(replayer_cmd, timeout=120)
                success = (result.returncode == 0)
            except subprocess.TimeoutExpired:
                print(f"Test FAILED: {file_name} timed out after 120 seconds")
                success = False
            results.append((file_name, success))

            status = "PASSED" if success else "FAILED"
            print(f"Test {status}: {file_name}")

        time.sleep(10)
    finally:
        # Stop the app
        print(f"\nStopping app... PID={app_process.pid}")
        if is_windows:
            # Nukes the whole process group on Windows
            subprocess.call(["taskkill", "/F", "/T", "/PID", str(app_process.pid)])
        else:
            # Nukes the entire process group on Unix
            os.killpg(app_process.pid, signal.SIGKILL)

    # Print summary
    print("\n===== TEST RESULTS =====")
    success_count = sum(bool(success)
                    for _, success in results)
    print(f"Passed: {success_count}/{len(results)}")

    for file_name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"{status}: {file_name}")

    return success_count == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
