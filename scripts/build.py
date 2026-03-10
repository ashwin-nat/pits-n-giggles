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

# ----------------------------------------------------------------------------------------------------------------------

import subprocess
import sys
import os
import shutil
import time

APP_NAME = "pits_n_giggles"  # or load from the spec file dynamically if needed
COLLECT_DIR_NAME = f"{APP_NAME}_build_tmp"

def remove_dir_if_exists(path: str):
    if os.path.isdir(path):
        shutil.rmtree(path)

def build_rust_backend() -> str:
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    manifest_path = os.path.join(project_root, "apps", "backend", "rust", "Cargo.toml")
    cargo = shutil.which("cargo")
    if not cargo:
        raise RuntimeError("cargo was not found in PATH. Rust is required for packaged builds.")

    subprocess.run(
        [
            cargo,
            "build",
            "--release",
            "--manifest-path",
            manifest_path,
            "-p",
            "backend",
        ],
        check=True,
    )

    binary_name = "backend.exe" if os.name == "nt" else "backend"
    binary_path = os.path.join(project_root, "apps", "backend", "rust", "target", "release", binary_name)
    if not os.path.isfile(binary_path):
        raise RuntimeError(f"Rust backend binary not found after build: {binary_path}")
    return binary_path

def resolve_pyinstaller_command() -> list[str]:
    pyinstaller = shutil.which("pyinstaller")
    if pyinstaller:
        return [pyinstaller]
    return [sys.executable, "-m", "PyInstaller"]

def verify_rust_backend_packaged(project_root: str, rust_backend_binary: str):
    toc_path = os.path.join(project_root, "build", "png", "PKG-00.toc")
    if not os.path.isfile(toc_path):
        raise RuntimeError(f"Expected PyInstaller TOC not found: {toc_path}")

    with open(toc_path, "r", encoding="utf-8") as f:
        toc_contents = f.read()

    binary_name = os.path.basename(rust_backend_binary)
    if binary_name not in toc_contents or rust_backend_binary not in toc_contents:
        raise RuntimeError(
            "Rust backend binary was built, but PyInstaller did not package it into PKG-00.toc"
        )

def main():
    script_dir = os.path.dirname(__file__)
    project_root = os.path.abspath(os.path.join(script_dir, ".."))
    spec_path = os.path.join(script_dir, "png.spec")
    collect_dir = os.path.join("dist", COLLECT_DIR_NAME)

    # 0. Cleanup previous files
    remove_dir_if_exists("build")
    remove_dir_if_exists("dist")

    # 1. Build the Rust backend companion binary
    rust_backend_binary = build_rust_backend()

    # 2. Run PyInstaller
    start_time = time.time()
    env = os.environ.copy()
    env["PNG_RUST_BACKEND_BIN"] = rust_backend_binary
    env["PNG_PROJECT_ROOT"] = project_root
    subprocess.run(
        [
            *resolve_pyinstaller_command(),
            "--clean",
            "--noconfirm",
            spec_path,
        ],
        check=True,
        env=env,
    )
    verify_rust_backend_packaged(project_root, rust_backend_binary)

    # 3. Cleanup the custom COLLECT dir
    remove_dir_if_exists(collect_dir)

    end_time = time.time()
    elapsed = end_time - start_time
    print(f"\n Build completed in {elapsed:.2f} seconds.")

if __name__ == "__main__":
    main()
