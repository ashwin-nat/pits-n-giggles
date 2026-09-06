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
import os
import sys
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Any, ClassVar, Dict, Generic, Optional, TypeVar, get_args

from lib.child_proc_mgmt import (notify_parent_init_complete,
                                 report_ipc_port_from_child,
                                 report_pid_from_child)
from lib.config import PngSettings, load_config_from_json
from lib.error_status import PNG_LOST_CONN_TO_PARENT, PngError
from lib.ipc import PngAppId
from lib.logger import PngLogger, get_logger
from lib.version import get_version
from meta.meta import APP_NAME

from .args import SubsystemArgs, add_dataclass_args

# -------------------------------------- TYPES -------------------------------------------------------------------------

# A subsystem names its args dataclass as a type parameter - AsyncSubsystem[McpArgs] - which
# both types self.args and tells the base what to construct. One declaration, two jobs.
ArgsT = TypeVar("ArgsT", bound=SubsystemArgs)

# -------------------------------------- ENUMS -------------------------------------------------------------------------

class PubSubRole(Enum):
    """Which end of the pub/sub fabric a subsystem sits on.

    Every subsystem has at most one. The broker is NONE because it *is* the fabric rather
    than a participant in it.
    """

    NONE = auto()
    PUBLISHER = auto()
    SUBSCRIBER = auto()

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

