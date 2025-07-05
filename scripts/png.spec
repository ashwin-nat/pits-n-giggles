# PyInstaller Spec File for Pits n' Giggles
# Onefile build with embedded dispatcher (via --module)
import os
import shutil
import tempfile
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT

# --------------------------------------------------------------------------------------------------
# Core application info
# --------------------------------------------------------------------------------------------------

APP_NAME = "pits_n_giggles"
APP_VERSION = "2.8.1"
ICON_PATH = "../assets/favicon.ico"

APP_BASENAME = f"{APP_NAME}_{APP_VERSION}"
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
    collect_submodules("apps.save_viewer")
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
]

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
    console=False,  # ✅ Suppress empty CMD window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON_PATH,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=APP_BASENAME,
)

# --------------------------------------------------------------------------------------------------
# Optional cleanup: remove dist/APP_BASENAME dir (created by COLLECT)
# --------------------------------------------------------------------------------------------------

collect_dir = os.path.join("dist", APP_BASENAME)
if os.path.isdir(collect_dir):
    shutil.rmtree(collect_dir)
