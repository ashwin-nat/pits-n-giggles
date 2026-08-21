# MIT License
#
# Copyright (c) [2025] [Ashwin Natarajan]
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# ----------------------------------------------------------------------------------------------------------------------

"""Helpers for the PyInstaller splash screen shown during startup of the frozen app.

The splash is configured in ``scripts/png.spec`` and only exists in a packaged build on Windows
and Linux. ``pyi_splash`` is injected by the PyInstaller bootloader, so it is absent when running
from source and on macOS (where PyInstaller does not support splash screens at all). Every call
site therefore has to tolerate the import failing, which is why that guard lives here once instead
of being repeated at each of the places that need to dismiss the splash.

Keep this module free of heavy imports: it is used from ``apps/launcher/__main__.py`` before Qt is
touched.
"""

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def splash_close() -> None:
    """Dismiss the startup splash screen, if one is showing.

    Safe to call unconditionally and more than once: it is a no-op when running from source, on
    macOS, or once the splash has already been closed.

    The splash is always-on-top, so this must be called before showing any window - including
    error dialogs on early-exit paths - or that window ends up buried underneath it.
    """
    try:
        import pyi_splash  # pyright: ignore[reportMissingModuleSource] # pylint: disable=import-outside-toplevel
        pyi_splash.close()
    except ImportError:
        # Not a frozen build, or a build without a splash screen (e.g. macOS).
        pass
    except (ConnectionError, RuntimeError):
        # The bootloader's IPC socket is unhealthy. Nothing useful to do; never block startup
        # over a cosmetic window.
        pass
