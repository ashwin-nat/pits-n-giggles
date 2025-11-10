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
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT, BUNDLE
from meta.meta import APP_VERSION, APP_NAME_SNAKE

# --------------------------------------------------------------------------------------------------
# Core application info
# --------------------------------------------------------------------------------------------------

ICON_PATH = "../assets/favicon.ico"
ICON_PATH_MAC = "../assets/logo.icns"

APP_BASENAME = f"{APP_NAME_SNAKE}_{APP_VERSION}"
COLLECT_DIR_NAME = f"{APP_NAME_SNAKE}_build_tmp"      # used for intermediate dist folder
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
# Modules and Assets
# --------------------------------------------------------------------------------------------------

hiddenimports = (
    collect_submodules("apps.launcher") +
    collect_submodules("apps.backend") +
    collect_submodules("apps.save_viewer") +
    collect_submodules("apps.hud")
)

datas = [
    # Frontend assets
    (os.path.join(PROJECT_ROOT, "apps", "frontend", "css"), "apps/frontend/css"),
    (os.path.join(PROJECT_ROOT, "apps", "frontend", "html"), "apps/frontend/html"),
    (os.path.join(PROJECT_ROOT, "apps", "frontend", "js"), "apps/frontend/js"),

    # Icons and images
    (os.path.join(PROJECT_ROOT, "assets", "favicon.ico"), "assets"),
    (os.path.join(PROJECT_ROOT, "assets", "logo.png"), "assets"),
    (os.path.join(PROJECT_ROOT, "assets", "settings.ico"), "assets"),

    # Tyre icons
    (os.path.join(PROJECT_ROOT, "assets", "tyre-icons", "soft_tyre.svg"), "assets/tyre-icons"),
    (os.path.join(PROJECT_ROOT, "assets", "tyre-icons", "medium_tyre.svg"), "assets/tyre-icons"),
    (os.path.join(PROJECT_ROOT, "assets", "tyre-icons", "hard_tyre.svg"), "assets/tyre-icons"),
    (os.path.join(PROJECT_ROOT, "assets", "tyre-icons", "wet_tyre.svg"), "assets/tyre-icons"),
    (os.path.join(PROJECT_ROOT, "assets", "tyre-icons", "intermediate_tyre.svg"), "assets/tyre-icons"),
    (os.path.join(PROJECT_ROOT, "assets", "tyre-icons", "super_soft_tyre.svg"), "assets/tyre-icons"),

    # Team icons
    (os.path.join(PROJECT_ROOT, "assets", "team-logos", "alpine.svg"), "assets/team-logos"),
    (os.path.join(PROJECT_ROOT, "assets", "team-logos", "aston_martin.svg"), "assets/team-logos"),
    (os.path.join(PROJECT_ROOT, "assets", "team-logos", "ferrari.svg"), "assets/team-logos"),
    (os.path.join(PROJECT_ROOT, "assets", "team-logos", "haas.svg"), "assets/team-logos"),
    (os.path.join(PROJECT_ROOT, "assets", "team-logos", "mclaren.svg"), "assets/team-logos"),
    (os.path.join(PROJECT_ROOT, "assets", "team-logos", "mercedes.svg"), "assets/team-logos"),
    (os.path.join(PROJECT_ROOT, "assets", "team-logos", "rb.svg"), "assets/team-logos"),
    (os.path.join(PROJECT_ROOT, "assets", "team-logos", "red_bull.svg"), "assets/team-logos"),
    (os.path.join(PROJECT_ROOT, "assets", "team-logos", "sauber.svg"), "assets/team-logos"),
    (os.path.join(PROJECT_ROOT, "assets", "team-logos", "williams.svg"), "assets/team-logos"),
    (os.path.join(PROJECT_ROOT, "assets", "team-logos", "default.svg"), "assets/team-logos"),
]

# Overlays
# overlays_base = os.path.join(PROJECT_ROOT, "apps", "hud", "ui", "overlays")

# # Dynamically add all overlay folders
# for overlay_name in os.listdir(overlays_base):
#     overlay_path = os.path.join(overlays_base, overlay_name)
#     if os.path.isdir(overlay_path):
#         datas.append(
#             (overlay_path, f"apps/hud/ui/overlays/{overlay_name}")
#         )

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
    # app is built for .app bundle, but we still pass `exe` to COLLECT

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
