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

import asyncio
import sys
from abc import abstractmethod
from typing import Any, Awaitable, Callable, Dict, List, Optional

from lib.ipc import (IpcDealerAsync, IpcPublisherAsync, IpcServerAsync,
                     IpcSubscriberAsync)
from lib.periodic_task import periodic_task

from .base import MgmtIpcHandle, PngSubsystem, PubSubRole

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

class AsyncSubsystem(PngSubsystem):
    """A subsystem whose main loop is an asyncio event loop.

    Owns the task registry and teardown, so a subsystem registers work with add_task() /
    add_periodic() instead of threading a `tasks` list through every init function.
    """

    ABSTRACT = True

    def __init__(self) -> None:
        """Construct the subsystem. The asyncio primitives are built once the loop is running."""

        super().__init__()
        self._tasks: List[asyncio.Task] = []
        self.shutdown_event: Optional[asyncio.Event] = None
        self._shutdown_requested: Optional[asyncio.Event] = None
        self._shutdown_reason: str = "N/A"

        # Built by the base before setup() runs, per the PUBSUB / DEALER declarations.
        # A subsystem sits on at most one end of the pub/sub fabric, so exactly one of
        # publisher / subscriber is ever non-None - but they are separate names so that
        # neither the reader nor the IDE has to work out which one it is holding.
        self.publisher: Optional[IpcPublisherAsync] = None
        self.subscriber: Optional[IpcSubscriberAsync] = None
        self.dealer: Optional[IpcDealerAsync] = None
        self._mgmt_server: Optional[IpcServerAsync] = None

    # -------------------------------------- MUST IMPLEMENT ------------------------------------------------------------

    @abstractmethod
    async def setup(self) -> None:
        """Build this subsystem's objects and register its tasks."""

    @abstractmethod
    async def on_shutdown(self, reason: str) -> None:
        """Tear this subsystem down. The base has already set self.shutdown_event.

        Abstract even when there is nothing to do, so that "this subsystem has nothing to tear
        down" is a stated decision in the file rather than an absence someone has to confirm.

        Args:
            reason (str): Why the shutdown was requested
        """

    # -------------------------------------- TASK REGISTRY -------------------------------------------------------------

    def add_task(self, coro: Awaitable[Any], name: str) -> asyncio.Task:
        """Register a long-lived task. The base gathers it and cancels it on teardown.

        Args:
            coro (Awaitable[Any]): Coroutine to run
            name (str): Task name, as it appears in logs

        Returns:
            asyncio.Task: The created task
        """

        task = asyncio.create_task(coro, name=name)
        self._tasks.append(task)
        return task

    def add_periodic(self,
                     interval_ms: int,
                     task_coro: Callable[..., Awaitable[Any]],
                     *args,
                     name: str,
                     **kwargs) -> asyncio.Task:
        """Register a task that runs task_coro every interval_ms until shutdown.

        Args:
            interval_ms (int): Interval in milliseconds
            task_coro (Callable[..., Awaitable[Any]]): Coroutine function to run periodically
            *args: Positional arguments for task_coro
            name (str): Task name, as it appears in logs
            **kwargs: Keyword arguments for task_coro

        Returns:
            asyncio.Task: The created task
        """

        return self.add_task(
            periodic_task(interval_ms, self.shutdown_event, self.logger, task_coro, *args, **kwargs),
            name=name)

    # -------------------------------------- SHUTDOWN ------------------------------------------------------------------

    def request_shutdown(self, reason: str) -> None:
        """Signal the teardown task. Synchronous and non-blocking by design.

        The management IPC server only sends its reply to the launcher once the shutdown
        handler returns, so doing the teardown inline would hold up the acknowledgement for as
        long as the teardown takes.

        Args:
            reason (str): Why the shutdown was requested
        """

        self._shutdown_reason = reason
        self._shutdown_requested.set()

    async def _teardown_task(self) -> None:
        """Wait for a shutdown request, then tear the subsystem down.

        Registered as a normal task so that asyncio.gather() waits on it. A bare
        create_task() here would let the gather return once the other tasks died, and
        asyncio.run() would then cancel the teardown mid-flight.
        """

        await self._shutdown_requested.wait()
        self.logger.debug("Received shutdown command. Reason: %s. Stopping tasks...", self._shutdown_reason)
        self.shutdown_event.set()
        await self.on_shutdown(self._shutdown_reason)
        await self._close_data_plane()

    # -------------------------------------- MANAGEMENT IPC ------------------------------------------------------------

    def _build_mgmt_ipc(self) -> None:
        """Stand up the management IPC server and wire the three base-owned handlers."""

        self.logger.debug("Starting IPC server")
        server = IpcServerAsync(
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
        async def _heartbeat_missed(count: int) -> None:
            self.handle_heartbeat_missed(count)

        @server.on_shutdown
        async def _shutdown(args: dict) -> Dict[str, Any]:
            reason = args.get("reason", "N/A")
            self.logger.info("Received shutdown command. Reason: %s", reason)
            self.request_shutdown(reason)
            return {"status": "success"}

        @server.on_get_stats
        async def _get_stats(args: dict) -> Dict[str, Any]:
            return self.build_stats_response(args)

    def _build_data_plane(self) -> None:
        """Construct whatever pub/sub and dealer endpoints this subsystem declared.

        Construction only - the base registers no routes. Topic names and handler bodies
        belong to the subsystem, and it attaches them in setup().
        """

        if self.PUBSUB is PubSubRole.PUBLISHER:
            self.publisher = IpcPublisherAsync(
                logger=self.logger, port=self.settings.Network.broker_xsub_port)
        elif self.PUBSUB is PubSubRole.SUBSCRIBER:
            self.subscriber = IpcSubscriberAsync(
                port=self.settings.Network.broker_xpub_port, logger=self.logger)

        if self.DEALER:
            self.dealer = IpcDealerAsync(
                host="127.0.0.1",
                port=self.settings.Network.broker_router_port,
                identity=str(self.APP_ID),
                logger=self.logger,
            )

    def _register_ipc_tasks(self) -> None:
        """Register the servicing task for each IPC endpoint.

        These classes spell "begin servicing this socket" three different ways - get_task(),
        run() and start(). Picking the right one is done here, once.
        """

        if self.publisher is not None:
            self._tasks.append(self.publisher.get_task())
        if self.subscriber is not None:
            self.add_task(self.subscriber.run(), name="Broker Subscriber Task")

        if self.DEALER:
            self.add_task(self.dealer.start(), name=f"{self.NAME} Dealer Recv")

        if self._mgmt_ipc_enabled:
            self.add_task(self._mgmt_server.run(), name="IPC Server")

    async def _close_data_plane(self) -> None:
        """Close the base-built endpoints. Runs only after on_shutdown() has returned, so the
        subsystem's own teardown ordering is preserved."""

        # IpcPublisherAsync.close() is a coroutine; IpcSubscriberAsync.close() is not
        if self.publisher is not None:
            await self.publisher.close()
        if self.subscriber is not None:
            self.subscriber.close()
        if self.dealer is not None:
            await self.dealer.close()

    # -------------------------------------- RUN -----------------------------------------------------------------------

    async def _async_main(self) -> None:
        """Boot the subsystem inside the event loop and run until shutdown."""

        self.shutdown_event = asyncio.Event()
        self._shutdown_requested = asyncio.Event()

        # Built before setup() so the subsystem can attach its handlers to self.mgmt,
        # self.publisher/subscriber and self.dealer there, alongside the rest of its wiring.
        if self._mgmt_ipc_enabled:
            self._build_mgmt_ipc()
        self._build_data_plane()

        await self.setup()

        self.add_task(self._teardown_task(), name="Shutdown Task")
        self._register_ipc_tasks()
        if self.READY_ON_SETUP_COMPLETE:
            self.notify_ready()

        self.logger.debug("Registered %d Tasks: %s",
                          len(self._tasks), [task.get_name() for task in self._tasks])
        try:
            await asyncio.gather(*self._tasks)
        except asyncio.CancelledError:
            self.logger.debug("Main task was cancelled.")
            self.request_shutdown("Main task was cancelled.")
            raise  # Ensure proper cancellation behavior

    def _run(self) -> None:
        """Run the event loop."""

        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        try:
            asyncio.run(self._async_main())
        except asyncio.CancelledError:
            self.logger.info("Program shutdown gracefully.")

# -------------------------------------- EXPORTS -----------------------------------------------------------------------

__all__ = [
    "AsyncSubsystem",
]
