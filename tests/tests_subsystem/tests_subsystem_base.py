"""Contract tests for lib/subsystem/ - the child-side lifecycle base.

Native pytest style per tests/README.md: plain assert, parametrize, bare async def.
Nothing here binds a real IPC port, so these stay parallel-safe.
"""

import argparse
import asyncio
import logging
import sys
import threading
from dataclasses import FrozenInstanceError, dataclass
from typing import Generic

import pytest

from lib.error_status import PNG_LOST_CONN_TO_PARENT, PngError
from lib.ipc import PngAppId
from lib.subsystem import (AsyncSubsystem, PubSubRole, SubsystemArgs,
                           SyncSubsystem, arg)
from lib.subsystem.args import add_dataclass_args
from lib.subsystem.base import ArgsT

# -------------------------------------- HELPERS -----------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _boot_env(monkeypatch):
    """Keep every subsystem constructed here off the real argv and the real config file.

    A subsystem parses argv and loads config in its constructor, so without this each
    construction would try to parse "-q", "tests/" and friends, and would read - or, for a
    missing file, write - png_config.json in the repo root. Tests that care about particular
    flags override the argv half with their own monkeypatch.setattr.
    """

    monkeypatch.setattr(sys, "argv", ["prog"])
    monkeypatch.setattr("lib.subsystem.base.load_config_from_json", lambda *a, **k: None)

def _test_logger(owner) -> logging.Logger:
    """Per-instance logger.

    get_logger() asserts a name is only initialized once per process, so every stub needs a
    logger of its own rather than one named after the subsystem.
    """

    logger = logging.getLogger(f"test_subsystem_{id(owner)}")
    logger.addHandler(logging.NullHandler())
    return logger

class _StubSync(SyncSubsystem[ArgsT], Generic[ArgsT]):
    """Minimal concrete SyncSubsystem that never talks to a launcher.

    Stays generic so a test can subclass it and still name its own args dataclass. A concrete
    intermediate would swallow the type parameter and pin every leaf to SubsystemArgs.
    """

    NAME = "stub_sync"
    DESCRIPTION = "Stub Sync Subsystem"

    # Counted by pre_boot() and on_exit(), both of which the base constructor can call before
    # this __init__ body runs - so they have to exist on the class, not be assigned down there.
    pre_boot_calls = 0
    on_exit_calls = 0

    def __init__(self, stats=None):
        super().__init__()
        self._stats = stats if stats is not None else {}
        self.setup_calls = 0
        self.shutdown_calls = 0
        self.shutdown_reasons = []

    def should_run_mgmt_ipc(self):
        return False

    def make_logger(self):
        return _test_logger(self)

    def pre_boot(self):
        self.pre_boot_calls += 1

    def on_exit(self):
        self.on_exit_calls += 1

    def setup(self):
        self.setup_calls += 1

    def run_forever(self):
        return

    def collect_stats(self):
        return self._stats

    def on_shutdown(self, reason):
        self.shutdown_calls += 1
        self.shutdown_reasons.append(reason)

class _StubAsync(AsyncSubsystem):
    """Minimal concrete AsyncSubsystem that never talks to a launcher."""

    NAME = "stub_async"
    DESCRIPTION = "Stub Async Subsystem"

    def __init__(self):
        super().__init__()
        self.shutdown_calls = 0
        self.shutdown_reasons = []

    def should_run_mgmt_ipc(self):
        return False

    def make_logger(self):
        return _test_logger(self)

    async def setup(self):
        return

    def collect_stats(self):
        return {}

    async def on_shutdown(self, reason):
        self.shutdown_calls += 1
        self.shutdown_reasons.append(reason)

class _FakeServer:
    """Stands in for IpcServerAsync/IpcServerSync, recording route registrations."""

    def __init__(self):
        self.routes = []

    def on(self, cmd_name):
        self.routes.append(cmd_name)
        return lambda fn: fn

    def on_shutdown(self, fn):
        raise AssertionError("a subsystem must not be able to reach on_shutdown")

    def on_get_stats(self, fn):
        raise AssertionError("a subsystem must not be able to reach on_get_stats")

    def on_heartbeat_missed(self, fn):
        raise AssertionError("a subsystem must not be able to reach on_heartbeat_missed")

# The IPC classes each spell "begin servicing this socket" and "close" differently, and the base
# is the one place that picks the right one per endpoint. These fakes exist to record which call
# it made, so that picking the wrong one fails loudly here instead of silently at runtime.

class _FakePublisher:
    """IpcPublisherAsync: creates its own task, and close() is a coroutine."""

    def __init__(self):
        self.calls = []

    def get_task(self):
        self.calls.append("get_task")
        return asyncio.create_task(asyncio.sleep(0), name="Publisher Reconnect")

    async def close(self):
        self.calls.append("close")

