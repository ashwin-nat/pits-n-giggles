import os
from pathlib import Path

# Helper function to join paths correctly
def get_data_paths():
    base_src_path = Path('src')

    data_paths = [
        (base_src_path / 'static' / 'favicon.ico', 'src/static/'),
        (base_src_path / 'templates' / 'index.html', 'src/templates/'),
        (base_src_path / 'templates' / 'player-stream-overlay.html', 'src/templates/')
    ]

    # Convert paths to strings for PyInstaller compatibility
    return [(str(src), dest) for src, dest in data_paths]

def get_icon_path():
    return str(Path('src/static/favicon.ico'))

# Use get_data_paths function to ensure correct path handling
a = Analysis(
    ['app.py'],
    pathex=[str(Path('png-venv/Lib/site-packages/'))],  # OS-independent path
    binaries=[],
    datas=get_data_paths(),  # Paths handled in a cross-platform manner
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='pits_n_giggles',
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