class PngSubsystem(ABC, Generic[ArgsT]):
    """Base class for the child side of a launcher-managed subsystem.

    Owns everything the launcher's contract requires - argument parsing, the logger, config
    loading, the handshake tokens, the management IPC server and its three built-in handlers,
    the stats envelope and the entry-point exception funnel - so that a subsystem only has to
    fill in what is actually specific to it.

    Generic over its args dataclass, which a subsystem names in its class header:

        class McpSubsystem(AsyncSubsystem[McpArgs]):

    That single declaration both types self.args and tells the base what to construct.

    The parent side of this same contract lives in `apps/launcher/subsystems/base_mgr.py`
    (`PngAppMgrBase`). Changes here must not alter the wire contract with it.
    """

    # -------------------------------------- IDENTITY ------------------------------------------------------------------

    # Logger name and management IPC server name, e.g. "backend", "hud", "web"
    NAME: Optional[str] = None
    # argparse description suffix, e.g. "Realtime Telemetry Server"
    DESCRIPTION: Optional[str] = None
    # Resolved by __init_subclass__ from the type parameter - do NOT assign this by hand.
    # Subclass SubsystemArgs to add flags, then name the subclass as the type parameter; the
    # parser is built from its fields, so there is no add_args() hook.
    ARGS: ClassVar[type[SubsystemArgs]] = SubsystemArgs
    # Passed to load_config_from_json(fail_if_missing=)
    CONFIG_REQUIRED: bool = False
    # Whether the base emits the init-complete token once setup() returns. False for
    # subsystems that are only genuinely ready later - see notify_ready().
    READY_ON_SETUP_COMPLETE: bool = True
    # Management IPC heartbeat tuning. These were only ever pinned by the broker; the rest
    # took library defaults that happened to match.
    HEARTBEAT_TIMEOUT: float = 5.0
    MAX_MISSED_HEARTBEATS: int = 3

    # -------------------------------------- DATA PLANE ----------------------------------------------------------------
    # Opt-in. The base constructs whatever is declared here from settings, registers its
    # task/thread, and closes it once on_shutdown() has returned - so per-subsystem teardown
    # ordering is preserved. It never registers a route and never merges these objects' stats
    # into the payload: topic names, handler bodies and collect_stats() stay subsystem-owned.

    # Dealer identity on the router. Required when DEALER is True.
    APP_ID: Optional[PngAppId] = None
    # Which end of the pub/sub fabric this subsystem sits on. PUBLISHER populates
    # self.publisher, SUBSCRIBER populates self.subscriber; only ever one of the two.
    PUBSUB: PubSubRole = PubSubRole.NONE
    # Whether to build a router/dealer client, exposed as self.dealer
    DEALER: bool = False

    def __init_subclass__(cls, **kwargs) -> None:
        """Fail at import time if a subclass forgot to fill in the mandatory identity fields"""

        super().__init_subclass__(**kwargs)
        cls._resolve_args_cls()
        # __dict__ holds only what this class's own body defined, so this asks "did THIS class
        # say it is abstract?" - cls.ABSTRACT would also find a parent's True and wrongly let a
        # concrete subclass skip the check.
        if cls.__dict__.get("ABSTRACT", False):
            return
        missing = [name for name, value in (
            ("NAME", cls.NAME),
            ("DESCRIPTION", cls.DESCRIPTION),
        ) if value is None]
        if missing:
            raise TypeError(f"{cls.__name__} must define: {', '.join(missing)}")
        # A dealer connects to the router under an identity. Getting this wrong is a one-typo
        # bug with confusing symptoms, so it is a declaration rather than a call argument.
        if cls.DEALER and cls.APP_ID is None:
            raise TypeError(f"{cls.__name__} sets DEALER but no APP_ID")

    @classmethod
    def _resolve_args_cls(cls) -> None:
        """Set ARGS from the type parameter, e.g. AsyncSubsystem[McpArgs] -> McpArgs.

        A subclass that does not parameterize keeps whatever its parent resolved to, which for
        a subsystem with no extra flags is SubsystemArgs.
        """

        # cls.__dict__, NOT getattr: __orig_bases__ is inherited, so getattr on an
        # unparameterized subclass hands back the PARENT's SyncSubsystem[~ArgsT] and would
        # resolve to the TypeVar itself - after which _parse_args() would try to call it.
        for base in cls.__dict__.get("__orig_bases__", ()):
            params = get_args(base)
            # An unfilled parameter is the TypeVar, not a dataclass. That is what
            # SyncSubsystem[ArgsT] looks like: still generic, nothing to resolve.
            if params and not isinstance(params[0], TypeVar):
                cls.ARGS = params[0]
                return

    # Populated by _bootstrap(). Declared here rather than assigned None in __init__ so it
    # types as the subsystem's own args dataclass everywhere, instead of Optional.
    args: ArgsT

    def __init__(self) -> None:
        """Construct the subsystem. Nothing is booted until main() runs."""

        self.logger: Optional[PngLogger] = None
        self.settings: Optional[PngSettings] = None
        self.version: str = ""
        # The launcher's control channel, the pub/sub endpoints and the dealer are all built
        # by AsyncSubsystem / SyncSubsystem, which hold them privately and expose them through
        # properties at the concrete type.
        self._mgmt_ipc_enabled: bool = False
        self._ready_notified: bool = False

    # -------------------------------------- MUST IMPLEMENT ------------------------------------------------------------

    @abstractmethod
    def collect_stats(self) -> Dict[str, Any]:
        """Return this subsystem's stats body, which the base wraps in the standard envelope.

        Abstract even for a subsystem with nothing to report - returning {} explicitly is a
        stated decision, where an inherited default would silently serve an empty payload to
        the launcher's stats panel.

        Returns:
            Dict[str, Any]: Stats body
        """

    # -------------------------------------- MAY OVERRIDE --------------------------------------------------------------

    def make_logger(self, args: ArgsT) -> PngLogger:
        """Build this subsystem's logger.

        Args:
            args (ArgsT): Parsed args

        Returns:
            PngLogger: Logger. JSONL on stdout by default, which the launcher captures.
        """

        return get_logger(self.NAME, args.debug, jsonl=True)

    def should_run_mgmt_ipc(self, args: ArgsT) -> bool:  # pylint: disable=unused-argument
        """Whether this run talks to a launcher at all.

        Gates the management IPC server *and* every handshake token, because a subsystem with
        no parent has nobody to send them to - and for MCP's stdio transport, stdout belongs
        to the protocol, so a stray token would corrupt it.

        Args:
            args (ArgsT): Parsed args

        Returns:
            bool: True if managed by a launcher
        """

        return True

    def pre_boot(self, args: ArgsT) -> None:
        """Run before the logger exists, for anything the rest of the boot depends on.

        Paired with on_exit(), which is guaranteed to run in a finally.

        Args:
            args (ArgsT): Parsed args
        """

    def on_exit(self) -> None:
        """Undo whatever pre_boot() did. Runs in a finally, on every exit path.

        Named for when it runs, which is last: after run_forever()/the task gather has returned
        and after on_shutdown() has torn the subsystem down. It is not a pre-shutdown hook -
        on_shutdown() is that.
        """

    # -------------------------------------- BASE OWNED ----------------------------------------------------------------

    def notify_ready(self) -> None:
        """Tell the launcher this subsystem is up. Idempotent.

        Called automatically after setup() when READY_ON_SETUP_COMPLETE is True. Subsystems
        that are only genuinely usable later - once a socket is actually listening, or windows
        are actually shown - set that to False and call this themselves from the point that is
        true. The launcher only reaches AppState.RUNNING on this token, so emitting it early
        would be a lie it acts on.
        """

        if self._ready_notified or not self._mgmt_ipc_enabled:
            return
        self._ready_notified = True
        notify_parent_init_complete()

    def build_stats_response(self, _args: Optional[dict] = None) -> Dict[str, Any]:
        """Wrap collect_stats() in the envelope the launcher expects.

        Takes and ignores the command args, so it can be registered as the get-stats handler
        directly.

        Returns:
            Dict[str, Any]: {"status": "success", "stats": <collect_stats()>}
        """

        return {"status": "success", "stats": self.collect_stats()}

    def handle_heartbeat_missed(self, count: int) -> None:
        """Terminate immediately - this process has outlived its parent.

        Args:
            count (int): Number of consecutive missed heartbeats
        """

        self.logger.error(
            "Missed heartbeat %d times. This process has probably been orphaned. Terminating...", count)
        # os._exit required: child process must terminate immediately without
        # running atexit handlers or flushing stdio buffers from parent.
        os._exit(PNG_LOST_CONN_TO_PARENT)

    def report_mgmt_ipc_port(self, port: int) -> None:
        """Report the management IPC port to the launcher.

        Args:
            port (int): Port the management IPC server bound to
        """

        if self._mgmt_ipc_enabled:
            report_ipc_port_from_child(port)

    # -------------------------------------- BOOT ----------------------------------------------------------------------

    def _parse_args(self) -> ArgsT:
        """Build the parser from ARGS' fields and parse into an instance of it.

        argparse's dest names are the field names, so the namespace maps onto the dataclass
        without a translation table.

        Returns:
            ArgsT: Parsed args, of whatever type the class header named
        """

        parser = argparse.ArgumentParser(description=f"{APP_NAME} {self.DESCRIPTION}")
        add_dataclass_args(parser, self.ARGS)
        return self.ARGS(**vars(parser.parse_args()))

    def _bootstrap(self) -> None:
        """Parse args and stand up the logger, before anything that can meaningfully fail."""

        self.args = self._parse_args()
        self._mgmt_ipc_enabled = self.should_run_mgmt_ipc(self.args)
        self.pre_boot(self.args)
        self.logger = self.make_logger(self.args)
        if self._mgmt_ipc_enabled:
            report_pid_from_child()

    def _load_settings(self) -> None:
        """Load config. Split from _bootstrap so failures land inside the exception funnel."""

        self.version = get_version()
        self.settings = load_config_from_json(
            self.args.config_file, self.logger, fail_if_missing=self.CONFIG_REQUIRED)

    @abstractmethod
    def _run(self) -> None:
        """Drive this subsystem's main loop. Implemented by AsyncSubsystem / SyncSubsystem."""

    @classmethod
    def main(cls) -> None:
        """Entry point. Boots the subsystem, runs it, and funnels every exit path."""

        self = cls()
        self._bootstrap()
        try:
            self._load_settings()
            self._run()
        except KeyboardInterrupt:
            self.logger.info("Program interrupted by user.")
        except PngError as e:
            self.logger.exception("Terminating due to Error: %s with code %d", e, e.exit_code)
            sys.exit(e.exit_code)
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.exception("Error in main: %s", e)
            sys.exit(1)
        finally:
            self.on_exit()

        self.logger.info("%s subsystem exiting normally.", self.NAME)
