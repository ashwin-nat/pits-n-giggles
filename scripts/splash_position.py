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

"""Build-time patch that puts the splash screen on the monitor holding the mouse cursor.

PyInstaller always centres its splash on the *primary* monitor: the generated Tcl computes the
position from ``winfo screenwidth``/``winfo screenheight``, which on Windows report the primary
display only. On a multi-monitor sim rig that regularly means the splash appears on a screen the
user is not looking at.

There is no supported option for this - the Tcl script is generated internally by
``PyInstaller.building.splash_templates`` with no hook - so this module rewrites the two lines
that compute the position. Everything else in PyInstaller's script is left untouched, and the
patch is a targeted string replacement rather than a copy of the whole template, so upstream
changes to the canvas setup are inherited rather than shadowed.

Tk has no multi-monitor API. The monitor under the cursor is found by placing a fully transparent
throwaway window at the pointer and maximising it: Windows snaps a maximised window to the work
area of the monitor it is on, which can then be read back with ``winfo``. The whole thing is
wrapped in a Tcl ``catch`` so that any failure silently falls back to PyInstaller's
primary-monitor centring - the splash is cosmetic and must never be able to break startup.

Probing needs ``update idletasks``, which would otherwise let Tk map the splash window before the
script has positioned it. So ``.`` is withdrawn for the whole script and deiconified again as the
very last step. That ordering is load-bearing: mapping ``.`` early and then applying
``wm overrideredirect`` makes Windows recreate the window and silently discard the geometry, which
lands the splash at Tk's default cascade position instead of the monitor that was computed. Two
templates are therefore patched - the position block and the final ``raise``.

Used by ``scripts/png.spec``.
"""

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

from PyInstaller.building import splash_templates

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

#: The exact lines emitted by PyInstaller's splash_canvas_setup template that we replace. If a
#: PyInstaller upgrade changes these, the patch no-ops with a warning instead of silently
#: producing a splash that ignores the cursor.
_STOCK_POSITION = """set x_position [expr {int(0.5*($display_width - $image_width))}]
set y_position [expr {int(0.5*($display_height - $image_height))}]"""

#: Replacement Tcl. Keeps the stock computation as the fallback value, then tries to improve on it.
#:
#: '.' is withdrawn here and stays withdrawn until the end of the script (see _STOCK_RAISE), so
#: the 'update idletasks' calls below cannot map the splash before it has been positioned.
_CURSOR_MONITOR_POSITION = """set x_position [expr {int(0.5*($display_width - $image_width))}]
set y_position [expr {int(0.5*($display_height - $image_height))}]

# Prefer the monitor the mouse cursor is on over the primary one.
wm withdraw .
if {[catch {
    lassign [winfo pointerxy .] _png_px _png_py
    toplevel .png_probe
    wm attributes .png_probe -alpha 0.0
    wm geometry .png_probe 1x1+$_png_px+$_png_py
    update idletasks
    wm state .png_probe zoomed
    update idletasks
    set _png_mw [winfo width .png_probe]
    set _png_mh [winfo height .png_probe]
    set _png_mx [winfo x .png_probe]
    set _png_my [winfo y .png_probe]
    destroy .png_probe
    if {$_png_mw < $image_width || $_png_mh < $image_height} {
        error "probe geometry smaller than the splash image"
    }
    set _png_nx [expr {int($_png_mx + 0.5*($_png_mw - $image_width))}]
    set _png_ny [expr {int($_png_my + 0.5*($_png_mh - $image_height))}]
}]} {
    catch {destroy .png_probe}
} else {
    set x_position $_png_nx
    set y_position $_png_ny
}"""

#: PyInstaller's final template, and the same with the window brought back. '.' stays withdrawn
#: from the probe above until here, so wm overrideredirect/geometry are both applied while the
#: window is still unmapped - which is the only ordering Windows honours.
_STOCK_RAISE = "raise ."
_DEICONIFY_RAISE = "wm deiconify .\nraise ."

