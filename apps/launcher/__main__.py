import os
import sys
import runpy

# --------------------------------------------------------------------------------------------------
# [Block 1] Frozen mode setup (PyInstaller bootstrapping)
# --------------------------------------------------------------------------------------------------
# If running from a PyInstaller-built EXE, sys._MEIPASS points to the unpacked temp dir.
# We add this to sys.path so that imports like 'apps.*' work as expected.

if getattr(sys, 'frozen', False):
    meipass = getattr(sys, '_MEIPASS', None)
    if meipass and os.path.isdir(meipass):
        sys.path.insert(0, meipass)
    else:
        print("[__main__.py] Warning: _MEIPASS not set or invalid")


# --------------------------------------------------------------------------------------------------
# [Block 2] Submodule dispatcher (run subsystems via --module)
# --------------------------------------------------------------------------------------------------
# Enables running subsystems like:
#   pits_n_giggles.exe --module apps.backend
#   pits_n_giggles.exe --module apps.save_viewer
#
# We rewrite sys.argv and use runpy to launch the target module.

if getattr(sys, 'frozen', False) and '--module' in sys.argv:
    idx = sys.argv.index('--module')
    module = sys.argv[idx + 1]
    args = sys.argv[idx + 2:]

    sys.path.insert(0, os.path.join(sys._MEIPASS))
    sys.argv = [module] + args

    try:
        runpy.run_module(module, run_name="__main__")
    # pylint: disable=broad-exception-caught
    except Exception as e:
        print(f"[__main__.py] Error launching module {module}: {e}")
        import traceback
        traceback.print_exc()
    sys.exit(0)


# --------------------------------------------------------------------------------------------------
# [Block 3] Force PyInstaller to include subsystem __main__.py files
# --------------------------------------------------------------------------------------------------
# PyInstaller won't include these unless we explicitly reference them.
# This block is never executed, but it's scanned by PyInstaller's static analysis.
# pylint: disable=using-constant-test
# pylint: disable=unused-import
if False:
    import apps.backend.__main__
    import apps.save_viewer.__main__


# --------------------------------------------------------------------------------------------------
# [Block 4] Main launcher entry point (only runs if not in --module mode)
# --------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        from apps.launcher.launcher import entry_point
    # pylint: disable=broad-exception-caught
    except Exception as e:
        print(f"[__main__.py] Failed to import launcher: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    entry_point()
