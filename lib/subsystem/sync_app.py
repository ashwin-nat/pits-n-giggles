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

import threading
from abc import abstractmethod
from typing import Any, Callable, Dict, List, Optional

from lib.ipc import IpcDealerClient, IpcServerSync, IpcSubscriberSync

from .base import MgmtIpcHandle, PngSubsystem, PubSubRole

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

# How long to wait for a registered thread to wind up before giving up on it
THREAD_JOIN_TIMEOUT_SEC = 3.0

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

class SyncSubsystem(PngSubsystem):
    """A subsystem whose main loop is blocking rather than an event loop.

    The subsystems in this shape - the broker and the Qt HUD - start their own daemon threads
    from their own classes, so the base only holds handles in order to join them on teardown.
    """

    ABSTRACT = True

    def __init__(self) -> None:
        """Construct the subsystem. Nothing is started until main() runs."""

        super().__init__()
        self.shutdown_event: threading.Event = threading.Event()
        self._threads: List[threading.Thread] = []
        self._shutdown_reason: str = "N/A"

        # Built by the base before setup() runs, per the PUBSUB / DEALER declarations.
        # There is no sync publisher, so there is no self.publisher to match AsyncSubsystem's.
        self.subscriber: Optional[IpcSubscriberSync] = None
        self.dealer: Optional[IpcDealerClient] = None
        self._mgmt_server: Optional[IpcServerSync] = None

    # -------------------------------------- MUST IMPLEMENT ------------------------------------------------------------

    @abstractmethod
    def setup(self) -> None:
        """Build this subsystem's objects and register its threads."""

    @abstractmethod
    def run_forever(self) -> None:
        """Block until this subsystem is done - the Qt event loop, or a wait on shutdown_event.

        Returns when the subsystem should shut down.
        """

    @abstractmethod
    def on_shutdown(self, reason: str) -> None:
        """Tear this subsystem down. The base has already set self.shutdown_event.

        Abstract even when there is nothing to do, so that "this subsystem has nothing to tear
        down" is a stated decision in the file rather than an absence someone has to confirm.

        Args:
            reason (str): Why the shutdown was requested
        """

    # -------------------------------------- MAY OVERRIDE --------------------------------------------------------------

    def request_stop(self) -> None:
        """Break out of run_forever(). Called from the IPC server's thread, not the main one.

        The default sets shutdown_event, which is all a run_forever() that waits on that event
        needs - the broker's does exactly that, and is currently its only waiter. Override when
        the main loop is something else - a Qt event loop, say - that has to be told to quit.

        An override only needs to call super() if something actually polls the event: _run()'s
        finally sets it regardless, before on_shutdown(), so calling it here just sets it
        earlier. The HUD skips it for that reason; a subsystem with threads watching the event
        would want it.

        Must not block: the IPC server only replies to the launcher once its shutdown handler
        returns, and the teardown proper happens in on_shutdown() once run_forever() has
        returned on the main thread.
        """

        self.shutdown_event.set()

    # -------------------------------------- THREAD REGISTRY -----------------------------------------------------------

    def add_thread(self, thread: threading.Thread) -> threading.Thread:
        """Register an already-started thread for join-on-teardown.

        Args:
            thread (threading.Thread): Running thread

        Returns:
            threading.Thread: The same thread, for convenience
        """

        self._threads.append(thread)
        return thread

    # -------------------------------------- MANAGEMENT IPC ------------------------------------------------------------

    def _build_mgmt_ipc(self) -> None:
        """Stand up the management IPC server and wire the three base-owned handlers."""

        self.logger.debug("Starting IPC server")
        server = IpcServerSync(
            name=self.NAME,
            max_missed_heartbeats=self.MAX_MISSED_HEARTBEATS,
            heartbeat_timeout=self.HEARTBEAT_TIMEOUT,
            logger=self.logger,
        )
        self._mgmt_server = server
        self.mgmt = MgmtIpcHandle(server)
        self.report_mgmt_ipc_port(server.port)
        self.logger.debug("Started IPC server on port %d", server.port)

        @server.on_heartbeat_missed
        def _heartbeat_missed(count: int) -> None:
            self.handle_heartbeat_missed(count)

        @server.on_shutdown
        def _shutdown(args: dict) -> Dict[str, Any]:
            reason = args.get("reason", "N/A")
            self.logger.info("Received shutdown command. Reason: %s", reason)
            self._shutdown_reason = reason
            self.request_stop()
            return {"status": "success"}

        @server.on_get_stats
        def _get_stats(args: dict) -> Dict[str, Any]:
            return self.build_stats_response(args)

    def _build_data_plane(self) -> None:
        """Construct whatever pub/sub and dealer endpoints this subsystem declared.

        Construction only - the base registers no routes. Topic names and handler bodies
        belong to the subsystem, and it attaches them in setup().
        """

        if self.PUBSUB is PubSubRole.SUBSCRIBER:
            self.subscriber = IpcSubscriberSync(
                port=self.settings.Network.broker_xpub_port, logger=self.logger)
        elif self.PUBSUB is PubSubRole.PUBLISHER:
            raise NotImplementedError("No sync publisher exists; use AsyncSubsystem to publish")

        if self.DEALER:
            self.dealer = IpcDealerClient(
                host="127.0.0.1",
                port=self.settings.Network.broker_router_port,
                identity=str(self.APP_ID),
                logger=self.logger,
            )

    def _start_ipc_threads(self) -> None:
        """Start a servicing thread for each IPC endpoint, and register it for join."""

        if self.subscriber is not None:
            self._spawn_thread(self.subscriber.start, f"{self.NAME}-Subscriber")
        if self.dealer is not None:
            self._spawn_thread(self.dealer.start, f"{self.NAME}-Dealer")
        if self._mgmt_ipc_enabled:
            # This one starts itself
            self.add_thread(self._mgmt_server.serve_in_thread())

    def _spawn_thread(self, target: Callable[[], None], name: str) -> None:
        """Start a daemon thread and register it for join-on-teardown.

        Args:
            target (Callable[[], None]): Blocking callable to run
            name (str): Thread name, as it appears in logs
        """

        thread = threading.Thread(target=target, daemon=True, name=name)
        thread.start()
        self.add_thread(thread)

    def _close_data_plane(self) -> None:
        """Close the base-built endpoints. Runs only after on_shutdown() has returned, so the
        subsystem's own teardown ordering is preserved."""

        if self.dealer is not None:
            self.dealer.close()
        if self.subscriber is not None:
            self.subscriber.close()

    # -------------------------------------- RUN -----------------------------------------------------------------------

    def _run(self) -> None:
        """Boot the subsystem, block in run_forever(), then tear down."""

        # Built before setup() so the subsystem can attach its handlers to self.mgmt,
        # self.publisher/subscriber and self.dealer there, alongside the rest of its wiring.
        if self._mgmt_ipc_enabled:
            self._build_mgmt_ipc()
        self._build_data_plane()

        self.setup()

        self._start_ipc_threads()
        if self.READY_ON_SETUP_COMPLETE:
            self.notify_ready()

        try:
            self.run_forever()
        finally:
            self.shutdown_event.set()
            self.on_shutdown(self._shutdown_reason)
            self._close_data_plane()
            self._join_threads()
            if self._mgmt_server:
                self._mgmt_server.close()

    def _join_threads(self) -> None:
        """Join every registered thread, without letting one hung thread wedge the exit."""

        for thread in self._threads:
            thread.join(timeout=THREAD_JOIN_TIMEOUT_SEC)
            if thread.is_alive():
                self.logger.warning("Thread %s did not exit within %.1fs", thread.name, THREAD_JOIN_TIMEOUT_SEC)

# -------------------------------------- EXPORTS -----------------------------------------------------------------------

__all__ = [
    "SyncSubsystem",
]
