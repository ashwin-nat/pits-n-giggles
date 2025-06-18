#!/usr/bin/env python3
# type: ignore
"""
PyInstaller build script for Pits n' Giggles application suite.
This script builds multiple executables and bundles them into a launcher application.

The script is designed to be easily extensible - add new apps to the APPS dictionary
and they will automatically be built and included in the launcher.
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import List, Tuple, Any, Optional

# ===== APPLICATION CONFIGURATION =====

# Core application info
APP_NAME = "pits_n_giggles"
APP_VERSION = "2.7.2"
ICON_PATH = "../assets/favicon.ico"

# Define all applications to be built
# Each app needs: script_path, name, console flag, and data_paths_func
APPS = {
    "backend": {
        "script_path": "../apps/backend/pits_n_giggles.py",
        "name": "backend",
        "console": False,
        "data_paths_func": "get_frontend_data_paths",
        "extra_pathex": [],
        "hidden_imports": [],
    },
    "save_viewer": {
        "script_path": "../apps/save_viewer/telemetry_post_race_data_viewer.py",
        "name": "save_viewer",
        "console": False,
        "data_paths_func": "get_frontend_data_paths",
        "extra_pathex": [str(Path('png-venv/Lib/site-packages/'))],
        "hidden_imports": [],
    },
}

# Launcher app info (this bundles all the other apps)
LAUNCHER_CONFIG = {
    "script_path": "../apps/launcher/launcher.py",
    "name": f"{APP_NAME}_{APP_VERSION}",  # Will be dynamically set
    "console": False,
    "data_paths_func": "get_launcher_data_paths",
    "extra_pathex": [],
    "hidden_imports": [],
}

# ===== ASSET PATH MANAGEMENT FUNCTIONS =====

def get_frontend_data_paths() -> List[Tuple[str, str]]:
    """
    Get data paths for frontend assets.

    Returns:
        List[Tuple[str, str]]: List of (source, target) paths
    """
    return [
        ('../apps/frontend/css/*', 'apps/frontend/css'),
        ('../apps/frontend/html/*', 'apps/frontend/html'),
        ('../apps/frontend/js/*', 'apps/frontend/js'),
        ('../assets/favicon.ico', 'assets/'),
        ('../assets/tyre-icons/intermediate_tyre.svg', 'assets/tyre-icons'),
        ('../assets/tyre-icons/hard_tyre.svg', 'assets/tyre-icons'),
        ('../assets/tyre-icons/soft_tyre.svg', 'assets/tyre-icons'),
        ('../assets/tyre-icons/medium_tyre.svg', 'assets/tyre-icons'),
        ('../assets/tyre-icons/wet_tyre.svg', 'assets/tyre-icons'),
        ('../assets/tyre-icons/super_soft_tyre.svg', 'assets/tyre-icons'),
    ]


def get_save_viewer_data_paths() -> List[Tuple[str, str]]:
    """
    Get data paths for the save viewer application.
    Adjusts paths based on whether running in bundled or development mode.

    Returns:
        List[Tuple[str, str]]: List of (source, target) paths
    """
    # Determine the base path depending on environment
    if getattr(sys, 'frozen', False):
        base_src_path = Path(sys._MEIPASS) / 'apps' / 'frontend'
    else:
        base_src_path = Path(os.getcwd()) / 'apps' / 'frontend'

    return [
        (str(base_src_path / 'css'), 'apps/frontend/css'),
        (str(base_src_path / 'html'), 'apps/frontend/html'),
        (str(base_src_path / 'js'), 'apps/frontend/js'),
    ]


def get_launcher_data_paths() -> List[Tuple[str, str]]:
    """
    Get data paths for the launcher application.
    Automatically includes all built executables.

    Returns:
        List[Tuple[str, str]]: List of (source, target) paths
    """
    # Basic assets
    paths = [
        ('../assets/logo.png', 'assets/'),
        ('../assets/settings.ico', 'assets/'),
        ('../assets/favicon.ico', 'assets/'),
    ]

    # Add all app executables
    paths.extend(
        (f'../dist/{app_name}.exe', 'embedded_exes')
        for app_name in APPS.keys()
    )
    return paths


# ===== BUILD UTILITY FUNCTIONS =====

def create_runtime_hook() -> str:
    """
    Create a temporary runtime hook file to set environment variables.

    Returns:
        str: Path to the created hook file
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        hook_path = os.path.join(temp_dir, 'hook-runtime.py')

        with open(hook_path, 'w') as f:
            f.write("import os\n")
            f.write(f"os.environ['PNG_VERSION'] = '{APP_VERSION}'\n")

        # Read and return the contents of the hook file
        with open(hook_path, 'r') as f:
            hook_contents = f.read()

    # Create a new temporary file that will persist beyond the context manager
    final_hook = tempfile.mktemp(suffix='.py')
    with open(final_hook, 'w') as f:
        f.write(hook_contents)

    return final_hook

