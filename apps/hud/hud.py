# MIT License
#
# Copyright (c) [2024] [Ashwin Natarajan]
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

import ctypes
import sys
import threading
from argparse import Namespace
from typing import Any, Dict, Optional, override

from lib.error_status import PNG_ERROR_CODE_UNSUPPORTED_OS
from lib.ipc import PngAppId
from lib.subsystem import PubSubRole, SyncSubsystem

from .ipc.dealer import register_dealer_routes
from .ipc.mgmt import register_mgmt_routes
from .ipc.pubsub import register_subscriber_routes
from .ui.infra import OverlaysMgr

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

class HudSubsystem(SyncSubsystem):
    """The always-on-top in-game overlay.

    Renders broker telemetry into Qt overlay windows, and answers the launcher's overlay
    control commands. Windows-only - see entry_point().
    """

    NAME = "hud"
    DESCRIPTION = "HUD"
    # The HUD is only genuinely up once its overlay windows are shown, which happens inside the
    # Qt loop, well after setup() returns. WindowManager emits the token from there instead.
    READY_ON_SETUP_COMPLETE = False

    APP_ID = PngAppId.HUD
    PUBSUB = PubSubRole.SUBSCRIBER
    DEALER = True

    def __init__(self) -> None:
        """Construct the subsystem. Nothing is started until main() runs."""

        super().__init__()
        self.overlays_mgr: Optional[OverlaysMgr] = None
        self._winmm: Optional[Any] = None

    # -------------------------------------- LIFECYCLE -----------------------------------------------------------------

    @override
    def pre_boot(self, args: Namespace) -> None:
        """Request 1 ms system timer resolution so QTimer::PreciseTimer fires on time.

        Windows default is 15.6 ms, which causes frame-budget misses at 30 FPS.

        Args:
            args (Namespace): Parsed args
        """

        self._winmm = ctypes.windll.winmm
        self._winmm.timeBeginPeriod(1)

    @override
    def on_exit(self) -> None:
        """Hand the system timer resolution back. Runs on every exit path."""

        if self._winmm:
            self._winmm.timeEndPeriod(1)

    @override
    def setup(self) -> None:
        """Build the overlays and attach the three IPC surfaces to them."""

        self.overlays_mgr = OverlaysMgr(
            self.logger, self.settings, on_ready=self.notify_ready, debug=self.args.debug)

        register_subscriber_routes(self.subscriber, self.overlays_mgr)
        register_dealer_routes(self.dealer, self.overlays_mgr)
        register_mgmt_routes(self.mgmt, self.logger, self.overlays_mgr)

    @override
    def run_forever(self) -> None:
        """Run the Qt event loop. Returns once request_stop() quits it."""

        self.overlays_mgr.run()

    @override
    def request_stop(self) -> None:
        """Quit the Qt event loop so run_forever() returns.

        Called from the IPC server's thread. A Qt loop cannot watch shutdown_event the way the
        broker's run_forever() does, so it has to be told explicitly.

        Handed to a thread because quitting Qt from outside its own thread takes ~200ms to come
        back, and the IPC server only replies to the launcher once this returns. Teardown
        proper still happens on the main thread once run_forever() unblocks.
        """

        # No super() call: nothing in the HUD polls shutdown_event - its subscriber and dealer
        # threads are closed explicitly by the base - and _run() sets the event anyway before
        # on_shutdown(). Add it back if this subsystem ever grows a thread that watches it.
        threading.Thread(target=self.overlays_mgr.stop, daemon=True, name="HUD Qt Stop").start()

    @override
    def collect_stats(self) -> Dict[str, Any]:
        """Return overlay, window manager and ingress stats.

        Returns:
            Dict[str, Any]: Stats body
        """

        return {
            "overlays": self.overlays_mgr.get_overlay_stats(),
            "window_mgr": self.overlays_mgr.get_window_mgr_stats(),
            "ingress": {
                "dealer": self.dealer.get_stats(),
                "subscriber": self.subscriber.get_stats(),
            },
        }

    @override
    def on_shutdown(self, reason: str) -> None:
        """Nothing left to tear down.

        The Qt loop has already been quit by request_stop() - that is what let run_forever()
        return - and the base closes the subscriber and dealer once this returns.

        Args:
            reason (str): Why the shutdown was requested
        """

        self.logger.debug("HUD stopped. Reason: %s", reason)

# -------------------------------------- ENTRY POINT -------------------------------------------------------------------

def entry_point():
    """Entry point"""

    # Guarded here rather than behind a base-class flag: platform gating is not expected to
    # recur, and three lines in one file beat a capability that exists for a single case.
    if sys.platform != 'win32':
        sys.exit(PNG_ERROR_CODE_UNSUPPORTED_OS)

    HudSubsystem.main()