class _FakeSubscriberAsync:
    """IpcSubscriberAsync: run() is a coroutine, but close() is NOT - the asymmetry the base's
    own comment warns about."""

    def __init__(self):
        self.calls = []

    async def run(self):
        self.calls.append("run")

    def close(self):
        self.calls.append("close")

class _FakeDealerAsync:
    """IpcDealerAsync: start() and close() are both coroutines."""

    def __init__(self):
        self.calls = []

    async def start(self):
        self.calls.append("start")

    async def close(self):
        self.calls.append("close")

class _FakeMgmtAsync:
    """IpcServerAsync, as the base uses it once built."""

    def __init__(self):
        self.calls = []

    async def run(self):
        self.calls.append("run")

    def close(self):
        self.calls.append("close")

class _FakeSyncEndpoint:
    """IpcSubscriberSync / IpcDealerClient: start() blocks, so the base hands it to a thread."""

    def __init__(self):
        self.calls = []

    def start(self):
        self.calls.append("start")

    def close(self):
        self.calls.append("close")

class _FakeMgmtSync:
    """IpcServerSync: unlike the other two, this one starts its own thread."""

    def __init__(self):
        self.calls = []

    def serve_in_thread(self):
        self.calls.append("serve_in_thread")
        thread = threading.Thread(target=lambda: None, name="fake-mgmt", daemon=True)
        thread.start()
        return thread

    def close(self):
        self.calls.append("close")

# -------------------------------------- IDENTITY ----------------------------------------------------------------------

def test_subclass_without_name_fails_at_import():
    """A subsystem missing NAME is rejected when the class body is executed."""

    with pytest.raises(TypeError, match="NAME"):
        class _NoName(SyncSubsystem):  # pylint: disable=unused-variable
            DESCRIPTION = "No name"

def test_subclass_without_description_fails_at_import():
    """A subsystem missing DESCRIPTION is rejected when the class body is executed."""

    with pytest.raises(TypeError, match="DESCRIPTION"):
        class _NoDescription(SyncSubsystem):  # pylint: disable=unused-variable
            NAME = "no_description"

def test_abstract_intermediates_are_exempt():
    """AsyncSubsystem and SyncSubsystem carry behaviour but are not subsystems themselves."""

    assert AsyncSubsystem.NAME is None
    assert SyncSubsystem.NAME is None

def test_abstract_flag_does_not_inherit():
    """A concrete subclass of an ABSTRACT intermediate still has to fill the fields in."""

    class _Intermediate(SyncSubsystem):
        ABSTRACT = True

    with pytest.raises(TypeError, match="NAME"):
        class _Concrete(_Intermediate):  # pylint: disable=unused-variable
            DESCRIPTION = "Concrete"

@pytest.mark.parametrize("missing", ["collect_stats", "on_shutdown", "run_forever"])
def test_missing_hook_cannot_be_instantiated(missing):
    """A subsystem that omits any must-implement hook fails at instantiation.

    setup() is not in this list because it no longer exists - a subsystem builds itself in
    __init__. See test_setup_hook_is_gone.
    """

    body = {
        "NAME": "incomplete",
        "DESCRIPTION": "Incomplete",
        # Without this the constructor would bind a real management IPC socket and report a
        # port to a launcher that is not there.
        "should_run_mgmt_ipc": lambda self: False,
        "run_forever": lambda self: None,
        "collect_stats": lambda self: {},
        "on_shutdown": lambda self, reason: None,
    }
    del body[missing]
    cls = type("_Incomplete", (SyncSubsystem,), body)

    with pytest.raises(TypeError, match="abstract"):
        cls()

def test_setup_hook_is_gone():
    """There is no second construction phase: a subsystem builds itself in __init__.

    Guards against setup() creeping back as an informal convention - the base would never call
    it, so it would silently never run.
    """

    assert not hasattr(AsyncSubsystem, "setup")
    assert not hasattr(SyncSubsystem, "setup")

# -------------------------------------- PARSER ------------------------------------------------------------------------

def test_base_flags_present(monkeypatch):
    """--config-file and --debug are pre-added by the base."""

    args = _StubSync().args

    assert args.config_file == "png_config.json"
    assert args.debug is False

def test_args_subclass_extras_merge_with_base_flags(monkeypatch):
    """A subsystem's own flags parse alongside the base's, neither clobbering the other."""

    @dataclass(frozen=True)
    class _ExtraArgs(SubsystemArgs):
        replay_server: bool = arg(False, "Enable the TCP replay debug server")

    class _WithExtras(_StubSync[_ExtraArgs]):
        NAME = "with_extras"
        DESCRIPTION = "With Extras"

    monkeypatch.setattr(sys, "argv", ["prog", "--debug", "--replay-server", "--config-file", "other.json"])
    args = _WithExtras().args

    assert isinstance(args, _ExtraArgs)
    assert args.debug is True
    assert args.replay_server is True
    assert args.config_file == "other.json"

