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
from typing import Any, Awaitable, Callable, Dict, Generic, List, Optional

from lib.ipc import (IpcDealerAsync, IpcPublisherAsync, IpcServerAsync,
                     IpcSubscriberAsync)
from lib.periodic_task import periodic_task

from .base import ArgsT, PngSubsystem, PubSubRole

# -------------------------------------- TYPES -------------------------------------------------------------------------

# The type of AsyncSubsystem.add_task, for code that registers work without owning the
# subsystem - see apps/backend's layer inits, which take it as a parameter. Named for the
# method it types, because it is that bound method and nothing else: call it, do not look for
# attributes on it.
AddTask = Callable[..., "SubsystemTask"]

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

class SubsystemTask:
    """One registered unit of work, held from registration until there is a loop to start it.

    A subsystem registers its work in __init__, where asyncio.create_task() raises - so the
    coroutine is held here and turned into a Task when _async_main() starts. Anything wanting
    to cancel its own task keeps one of these rather than a raw Task, which does not exist yet
    at registration time.
    """

    def __init__(self, coro: Optional[Awaitable[Any]], name: str) -> None:
        """Hold a coroutine until the loop is up.

        Args:
            coro (Optional[Awaitable[Any]]): Coroutine to run. None when adopting a live task.
            name (str): Task name, as it appears in logs
        """

        self._coro = coro
        self._name = name
        self._task: Optional[asyncio.Task] = None

    @classmethod
    def adopted(cls, task: asyncio.Task) -> "SubsystemTask":
        """Wrap a Task its owner already created - see AsyncSubsystem.adopt_task().

        Args:
            task (asyncio.Task): An already-created task

        Returns:
            SubsystemTask: A handle already in the started state
        """

        handle = cls(None, task.get_name())
        handle._task = task
        return handle

    @property
    def name(self) -> str:
        """str: Task name, readable before the task exists."""

        return self._name

    def start(self) -> asyncio.Task:
        """Create the real task. Called by AsyncSubsystem once the loop is running.

        Returns:
            asyncio.Task: The running task
        """

        if self._task is None:
            self._task = asyncio.create_task(self._coro, name=self._name)
        return self._task

    def cancel(self) -> None:
        """Cancel the task. A no-op if the loop never got as far as starting it."""

        if self._task is not None:
            self._task.cancel()

