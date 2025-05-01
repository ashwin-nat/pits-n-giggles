import os
import sys
import tempfile
from pathlib import Path

app_name = 'pits_n_giggles'
app_ver = '2.3.2'

# Create a temporary runtime hook file
temp_dir = tempfile.mkdtemp()
hook_path = os.path.join(temp_dir, 'hook-runtime.py')

with open(hook_path, 'w') as f:
    f.write("import os\n")
    f.write(f"os.environ['PNG_VERSION'] = '{app_ver}'\n")

def get_data_paths_frontend():
    return [
        ('../apps/frontend/css/*', 'apps/frontend/css'),
        ('../apps/frontend/html/*', 'apps/frontend/html'),
        ('../apps/frontend/js/*', 'apps/frontend/js'),
        ('../assets/favicon.ico', 'assets/'),  # Corrected path
        ('../assets/tyre-icons/intermediate_tyre.svg', 'assets/tyre-icons'),
        ('../assets/tyre-icons/hard_tyre.svg', 'assets/tyre-icons'),
        ('../assets/tyre-icons/soft_tyre.svg', 'assets/tyre-icons'),
        ('../assets/tyre-icons/medium_tyre.svg', 'assets/tyre-icons'),
        ('../assets/tyre-icons/wet_tyre.svg', 'assets/tyre-icons'),
        ('../assets/tyre-icons/super_soft_tyre.svg', 'assets/tyre-icons'),
    ]

def get_data_paths_save_viewer():
    # Determine the base path depending on whether we are in a bundled or normal environment
    if getattr(sys, 'frozen', False):  # Check if we're running as a bundled app
        base_src_path = Path(sys._MEIPASS) / 'apps' / 'frontend'  # Use the extracted folder
    else:
        base_src_path = Path(os.getcwd()) / 'apps' / 'frontend'  # Normal environment

    # Return the appropriate paths for the actual directories
    return [
        (str(base_src_path / 'css'), 'apps/frontend/css'),
        (str(base_src_path / 'html'), 'apps/frontend/html'),
        (str(base_src_path / 'js'), 'apps/frontend/js'),
    ]

def get_icon_path():
    return str(Path('../assets/favicon.ico'))

def get_name():
    return app_name + '_' + app_ver

def get_viewer_name():
    return 'png_save_data_viewer_' + app_ver

# === Analysis for backend ===

a = Analysis(
    ['../apps/backend/pits_n_giggles.py'],  # Correct path to the main script
    pathex=['.'],
    binaries=[],
    datas=get_data_paths_frontend(),
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[]
)

# === Analysis for save viewer ===
b = Analysis(
    ['../apps/save_viewer/telemetry_post_race_data_viewer.py'],
    pathex=[str(Path('png-venv/Lib/site-packages/'))],
    binaries=[],
    datas=get_data_paths_frontend(),
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[hook_path],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)
pyz_b = PYZ(b.pure)

exe1 = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=get_name(),
    icon=get_icon_path(),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=True,
    arguments=['--version', app_ver],
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    onefile=True,
)

exe2 = EXE(
    pyz_b,
    b.scripts,
    b.binaries,
    b.datas,
    [],
    name=get_viewer_name(),
    icon=get_icon_path(),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=True,
    arguments=['--version', app_ver],
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    onefile=True,
)