def test_underscored_field_becomes_dashed_flag(monkeypatch):
    """replay_server is spelled --replay-server on the command line.

    The launcher spawns children with the dashed spelling, so the derivation is part of the
    wire contract rather than a cosmetic choice.
    """

    @dataclass(frozen=True)
    class _ExtraArgs(SubsystemArgs):
        replay_server: bool = arg(False, "help")

    class _WithExtras(_StubSync[_ExtraArgs]):
        NAME = "dashed"
        DESCRIPTION = "Dashed"

    monkeypatch.setattr(sys, "argv", ["prog", "--replay_server"])
    with pytest.raises(SystemExit):
        _WithExtras()

def test_unparameterized_subclass_falls_back_to_base_args(monkeypatch):
    """A subsystem with no extra flags inherits SubsystemArgs, not the unfilled TypeVar.

    Regression: __orig_bases__ is inherited, so reading it with getattr rather than
    cls.__dict__ hands back the PARENT's SyncSubsystem[~ArgsT]. ARGS would then be the TypeVar
    itself, and _parse_args() would try to call it.
    """

    class _NoExtras(_StubSync):
        NAME = "no_extras"
        DESCRIPTION = "No Extras"

    assert _NoExtras.ARGS is SubsystemArgs

    assert isinstance(_NoExtras().args, SubsystemArgs)

@pytest.mark.parametrize("argv, expected", [
    (["prog"], 0),
    (["prog", "--retries", "7"], 7),
])
def test_non_bool_field_is_coerced_from_its_annotation(monkeypatch, argv, expected):
    """An int field parses as an int, with no type= written anywhere.

    No subsystem currently declares a non-str, non-bool flag, so this is the only cover for
    the generator handing argparse a type it derived rather than one a caller supplied.
    """

    @dataclass(frozen=True)
    class _IntArgs(SubsystemArgs):
        retries: int = arg(0, "How many times to retry")

    class _WithInt(_StubSync[_IntArgs]):
        NAME = "with_int"
        DESCRIPTION = "With Int"

    monkeypatch.setattr(sys, "argv", argv)
    assert _WithInt().args.retries == expected

def test_non_bool_field_rejects_a_value_of_the_wrong_type(monkeypatch):
    """argparse refuses a non-integer for an int field rather than passing the string through."""

    @dataclass(frozen=True)
    class _IntArgs(SubsystemArgs):
        retries: int = arg(0, "How many times to retry")

    class _WithInt(_StubSync[_IntArgs]):
        NAME = "with_bad_int"
        DESCRIPTION = "With Bad Int"

    monkeypatch.setattr(sys, "argv", ["prog", "--retries", "abc"])
    with pytest.raises(SystemExit):
        _WithInt()

def test_bool_defaulting_true_is_rejected():
    """store_true cannot express "on unless passed" - the flag could never switch it off."""

    @dataclass(frozen=True)
    class _BadArgs(SubsystemArgs):
        already_on: bool = arg(True, "help")

    with pytest.raises(TypeError, match="could switch off"):
        add_dataclass_args(argparse.ArgumentParser(), _BadArgs)

def test_args_are_frozen(monkeypatch):
    """The parsed args are the invocation, not mutable state."""

    args = _StubSync().args

    with pytest.raises(FrozenInstanceError):
        args.debug = True

# -------------------------------------- TOKEN GATING ------------------------------------------------------------------

def test_no_tokens_reach_stdout_when_unmanaged(capsys, monkeypatch):
    """The MCP stdio guarantee: with mgmt IPC off, nothing at all is printed.

    In stdio mode stdout is the MCP transport, so a stray handshake token would corrupt it.
    """

    app = _StubSync()
    app.notify_ready()
    app.report_mgmt_ipc_port(12345)

    assert capsys.readouterr().out == ""

def test_notify_ready_is_idempotent(capsys, monkeypatch):
    """Repeated notify_ready() calls emit the init-complete token exactly once."""

    app = _StubSync()
    app._mgmt_ipc_enabled = True

    app.notify_ready()
    app.notify_ready()
    app.notify_ready()

    assert capsys.readouterr().out.count("__PNG_SUBSYSTEM_INIT_COMPLETE__") == 1

def test_ready_not_emitted_when_subsystem_owns_the_timing(capsys, monkeypatch):
    """READY_ON_START = False leaves the token for the subsystem to send itself."""

    class _LateReady(_StubSync):
        NAME = "late_ready"
        DESCRIPTION = "Late Ready"
        READY_ON_START = False

    app = _LateReady()
    app._mgmt_ipc_enabled = True
    # The stub declined mgmt IPC, so there is no server for _run() to service.
    monkeypatch.setattr(app, "_start_ipc_threads", lambda: None)
    app._run()

    assert "__PNG_SUBSYSTEM_INIT_COMPLETE__" not in capsys.readouterr().out
    assert app._ready_notified is False