class AsyncSubsystem(PngSubsystem[ArgsT], Generic[ArgsT]):
    """A subsystem whose main loop is an asyncio event loop.

    Owns the task registry and teardown, so a subsystem registers work with add_task() /
    add_periodic() instead of threading a `tasks` list through every init function.

    A concrete subsystem declares its shape with class variables, all defined on
    PngSubsystem. Required:

        SUBSYS_ID                PngSubsysId member - the whole identity: logger,
                                 management IPC server, argparse, and the ZMQ dealer

    Optional. Each default is a real answer rather than a placeholder, so a subsystem that
    wants it says nothing:

        CONFIG_REQUIRED          False; True makes a missing config file fatal
        READY_ON_START           True; False when the subsystem is not usable until later
                                 and calls notify_ready() itself
        PUBSUB                   PubSubRole.NONE; PUBLISHER populates self.publisher,
                                 SUBSCRIBER populates self.subscriber
        DEALER                   False; True populates self.dealer

    SUBSYS_ID is enforced at import time by PngSubsystem.__init_subclass__. The rest are only
    read where they are used, and the handle properties below assert if you reach for one
    this subsystem never declared.
    """

    ABSTRACT = True

    def __init__(self) -> None:
        """Construct the subsystem. Nothing is started until main() runs."""

        super().__init__()
        self._tasks: List[SubsystemTask] = []
        # Safe to build with no loop running: asyncio.Event stopped capturing a loop at
        # construction in 3.10, and binds lazily on the first wait(). SyncSubsystem has always
        # built its threading.Event here.
        self.shutdown_event: asyncio.Event = asyncio.Event()
        self._shutdown_requested: asyncio.Event = asyncio.Event()
        self._shutdown_reason: str = "N/A"

        # Built here, before the subclass's own __init__ body, so that it can attach handlers
        # and register tasks alongside the rest of its wiring. These bind real sockets, which
        # is why a subsystem is a process rather than an object you make several of.
        #
        # Each is assigned exactly once, from a builder that owns its own condition. They stay
        # Optional because a subsystem sits on at most one end of the pub/sub fabric and may
        # want neither - so None here means "this subsystem declared no such endpoint", never
        # "not built yet". The properties below turn that None into a readable assert.
        self._mgmt_server: Optional[IpcServerAsync] = self._build_mgmt_ipc()
        self._publisher: Optional[IpcPublisherAsync] = self._build_publisher()
        self._subscriber: Optional[IpcSubscriberAsync] = self._build_subscriber()
        self._dealer: Optional[IpcDealerAsync] = self._build_dealer()

    # -------------------------------------- MUST IMPLEMENT ------------------------------------------------------------

    @abstractmethod
    async def on_shutdown(self, reason: str) -> None:
        """Tear this subsystem down. The base has already set self.shutdown_event.

        Abstract even when there is nothing to do, so that "this subsystem has nothing to tear
        down" is a stated decision in the file rather than an absence someone has to confirm.

        Args:
            reason (str): Why the shutdown was requested
        """

    # -------------------------------------- TASK REGISTRY -------------------------------------------------------------

    def add_task(self, coro: Awaitable[Any], name: str) -> SubsystemTask:
        """Register a long-lived task. The base starts it, gathers it, and cancels it on teardown.

        Registration is deliberately separate from creation, so that this can be called from
        __init__ - where there is no loop yet - as well as from inside one.

        Args:
            coro (Awaitable[Any]): Coroutine to run
            name (str): Task name, as it appears in logs

        Returns:
            SubsystemTask: Handle to the registered task. Hold it only if you need to cancel.
        """

        handle = SubsystemTask(coro, name)
        self._tasks.append(handle)
        return handle

    def _adopt_task(self, task: asyncio.Task) -> SubsystemTask:
        """Register a task that its own owner already created.

        Private because add_task() is the registration API and this has one caller - the
        publisher, below. Make it public again if a subsystem ever owns a task of its own that
        it cannot hand over as a coroutine.

        IpcPublisherAsync creates its reconnect task itself, and close() cancels it, so it
        cannot hand over a bare coroutine. Giving it a run() coroutine instead was tried and
        reverted: start() has 19 callers in tests/ipc/tests_pubsub.py that rely on it returning
        immediately.

        Such a task still belongs in the registry, so that it is logged with the rest and so
        that the subsystem comes down if it dies unexpectedly. The cost is that cancelling it
        surfaces as a cancelled child in the gather, which is why the backend's shutdown ends
        in CancelledError where the web app's completes normally.

        Args:
            task (asyncio.Task): An already-created task

        Returns:
            SubsystemTask: Handle wrapping it, already started
        """

        handle = SubsystemTask.adopted(task)
        self._tasks.append(handle)
        return handle

    def add_periodic(self,
                     interval_ms: int,
                     task_coro: Callable[..., Awaitable[Any]],
                     *args,
                     name: str,
                     **kwargs) -> SubsystemTask:
        """Register a task that runs task_coro every interval_ms until shutdown.

        Args:
            interval_ms (int): Interval in milliseconds
            task_coro (Callable[..., Awaitable[Any]]): Coroutine function to run periodically
            *args: Positional arguments for task_coro
            name (str): Task name, as it appears in logs
            **kwargs: Keyword arguments for task_coro

        Returns:
            SubsystemTask: Handle to the registered task
        """

        return self.add_task(
            periodic_task(interval_ms, self.shutdown_event, self.logger, task_coro, *args, **kwargs),
            name=name)

    # -------------------------------------- IPC HANDLES ---------------------------------------------------------------

    @property
    def mgmt(self) -> IpcServerAsync:
        assert self._mgmt_server and self._mgmt_ipc_enabled, \
            "Management IPC is not enabled for this run"
        return self._mgmt_server

    @property
    def publisher(self) -> IpcPublisherAsync:
        assert self._publisher and self.PUBSUB == PubSubRole.PUBLISHER, \
            "Publisher is not built - check PUBSUB declaration"
        return self._publisher

    @property
    def subscriber(self) -> IpcSubscriberAsync:
        assert self._subscriber and self.PUBSUB == PubSubRole.SUBSCRIBER, \
            "Subscriber is not built - check PUBSUB declaration"
        return self._subscriber

    @property
    def dealer(self) -> IpcDealerAsync:
        assert self._dealer and self.DEALER, "Dealer is not built - check DEALER declaration"
        return self._dealer

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

    def _build_mgmt_ipc(self) -> Optional[IpcServerAsync]:
        """Stand up the management IPC server and wire the three base-owned handlers.

        Returns:
            Optional[IpcServerAsync]: The server, or None when this run has no launcher
        """

        if not self._mgmt_ipc_enabled:
            return None

        self.logger.debug("Starting IPC server")
        server = IpcServerAsync(name=str(self.SUBSYS_ID), logger=self.logger)
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

        return server

    # -------------------------------------- DATA PLANE ----------------------------------------------------------------
    # Construction only - the base registers no routes. Topic names and handler bodies belong
    # to the subsystem, and it attaches them in its own __init__.

    def _build_publisher(self) -> Optional[IpcPublisherAsync]:
        """Returns:
            Optional[IpcPublisherAsync]: The publisher, or None unless PUBSUB is PUBLISHER
        """

        if self.PUBSUB is not PubSubRole.PUBLISHER:
            return None
        return IpcPublisherAsync(
            logger=self.logger, port=self.settings.Network.broker_xsub_port)

    def _build_subscriber(self) -> Optional[IpcSubscriberAsync]:
        """Returns:
            Optional[IpcSubscriberAsync]: The subscriber, or None unless PUBSUB is SUBSCRIBER
        """

        if self.PUBSUB is not PubSubRole.SUBSCRIBER:
            return None
        return IpcSubscriberAsync(
            port=self.settings.Network.broker_xpub_port, logger=self.logger)

    def _build_dealer(self) -> Optional[IpcDealerAsync]:
        """Returns:
            Optional[IpcDealerAsync]: The dealer, or None unless DEALER is set
        """

        if not self.DEALER:
            return None
        return IpcDealerAsync(
            host="127.0.0.1",
            port=self.settings.Network.broker_router_port,
            identity=str(self.SUBSYS_ID),
            logger=self.logger,
        )

    def _register_ipc_tasks(self) -> None:
        """Register the servicing task for each IPC endpoint.

        These classes spell "begin servicing this socket" three different ways - get_task(),
        run() and start(). Picking the right one is done here, once.
        """

        if self._publisher is not None:
            self._adopt_task(self._publisher.get_task())
        if self._subscriber is not None:
            self.add_task(self._subscriber.run(), name="Broker Subscriber Task")

        if self.DEALER:
            self.add_task(self._dealer.start(), name=f"{self.SUBSYS_ID} Dealer Recv")

        if self._mgmt_server is not None:
            self.add_task(self._mgmt_server.run(), name="IPC Server")

    async def _close_data_plane(self) -> None:
        """Close the base-built endpoints. Runs only after on_shutdown() has returned, so the
        subsystem's own teardown ordering is preserved."""

        # IpcPublisherAsync.close() is a coroutine; IpcSubscriberAsync.close() is not
        if self._publisher is not None:
            await self._publisher.close()
        if self._subscriber is not None:
            self._subscriber.close()
        if self._dealer is not None:
            await self._dealer.close()

    # -------------------------------------- RUN -----------------------------------------------------------------------

    async def _async_main(self) -> None:
        """Start everything the constructor registered, and run until shutdown."""

        self.add_task(self._teardown_task(), name="Shutdown Task")
        self._register_ipc_tasks()

        # The first point at which a Task can exist. Everything above only registered work.
        started = [handle.start() for handle in self._tasks]
        if self.READY_ON_START:
            self.notify_ready()

        self.logger.debug("Registered %d Tasks: %s",
                          len(self._tasks), [handle.name for handle in self._tasks])
        try:
            await asyncio.gather(*started)
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
