import os
import sys
import tempfile
from pathlib import Path

app_name = 'pits_n_giggles'
app_ver = '2.3.2'

backend_name = 'backend'
save_viewer_name = 'save_viewer'

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

def get_data_paths_launcher():
    return [
        ('../assets/logo.png', 'assets/'),
        ('../assets/settings.ico', 'assets/'),
        ('../assets/favicon.ico', 'assets/'),
        ('../dist/backend.exe', 'embedded_exes'),  # (source, target_dir_inside_launcher)
        ('../dist/save_viewer.exe', 'embedded_exes'),
    ]

def get_icon_path():
    return str(Path('../assets/favicon.ico'))

def get_launcher_name():
    return app_name + '_' + app_ver

# === Analysis for backend ===
backend_analysis = Analysis(
    ['../apps/backend/pits_n_giggles.py'],  # Correct path to the main script
    pathex=['.'],
    binaries=[],
    datas=get_data_paths_frontend(),
    hiddenimports=[],
    runtime_hooks=[hook_path],
    excludes=[]
)

# === Analysis for save viewer ===
save_viewer_analysis = Analysis(
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

backend_pyz = PYZ(backend_analysis.pure)
save_viewer_pyz = PYZ(save_viewer_analysis.pure)

backend_exe = EXE(
    backend_pyz,
    backend_analysis.scripts,
    backend_analysis.binaries,
    backend_analysis.datas,
    [],
    name=backend_name,
    icon=get_icon_path(),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    arguments=['--version', app_ver],
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    onefile=True,
)

save_viewer_exe = EXE(
    save_viewer_pyz,
    save_viewer_analysis.scripts,
    save_viewer_analysis.binaries,
    save_viewer_analysis.datas,
    [],
    name=save_viewer_name,
    icon=get_icon_path(),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    arguments=['--version', app_ver],
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    onefile=True,
)

# Launcher analysis
launcher_analysis = Analysis(
    ['../apps/launcher/launcher.py'],  # or the path to the launcher module
    pathex=['.'],
    binaries=[],
    datas=get_data_paths_launcher(),
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[hook_path],
    excludes=[],
)

launcher_pyz = PYZ(launcher_analysis.pure)

exe_launcher = EXE(
    launcher_pyz,
    launcher_analysis.scripts,
    launcher_analysis.binaries,
    launcher_analysis.datas,
    [],
    name=get_launcher_name(),
    icon=get_icon_path(),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    arguments=['--version', app_ver],
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    onefile=True,
)

# === CLEANUP STEP ===
for exe_name in ['backend.exe', 'save_viewer.exe']:
    exe_path = Path('.') / 'dist' / exe_name
    if exe_path.exists():
        exe_path.unlink()
