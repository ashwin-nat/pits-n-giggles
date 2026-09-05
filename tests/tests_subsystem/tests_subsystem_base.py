"""Contract tests for lib/subsystem/ - the child-side lifecycle base.

Native pytest style per tests/README.md: plain assert, parametrize, bare async def.
Nothing here binds a real IPC port, so these stay parallel-safe.
"""

import asyncio
import logging
import sys

import pytest

from lib.error_status import PNG_LOST_CONN_TO_PARENT, PngError
from lib.ipc import PngAppId
from lib.subsystem import (AsyncSubsystem, MgmtIpcHandle, PubSubRole,
                           SyncSubsystem)

# -------------------------------------- HELPERS -----------------------------------------------------------------------

def _test_logger(owner) -> logging.Logger:
    """Per-instance logger.

    get_logger() asserts a name is only initialized once per process, so every stub needs a
    logger of its own rather than one named after the subsystem.
    """

    logger = logging.getLogger(f"test_subsystem_{id(owner)}")
    logger.addHandler(logging.NullHandler())
    return logger

class _StubSync(SyncSubsystem):
    """Minimal concrete SyncSubsystem that never talks to a launcher."""

    NAME = "stub_sync"
    DESCRIPTION = "Stub Sync Subsystem"

    def __init__(self, stats=None):
        super().__init__()
        self._stats = stats if stats is not None else {}
        self.setup_calls = 0
        self.shutdown_calls = 0
        self.shutdown_reasons = []
        self.pre_boot_calls = 0
        self.on_exit_calls = 0

    def should_run_mgmt_ipc(self, args):
        return False

    def make_logger(self, args):
        return _test_logger(self)

    def pre_boot(self, args):
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

    def should_run_mgmt_ipc(self, args):
        return False

    def make_logger(self, args):
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

@pytest.mark.parametrize("missing", ["setup", "collect_stats", "on_shutdown", "run_forever"])
def test_missing_hook_cannot_be_instantiated(missing):
    """A subsystem that omits any must-implement hook fails at instantiation."""

    body = {
        "NAME": "incomplete",
        "DESCRIPTION": "Incomplete",
        "setup": lambda self: None,
        "run_forever": lambda self: None,
        "collect_stats": lambda self: {},
        "on_shutdown": lambda self, reason: None,
    }
    del body[missing]
    cls = type("_Incomplete", (SyncSubsystem,), body)

    with pytest.raises(TypeError, match="abstract"):
        cls()

# -------------------------------------- PARSER ------------------------------------------------------------------------

def test_base_flags_present(monkeypatch):
    """--config-file and --debug are pre-added by the base."""

    monkeypatch.setattr(sys, "argv", ["prog"])
    args = _StubSync()._parse_args()

    assert args.config_file == "png_config.json"
    assert args.debug is False

def test_add_args_extras_merge_with_base_flags(monkeypatch):
    """A subsystem's own flags parse alongside the base's, neither clobbering the other."""

    class _WithExtras(_StubSync):
        NAME = "with_extras"
        DESCRIPTION = "With Extras"

        def add_args(self, parser):
            parser.add_argument("--replay-server", action="store_true")

    monkeypatch.setattr(sys, "argv", ["prog", "--debug", "--replay-server", "--config-file", "other.json"])
    args = _WithExtras()._parse_args()

    assert args.debug is True
    assert args.replay_server is True
    assert args.config_file == "other.json"

# -------------------------------------- TOKEN GATING ------------------------------------------------------------------

def test_no_tokens_reach_stdout_when_unmanaged(capsys, monkeypatch):
    """The MCP stdio guarantee: with mgmt IPC off, nothing at all is printed.

    In stdio mode stdout is the MCP transport, so a stray handshake token would corrupt it.
    """

    monkeypatch.setattr(sys, "argv", ["prog"])
    app = _StubSync()
    app._bootstrap()
    app.notify_ready()
    app.report_mgmt_ipc_port(12345)

    assert capsys.readouterr().out == ""

def test_notify_ready_is_idempotent(capsys, monkeypatch):
    """Repeated notify_ready() calls emit the init-complete token exactly once."""

    monkeypatch.setattr(sys, "argv", ["prog"])
    app = _StubSync()
    app._bootstrap()
    app._mgmt_ipc_enabled = True

    app.notify_ready()
    app.notify_ready()
    app.notify_ready()

    assert capsys.readouterr().out.count("__PNG_SUBSYSTEM_INIT_COMPLETE__") == 1