# -------------------------------------- PROFILER ----------------------------------------------------------------------

def test_profiler_is_off_and_costs_nothing(monkeypatch):
    """PROFILE defaults False, and a normal boot must not even import yappi.

    The import is inside the branch precisely so that every subsystem can carry this in its
    constructor without paying for it.
    """

    monkeypatch.delitem(sys.modules, "yappi", raising=False)

    app = _StubSync()

    assert app.PROFILE is False
    assert app._profiler is None
    assert "yappi" not in sys.modules

# -------------------------------------- STATS ENVELOPE ----------------------------------------------------------------

def test_stats_envelope_wraps_collect_stats():
    """collect_stats() -> {"a": 1} yields exactly {"status": "success", "stats": {"a": 1}}."""

    app = _StubSync(stats={"a": 1})

    assert app.build_stats_response({}) == {"status": "success", "stats": {"a": 1}}

def test_stats_envelope_preserves_empty_body():
    """A subsystem with nothing to report still gets a well-formed envelope."""

    assert _StubSync(stats={}).build_stats_response({}) == {"status": "success", "stats": {}}

# -------------------------------------- HEARTBEAT ---------------------------------------------------------------------

def test_heartbeat_missed_logs_and_exits(monkeypatch, caplog):
    """Missed heartbeats log at error level AND hard-exit.

    The logging half is the regression guard: the MCP server used print(), so an orphaned
    MCP server's death reason never reached png.log.
    """

    exits = []
    monkeypatch.setattr("lib.subsystem.base.os._exit", exits.append)

    app = _StubSync()
    app.logger = logging.getLogger("heartbeat_test")

    with caplog.at_level(logging.ERROR, logger="heartbeat_test"):
        app.handle_heartbeat_missed(3)

    assert exits == [PNG_LOST_CONN_TO_PARENT]
    assert "orphaned" in caplog.text

# -------------------------------------- ROUTE FACADE ------------------------------------------------------------------

def test_mgmt_exposes_the_management_server():
    """self.mgmt is the server itself, so @self.mgmt.on(...) registers a launcher command.

    The three reserved slots on it are protected at the library level now: registering a second
    shutdown / get-stats / heartbeat-missed handler raises rather than silently replacing the
    base's. See tests/ipc/tests_parent_child.py::TestReservedCallbackSlots.
    """

    server = _FakeServer()
    app = _StubSync()
    app._mgmt_ipc_enabled = True
    app._mgmt_server = server

    @app.mgmt.on("manual-save")
    def _handler(_args):
        return {}

    assert server.routes == ["manual-save"]

def test_mgmt_refuses_when_mgmt_ipc_is_off():
    """An unmanaged run has no launcher to answer, so there is no server to hand out."""

    app = _StubSync()

    with pytest.raises(AssertionError, match="Management IPC is not enabled"):
        _ = app.mgmt

# -------------------------------------- DATA PLANE DECLARATION --------------------------------------------------------

def test_dealer_without_app_id_fails_at_import():
    """A dealer needs an identity on the router; a typo there is a confusing bug."""

    with pytest.raises(TypeError, match="APP_ID"):
        class _NoAppId(_StubSync):  # pylint: disable=unused-variable
            NAME = "no_app_id"
            DESCRIPTION = "No App Id"
            DEALER = True

def test_dealer_with_app_id_is_accepted():
    """Declaring both is enough - the base builds the dealer from settings."""

    class _WithAppId(_StubSync):
        NAME = "with_app_id"
        DESCRIPTION = "With App Id"
        DEALER = True
        APP_ID = PngAppId.HUD

    assert _WithAppId.APP_ID is PngAppId.HUD

def test_data_plane_defaults_to_nothing():
    """A subsystem that declares no data plane gets none - the broker's case."""

    assert _StubSync.PUBSUB is PubSubRole.NONE
    assert _StubSync.DEALER is False

    app = _StubSync()

    assert app._subscriber is None
    assert app._dealer is None

def test_undeclared_handles_raise_rather_than_return_none():
    """The properties guard: reaching for a handle you never declared says so."""

    app = _StubSync()

    with pytest.raises(AssertionError, match="Subscriber is not built"):
        _ = app.subscriber
    with pytest.raises(AssertionError, match="Dealer is not built"):
        _ = app.dealer

def test_sync_publisher_is_rejected():
    """There is no sync publisher; declaring one is a mistake worth surfacing loudly."""

    class _SyncPublisher(_StubSync):
        NAME = "sync_publisher"
        DESCRIPTION = "Sync Publisher"
        PUBSUB = PubSubRole.PUBLISHER

    with pytest.raises(NotImplementedError, match="sync publisher"):
        _SyncPublisher()

