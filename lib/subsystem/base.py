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
from types import ModuleType
from typing import (Any, ClassVar, Dict, Generic, NoReturn, Optional, TypeVar,
                    get_args)

from lib.child_proc_mgmt import (notify_parent_init_complete,
                                 report_ipc_port_from_child,
                                 report_pid_from_child)
from lib.config import PngSettings, load_config_from_json
from lib.error_status import PNG_LOST_CONN_TO_PARENT, PngError
from lib.logger import PngLogger, get_logger
from lib.version import get_version

from .args import SubsystemArgs, add_dataclass_args
from .identity import PngSubsysId
from .profiling import start_profiler, stop_profiler

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

    # Which subsystem this is. The single identity declaration: the logger name, the management
    # IPC server name, the argparse description and - when DEALER is set - the ZMQ identity all
    # come off it, so they cannot drift apart or be filled in inconsistently. UNKNOWN rather
    # than None, so every reader gets a PngSubsysId without narrowing an Optional first.
    SUBSYS_ID: PngSubsysId = PngSubsysId.UNKNOWN
    # Resolved by __init_subclass__ from the type parameter - do NOT assign this by hand.
    # Subclass SubsystemArgs to add flags, then name the subclass as the type parameter; the
    # parser is built from its fields, so there is no add_args() hook.
    ARGS: ClassVar[type[SubsystemArgs]] = SubsystemArgs
    # Passed to load_config_from_json(fail_if_missing=)
    CONFIG_REQUIRED: bool = False
    # Whether the base emits the init-complete token as soon as the run starts. False for
    # subsystems that are only genuinely ready later - see notify_ready().
    READY_ON_START: bool = True
    # Dev aid. Every concrete subsystem restates this as False next to its other class vars, so
    # turning a profile on is a one-word edit in the file you are already reading; set it here
    # instead to cover all five at once.
    PROFILE: bool = False

    # -------------------------------------- DATA PLANE ----------------------------------------------------------------
    # Opt-in. The base constructs whatever is declared here from settings, registers its
    # task/thread, and closes it once on_shutdown() has returned - so per-subsystem teardown
    # ordering is preserved. It never registers a route and never merges these objects' stats
    # into the payload: topic names, handler bodies and collect_stats() stay subsystem-owned.

    # Which end of the pub/sub fabric this subsystem sits on. PUBLISHER populates
    # self.publisher, SUBSCRIBER populates self.subscriber; only ever one of the two.
    PUBSUB: PubSubRole = PubSubRole.NONE
    # Whether to build a router/dealer client, exposed as self.dealer
    DEALER: bool = False

    def __init_subclass__(cls, **kwargs) -> None:
        """Fail at import time if a subclass did not say which subsystem it is"""

        super().__init_subclass__(**kwargs)
        cls._resolve_args_cls()
        # __dict__ holds only what this class's own body defined, so this asks "did THIS class
        # say it is abstract?" - cls.ABSTRACT would also find a parent's True and wrongly let a
        # concrete subclass skip the check.
        if cls.__dict__.get("ABSTRACT", False):
            return
        if cls.SUBSYS_ID is PngSubsysId.UNKNOWN:
            raise TypeError(f"{cls.__name__} must define: SUBSYS_ID")

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

    def __init__(self) -> None:
        """Boot the subsystem: command line, then logger, then config.

        Takes no arguments, so a subsystem is constructed the same way everywhere -
        BackendSubsystem().main(). Everything it needs, it reads.

        By the time this returns, self.args, self.logger and self.settings are all populated,
        so a subclass's own __init__ body can build from any of them. What it still cannot
        reach are the IPC handles: those bind sockets and report a port to the launcher, which
        is not constructor work, and they are built later from the settings loaded here.

        Four hooks are called from here - pre_boot(), make_logger(), should_run_mgmt_ipc(), and
        on_exit() if the config load fails. All four therefore run BEFORE the subclass's own
        __init__ body, so an override must keep to class vars and to self.args / self.logger,
        and whatever one of them sets must not be assigned over further down. HudSubsystem is
        the worked example: its _winmm is a class attribute for exactly this reason.
        """

        # First, so the profile covers the whole boot - which is now most of the work.
        self._profiler: Optional[ModuleType] = start_profiler(self.PROFILE)

        self.args: ArgsT = self._parse_args()
        # The launcher's control channel, the pub/sub endpoints and the dealer are all built
        # by AsyncSubsystem / SyncSubsystem, which hold them privately and expose them through
        # properties at the concrete type.
        self._mgmt_ipc_enabled: bool = self.should_run_mgmt_ipc()
        self._ready_notified: bool = False

        self.pre_boot()
        self.logger: PngLogger = self.make_logger()
        if self._mgmt_ipc_enabled:
            report_pid_from_child()

        # Config is the boot step most likely to fail, and a bad file is a user problem rather
        # than a crash - so it is reported and exited rather than thrown. It is handled here
        # rather than in run_subsystem() because only here is the logger known to exist and
        # pre_boot() known to have run.
        try:
            self.version: str = get_version()
            self.settings: PngSettings = load_config_from_json(
                self.args.config_file, self.logger, fail_if_missing=self.CONFIG_REQUIRED)
        except Exception as e:  # pylint: disable=broad-exception-caught
            self._report_fatal(e)

    def _report_fatal(self, e: BaseException) -> NoReturn:
        """Report a boot failure and exit with the code the launcher expects.

        The launcher maps a child's exit code to a dialog - PngTelemetryPortInUseError's 102
        becomes "UDP port in use" naming the setting to change. Letting the exception escape
        instead would exit 1, which is the generic "Unknown" branch.

        Call only once the logger exists and pre_boot() has run - the config load is the one
        step that qualifies. Anything failing earlier than that has nothing to report through
        and nothing to undo, and anything later is run_subsystem()'s to catch.

        Args:
            e (BaseException): The failure

        Raises:
            SystemExit: Always
        """

        self.logger.exception("Boot failed: %s", e)
        self.on_exit()
        stop_profiler(self._profiler, str(self.SUBSYS_ID), self.logger)
        sys.exit(e.exit_code if isinstance(e, PngError) else 1)

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

    def make_logger(self) -> PngLogger:
        """Build this subsystem's logger.

        Called from __init__, so self.args is set but nothing else is.

        Returns:
            PngLogger: Logger. JSONL on stdout by default, which the launcher captures.
        """

        return get_logger(str(self.SUBSYS_ID), self.args.debug, jsonl=True)

    def should_run_mgmt_ipc(self) -> bool:
        """Whether this run talks to a launcher at all.

        Gates the management IPC server *and* every handshake token, because a subsystem with
        no parent has nobody to send them to - and for MCP's stdio transport, stdout belongs
        to the protocol, so a stray token would corrupt it.

        Called from __init__, so self.args is set but nothing else is - not even the logger.

        Returns:
            bool: True if managed by a launcher
        """

        return True

    def pre_boot(self) -> None:
        """Run before the logger exists, for anything the rest of the boot depends on.

        Called from __init__, so self.args is set but nothing else is. Paired with on_exit(),
        which is guaranteed to run in a finally.
        """

    def on_exit(self) -> None:
        """Undo whatever pre_boot() did. Runs on every exit path.

        Named for when it runs, which is last: after run_forever()/the task gather has returned
        and after on_shutdown() has torn the subsystem down. It is not a pre-shutdown hook -
        on_shutdown() is that.

        The one exception to "last" is a failed config load, which __init__ reports and exits
        from - so this can also run before the subclass's own __init__ body has, and must not
        assume anything that body sets exists.
        """

    # -------------------------------------- BASE OWNED ----------------------------------------------------------------

    def notify_ready(self) -> None:
        """Tell the launcher this subsystem is up. Idempotent.

        Called automatically when the run starts, if READY_ON_START is True. Subsystems
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

        parser = argparse.ArgumentParser(description=str(self.SUBSYS_ID))
        add_dataclass_args(parser, self.ARGS)
        return self.ARGS(**vars(parser.parse_args()))

    @abstractmethod
    def _run(self) -> None:
        """Drive this subsystem's main loop. Implemented by AsyncSubsystem / SyncSubsystem."""

    def _exit_smoke_ok(self) -> NoReturn:
        """Construction succeeded. Report and leave without running anything.

        os._exit, not sys.exit, on purpose - so the flushes are mandatory. By this point the
        constructor has left live daemon threads (the broker's xsub/xpub and router threads),
        a QApplication with overlay windows that never had an event loop (HUD), and
        registered-but-never-awaited coroutines in self._tasks (every AsyncSubsystem). Unwinding
        normally would emit "coroutine was never awaited" warnings and run Qt destructors for a
        loop that never ran. handle_heartbeat_missed() takes the same hard exit for the same
        reason.
        """

        self.logger.info("Smoke test: %s constructed successfully", self.SUBSYS_ID)
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(0)

    def main(self) -> None:
        """Run until shutdown, funnelling every exit path.

        The constructor has already booted the subsystem, which is what makes this funnel able
        to report at all: it is the step that produced the logger.
        """

        try:
            if self.args.smoke_test:
                self._exit_smoke_ok()   # NoReturn
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
            stop_profiler(self._profiler, str(self.SUBSYS_ID), self.logger)

        self.logger.info("%s subsystem exiting normally.", self.SUBSYS_ID)

# -------------------------------------- ENTRY POINT -------------------------------------------------------------------

def run_subsystem(cls: type[PngSubsystem]) -> None:
    """Construct a subsystem and run it. The whole body of an entry point.

    Construction is inside the try on purpose. A subsystem binds its ports there - the
    backend's UDP socket, the broker's XSUB/XPUB/ROUTER - and a conflict raises a PngError
    carrying the exit code the launcher turns into an actionable dialog ("UDP port in use",
    and which setting to change). main() cannot cover that: it only starts once construction
    has already returned, so an escaped PngError would exit 1 and land in the launcher's
    generic "Unknown" branch instead.

    Nothing is logged here. There is no instance to log through when construction is what
    failed, and the sites that raise these errors already log before raising.

    Args:
        cls (type[PngSubsystem]): The subsystem to run
    """

    try:
        cls().main()
    except PngError as e:
        sys.exit(e.exit_code)
