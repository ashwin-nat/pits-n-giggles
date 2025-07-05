import sys
import os

# When frozen, add _MEIPASS to sys.path so apps.* imports work
if getattr(sys, 'frozen', False):
    meipass = getattr(sys, '_MEIPASS', None)
    if meipass and os.path.isdir(meipass):
        sys.path.insert(0, meipass)
    else:
        print("[__main__.py] Warning: _MEIPASS not set or invalid")

if __name__ == "__main__":
    print("in __main__.py")

    try:
        from apps.launcher.launcher import entry_point
    except Exception as e:
        print(f"[__main__.py] Failed to import launcher: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    entry_point()
