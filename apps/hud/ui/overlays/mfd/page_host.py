# MIT License
#
# Copyright (c) [2026] [Ashwin Natarajan]
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

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

from typing import TYPE_CHECKING, Any, Callable, Dict, Iterable, Optional

from apps.hud.ui.overlays.base.base_overlay import BaseOverlay

if TYPE_CHECKING:
    # Deferred: importing MfdPageBase at module scope would force
    # apps.hud.ui.overlays.mfd.pages.__init__ to run, which imports
    # standalone_host.py, which imports this module - a real circular import,
    # not just a type-checking convenience. MfdPageBase is only ever used in
    # type hints here (duck-typed at runtime via get_handled_event_types()/
    # dispatch_event()), so it costs nothing to defer.
    from apps.hud.ui.overlays.mfd.pages.base_page import MfdPageBase

# -------------------------------------- TYPES -------------------------------------------------------------------------

ActivePageGetter = Callable[[], Optional["MfdPageBase"]]

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def register_page_event_bridge(host: BaseOverlay, event_type: str, get_active_page: ActivePageGetter) -> None:
    """Register a handler on host that forwards event_type to whichever page get_active_page()
    returns at delivery time.

    get_active_page is a zero-arg callable so the answer can change over time (MfdOverlay's
    carousel index moves; StandalonePageHost's is fixed).

    Lives here rather than as a method on MfdOverlay or StandalonePageHost because both hosts
    need the identical forwarding logic and neither is a natural home for the other's copy:
    MfdOverlay (the N-page carousel) importing from standalone_host.py (the exactly-one-page
    wrapper), or vice versa, would be a backwards dependency between two peer classes. A
    sibling module keeps the shared bridge dependency-free in either direction, and a plain
    function (over e.g. a mixin) avoids pulling MFD-page concepts like "active page" into
    BaseOverlay's inheritance chain for the other overlay types that never host pages.
    """
    @host.on_event(event_type)
    def _forward(data: Dict[str, Any], _et=event_type):
        page = get_active_page()
        if page is None:
            host.logger.warning("%s | Event '%s' received but no active page", host.OVERLAY_ID, event_type)
            return
        page.dispatch_event(_et, data)


def register_page_event_handlers(host: BaseOverlay, pages: Iterable["MfdPageBase"], get_active_page: ActivePageGetter) -> None:
    """Register a forwarding handler on host for every unique event type across pages.

    Shared by MfdOverlay and StandalonePageHost (see register_page_event_bridge for why
    this is a free function in its own module rather than a method on either of them).
    """
    all_event_types = set()
    for page in pages:
        all_event_types.update(page.get_handled_event_types())

    for event_type in all_event_types:
        register_page_event_bridge(host, event_type, get_active_page)

    host.logger.debug("%s | Registered %d page event handlers %s",
                      host.OVERLAY_ID, len(all_event_types), all_event_types)
