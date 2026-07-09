"""Lint all QML files under apps/hud using Qt's qmllint.

Invokes the real Qt qmllint binary bundled inside the PySide6 package
directory (PySide6/qmllint[.exe]) rather than the `pyside6-qmllint`
console-script wrapper installed on PATH. On Windows that wrapper is built
without an attached console and reports its output via a blocking message
box instead of stdout/stderr, which hangs any non-interactive invocation.
"""
import subprocess
import sys
from pathlib import Path

import PySide6

QML_ROOT = Path(__file__).resolve().parent.parent / "apps" / "hud"


def find_qmllint() -> Path:
    pyside_dir = Path(PySide6.__file__).resolve().parent
    binary_name = "qmllint.exe" if sys.platform == "win32" else "qmllint"
    qmllint_path = pyside_dir / binary_name
    if not qmllint_path.is_file():
        raise FileNotFoundError(f"qmllint binary not found at {qmllint_path}")
    return qmllint_path


def main() -> int:
    if len(sys.argv) > 1:
        qml_files = [Path(arg).resolve() for arg in sys.argv[1:]]
    else:
        qml_files = sorted(QML_ROOT.rglob("*.qml"))

    if not qml_files:
        print(f"No .qml files found under {QML_ROOT}")
        return 0

    qmllint = find_qmllint()
    result = subprocess.run(
        [str(qmllint), "--max-warnings", "0", *[str(f) for f in qml_files]],
        stdin=subprocess.DEVNULL,
    )
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
