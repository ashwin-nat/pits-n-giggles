# scripts/png.spec

# PyInstaller Spec File for Pits n' Giggles
# Onefile build with embedded dispatcher (via --module)

from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT
import os

block_cipher = None

project_root = os.path.abspath(".")

# Entry script
entry_script = os.path.join(project_root, "apps", "launcher", "__main__.py")

# All importable modules in your app suite
hiddenimports = (
    collect_submodules("apps.launcher") +
    collect_submodules("apps.backend") +
    collect_submodules("apps.save_viewer") +
    collect_submodules("apps.save_viewer.telemetry_post_race_data_viewer")
)

# Data files (hardcoded)
datas = [
    # Frontend assets
    (os.path.join(project_root, "apps", "frontend", "css"), "apps/frontend/css"),
    (os.path.join(project_root, "apps", "frontend", "html"), "apps/frontend/html"),
    (os.path.join(project_root, "apps", "frontend", "js"), "apps/frontend/js"),

    # Icons and images
    (os.path.join(project_root, "assets", "favicon.ico"), "assets"),
    (os.path.join(project_root, "assets", "logo.png"), "assets"),
    (os.path.join(project_root, "assets", "settings.ico"), "assets"),

    # Tyre icons
    (os.path.join(project_root, "assets", "tyre-icons", "soft_tyre.svg"), "assets/tyre-icons"),
    (os.path.join(project_root, "assets", "tyre-icons", "medium_tyre.svg"), "assets/tyre-icons"),
    (os.path.join(project_root, "assets", "tyre-icons", "hard_tyre.svg"), "assets/tyre-icons"),
    (os.path.join(project_root, "assets", "tyre-icons", "wet_tyre.svg"), "assets/tyre-icons"),
    (os.path.join(project_root, "assets", "tyre-icons", "intermediate_tyre.svg"), "assets/tyre-icons"),
    (os.path.join(project_root, "assets", "tyre-icons", "super_soft_tyre.svg"), "assets/tyre-icons"),
]

a = Analysis(
    [entry_script],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='pits_n_giggles',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # flip to False for windowed GUI (no console)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='pits_n_giggles'
)
