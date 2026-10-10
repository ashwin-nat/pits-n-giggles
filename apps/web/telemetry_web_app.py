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

from dataclasses import dataclass
import signal
import sys
from pathlib import Path
from typing import Any, Dict, override

from lib.error_status import PNG_ERROR_CODE_HTTP_PORT_IN_USE
from lib.file_path import get_app_base_dir
from lib.logger import PngLogger, get_logger
from lib.subsystem import (AsyncSubsystem, PngSubsysId, PubSubRole, SubsystemArgs,
                           arg, run_subsystem)
from lib.version import get_version
from lib.web_server import ClientType

from .tasks import raceTableEmitTask, streamOverlayEmitTask
from .web_server import WebServer

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

@dataclass(frozen=True)
class WebArgs(SubsystemArgs):
    """The web app's flags, on top of the base --config-file and --debug."""

    headless: bool = arg(False, "Run without a launcher or live data; serves the save-viewer only")
    log_file: str = arg("png_web_headless.log", "Log file name (headless only)")

class WebSubsystem(AsyncSubsystem[WebArgs]):
    """The unified web app - serves the live dashboards, save-viewer and home page.

    Consumes broker telemetry over pub/sub and bridges browser pulls to the backend over the
    router/dealer channel. With --headless it runs standalone: no launcher, no broker, no
    backend, just the save-viewer served from the session directory. The config file must
    already exist (see apps/generate_default_config.py).
    """

    CONFIG_REQUIRED = True
    # The web app is only genuinely up once its socket is listening, which happens well after
    # construction returns. WebServer emits the token from its post-start callback instead - the
    # launcher only reaches AppState.RUNNING on that token, so sending it early would be a lie
    # it acts on.
    READY_ON_START = False

    SUBSYS_ID = PngSubsysId.WEB
    PUBSUB = PubSubRole.SUBSCRIBER
    DEALER = True

    PROFILE = False

    @override
    def should_run_mgmt_ipc(self) -> bool:
        """Headless runs have no launcher to handshake with."""

        return not self.args.headless

    @override
    def should_run_data_plane(self) -> bool:
        """Headless runs have no broker or backend to talk to."""

        return not self.args.headless

    @override
    def make_logger(self) -> PngLogger:
        """JSONL on stdout is the launcher's channel; headless logs plain text to a file."""

        if self.args.headless:
            return get_logger(
                str(self.SUBSYS_ID), self.args.debug, jsonl=False, file_path=self.args.log_file)
        return super().make_logger()

    @override
    def on_exit(self) -> None:
        """Tell a headless user the server is down, whichever way it got there."""

        if self.args.headless and self._headless_started:
            print("Web server stopped.", flush=True)

    @override
    def main(self) -> None:
        """Run, and tell a headless user on stderr when the port is taken (logs go to a file)."""

        try:
            super().main()
        except SystemExit as e:
            if self.args.headless and e.code == PNG_ERROR_CODE_HTTP_PORT_IN_USE:
                net = self.settings.Network
                print(f"Error: cannot start, port {net.server_port} on {net.bind_address} is already in use.\n"
                      "Stop the other process or change Network.server_port in the config file.",
                      file=sys.stderr, flush=True)
            raise

    def __init__(self) -> None:
        """Build the web server and wire the subscriber, dealer and emit timers to it."""

        super().__init__()
        self._headless_started = False
        self.logger.info("Starting web app, version=%s", self.version)

        session_dir_setting = self.settings.Capture.session_dir_path
        session_dir = session_dir_setting if session_dir_setting.is_absolute() \
            else (get_app_base_dir() / session_dir_setting).resolve()
        viewer_dir = Path(__file__).resolve().parent.parent / "external" / "f1-save-viewer" / "dist"
        analyzer_dir = Path(__file__).resolve().parent.parent / "lap-analyzer" / "dist"
        self.logger.debug("Session directory: %s", session_dir)
        self.logger.debug("Viewer directory: %s", viewer_dir)
        self.logger.debug("Analyzer directory: %s", analyzer_dir)

        self.web_server = WebServer(
            settings=self.settings,
            ver_str=get_version(use_meta_version=True),
            logger=self.logger,
            session_dir=session_dir,
            viewer_dir=viewer_dir,
            analyzer_dir=analyzer_dir,
            on_ready=self._announce_headless if self.args.headless else self.notify_ready,
            debug_mode=self.args.debug,
            headless=self.args.headless)
        self.add_task(self._serve_headless() if self.args.headless else self.web_server.run(),
                      name="Web Server Task")
        if self.args.headless:
            return

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

    async def _serve_headless(self) -> None:
        """Run the server, then tear down. No launcher exists to ask for it, and uvicorn
        consumes SIGINT without ending the process."""

        # Uvicorn re-raises SIGTERM on exit with whatever handler it replaced. The default
        # kills the process before the exit funnel runs, so install one that doesn't.
        signal.signal(signal.SIGTERM, lambda *_: self.request_shutdown("SIGTERM"))
        try:
            await self.web_server.run()
        finally:
            self.request_shutdown("web server exited")

    def _announce_headless(self) -> None:
        """Print the startup banner to stdout; the log file is not where a user looks first."""

        self._headless_started = True
        print(f"Pits n' Giggles web server started (headless), version {self.version}\n"
              f"  Config: {Path(self.args.config_file).resolve()}\n"
              f"  Log:    {Path(self.args.log_file).resolve()}\n"
              "Press Ctrl+C to stop.", flush=True)

    @override
    def collect_stats(self) -> Dict[str, Any]:
        """Return web server, subscriber and dealer stats.

        Returns:
            Dict[str, Any]: Stats body
        """

        if self.args.headless:
            return {"web_server": self.web_server.get_stats()}
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

    run_subsystem(WebSubsystem)