# -------------------------------------- EXCEPTION FUNNEL --------------------------------------------------------------

def test_png_error_exits_with_its_own_code(monkeypatch):
    """PngError -> SystemExit(e.exit_code)."""

    class _Failing(_StubSync):
        NAME = "failing"
        DESCRIPTION = "Failing"

        def run_forever(self):
            raise PngError(42, "boom")


    with pytest.raises(SystemExit) as exc:
        _Failing().main()

    assert exc.value.code == 42

@pytest.mark.parametrize("raised, expected_code", [
    (FileNotFoundError("no config"), 1),
    (PngError(42, "boom"), 42),
])
def test_config_failure_in_the_constructor_exits_with_a_code(monkeypatch, raised, expected_code):
    """A bad config file is reported and mapped, not thrown out of the constructor.

    The load moved into __init__, which is outside main()'s funnel - so the constructor has to
    do this reporting itself, or the launcher would see a bare traceback instead of an exit
    code it can read.
    """

    class _BadConfig(_StubSync):
        NAME = "bad_config"
        DESCRIPTION = "Bad Config"

    def _raise(*_args, **_kwargs):
        raise raised

    monkeypatch.setattr("lib.subsystem.base.load_config_from_json", _raise)

    with pytest.raises(SystemExit) as exc:
        _BadConfig()

    assert exc.value.code == expected_code

def test_on_exit_runs_when_the_constructor_fails_on_config(monkeypatch):
    """pre_boot() has already run by then, so its side effects still have to be undone."""

    calls = []

    class _BadConfig(_StubSync):
        NAME = "bad_config_on_exit"
        DESCRIPTION = "Bad Config On Exit"

        def on_exit(self):
            calls.append("on_exit")

    def _raise(*_args, **_kwargs):
        raise FileNotFoundError("no config")

    monkeypatch.setattr("lib.subsystem.base.load_config_from_json", _raise)

    with pytest.raises(SystemExit):
        _BadConfig()

    assert calls == ["on_exit"]

def test_bare_exception_exits_one(monkeypatch):
    """An unexpected exception -> SystemExit(1), logged with a traceback."""

    class _Failing(_StubSync):
        NAME = "failing_bare"
        DESCRIPTION = "Failing Bare"

        def run_forever(self):
            raise ValueError("unexpected")


    with pytest.raises(SystemExit) as exc:
        _Failing().main()

    assert exc.value.code == 1

def test_on_exit_runs_even_when_the_run_raises(monkeypatch):
    """on_exit() is guaranteed, so pre_boot()'s side effects are always undone."""

    class _Failing(_StubSync):
        NAME = "failing_on_exit"
        DESCRIPTION = "Failing Post Boot"

        def run_forever(self):
            raise ValueError("unexpected")


    app_holder = {}
    original_init = _Failing.__init__

    def _capture_init(self):
        original_init(self)
        app_holder["app"] = self

    monkeypatch.setattr(_Failing, "__init__", _capture_init)

    with pytest.raises(SystemExit):
        _Failing().main()

    assert app_holder["app"].pre_boot_calls == 1
    assert app_holder["app"].on_exit_calls == 1

# -------------------------------------- SYNC LIFECYCLE ----------------------------------------------------------------

def test_sync_teardown_runs_after_run_forever(monkeypatch):
    """__init__ -> run_forever() -> on_shutdown(), with the event set before teardown."""

    order = []

    class _Ordered(_StubSync):
        NAME = "ordered"
        DESCRIPTION = "Ordered"

        def __init__(self):
            super().__init__()
            order.append("__init__")

        def run_forever(self):
            order.append("run_forever")

        def on_shutdown(self, reason):
            order.append("on_shutdown")
            assert self.shutdown_event.is_set()

    app = _Ordered()
    app._run()

    assert order == ["__init__", "run_forever", "on_shutdown"]

def test_sync_teardown_runs_even_when_run_forever_raises(monkeypatch):
    """A crash in the main loop still tears the subsystem down."""

    class _Crashing(_StubSync):
        NAME = "crashing"
        DESCRIPTION = "Crashing"

        def run_forever(self):
            raise RuntimeError("crash")

    app = _Crashing()

    with pytest.raises(RuntimeError):
        app._run()

    assert app.shutdown_calls == 1

# -------------------------------------- ASYNC LIFECYCLE ---------------------------------------------------------------

async def test_add_task_registers_and_runs(monkeypatch):
    """add_task() puts work in the registry and the base gathers it."""

    app = _StubAsync()

    ran = []

    async def _work():
        ran.append(True)

    handle = app.add_task(_work(), name="Work")

    assert handle in app._tasks
    assert handle.name == "Work"

    await handle.start()
    assert ran == [True]

