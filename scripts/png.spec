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
from PyInstaller.utils.hooks import collect_submodules, collect_data_files, copy_metadata
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT, BUNDLE
from PyInstaller.building.splash import Splash
from meta.meta import APP_VERSION, APP_NAME_SNAKE

# `scripts/` is on sys.path (see the insert above), so this resolves the same way meta.meta does.
from gen_splash import render_splash
from splash_position import use_cursor_monitor_centring

# --------------------------------------------------------------------------------------------------
# Core application info
# --------------------------------------------------------------------------------------------------

ICON_PATH = "../assets/favicon.ico"
ICON_PATH_MAC = "../assets/logo.icns"

APP_BASENAME = f"{APP_NAME_SNAKE}_{APP_VERSION}"
COLLECT_DIR_NAME = f"{APP_NAME_SNAKE}_build_tmp"
PROJECT_ROOT = os.path.abspath(".")

IS_MACOS = platform.system() == "Darwin"

# --------------------------------------------------------------------------------------------------
# Debug builds
#
# Enabled by `python scripts/build.py --debug`, which forwards `-- --force-debug` to PyInstaller.
# PyInstaller splits its command line on `--` and hands everything after it to the spec as
# sys.argv[1:] (sys.argv[0] stays the spec path, so the sys.path insert above is unaffected).
# Building the spec directly works too: `pyinstaller scripts/png.spec -- --force-debug`.
#
# The launcher only enables debug logging when it is started with --debug, and it forwards that
# flag to every subsystem it spawns. When this is on, the runtime hook below appends --debug to
# sys.argv at startup, so the packaged app behaves as if the user had passed it.
#
# Side effect worth knowing: with debug mode on, subsystems no longer self-terminate after missing
# heartbeats (see apps/launcher/subsystems/base_mgr.py), so a wedged child process will linger
# instead of exiting.
# --------------------------------------------------------------------------------------------------

FORCE_DEBUG_MODE = "--force-debug" in sys.argv[1:]

# --------------------------------------------------------------------------------------------------
# Runtime hook: inject PNG_VERSION env var before app starts
# --------------------------------------------------------------------------------------------------

runtime_hook_lines = [
    "import os",
    f'os.environ["PNG_VERSION"] = "{APP_VERSION}"',
]

if FORCE_DEBUG_MODE:
    # Appended, never inserted: the frozen submodule dispatcher locates its module by
    # the index of --module in sys.argv, so nothing before that may shift.
    runtime_hook_lines += [
        "import sys",
        'if "--debug" not in sys.argv:',
        '    sys.argv.append("--debug")',
    ]

runtime_hook_code = "\n".join(runtime_hook_lines) + "\n"
runtime_hook_path = os.path.join(tempfile.gettempdir(), "png_runtime_hook.py")

with open(runtime_hook_path, "w", encoding="utf-8") as f:
    f.write(runtime_hook_code)

if FORCE_DEBUG_MODE:
    print("=" * 80)
    print("png.spec: FORCE_DEBUG_MODE is ON — this build always runs with --debug.")
    print("=" * 80)

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
    collect_submodules("apps.web") +
    collect_submodules("apps.hud") +
    collect_submodules("apps.broker") +
    collect_submodules("apps.mcp_server")
)

# Automatically collect all assets and frontend files
datas = []

# Package metadata required by packages that call importlib.metadata.version() at import time
datas += copy_metadata("fastmcp")

# Frontend assets (CSS, HTML, JS)
datas.extend(collect_directory("apps/frontend/css", "apps/frontend/css"))
datas.extend(collect_directory("apps/frontend/html", "apps/frontend/html"))
datas.extend(collect_directory("apps/frontend/js", "apps/frontend/js"))

# All assets (icons, images, fonts, etc.)
datas.extend(collect_directory("assets", "assets"))

