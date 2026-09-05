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

from pathlib import Path
from typing import Any, Dict, Optional, override

from lib.file_path import get_app_base_dir
from lib.ipc import PngAppId
from lib.subsystem import AsyncSubsystem, PubSubRole
from lib.version import get_version
from lib.web_server import ClientType

from .tasks import raceTableEmitTask, streamOverlayEmitTask
from .web_server import WebServer

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

class WebSubsystem(AsyncSubsystem):
    """The unified web app - serves the live dashboards, save-viewer and home page.

    Consumes broker telemetry over pub/sub and bridges browser pulls to the backend over the
    router/dealer channel.
    """

    NAME = "web"
    DESCRIPTION = "unified web app"
    CONFIG_REQUIRED = True
    # The web app is only genuinely up once its socket is listening, which happens well after
    # setup() returns. WebServer emits the token from its post-start callback instead - the
    # launcher only reaches AppState.RUNNING on that token, so sending it early would be a lie
    # it acts on.
    READY_ON_SETUP_COMPLETE = False

    APP_ID = PngAppId.WEB
    PUBSUB = PubSubRole.SUBSCRIBER
    DEALER = True

    def __init__(self) -> None:
        """Construct the subsystem. Nothing is started until main() runs."""

        super().__init__()
        self.web_server: Optional[WebServer] = None

    @override
    async def setup(self) -> None:
        """Build the web server and wire the subscriber, dealer and emit timers to it."""

        self.logger.info("Starting web app, version=%s", self.version)

        session_dir_setting = self.settings.Capture.session_dir_path
        session_dir = session_dir_setting if session_dir_setting.is_absolute() \
            else (get_app_base_dir() / session_dir_setting).resolve()
        viewer_dir = Path(__file__).resolve().parent.parent / "external" / "f1-save-viewer" / "dist"
        self.logger.debug("Session directory: %s", session_dir)
        self.logger.debug("Viewer directory: %s", viewer_dir)

        self.web_server = WebServer(
            settings=self.settings,
            ver_str=get_version(use_meta_version=True),
            logger=self.logger,
            session_dir=session_dir,
            viewer_dir=viewer_dir,
            on_ready=self.notify_ready,
            debug_mode=self.args.debug)
        self.add_task(self.web_server.run(), name="Web Server Task")

        # Broker telemetry. These only cache the latest payload - emission to browsers happens
        # on the web server's own timer below, not at broker cadence.
        @self.subscriber.route("race-table-update")
        async def _race_table_update(data: Dict[str, Any]) -> None:
            self.web_server.update_race_table_cache(data)

        @self.subscriber.route("stream-overlay-update")
        async def _stream_overlay_update(data: Dict[str, Any]) -> None:
            self.web_server.update_stream_overlay_cache(data)

        # The backend's unsolicited push. The dealer is also handed to the web server, which
        # uses it to bridge the /driver-info and /race-info pulls back to the backend.
        @self.dealer.route("frontend-update")
        async def _frontend_update(data: dict, _sender: str) -> None:
            await self.web_server.send_to_clients_of_type(
                event='frontend-update',
                data=data,
                client_type=ClientType.RACE_TABLE)

        self.web_server.set_dealer(self.dealer)

        refresh_interval = self.settings.Display.refresh_interval
        self.add_periodic(refresh_interval, raceTableEmitTask, self.web_server,
                          name="Race Table Emit Task")
        self.add_periodic(refresh_interval, streamOverlayEmitTask, self.web_server,
                          name="Stream Overlay Emit Task")

    @override
    def collect_stats(self) -> Dict[str, Any]:
        """Return web server, subscriber and dealer stats.

        Returns:
            Dict[str, Any]: Stats body
        """

        return {
            "web_server": self.web_server.get_stats(),
            "ipc_sub": self.subscriber.get_stats(),
            "dealer": self.dealer.get_stats(),
        }

    @override
    async def on_shutdown(self, reason: str) -> None:
        """Stop the web server. The base closes the subscriber and dealer after this returns.

        Args:
            reason (str): Why the shutdown was requested
        """

        self.logger.debug("Shutting down the web server. Reason: %s", reason)
        await self.web_server.stop()

# -------------------------------------- ENTRY POINT -------------------------------------------------------------------

def entry_point():
    """Entry point"""

    WebSubsystem.main()