async def test_add_periodic_runs_until_shutdown(monkeypatch):
    """add_periodic() wires the base's shutdown_event into the periodic helper."""

    app = _StubAsync()

    ticks = []

    async def _tick():
        ticks.append(True)
        if len(ticks) >= 2:
            app.shutdown_event.set()

    await app.add_periodic(1, _tick, name="Ticker").start()

    assert len(ticks) >= 2

async def test_request_shutdown_triggers_teardown_once(monkeypatch):
    """The teardown task wakes on request, sets the event, and calls on_shutdown once."""

    app = _StubAsync()

    teardown = asyncio.create_task(app._teardown_task())
    app.request_shutdown("test reason")
    await teardown

    assert app.shutdown_calls == 1
    assert app.shutdown_reasons == ["test reason"]
    assert app.shutdown_event.is_set()

async def test_request_shutdown_does_not_block(monkeypatch):
    """request_shutdown() returns immediately even when teardown is slow.

    The management IPC server only replies to the launcher once its shutdown handler
    returns, so this is what keeps the launcher's stop acknowledgement prompt.
    """

    class _SlowTeardown(_StubAsync):
        NAME = "slow_teardown"
        DESCRIPTION = "Slow Teardown"

        async def on_shutdown(self, reason):
            await asyncio.sleep(0.5)
            self.shutdown_calls += 1

    app = _SlowTeardown()

    teardown = asyncio.create_task(app._teardown_task())
    await asyncio.sleep(0)

    loop = asyncio.get_running_loop()
    started = loop.time()
    app.request_shutdown("stop")
    elapsed = loop.time() - started

    assert elapsed < 0.05
    await teardown
    assert app.shutdown_calls == 1

async def test_teardown_task_is_gathered(monkeypatch):
    """The teardown task sits in the registry, so gather() waits for it to finish.

    A bare create_task() would let the gather return once the other tasks died, and
    asyncio.run() would then cancel the teardown mid-flight.
    """

    app = _StubAsync()

    app.add_task(app._teardown_task(), name="Shutdown Task")

    assert "Shutdown Task" in [handle.name for handle in app._tasks]

    started = [handle.start() for handle in app._tasks]
    app.request_shutdown("done")
    await asyncio.gather(*started)

    assert app.shutdown_calls == 1


# -------------------------------------- TASK REGISTRY -----------------------------------------------------------------

def test_work_can_be_registered_with_no_event_loop_running():
    """The property the whole constructor-only boot rests on.

    A subsystem registers its work in __init__, where asyncio.create_task() raises. add_task()
    therefore has to hold the coroutine rather than start it.
    """

    app = _StubAsync()

    async def _work():
        return None

    coro = _work()
    try:
        handle = app.add_task(coro, name="Work")

        assert handle in app._tasks
        assert handle.name == "Work"
    finally:
        coro.close()

async def test_start_is_idempotent():
    """_async_main() starts the registry once; a second start must not make a second task."""

    app = _StubAsync()

    async def _work():
        return None

    handle = app.add_task(_work(), name="Work")

    first = handle.start()
    assert handle.start() is first

    await first

def test_cancel_before_start_is_a_no_op():
    """Teardown can run before the loop ever started - a boot that failed, say."""

    app = _StubAsync()

    async def _work():
        return None

    coro = _work()
    try:
        app.add_task(coro, name="Work").cancel()
    finally:
        coro.close()

async def test_cancel_reaches_the_task_once_started():
    """McpSubsystem and F1TelemetryHandler hold a handle for exactly this."""

    app = _StubAsync()

    async def _hang():
        await asyncio.sleep(60)

    handle = app.add_task(_hang(), name="Hang")
    task = handle.start()
    await asyncio.sleep(0)

    handle.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task

async def test_adopt_task_wraps_a_task_its_owner_created():
    """IpcPublisherAsync creates its own reconnect task; the registry still has to gather it."""

    app = _StubAsync()
    task = asyncio.create_task(asyncio.sleep(0), name="Publisher Reconnect")

    handle = app.adopt_task(task)

    assert handle in app._tasks
    assert handle.name == "Publisher Reconnect"
    assert handle.start() is task

    await task

# -------------------------------------- IPC WIRING, ASYNC -------------------------------------------------------------

class _WiredAsync(_StubAsync):
    """An async subsystem whose endpoints are fakes.

    The builders are overridden rather than the attributes assigned afterwards, so the real
    constructor wiring runs - and so no test here needs settings or a real port.
    """

    NAME = "wired_async"
    DESCRIPTION = "Wired Async"
    PUBSUB = PubSubRole.PUBLISHER
    APP_ID = PngAppId.BACKEND
    DEALER = True

    def should_run_mgmt_ipc(self):
        return True

    def _build_mgmt_ipc(self):
        return _FakeMgmtAsync()

    def _build_publisher(self):
        return _FakePublisher()

    def _build_dealer(self):
        return _FakeDealerAsync()