# f1-telemetry-viewer React app (built by build.py before PyInstaller runs)
datas.extend(collect_directory("apps/external/f1-save-viewer/dist", "apps/external/f1-save-viewer/dist"))

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
    qml_file("apps/hud/ui/overlays/base", "OverlayBorder.qml"),
    qml_file("apps/hud/ui/overlays/base", "DiffedTableModel.qml"),
    qml_file("apps/hud/ui/overlays/track_radar", "track_radar.qml"),
    qml_file("apps/hud/ui/overlays/input_telemetry", "input_telemetry.qml"),
    qml_file("apps/hud/ui/overlays/timing_tower", "timing_tower.qml"),
    qml_file("apps/hud/ui/overlays/lap_timer", "lap_timer_overlay.qml"),
    qml_file("apps/hud/ui/overlays/circuit_info", "circuit_info.qml"),
    qml_file("apps/hud/ui/overlays/pu", "pu.qml"),
    qml_file("apps/hud/ui/overlays/hud_overlay", "hud_overlay.qml"),
    qml_file("apps/hud/ui/overlays/mfd", "mfd.qml"),
    qml_file("apps/hud/ui/overlays/mfd/pages/collapsed", "collapsed_page.qml"),
    qml_file("apps/hud/ui/overlays/mfd/pages/fuel", "fuel_page.qml"),
    qml_file("apps/hud/ui/overlays/mfd/pages/lap_times", "lap_times_page.qml"),
    qml_file("apps/hud/ui/overlays/mfd/pages/pace_comp", "pace_comp_page.qml"),
    qml_file("apps/hud/ui/overlays/mfd/pages/pit_rejoin", "pit_rejoin_page.qml"),
    qml_file("apps/hud/ui/overlays/mfd/pages/traffic_monitor", "traffic_monitor_page.qml"),
    qml_file("apps/hud/ui/overlays/mfd/pages/tyre_sets", "tyre_sets_page.qml"),
    qml_file("apps/hud/ui/overlays/mfd/pages/tyre_wear", "tyre_wear_page.qml"),
    qml_file("apps/hud/ui/overlays/mfd/pages/weather", "weather_page.qml"),
    qml_file("apps/hud/ui/overlays/mfd/pages", "standalone_wrapper.qml")
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

# --------------------------------------------------------------------------------------------------
# Splash screen
#
# This is a onefile build, so the bootloader must unpack the whole bundle into _MEIPASS before any
# Python runs. That takes several seconds during which the user sees nothing at all. The splash
# covers that gap, and the launcher closes it once the real window is on screen.
#
# PyInstaller's splash is one static PNG plus a single live text line - the Tcl script is generated
# internally and has no hook for custom widgets. The whole design therefore lives in the image,
# which gen_splash.py renders fresh each build so the version can never go stale.
#
# No text options are passed on purpose. Supplying text_pos switches on PyInstaller's live text
# field, which in onefile mode the bootloader drives with the name of every file it extracts -
# far more detail than is useful. Leaving it off makes the splash fully static, and the
# "Loading..." line is baked into the image instead.
#
# Not available on macOS: PyInstaller raises SystemExit there because the splash needs a secondary
# thread and macOS only allows UI work on the main one. CI builds macOS too, hence the guard.
# --------------------------------------------------------------------------------------------------

splash = None
if IS_MACOS:
    print("png.spec: macOS build - splash screen is not supported on this platform, skipping.")
else:
    # Must happen before Splash() is constructed - that is when the Tcl script is generated.
    use_cursor_monitor_centring()
    splash = Splash(
        render_splash(os.path.join(PROJECT_ROOT, "build", "splash", "splash.png")),
        binaries=a.binaries,
        datas=a.datas,
        always_on_top=True,
    )

exe = EXE(
    pyz,
    a.scripts,
    # Onefile needs both the Splash target and its Tcl/Tk binaries in the EXE args.
    *([splash, splash.binaries] if splash else []),
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=APP_BASENAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON_PATH,
    stdout=None,
    stderr=None,
)

if IS_MACOS:
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
    upx=False,
    upx_exclude=[],
    name=COLLECT_DIR_NAME,
)