def test_ready_not_emitted_when_subsystem_owns_the_timing(capsys, monkeypatch):
    """READY_ON_SETUP_COMPLETE = False leaves the token for the subsystem to send itself."""

    class _LateReady(_StubSync):
        NAME = "late_ready"
        DESCRIPTION = "Late Ready"
        READY_ON_SETUP_COMPLETE = False

    monkeypatch.setattr(sys, "argv", ["prog"])
    app = _LateReady()
    app._bootstrap()
    app._mgmt_ipc_enabled = True
    app._run()

    assert "__PNG_SUBSYSTEM_INIT_COMPLETE__" not in capsys.readouterr().out
    assert app._ready_notified is False

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
    monkeypatch.setattr(sys, "argv", ["prog"])
    monkeypatch.setattr("lib.subsystem.base.os._exit", exits.append)

    app = _StubSync()
    app.logger = logging.getLogger("heartbeat_test")

    with caplog.at_level(logging.ERROR, logger="heartbeat_test"):
        app.handle_heartbeat_missed(3)

    assert exits == [PNG_LOST_CONN_TO_PARENT]
    assert "orphaned" in caplog.text

# -------------------------------------- ROUTE FACADE ------------------------------------------------------------------

@pytest.mark.parametrize("blocked", ["on_shutdown", "on_get_stats", "on_heartbeat_missed"])
def test_mgmt_handle_hides_the_lifecycle_callbacks(blocked):
    """self.mgmt cannot reach the three base-owned handlers.

    They live in separate callback slots rather than the route table, so a subsystem
    registering its own would silently replace the base's with no error.
    """

    mgmt = MgmtIpcHandle(_FakeServer())

    assert not hasattr(mgmt, blocked)

def test_mgmt_handle_forwards_on():
    """Subsystem-specific commands still register normally, via @self.mgmt.on(...)."""

    server = _FakeServer()
    mgmt = MgmtIpcHandle(server)

    @mgmt.on("manual-save")
    def _handler(_args):
        return {}

    assert server.routes == ["manual-save"]

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

    assert app.subscriber is None
    assert app.dealer is None

def test_sync_publisher_is_rejected():
    """There is no sync publisher; declaring one is a mistake worth surfacing loudly."""

    class _SyncPublisher(_StubSync):
        NAME = "sync_publisher"
        DESCRIPTION = "Sync Publisher"
        PUBSUB = PubSubRole.PUBLISHER

    app = _SyncPublisher()
    app.settings = None

    with pytest.raises(NotImplementedError, match="sync publisher"):
        app._build_data_plane()

# -------------------------------------- EXCEPTION FUNNEL --------------------------------------------------------------

def test_png_error_exits_with_its_own_code(monkeypatch):
    """PngError -> SystemExit(e.exit_code)."""

    class _Failing(_StubSync):
        NAME = "failing"
        DESCRIPTION = "Failing"

        def setup(self):
            raise PngError(42, "boom")

    monkeypatch.setattr(sys, "argv", ["prog"])
    monkeypatch.setattr("lib.subsystem.base.load_config_from_json", lambda *a, **k: None)

    with pytest.raises(SystemExit) as exc:
        _Failing.main()

    assert exc.value.code == 42

def test_bare_exception_exits_one(monkeypatch):
    """An unexpected exception -> SystemExit(1), logged with a traceback."""

    class _Failing(_StubSync):
        NAME = "failing_bare"
        DESCRIPTION = "Failing Bare"

        def setup(self):
            raise ValueError("unexpected")

    monkeypatch.setattr(sys, "argv", ["prog"])
    monkeypatch.setattr("lib.subsystem.base.load_config_from_json", lambda *a, **k: None)

    with pytest.raises(SystemExit) as exc:
        _Failing.main()

    assert exc.value.code == 1