async def test_declared_async_handles_are_exposed(capsys):
    """The properties hand back what the builders returned."""

    app = _WiredAsync()
    capsys.readouterr()

    assert isinstance(app.publisher, _FakePublisher)
    assert isinstance(app.dealer, _FakeDealerAsync)
    assert isinstance(app.mgmt, _FakeMgmtAsync)
    # PUBSUB is PUBLISHER, so the other end of the fabric was never built.
    with pytest.raises(AssertionError, match="Subscriber is not built"):
        _ = app.subscriber

async def test_register_ipc_tasks_picks_the_right_call_per_endpoint(capsys):
    """Each IPC class starts servicing differently; the base picks, so assert what it picked."""

    app = _WiredAsync()
    capsys.readouterr()

    app._register_ipc_tasks()

    assert [handle.name for handle in app._tasks] == [
        "Publisher Reconnect", "wired_async Dealer Recv", "IPC Server"]
    # The publisher hands over a live task; the other two hand over coroutines, which have not
    # run yet.
    assert app._publisher.calls == ["get_task"]
    assert app._dealer.calls == []
    assert app._mgmt_server.calls == []

    await asyncio.gather(*(handle.start() for handle in app._tasks))

    assert app._dealer.calls == ["start"]
    assert app._mgmt_server.calls == ["run"]

async def test_close_data_plane_awaits_or_calls_as_each_endpoint_requires(capsys):
    """IpcPublisherAsync.close() is a coroutine; IpcSubscriberAsync.close() is not.

    Getting this backwards leaves a never-awaited coroutine and an unclosed socket, which is
    why the base has a comment about it rather than a uniform loop.
    """

    class _BothEnds(_WiredAsync):
        NAME = "both_ends"
        DESCRIPTION = "Both Ends"

        def _build_subscriber(self):
            return _FakeSubscriberAsync()

    app = _BothEnds()
    capsys.readouterr()

    await app._close_data_plane()

    assert app._publisher.calls == ["close"]
    assert app._subscriber.calls == ["close"]
    assert app._dealer.calls == ["close"]

async def test_close_data_plane_skips_what_was_never_built():
    """A subsystem that declared no data plane still tears down cleanly."""

    app = _StubAsync()

    await app._close_data_plane()   # must not raise on the Nones

# -------------------------------------- ASYNC RUN ---------------------------------------------------------------------

async def test_async_main_starts_the_registry_and_notifies_ready(capsys):
    """Everything registered before the loop existed gets started, once, in _async_main()."""

    ran = []

    class _App(_StubAsync):
        NAME = "async_main"
        DESCRIPTION = "Async Main"

    app = _App()
    app._mgmt_ipc_enabled = True    # so notify_ready() actually emits its token

    async def _work():
        ran.append(True)
        app.request_shutdown("work done")

    app.add_task(_work(), name="Work")

    await app._async_main()

    assert ran == [True]
    assert app.shutdown_calls == 1
    assert app.shutdown_reasons == ["work done"]
    assert "__PNG_SUBSYSTEM_INIT_COMPLETE__" in capsys.readouterr().out

async def test_async_main_requests_shutdown_when_the_gather_is_cancelled():
    """Ctrl-C lands here. Teardown still has to be asked for, and the cancel still propagates."""

    app = _StubAsync()

    async def _hang():
        await asyncio.sleep(60)

    app.add_task(_hang(), name="Hang")

    task = asyncio.create_task(app._async_main())
    await asyncio.sleep(0)
    await asyncio.sleep(0)
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task

    assert app._shutdown_reason == "Main task was cancelled."

# -------------------------------------- IPC WIRING, SYNC --------------------------------------------------------------

class _WiredSync(_StubSync):
    """A sync subsystem whose endpoints are fakes. See _WiredAsync."""

    NAME = "wired_sync"
    DESCRIPTION = "Wired Sync"
    PUBSUB = PubSubRole.SUBSCRIBER
    APP_ID = PngAppId.HUD
    DEALER = True

    def should_run_mgmt_ipc(self):
        return True

    def _build_mgmt_ipc(self):
        return _FakeMgmtSync()

    def _build_subscriber(self):
        return _FakeSyncEndpoint()

    def _build_dealer(self):
        return _FakeSyncEndpoint()

def test_declared_sync_handles_are_exposed(capsys):
    """As the async case, minus a publisher - which is a hard error rather than an absence."""

    app = _WiredSync()
    capsys.readouterr()

    assert isinstance(app.subscriber, _FakeSyncEndpoint)
    assert isinstance(app.dealer, _FakeSyncEndpoint)
    assert isinstance(app.mgmt, _FakeMgmtSync)
    with pytest.raises(NotImplementedError, match="sync publisher"):
        _ = app.publisher