def create_analysis(
    script_path: str,
    datas: List[Tuple[str, str]],
    runtime_hook: str,
    pathex: Optional[List[str]] = None,
    hiddenimports: Optional[List[str]] = None,
) -> Any:
    """
    Create a PyInstaller Analysis object.

    Args:
        script_path: Path to the main script
        datas: List of data files to include
        runtime_hook: Path to runtime hook file
        pathex: Additional paths to search for imports
        hiddenimports: List of hidden imports

    Returns:
        Analysis: PyInstaller Analysis object
    """
    return Analysis(
        [script_path],
        pathex=pathex or ['.'],
        binaries=[],
        datas=datas,
        hiddenimports=hiddenimports or [],
        runtime_hooks=[runtime_hook],
        excludes=[],
        hookspath=[],
        hooksconfig={},
        noarchive=False,
    )


def create_executable(
    analysis_obj: Any,
    pyz_obj: Any,
    name: str,
    icon_path: str,
    console: bool = False,
    onefile: bool = True,
) -> Any:
    """
    Create a PyInstaller EXE object.

    Args:
        analysis_obj: PyInstaller Analysis object
        pyz_obj: PyInstaller PYZ object
        name: Name of the executable
        icon_path: Path to icon file
        console: Whether to show console window
        onefile: Whether to create a single file executable

    Returns:
        EXE: PyInstaller EXE object
    """
    return EXE(
        pyz_obj,
        analysis_obj.scripts,
        analysis_obj.binaries,
        analysis_obj.datas,
        [],
        name=name,
        icon=icon_path,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=console,
        disable_windowed_traceback=False,
        argv_emulation=True,
        arguments=['--version', APP_VERSION],
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        onefile=onefile,
    )


def cleanup_additional_executables() -> None:
    """
    Remove all application executables except the launcher.
    """
    dist_path = Path('./dist')

    # List of base executable names to delete (all apps except launcher)
    executables_to_delete = list(APPS.keys())

    # Remove specified executables using wildcard matching
    for app_name in executables_to_delete:
        matching_files = list(dist_path.glob(f"{app_name}*"))
        for file_path in matching_files:
            print(f"Removing additional executable: {file_path}")
            file_path.unlink()


def ensure_dist_directory() -> None:
    """Ensure dist directory exists."""
    dist_path = Path('./dist')
    if not dist_path.exists():
        dist_path.mkdir(parents=True)


# ===== MAIN BUILD PROCESS =====

def build_all_apps():
    """Build all apps defined in the APPS dictionary."""
    # Create runtime hook for environment variables
    runtime_hook = create_runtime_hook()

    # Ensure dist directory exists
    ensure_dist_directory()

    # Store all built executables
    built_executables = {}

    # Build each app
    for app_name, app_config in APPS.items():
        print(f"Building {app_name}...")

        # Get the data paths function
        data_paths_func = globals()[app_config["data_paths_func"]]
        data_paths = data_paths_func()

        # Set up pathex
        pathex = ['.'] + app_config["extra_pathex"]

        # Create Analysis object
        analysis = create_analysis(
            app_config["script_path"],
            data_paths,
            runtime_hook,
            pathex=pathex,
            hiddenimports=app_config["hidden_imports"]
        )

        # Create PYZ object
        pyz = PYZ(analysis.pure)

        # Create EXE object
        exe = create_executable(
            analysis,
            pyz,
            app_config["name"],
            ICON_PATH,
            console=app_config["console"]
        )

        built_executables[app_name] = exe

    # Build launcher after all other apps are built
    print("Building launcher...")

    # Get the launcher data paths function
    launcher_data_paths_func = globals()[LAUNCHER_CONFIG["data_paths_func"]]
    launcher_data_paths = launcher_data_paths_func()

    # Create launcher Analysis object
    launcher_analysis = create_analysis(
        LAUNCHER_CONFIG["script_path"],
        launcher_data_paths,
        runtime_hook,
        pathex=['.'] + LAUNCHER_CONFIG["extra_pathex"],
        hiddenimports=LAUNCHER_CONFIG["hidden_imports"]
    )

    # Create launcher PYZ object
    launcher_pyz = PYZ(launcher_analysis.pure)

    # Create launcher EXE object
    launcher_exe = create_executable(
        launcher_analysis,
        launcher_pyz,
        LAUNCHER_CONFIG["name"],
        ICON_PATH,
        console=LAUNCHER_CONFIG["console"]
    )

    # Add launcher to built_executables
    built_executables["launcher"] = launcher_exe

    # Clean up additional executables, keeping only the launcher
    cleanup_additional_executables()

    return built_executables


# ===== EXECUTION STARTS HERE =====

def main():
    """Build all apps."""
    all_executables = build_all_apps()

    # Expose executables for PyInstaller
    for app_name, exe in all_executables.items():
        globals()[f"{app_name}_exe"] = exe

    return all_executables

# Expose executables to PyInstaller
all_executables = main()
for app_name, exe in all_executables.items():
    globals()[f"{app_name}_exe"] = exe