# -------------------------------------- PYINSTALLER INTERNALS ---------------------------------------------------------
#
# Every read of and write to PyInstaller's private template module goes through the four
# accessors below. They are one-liners on purpose: if a future PyInstaller renames or relocates
# these attributes, this is the only block that needs touching.

def _read_canvas_setup_tcl() -> str:
    """Return PyInstaller's Tcl that builds the splash canvas and computes its position.

    Returns:
        str: The current ``splash_canvas_setup`` template.
    """
    return splash_templates.splash_canvas_setup


def _write_canvas_setup_tcl(tcl: str) -> None:
    """Replace PyInstaller's canvas-setup Tcl.

    Args:
        tcl (str): The template to install in place of the current one.
    """
    splash_templates.splash_canvas_setup = tcl


def _read_raise_tcl() -> str:
    """Return PyInstaller's Tcl for the final "bring the splash to the front" step.

    Returns:
        str: The current ``raise_window`` template.
    """
    return splash_templates.raise_window


def _write_raise_tcl(tcl: str) -> None:
    """Replace PyInstaller's final raise Tcl.

    Args:
        tcl (str): The template to install in place of the current one.
    """
    splash_templates.raise_window = tcl

# -------------------------------------- PATCH STATE -------------------------------------------------------------------

def _is_already_patched(canvas_setup_tcl: str, raise_tcl: str) -> bool:
    """Check whether both templates already carry this module's replacements.

    Args:
        canvas_setup_tcl (str): Current canvas-setup template.
        raise_tcl (str): Current raise template.

    Returns:
        bool: True if there is nothing left to do.
    """
    return _CURSOR_MONITOR_POSITION in canvas_setup_tcl and _DEICONIFY_RAISE in raise_tcl


def _are_templates_recognised(canvas_setup_tcl: str, raise_tcl: str) -> bool:
    """Check that both templates still contain the stock text this module rewrites.

    Both halves are required. Patching only one would either leave the splash centred on the
    primary monitor or - far worse - leave it withdrawn and never shown at all.

    Args:
        canvas_setup_tcl (str): Current canvas-setup template.
        raise_tcl (str): Current raise template.

    Returns:
        bool: True if it is safe to patch.
    """
    return _STOCK_POSITION in canvas_setup_tcl and _STOCK_RAISE in raise_tcl


def _warn_templates_changed() -> None:
    """Tell the developer the patch was skipped, in the banner style png.spec already uses."""
    print(
        "=" * 80 + "\n"
        "png.spec: could not patch the splash screen position - PyInstaller's splash\n"
        "templates have changed. The splash will still work, but it will appear on the\n"
        "primary monitor instead of the one holding the mouse cursor.\n"
        "Update _STOCK_POSITION / _STOCK_RAISE in scripts/splash_position.py to match.\n"
        + "=" * 80
    )

# -------------------------------------- ENTRY POINT -------------------------------------------------------------------

def use_cursor_monitor_centring() -> bool:
    """Patch PyInstaller so the splash centres on the monitor holding the mouse cursor.

    Must be called before constructing the ``Splash`` target, which is when the Tcl script is
    generated. Safe to call more than once.

    Returns:
        bool: True if the patch was applied, False if PyInstaller's template no longer matches
            (in which case the stock primary-monitor centring stays in effect).
    """
    canvas_setup_tcl = _read_canvas_setup_tcl()
    raise_tcl = _read_raise_tcl()

    if _is_already_patched(canvas_setup_tcl, raise_tcl):
        return True

    if not _are_templates_recognised(canvas_setup_tcl, raise_tcl):
        _warn_templates_changed()
        return False

    _write_canvas_setup_tcl(canvas_setup_tcl.replace(_STOCK_POSITION, _CURSOR_MONITOR_POSITION))
    _write_raise_tcl(raise_tcl.replace(_STOCK_RAISE, _DEICONIFY_RAISE))
    return True
