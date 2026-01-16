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

# --------------------------------------------------------------------------------------------------

# PyInstaller Spec File for Pits n' Giggles
# Onefile build with embedded dispatcher (via --module)

# Add 'scripts/' to sys.path so 'version.py' can be imported
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(sys.argv[0])))

import os
import platform
import shutil
import tempfile
from PyInstaller.utils.hooks import collect_submodules, collect_data_files
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT, BUNDLE
from meta.meta import APP_VERSION, APP_NAME_SNAKE

# --------------------------------------------------------------------------------------------------
# Core application info
# --------------------------------------------------------------------------------------------------

ICON_PATH = "../assets/favicon.ico"
ICON_PATH_MAC = "../assets/logo.icns"

APP_BASENAME = f"{APP_NAME_SNAKE}_{APP_VERSION}"
COLLECT_DIR_NAME = f"{APP_NAME_SNAKE}_build_tmp"
PROJECT_ROOT = os.path.abspath(".")

# --------------------------------------------------------------------------------------------------
# Runtime hook: inject PNG_VERSION env var before app starts
# --------------------------------------------------------------------------------------------------

runtime_hook_code = f'import os\nos.environ["PNG_VERSION"] = "{APP_VERSION}"\n'
runtime_hook_path = os.path.join(tempfile.gettempdir(), "png_runtime_hook.py")

with open(runtime_hook_path, "w", encoding="utf-8") as f:
    f.write(runtime_hook_code)

# --------------------------------------------------------------------------------------------------
# Entrypoint script
# --------------------------------------------------------------------------------------------------

entry_script = os.path.join(PROJECT_ROOT, "apps", "launcher", "__main__.py")

# --------------------------------------------------------------------------------------------------
# Helper function to collect directories recursively
# --------------------------------------------------------------------------------------------------

def collect_directory(src_dir, dest_dir):
    """Collect all files in a directory recursively."""
    items = []
    src_path = os.path.join(PROJECT_ROOT, src_dir)

    if not os.path.exists(src_path):
        print(f"Warning: {src_path} does not exist")
        return items

    for root, dirs, files in os.walk(src_path):
        for file in files:
            src_file = os.path.join(root, file)
            rel_path = os.path.relpath(root, PROJECT_ROOT)
            items.append((src_file, rel_path))

    return items

# --------------------------------------------------------------------------------------------------
# Modules and Assets
# --------------------------------------------------------------------------------------------------

hiddenimports = (
    collect_submodules("apps.launcher") +
    collect_submodules("apps.backend") +
    collect_submodules("apps.save_viewer") +
    collect_submodules("apps.hud") +
    collect_submodules("apps.broker")
)

# Automatically collect all assets and frontend files
datas = []

# Frontend assets (CSS, HTML, JS)
datas.extend(collect_directory("apps/frontend/css", "apps/frontend/css"))
datas.extend(collect_directory("apps/frontend/html", "apps/frontend/html"))
datas.extend(collect_directory("apps/frontend/js", "apps/frontend/js"))

# All assets (icons, images, fonts, etc.)
datas.extend(collect_directory("assets", "assets"))

# QML files (hardcoded intentionally, since they don't have an explicit assets path)
def qml_file(path, filename):
    """Helper to add a QML file with less repetition.

    Args:
        path: Relative path from PROJECT_ROOT (e.g., "apps/hud/ui/overlays/track_radar")
        filename: QML filename (e.g., "track_radar.qml")
    """
    full_path = os.path.join(PROJECT_ROOT, path, filename)
    return (full_path, path)

datas.extend([
    qml_file("apps/hud/ui/overlays/track_radar", "track_radar.qml"),
    qml_file("apps/hud/ui/overlays/input_telemetry", "input_telemetry.qml"),
    qml_file("apps/hud/ui/overlays/timing_tower", "timing_tower.qml"),
    qml_file("apps/hud/ui/overlays/lap_timer", "lap_timer_overlay.qml"),
    qml_file("apps/hud/ui/overlays/mfd", "mfd.qml"),
    qml_file("apps/hud/ui/overlays/mfd/pages/collapsed", "collapsed_page.qml"),
    qml_file("apps/hud/ui/overlays/mfd/pages/fuel", "fuel_page.qml"),
    qml_file("apps/hud/ui/overlays/mfd/pages/lap_times", "lap_times_page.qml"),
    qml_file("apps/hud/ui/overlays/mfd/pages/pit_rejoin", "pit_rejoin_page.qml"),
    qml_file("apps/hud/ui/overlays/mfd/pages/tyre_sets", "tyre_sets_page.qml"),
    qml_file("apps/hud/ui/overlays/mfd/pages/tyre_wear", "tyre_wear_page.qml"),
    qml_file("apps/hud/ui/overlays/mfd/pages/weather", "weather_page.qml"),
])

# --------------------------------------------------------------------------------------------------
# Build pipeline
# --------------------------------------------------------------------------------------------------

a = Analysis(
    [entry_script],
    pathex=[PROJECT_ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[runtime_hook_path],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=APP_BASENAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON_PATH,
    stdout=None,
    stderr=None,
)

if platform.system() == "Darwin":
    from PyInstaller.building.build_main import BUNDLE

    app = BUNDLE(
        exe,
        name=f"{APP_BASENAME}.app",
        icon=ICON_PATH_MAC,
        bundle_identifier="com.pitsngiggles.app",
    )

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=COLLECT_DIR_NAME,
)
