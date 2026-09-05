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

import argparse
import asyncio
import logging
import os
import sys
from typing import Any, Dict, Optional, override

from lib.ipc import PngAppId
from lib.logger import PngLogger, get_logger
from lib.subsystem import AsyncSubsystem, PubSubRole

from .mcp_server import MCPBridge
from .subscriber import McpSubscriber

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

# How long the data stream may go quiet before the subscriber reports itself disconnected
WDT_TIMEOUT_SEC = 10.0

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

class McpSubsystem(AsyncSubsystem):
    """Exposes live telemetry to MCP clients as tools.

    The only subsystem that also runs unmanaged. With a launcher it serves HTTP and speaks the
    full handshake; standalone it serves stdio, where stdout belongs to the MCP protocol and
    nothing else may be written to it - see should_run_mgmt_ipc(). Either way it consumes broker
    telemetry over pub/sub and pulls detail from the backend over the router/dealer channel.
    """

    NAME = "mcp"
    DESCRIPTION = "MCP server"
    CONFIG_REQUIRED = True
    # The HTTP transport is only genuinely up once MCPBridge has bound its port, which happens
    # inside run(), after setup() returns. A port conflict raises from there, so notifying early
    # would tell the launcher RUNNING about a process that is about to die. MCPBridge emits the
    # token itself once the bind succeeds. In stdio mode notify_ready() is a no-op anyway.
    READY_ON_SETUP_COMPLETE = False

    APP_ID = PngAppId.MCP
    PUBSUB = PubSubRole.SUBSCRIBER
    DEALER = True

    def __init__(self) -> None:
        """Construct the subsystem. Nothing is started until main() runs."""

        super().__init__()
        self.mcp_bridge: Optional[MCPBridge] = None
        self.mcp_subscriber: Optional[McpSubscriber] = None
        self._mcp_task: Optional[asyncio.Task] = None

    # -------------------------------------- BOOT ----------------------------------------------------------------------

    @override
    def add_args(self, parser: argparse.ArgumentParser) -> None:
        """Add the MCP-specific arguments. --config-file and --debug are pre-added.

        --log-file and --wd have no callers in this repo: they are part of the contract with the
        user's MCP client config, so their names and defaults are fixed.

        Args:
            parser (argparse.ArgumentParser): Parser to extend
        """

        parser.add_argument("--managed", action="store_true",
                            help="Indicates if process is managed by parent")
        parser.add_argument("--log-file", type=str, default="png_mcp_stdio.log",
                            help="Log file name")
        parser.add_argument("--wd", type=str, default=None, help="Working directory")

    @override
    def should_run_mgmt_ipc(self, args: argparse.Namespace) -> bool:
        """Whether a launcher spawned this run.

        Gates the management IPC server and all three handshake tokens. Unmanaged runs speak
        stdio, where stdout carries the MCP protocol - a stray token would corrupt it.

        Args:
            args (argparse.Namespace): Parsed args

        Returns:
            bool: True if launcher-managed
        """

        return args.managed

    @override
    def pre_boot(self, args: argparse.Namespace) -> None:
        """Move to the requested working directory and check the config is there.

        Both report failure on stderr and exit, because neither the logger nor a parent exists
        yet - and for an unmanaged run stderr stays the only channel the MCP client surfaces.

        Args:
            args (argparse.Namespace): Parsed args
        """

        if args.wd:
            try:
                os.chdir(args.wd)
            except FileNotFoundError:
                print(f"Working directory does not exist: {args.wd}", file=sys.stderr)
                sys.exit(1)
            except NotADirectoryError:
                print(f"Not a directory: {args.wd}", file=sys.stderr)
                sys.exit(1)

        # CONFIG_REQUIRED makes load_config_from_json raise, but that lands in the base's funnel
        # and goes to the logger - which for an unmanaged run is a file nobody is watching.
        if not args.managed and not os.path.exists(args.config_file):
            print(f"Fatal: config file not found: {args.config_file}. "
                  f"Run the pits n giggles launcher first. CWD: {os.getcwd()}", file=sys.stderr)
            sys.exit(1)

    @override
    def make_logger(self, args: argparse.Namespace) -> PngLogger:
        """Build the logger, and quieten the MCP libraries.

        Managed runs emit JSONL on stdout for the launcher to capture. Unmanaged runs cannot
        touch stdout at all, so they log to a file instead.

        Args:
            args (argparse.Namespace): Parsed args

        Returns:
            PngLogger: Logger
        """

        # TODO: make rotating logging configurable
        if args.managed:
            logger = get_logger(self.NAME, args.debug, jsonl=True)
        else:
            logger = get_logger(self.NAME, args.debug, jsonl=False, file_path=args.log_file)

        logging.getLogger("mcp.server").setLevel(logging.WARNING)
        logging.getLogger("mcp.client").setLevel(logging.WARNING)
        return logger

    # -------------------------------------- LIFECYCLE -----------------------------------------------------------------

    @override
    async def setup(self) -> None:
        """Build the MCP bridge and attach the watchdog-backed subscriber to the data stream."""

        transport = "http" if self.args.managed else "stdio"
        self.logger.info("Starting MCP server, version %s transport %s...", self.version, transport)

        self.mcp_subscriber = McpSubscriber(self.subscriber, timeout=WDT_TIMEOUT_SEC)
        self.add_task(self.mcp_subscriber.m_wdt.run(), name="IPC Watchdog Task")

        self.mcp_bridge = MCPBridge(
            dealer=self.dealer,
            logger=self.logger,
            version=self.version,
            transport=transport,
            on_ready=self.notify_ready,
            port=self.settings.MCP.mcp_http_port,
        )
        # Held because run() has no cooperative exit - both transports block until cancelled.
        self._mcp_task = self.add_task(self.mcp_bridge.run(), name="MCP Server Task")

    @override
    def collect_stats(self) -> Dict[str, Any]:
        """Return subscriber, MCP and dealer stats.

        Returns:
            Dict[str, Any]: Stats body
        """

        return {
            "INGRESS": self.subscriber.get_stats(),
            "MCP": self.mcp_bridge.get_stats(),
            "DEALER": self.dealer.get_stats(),
        }

    @override
    async def on_shutdown(self, reason: str) -> None:
        """Stop the watchdog and the MCP server. The base closes the sockets after this returns.

        Args:
            reason (str): Why the shutdown was requested
        """

        self.logger.info("Shutting down MCP. Reason: %s", reason)
        self.mcp_subscriber.m_wdt.stop()
        self._mcp_task.cancel()

# -------------------------------------- ENTRY POINT -------------------------------------------------------------------

def entry_point():
    """Entry point"""

    McpSubsystem.main()