def test_on_exit_runs_even_when_setup_raises(monkeypatch):
    """on_exit() is guaranteed, so pre_boot()'s side effects are always undone."""

    class _Failing(_StubSync):
        NAME = "failing_on_exit"
        DESCRIPTION = "Failing Post Boot"

        def setup(self):
            raise ValueError("unexpected")

    monkeypatch.setattr(sys, "argv", ["prog"])
    monkeypatch.setattr("lib.subsystem.base.load_config_from_json", lambda *a, **k: None)

    app_holder = {}
    original_init = _Failing.__init__

    def _capture_init(self):
        original_init(self)
        app_holder["app"] = self

    monkeypatch.setattr(_Failing, "__init__", _capture_init)

    with pytest.raises(SystemExit):
        _Failing.main()

    assert app_holder["app"].pre_boot_calls == 1
    assert app_holder["app"].on_exit_calls == 1

# -------------------------------------- SYNC LIFECYCLE ----------------------------------------------------------------

def test_sync_teardown_runs_after_run_forever(monkeypatch):
    """setup() -> run_forever() -> on_shutdown(), with the event set before teardown."""

    order = []

    class _Ordered(_StubSync):
        NAME = "ordered"
        DESCRIPTION = "Ordered"

        def setup(self):
            order.append("setup")

        def run_forever(self):
            order.append("run_forever")

        def on_shutdown(self, reason):
            order.append("on_shutdown")
            assert self.shutdown_event.is_set()

    monkeypatch.setattr(sys, "argv", ["prog"])
    app = _Ordered()
    app._bootstrap()
    app._run()

    assert order == ["setup", "run_forever", "on_shutdown"]

def test_sync_teardown_runs_even_when_run_forever_raises(monkeypatch):
    """A crash in the main loop still tears the subsystem down."""

    monkeypatch.setattr(sys, "argv", ["prog"])

    class _Crashing(_StubSync):
        NAME = "crashing"
        DESCRIPTION = "Crashing"

        def run_forever(self):
            raise RuntimeError("crash")

    app = _Crashing()
    app._bootstrap()

    with pytest.raises(RuntimeError):
        app._run()

    assert app.shutdown_calls == 1

# -------------------------------------- ASYNC LIFECYCLE ---------------------------------------------------------------

async def test_add_task_registers_and_runs(monkeypatch):
    """add_task() puts work in the registry and the base gathers it."""

    monkeypatch.setattr(sys, "argv", ["prog"])
    app = _StubAsync()
    app._bootstrap()
    app.shutdown_event = asyncio.Event()
    app._shutdown_requested = asyncio.Event()

    ran = []

    async def _work():
        ran.append(True)

    task = app.add_task(_work(), name="Work")
    await task

    assert ran == [True]
    assert task in app._tasks
    assert task.get_name() == "Work"

async def test_add_periodic_runs_until_shutdown(monkeypatch):
    """add_periodic() wires the base's shutdown_event into the periodic helper."""

    monkeypatch.setattr(sys, "argv", ["prog"])
    app = _StubAsync()
    app._bootstrap()
    app.shutdown_event = asyncio.Event()
    app._shutdown_requested = asyncio.Event()

    ticks = []

    async def _tick():
        ticks.append(True)
        if len(ticks) >= 2:
            app.shutdown_event.set()

    await app.add_periodic(1, _tick, name="Ticker")

    assert len(ticks) >= 2

async def test_request_shutdown_triggers_teardown_once(monkeypatch):
    """The teardown task wakes on request, sets the event, and calls on_shutdown once."""

    monkeypatch.setattr(sys, "argv", ["prog"])
    app = _StubAsync()
    app._bootstrap()
    app.shutdown_event = asyncio.Event()
    app._shutdown_requested = asyncio.Event()

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

    monkeypatch.setattr(sys, "argv", ["prog"])

    class _SlowTeardown(_StubAsync):
        NAME = "slow_teardown"
        DESCRIPTION = "Slow Teardown"

        async def on_shutdown(self, reason):
            await asyncio.sleep(0.5)
            self.shutdown_calls += 1

    app = _SlowTeardown()
    app._bootstrap()
    app.shutdown_event = asyncio.Event()
    app._shutdown_requested = asyncio.Event()

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

    monkeypatch.setattr(sys, "argv", ["prog"])
    app = _StubAsync()
    app._bootstrap()
    app.shutdown_event = asyncio.Event()
    app._shutdown_requested = asyncio.Event()

    app.add_task(app._teardown_task(), name="Shutdown Task")

    assert "Shutdown Task" in [task.get_name() for task in app._tasks]

    app.request_shutdown("done")
    await asyncio.gather(*app._tasks)

    assert app.shutdown_calls == 1