def test_start_ipc_threads_spawns_one_per_endpoint(capsys):
    """The subscriber and dealer block, so the base threads them; the mgmt server threads itself."""

    app = _WiredSync()
    capsys.readouterr()

    app._start_ipc_threads()

    assert [thread.name for thread in app._threads] == [
        "wired_sync-Subscriber", "wired_sync-Dealer", "fake-mgmt"]
    assert app._mgmt_server.calls == ["serve_in_thread"]

    for thread in app._threads:
        thread.join(timeout=1)

def test_sync_close_data_plane_closes_both_endpoints(capsys):
    """Only what was built, and each exactly once."""

    app = _WiredSync()
    capsys.readouterr()

    app._close_data_plane()

    assert app._dealer.calls == ["close"]
    assert app._subscriber.calls == ["close"]

def test_request_stop_sets_the_shutdown_event():
    """The default, for a run_forever() that waits on the event - the broker's does."""

    app = _StubSync()
    assert app.shutdown_event.is_set() is False

    app.request_stop()

    assert app.shutdown_event.is_set() is True

def test_add_thread_returns_the_thread_it_registered():
    """Returned for convenience, so a caller can start and register in one expression."""

    app = _StubSync()
    thread = threading.Thread(target=lambda: None, name="registered", daemon=True)

    assert app.add_thread(thread) is thread
    assert app._threads == [thread]

def test_join_threads_warns_rather_than_wedging_the_exit(monkeypatch, caplog):
    """One hung thread must not stop the process exiting - it gets a warning and a shrug."""

    monkeypatch.setattr("lib.subsystem.sync_app.THREAD_JOIN_TIMEOUT_SEC", 0.05)

    app = _StubSync()
    release = threading.Event()
    stuck = threading.Thread(target=release.wait, name="stuck", daemon=True)
    stuck.start()
    app.add_thread(stuck)
    # A second thread, so the loop is shown to carry on past the one it gave up on.
    tidy = threading.Thread(target=lambda: None, name="tidy", daemon=True)
    tidy.start()
    app.add_thread(tidy)

    try:
        with caplog.at_level(logging.WARNING):
            app._join_threads()

        assert "stuck" in caplog.text
        assert "did not exit" in caplog.text
    finally:
        release.set()
        stuck.join(timeout=1)

async def test_subscriber_end_is_wired_the_same_way(capsys):
    """The pub/sub fabric has two ends and the base builds either; cover the one _WiredAsync
    does not."""

    class _SubEnd(_StubAsync):
        NAME = "sub_end"
        DESCRIPTION = "Sub End"
        PUBSUB = PubSubRole.SUBSCRIBER

        def _build_subscriber(self):
            return _FakeSubscriberAsync()

    app = _SubEnd()
    capsys.readouterr()

    assert isinstance(app.subscriber, _FakeSubscriberAsync)

    app._register_ipc_tasks()

    assert [handle.name for handle in app._tasks] == ["Broker Subscriber Task"]

    await asyncio.gather(*(handle.start() for handle in app._tasks))
    assert app._subscriber.calls == ["run"]

async def test_async_main_leaves_the_token_alone_when_the_subsystem_owns_the_timing(capsys):
    """READY_ON_START = False is the common case - web, hud and mcp all send it themselves."""

    class _LateReady(_StubAsync):
        NAME = "late_ready_async"
        DESCRIPTION = "Late Ready Async"
        READY_ON_START = False

    app = _LateReady()
    app._mgmt_ipc_enabled = True

    async def _work():
        app.request_shutdown("done")

    app.add_task(_work(), name="Work")

    await app._async_main()

    assert app._ready_notified is False
    assert "__PNG_SUBSYSTEM_INIT_COMPLETE__" not in capsys.readouterr().out

def test_sync_run_tears_down_in_order(capsys):
    """_run()'s finally is the whole sync teardown contract, mgmt server included."""

    order = []

    class _Ordered(_WiredSync):
        NAME = "ordered_sync"
        DESCRIPTION = "Ordered Sync"

        def run_forever(self):
            order.append("run_forever")

        def on_shutdown(self, reason):
            order.append("on_shutdown")
            assert self.shutdown_event.is_set()

    app = _Ordered()
    capsys.readouterr()

    app._run()

    assert order == ["run_forever", "on_shutdown"]
    # Closed after on_shutdown() returned, so a subsystem's own teardown still had its handles.
    assert app._subscriber.calls == ["start", "close"]
    assert app._dealer.calls == ["start", "close"]
    assert app._mgmt_server.calls == ["serve_in_thread", "close"]
