import os
from pathlib import Path

app_name = 'pits_n_giggles'
app_ver = '2.0.4'

# Helper function to join paths correctly
def get_data_paths_main_app():
    base_src_path = Path('src')

    data_paths = [
        (base_src_path / 'static' / 'favicon.ico', 'src/static/'),
        (base_src_path / 'static' , 'src/static/'),
        (base_src_path / 'templates' / 'index.html', 'src/templates/'),
        (base_src_path / 'templates' / 'player-stream-overlay.html', 'src/templates/')
    ]

    # Convert paths to strings for PyInstaller compatibility
    return [(str(src), dest) for src, dest in data_paths]

def get_data_paths_replayer():
    base_src_path = Path('src')

    data_paths = [
        (str(base_src_path / 'static'), 'static'),
        (str(base_src_path / 'templates'), 'templates'),
    ]

    # Convert paths to strings for PyInstaller compatibility
    return [(str(src), dest) for src, dest in data_paths]

def get_icon_path():
    return str(Path('src/static/favicon.ico'))

def get_name():
    return app_name + '_' + app_ver

def get_viewer_name():
    return 'png_save_data_viewer_' + app_ver

a = Analysis(
    ['app.py'],
    pathex=[str(Path('png-venv/Lib/site-packages/'))],  # OS-independent path
    binaries=[],
    datas=get_data_paths_main_app(),  # Paths handled in a cross-platform manner
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

# Analysis for the second executable
b = Analysis(
    ['utils/telemetry_post_race_data_viewer.py'],
    pathex=[str(Path('png-venv/Lib/site-packages/'))],
    binaries=[],
    datas=get_data_paths_replayer(),  # Paths handled in a cross-platform manner
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)
pyz_b = PYZ(b.pure)

# First executable for app.py
exe1 = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=get_name(),
    icon=get_icon_path(),  # Set the icon path here
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    onefile=True,
)

# Second executable for telemetry_post_race_data_viewer.py
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
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    onefile=True,
)

