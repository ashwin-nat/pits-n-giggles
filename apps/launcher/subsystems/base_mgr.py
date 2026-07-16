# MIT License
#
# Copyright (c) [2025] [Ashwin Natarajan]
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

import os
import random
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Callable, List, Optional

import psutil
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QPushButton

from lib.child_proc_mgmt import (extract_ipc_port_from_line,
                                 extract_pid_from_line, is_init_complete)
from lib.config import PngSettings
from lib.error_status import (PNG_ERROR_CODE_UNKNOWN,
                              PNG_ERROR_CODE_UNSUPPORTED_OS,
                              PNG_LOST_CONN_TO_PARENT)
from lib.event_counter import EventCounter
from lib.ipc import IpcClientSync

if TYPE_CHECKING:
    from apps.launcher.gui import PngLauncherWindow

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class AppState(Enum):
    """Lifecycle state of a managed subsystem. The value doubles as the default display string."""

    STOPPED     = "Stopped"
    STARTING    = "Starting"      # process spawned, waiting for the child to report init-complete
    RUNNING     = "Running"
    STOPPING    = "Stopping"
    RESTARTING  = "Restarting"
    CRASHED     = "Crashed"
    DISABLED    = "Disabled"      # turned off in settings; will not start
    UNSUPPORTED = "Unsupported"   # not available on this OS; will not start

# States in which a child process exists and has not been reaped yet
ACTIVE_STATES = frozenset({AppState.STARTING, AppState.RUNNING, AppState.STOPPING})

# States from which a stop can be claimed
STOPPABLE_STATES = frozenset({AppState.STARTING, AppState.RUNNING})

# States in which an exiting child is expected to be exiting, and must not be treated as a crash
SHUTTING_DOWN_STATES = frozenset({AppState.STOPPING, AppState.RESTARTING})

@dataclass(slots=True)
class ProcessRun:
    """Everything belonging to one launch of a subsystem's child process.

    A run is created per start() and never reused: the manager drops it the moment the process
    is reaped. Each worker thread is handed the run it was spawned for, so a thread left over
    from an abandoned run reads and writes that dead object instead of racing the run that
    replaced it. `mgr._run is run` is then the one question a straggler has to ask before it
    acts on the manager itself.

    Every mutable field here is written only by the run's own output-capture thread, so they
    need no lock; the manager's lock guards which run is current, not what is in one.
    """

    process: subprocess.Popen
    start_ts_ns: int

    # The process we spawned, until the child reports its own PID (they differ under PyInstaller,
    # where the process we spawn is a bootstrapper that re-execs)
    child_pid: int

    # Reported by the child once it has bound its IPC socket
    ipc_port: Optional[int] = None

    # Startup sync flags: post-start fires only once both tokens have been seen
    init_complete_received: bool = False
    post_start_fired: bool = False

    # Set once this run's process has been reaped, to stop this run's heartbeat thread
    stop_heartbeat: threading.Event = field(default_factory=threading.Event)

    @classmethod
    def spawn(cls, launch_cmd: List[str]) -> "ProcessRun":
        """Launch the child process and build the run around it.

        Args:
            launch_cmd: Command to launch

        Returns:
            The new run

        Raises:
            Whatever Popen raises if the child cannot be launched
        """
        # pylint: disable=consider-using-with
        process = subprocess.Popen(
            launch_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            stdin=subprocess.PIPE
        )
        return cls(process=process, start_ts_ns=time.time_ns(), child_pid=process.pid)

@dataclass(frozen=True)
class ExitReason:
    code: int
    status: str
    title: str
    message: str
    can_restart: bool
    settings_field: Optional[str] = None

@dataclass(slots=True, frozen=True)
class PngAppMgrConfig:
    window: "PngLauncherWindow"
    settings: PngSettings
    args: Optional[List[str]] = None
    debug_mode: bool = False
    coverage_enabled: bool = False
    post_start_cb: Optional[Callable[[], None]] = None
    post_stop_cb: Optional[Callable[[], None]] = None
    auto_restart: bool = True
    max_restart_attempts: int = 3
    restart_delay: float = 2.0
    integration_test_mode: bool = False

class PngAppMgrBase(QObject):
    """Base class for managing subsystem processes"""

    # Qt signals
    status_changed = Signal(str)
    post_start_signal = Signal()
    post_stop_signal = Signal()

    BASE_EXIT_REASONS: dict[int, ExitReason] = {
        PNG_LOST_CONN_TO_PARENT: ExitReason(
            code=PNG_LOST_CONN_TO_PARENT,
            status="Timed out",
            title="Lost Connection to Parent",
            message="The parent process has probably been orphaned. Terminating...",
            can_restart=True,
        ),
        PNG_ERROR_CODE_UNSUPPORTED_OS: ExitReason(
            code=PNG_ERROR_CODE_UNSUPPORTED_OS,
            status="Unsupported OS",
            title="Unsupported OS",
            message="This subsystem is only supported on Windows.",
            can_restart=False,
        ),
        PNG_ERROR_CODE_UNKNOWN: ExitReason(
            code=PNG_ERROR_CODE_UNKNOWN,
            status="Crashed",
            title="Unknown Error",
            message="Please check the logs for details.",
            can_restart=True,
        ),
    }

    # Derived classes MUST override these with specific values
    MODULE_PATH: Optional[str] = None
    DISPLAY_NAME: Optional[str] = None
    SHORT_NAME: Optional[str] = None

    # Derived classes MAY override these
    START_BY_DEFAULT: bool = True
    SHOULD_DISPLAY: bool = True

    def __init_subclass__(cls, **kwargs):
        """Fail at import time if a subclass forgot to fill in the mandatory identity fields"""
        super().__init_subclass__(**kwargs)
        missing = [name for name, value in (
            ("MODULE_PATH", cls.MODULE_PATH),
            ("DISPLAY_NAME", cls.DISPLAY_NAME),
            ("SHORT_NAME", cls.SHORT_NAME),
        ) if value is None]
        if missing:
            raise TypeError(f"{cls.__name__} must define: {', '.join(missing)}")

    def __init__(self,
                 config: PngAppMgrConfig):
        """
        Initialize the subsystem manager

        Args:
            config: Configuration object
        """

        assert self.MODULE_PATH is not None
        assert self.DISPLAY_NAME is not None
        assert self.SHORT_NAME is not None

        super().__init__()
        # ExitReason is frozen, so a shallow copy is enough to give this instance its own map
        self.exit_reasons = dict(self.BASE_EXIT_REASONS)

        self.window = config.window
        self.args = config.args or []
        self.debug_mode = config.debug_mode
        self.coverage_enabled = config.coverage_enabled
        self.curr_settings = config.settings
        self.integration_test_mode = config.integration_test_mode

        # Makes whole lifecycle operations atomic: one start/stop/restart runs to completion before
        # the next decides what to do. Held across the child's shutdown I/O, so for seconds at a
        # time.
        self._lifecycle_lock = threading.Lock()

        # Guards which run is current and the state that goes with it - never the contents of a
        # run. Must stay short, because _capture_output takes it and that thread is what drains
        # the child's stdout: stall it and the pipe fills, the child blocks mid-write, and a child
        # blocked on write cannot answer the shutdown _lifecycle_lock is waiting on. That is why
        # these are two locks. Order, when both are taken: _lifecycle_lock, then _process_lock.
        #
        # Invariant: _run is not None exactly while _state is in ACTIVE_STATES; _launch_locked
        # establishes it and _finalize_stop tears it down, both under this lock.
        self._run: Optional[ProcessRun] = None
        self._process_lock = threading.Lock()

        # Lifecycle state. Transitions are made under _process_lock; reads are lock-free.
        self._state = AppState.STOPPED
        # Overrides the state's own display string when set (crash reason, restart counter)
        self._status_label: Optional[str] = None

        # Auto-restart configuration
        self.auto_restart = config.auto_restart
        self.max_restart_attempts = config.max_restart_attempts
        self.restart_delay = config.restart_delay
        self._restart_count = 0
        self._stats: Optional[dict] = None

        # Hooks
        self._post_start_hook: Optional[Callable[[], None]] = config.post_start_cb
        self._post_stop_hook: Optional[Callable[[], None]] = config.post_stop_cb
        if self._post_start_hook:
            self.post_start_signal.connect(self._post_start_hook)

        if self._post_stop_hook:
            self.post_stop_signal.connect(self._post_stop_hook)

        # IPC and heartbeat settings
        self.heartbeat_interval: float = 5.0  # seconds
        self.heartbeat_timeout_ms: int = 3000  # must be shorter than heartbeat_interval
        self.num_missable_heartbeats: int = 3

        # Lifecycle stats
        self._lifecycle_stats = EventCounter()

    @property
    def ipc_port(self) -> Optional[int]:
        """IPC port reported by the running child, or None if there is no child or it has not
        reported one yet"""
        return self._run.ipc_port if self._run else None

    @property
    def status(self) -> str:
        """Display string for the current state"""
        return self._status_label or self._state.value

    @property
    def is_running(self) -> bool:
        """True while this manager owns a child process, from a successful spawn until the
        process has exited and been reaped"""
        return self._state in ACTIVE_STATES

    def register_exit_reason(self, code: int, reason: ExitReason):
        """Register an exit reason

        Args:
            code: Process Exit code
            reason: Exit reason
        """
        self.exit_reasons[code] = reason

    def get_buttons(self) -> List[QPushButton]:
        """
        Return button definitions for this subsystem's UI panel

        Returns:
            List of buttons
        """
        raise NotImplementedError

    def on_settings_change(self, new_settings: PngSettings) -> bool:
        """Handle changes in settings for the sub-application

        :param new_settings: New settings

        :return: True if the app needs to be restarted
        """
        raise NotImplementedError

    def get_start_by_default(self) -> bool:
        """Base implementation just uses the class attribute, but this can be overridden for more complex logic"""
        return self.START_BY_DEFAULT

    def get_should_display(self) -> bool:
        """Base implementation just uses the class attribute, but this can be overridden for more complex logic"""
        return self.SHOULD_DISPLAY

    def get_launch_command(self) -> List[str]:
        """Build the subprocess launch command"""
        if getattr(sys, "frozen", False):
            # PyInstaller frozen executable
            cmd = [sys.executable, "--module", self.MODULE_PATH]
        elif self.coverage_enabled:
            # Coverage mode
            cmd = [
                sys.executable,
                '-m', 'coverage',
                'run',
                '--parallel-mode',
                '--rcfile', 'scripts/.coveragerc_integration',
                '-m', self.MODULE_PATH
            ]
        else:
            # Normal Python execution
            cmd = [sys.executable, "-m", self.MODULE_PATH]

        # Add additional arguments
        cmd.extend(self.args)
        return cmd

    def start(self, reason: str):
        """Start the subsystem process"""
        with self._lifecycle_lock:
            self._do_start(reason)

    def _do_start(self, reason: str):
        """Body of start(). Caller holds _lifecycle_lock.

        Args:
            reason: Why the subsystem is being started
        """
        with self._process_lock:
            if self.is_running:
                self.debug_log(f"{self.DISPLAY_NAME} is already running")
                return

            if reason != "Initial auto-start":
                self.info_log(f"Starting {self.DISPLAY_NAME}... Reason: {reason}")

            # Stats belong to the child that reported them, and outlive the run they came from
            self._stats = None

            try:
                self._launch_locked()
                self._lifecycle_stats.track_event("lifecycle", "start")
                start_error = None

            except Exception as e: # pylint: disable=broad-exception-caught
                self.error_log(f"Failed to start {self.DISPLAY_NAME}: {e}")
                self._set_state_locked(AppState.CRASHED)
                self._lifecycle_stats.track_event("lifecycle", "start_failed")
                start_error = f"Failed to start {self.DISPLAY_NAME}: {e}"

        self._publish_status()
        if start_error:
            self._integration_fail(start_error)

    def _launch_locked(self):
        """Spawn the child process and the workers that watch it.

        Caller holds _process_lock and owns what happens if this raises.

        Raises:
            Whatever Popen raises if the child cannot be launched
        """
        launch_cmd = self.get_launch_command()
        self.debug_log(f"Launch command: {' '.join(launch_cmd)}")

        run = ProcessRun.spawn(launch_cmd)
        self._run = run

        # Both must be set before the workers are spawned: each thread compares its own run
        # against the current one, and reads the state, to know it is still wanted.
        self._set_state_locked(AppState.STARTING)
        try:
            self._spawn_workers(run)
        except Exception:
            # The child is alive but nothing is watching it. Drop the run and kill it, so the
            # caller's CRASHED state does not leave _run set - a later start() would otherwise
            # overwrite _run and lose this process for good.
            self._run = None
            self._terminate_process(run)
            raise

        self.debug_log(f"{self.DISPLAY_NAME} started (PID: {run.child_pid})")

    def _spawn_workers(self, run: ProcessRun):
        """Start the three threads that watch one run, each bound to the run it watches.

        Args:
            run: The run to watch
        """
        for target, name in (
            (self._capture_output, "output"),
            (self._monitor_exit, "monitor"),
            (self._send_heartbeat, "heartbeat"),
        ):
            threading.Thread(
                target=target,
                args=(run,),
                daemon=True,
                name=f"{self.DISPLAY_NAME}-{name}"
            ).start()

    def stop(self, reason: str, final_state: AppState = AppState.STOPPED):
        """Stop the subsystem process

        Args:
            reason: Why the subsystem is being stopped
            final_state: State to settle in once the child is gone. RESTARTING keeps the manager
                         marked as shutting down across a restart's stop/start seam.
        """
        with self._lifecycle_lock:
            self._do_stop(reason, final_state)

    def _do_stop(self, reason: str, final_state: AppState):
        """Body of stop(). Caller holds _lifecycle_lock, and holds it for the whole shutdown:
        restart() needs the child to actually be gone when this returns, and _monitor_exit
        needs a settled state to mean that no shutdown is in flight.

        restart() calls this directly, so a subclass that overrides stop() would not be
        consulted by a restart. No subclass does; override this instead if one ever needs to.

        Args:
            reason: Why the subsystem is being stopped
            final_state: State to settle in once the child is gone
        """
        with self._process_lock:
            if self._state not in STOPPABLE_STATES:
                self.debug_log(f"{self.DISPLAY_NAME} is not running")
                return

            # Claim the stop while holding the lock: _monitor_exit reads the state to tell an
            # expected exit from a crash, and a concurrent stop() must bail out on it.
            self._set_state_locked(AppState.STOPPING)
            run = self._run

        self._publish_status()
        self.debug_log(f"Stopping {self.DISPLAY_NAME}... Reason: {reason}")
        self._lifecycle_stats.track_event("lifecycle", "stop")

        # Force Qt to update UI now. Only does anything on the GUI thread, which is the
        # start/stop button path; on the task threads there is no event loop to pump.
        self.window.process_events()

        # Try graceful shutdown first (IPC would go here)
        if self._send_ipc_shutdown(run, reason):
            try:
                run.process.wait(timeout=10)
                self.debug_log(f"{self.DISPLAY_NAME} exited gracefully")
            except subprocess.TimeoutExpired:
                self.debug_log(f"{self.DISPLAY_NAME} did not exit in time, forcing...")
                self._terminate_process(run)
        else:
            self._terminate_process(run)

        self._finalize_stop(final_state)

    def _finalize_stop(self, state: AppState, label: Optional[str] = None):
        """Clear per-run state, publish the terminal state and fire the post-stop hook.

        Shared tail of the expected (stop) and unexpected (crash) shutdown paths. Must be
        called without _process_lock held - the hook may be delivered to a directly
        connected slot, which must never run while the lock is held.

        Args:
            state: State to settle in now that no child process is left
            label: Display string, if the state's own name is not specific enough
        """
        with self._process_lock:
            # Dropping the run is the whole cleanup: its threads can still write to it, but
            # nothing reads it any more, and `mgr._run is run` now answers False for all of them
            self._run = None
            self._set_state_locked(state, label)

        self._publish_status()
        if self._post_stop_hook:
            self.post_stop_signal.emit()

    def restart(self, reason: str):
        """Restart the subsystem"""
        self.debug_log(f"Restarting {self.DISPLAY_NAME}...")
        _reason = f"Restarting: {reason}"

        # The stop has to complete under one claim: a stop already in flight would otherwise make
        # ours a no-op, and then our start would bail on the STOPPING state, silently turning a
        # restart into a stop.
        with self._lifecycle_lock:
            # Settling in RESTARTING rather than STOPPED marks the manager as shutting down for
            # the whole stop/start seam, so a straggler thread from the old run stays quiet.
            if self.is_running:
                self._do_stop(_reason, final_state=AppState.RESTARTING)
            else:
                self._set_state(AppState.RESTARTING)

        time.sleep(1)  # Brief pause

        # Outside the claim, and start() rather than _do_start(): subclasses override start() to
        # refuse to come up at all (HudAppMgr, when disabled or unsupported), and a restart must
        # honour that. Safe to let go of the lock here because RESTARTING is holding the seam -
        # it is not a stoppable state, so nothing can shut us down between the two halves.
        self.start(_reason)

    def start_stop(self, reason: str):
        """Toggle between start and stop"""
        if self.is_running:
            self.stop(reason)
        else:
            # Reset restart counter on manual stop
            self._restart_count = 0
            self.debug_log(f"{self.DISPLAY_NAME} Reset restart counter on manual stop")
            self.start(reason)

    def get_stats(self) -> dict:
        """Get stats combining child process stats and local lifecycle stats"""
        result = {}
        if self._stats:
            result.update(self._stats)
        result["__mgr_lifecycle__"] = self._lifecycle_stats.get_stats()
        return result

    def _should_auto_restart(self, exit_code: int) -> bool:
        reason = self.exit_reasons.get(exit_code)

        if reason and not reason.can_restart:
            return False

        if not self.auto_restart:
            return False

        if self._restart_count >= self.max_restart_attempts:
            self.error_log(
                f"{self.DISPLAY_NAME} has reached maximum restart attempts ({self.max_restart_attempts})"
            )
            return False

        return True

    def _auto_restart(self):
        """Attempt automatic restart after unexpected exit"""
        self._restart_count += 1
        self._lifecycle_stats.track_event("lifecycle", "auto_restart")

        self.warning_log(
            f"{self.DISPLAY_NAME} auto-restart attempt {self._restart_count}/{self.max_restart_attempts}"
        )
        self._set_state(
            AppState.RESTARTING,
            label=f"Restarting ({self._restart_count}/{self.max_restart_attempts})")

        # Wait before restarting
        time.sleep(self.restart_delay)

        # Attempt restart. start() takes the state out of RESTARTING, on both its paths.
        self.start(f"Auto-restart attempt {self._restart_count}")

    def _capture_output(self, run: ProcessRun):
        """Capture subprocess output and react to structured launcher tokens.

        Sole writer of the run's mutable fields, which is why they need no lock.

        Args:
            run: The run whose output to capture
        """

        stdout = run.process.stdout
        if not stdout:
            return

        self.debug_log(f"Capturing {self.DISPLAY_NAME} output...")

        for raw_line in stdout:
            if not raw_line:
                break

            line = raw_line.rstrip()

            # ---------------------------------------------------------
            # 1. PID token
            # ---------------------------------------------------------
            if pid := extract_pid_from_line(line):
                pid_recv_ts = time.time_ns()
                # Against the PID we spawned, not the last one reported: what this tells us is
                # whether the child re-exec'd (PyInstaller), which is a fact about the launch
                changed = (pid != run.process.pid)
                run.child_pid = pid
                self._lifecycle_stats.track_packet_latency(
                    "startup_latency", "to_pid", run.start_ts_ns, pid_recv_ts)
                self.debug_log(f"{self.DISPLAY_NAME} PID update: {pid} changed={changed}")
                continue

            # ---------------------------------------------------------
            # 2. IPC PORT token
            # ---------------------------------------------------------
            if port := extract_ipc_port_from_line(line):
                port_recv_ts = time.time_ns()
                run.ipc_port = port
                self._lifecycle_stats.track_packet_latency(
                    "startup_latency", "to_ipc_port", run.start_ts_ns, port_recv_ts)
                self.debug_log(f"{self.DISPLAY_NAME} IPC port reported: {port}")
                self._maybe_fire_post_start(run)
                continue

            # ---------------------------------------------------------
            # 3. INIT COMPLETE token
            # ---------------------------------------------------------
            if is_init_complete(line):
                init_recv_ts = time.time_ns()
                self.debug_log(f"{self.DISPLAY_NAME} initialization complete")
                run.init_complete_received = True
                with self._process_lock:
                    # Guarded: only this run may report itself ready, and only out of STARTING,
                    # so a late token cannot drag a stop back into RUNNING
                    became_ready = self._run is run and self._state is AppState.STARTING
                    if became_ready:
                        self._set_state_locked(AppState.RUNNING)
                if became_ready:
                    self._publish_status()
                self._lifecycle_stats.track_packet_latency(
                    "startup_latency", "to_init_complete", run.start_ts_ns, init_recv_ts)
                self._maybe_fire_post_start(run)
                continue

            # ---------------------------------------------------------
            # 4. Regular stdout (non-token) - send to info log
            # ---------------------------------------------------------
            self.info_log(line, src=self.SHORT_NAME)

    def _monitor_exit(self, run: ProcessRun):
        """Monitor for unexpected process exit

        Args:
            run: The run whose process to wait on
        """
        try:
            ret_code = run.process.wait()

            # Decide under the operation lock. A stop() may be killing this very run right now,
            # in which case the exit is expected and settling it is its job - waiting for it to
            # finish is what stops a stop and a crash from both finalizing the same run.
            with self._lifecycle_lock:
                # Only the current run may speak for the manager: an abandoned run's process
                # exiting is expected, and whoever abandoned it has already accounted for it.
                if self._run is not run:
                    return

                # An expected exit, already being handled by stop() or restart()
                if self._state in SHUTTING_DOWN_STATES:
                    return

                # Unexpected exit
                if self.is_running:
                    self._handle_unexpected_exit(ret_code)

        finally:
            self.debug_log(f"{self.DISPLAY_NAME} Setting heartbeat stop flag...")
            run.stop_heartbeat.set()

    def _handle_unexpected_exit(self, ret_code: int):
        """Handle unexpected process termination"""
        err_msg = f"{self.DISPLAY_NAME} exited unexpectedly (code: {ret_code})"
        self.error_log(err_msg)
        self._lifecycle_stats.track_event("lifecycle", "unexpected_exit")
        self._integration_fail(err_msg)

        reason = self.exit_reasons.get(ret_code, self.exit_reasons[PNG_ERROR_CODE_UNKNOWN])
        self._finalize_stop(AppState.CRASHED, label=reason.status)

        if reason.settings_field:
            self.show_error(reason.title, f"{reason.message}\nField: {reason.settings_field}")
        else:
            self.show_error(reason.title, reason.message)

        # Attempt auto-restart if enabled
        if self._should_auto_restart(ret_code):
            threading.Thread(
                target=self._auto_restart,
                daemon=True,
                name=f"{self.DISPLAY_NAME}-auto-restart"
            ).start()
        elif self.auto_restart:
            self.error_log(
                f"{self.DISPLAY_NAME} will not auto-restart (max attempts reached)"
            )

    def _send_heartbeat(self, run: ProcessRun):
        """Send periodic heartbeat to child process

        Args:
            run: The run whose child to beat against
        """
        # Initial random delay. The run can end while we sleep, in which case the loop below
        # never runs a beat.
        time.sleep(random.uniform(0, 2.0))

        failed_count = 0
        self.debug_log(f"{self.DISPLAY_NAME}: Heartbeat job starting...")

        # A beat that can outlive its own interval would stack up behind itself. Checked here
        # rather than in __init__, where both knobs still hold their (correct) defaults.
        assert self.heartbeat_timeout_ms < self.heartbeat_interval * 1000, \
            f"{self.DISPLAY_NAME}: heartbeat timeout must be shorter than the interval"

        while not run.stop_heartbeat.is_set():
            # Our own process is normally reaped before this, which sets the flag above. Check
            # anyway: a stale run must never stop the run that replaced it.
            if self._run is not run:
                self.debug_log(f"{self.DISPLAY_NAME}: Heartbeat exiting, run superseded.")
                break

            # If we are stopping or restarting, do not treat missing port as failure
            if self._state in SHUTTING_DOWN_STATES:
                self.debug_log(f"{self.DISPLAY_NAME}: Heartbeat exiting, subsystem is shutting down.")
                break

            self.debug_log(f"{self.DISPLAY_NAME}: Sending heartbeat to port {run.ipc_port}...")
            port = run.ipc_port

            if not port:
                # No port means child hasn't initialised yet - treat as a missed heartbeat
                failed_count += 1
                self._lifecycle_stats.track_event("heartbeat", "miss")
                self.debug_log(f"{self.DISPLAY_NAME}: No IPC port yet, missed heartbeat count={failed_count}")
            else:
                try:
                    rsp = IpcClientSync(port, self.heartbeat_timeout_ms).heartbeat()
                    if rsp.get("status") == "success":
                        failed_count = 0
                        self._lifecycle_stats.track_event("heartbeat", "success")
                        self.debug_log(f"{self.DISPLAY_NAME}: Heartbeat success response: {rsp} on port {port}")
                    else:
                        failed_count += 1
                        self._lifecycle_stats.track_event("heartbeat", "miss")
                        self.debug_log(f"{self.DISPLAY_NAME}: Heartbeat failed with response: {rsp} on port {port}")
                except Exception as e: # pylint: disable=broad-exception-caught
                    self.debug_log(f"Heartbeat error: {e}")
                    self._lifecycle_stats.track_event("heartbeat", "miss")
                    failed_count += 1

            # Check for excessive failures
            if failed_count > self.num_missable_heartbeats and not self.debug_mode:
                self.error_log(
                    f"{self.DISPLAY_NAME} missed {failed_count} heartbeats, stopping..."
                )
                self._lifecycle_stats.track_event("heartbeat", "fail_stop")
                self.stop("Heartbeat failure")
                break

            run.stop_heartbeat.wait(self.heartbeat_interval)

        self.debug_log(f"{self.DISPLAY_NAME}: Heartbeat job exiting...")

    def _send_ipc_shutdown(self, run: ProcessRun, reason: str) -> bool:
        """Send IPC shutdown command

        Args:
            run: The run to shut down
            reason: Why the subsystem is being stopped

        Returns:
            True if the child acknowledged the shutdown
        """
        if not run.ipc_port:
            self.debug_log("Cannot send IPC shutdown - no IPC port detected from child.")
            return False

        try:
            ipc_client = IpcClientSync(run.ipc_port)
            stats_rsp = ipc_client.get_stats()
            if stats_rsp.get("status") == "success":
                self._stats = stats_rsp.get("stats")
            else:
                self.debug_log(f"IPC get-stats failed: {stats_rsp}")
                self._stats = None

            rsp = ipc_client.shutdown_child(reason)
            ok = rsp.get("status") == "success"
            self._lifecycle_stats.track_event("ipc", "shutdown_ok" if ok else "shutdown_fail")
            return ok
        except Exception as e: # pylint: disable=broad-exception-caught
            self.debug_log(f"{self.DISPLAY_NAME} | IPC shutdown failed: {e}")
            self._lifecycle_stats.track_event("ipc", "shutdown_fail")
            return False

    def _terminate_process(self, run: ProcessRun):
        """Force-terminate the run's process and all its subprocesses

        Args:
            run: The run to terminate
        """
        # The PID we spawned, or the one the child reported for itself (PyInstaller case)
        target_pid = run.child_pid
        try:
            parent = psutil.Process(target_pid)
            children = parent.children(recursive=True)
            for child in children:
                child.terminate()
            parent.terminate()
            _, alive = psutil.wait_procs([parent] + children, timeout=5)
            for p in alive:
                p.kill()
        except Exception as e: # pylint: disable=broad-exception-caught
            self.debug_log(f"Failed to terminate process tree for PID {target_pid}: {e}")

    def _maybe_fire_post_start(self, run: ProcessRun) -> None:
        """Fire the post-start hook only once and only after both init & ipc port received.

        Args:
            run: The run reporting itself started
        """
        if run.post_start_fired or not run.init_complete_received or run.ipc_port is None:
            return

        # An abandoned run must not announce itself as started: its post-start hook would tell
        # the UI a subsystem is up when what is up is a different run, or nothing at all.
        if self._run is not run:
            return

        run.post_start_fired = True
        self.debug_log(f"{self.DISPLAY_NAME}: All startup signals received - firing post-start hook")
        if self._post_start_hook:
            self.post_start_signal.emit()

    def _set_state(self, state: AppState, label: Optional[str] = None):
        """Transition to a new state and publish it. Must be called without _process_lock held.

        Args:
            state: New state
            label: Display string, if the state's own name is not specific enough
        """
        with self._process_lock:
            self._set_state_locked(state, label)
        self._publish_status()

    def _set_state_locked(self, state: AppState, label: Optional[str] = None):
        """Transition to a new state without publishing it.

        For transitions that must be atomic with the surrounding critical section. The caller
        holds _process_lock and must call _publish_status() once it has released it.

        Args:
            state: New state
            label: Display string, if the state's own name is not specific enough
        """
        self._state = state
        self._status_label = label

    def _publish_status(self):
        """Emit the current display string. Must be called without _process_lock held, since a
        directly connected slot would otherwise run under it."""
        if self.SHOULD_DISPLAY:
            self.status_changed.emit(self.status)

    # Logging methods
    def info_log(self, message: str, src: str = ''):
        """Log info message"""
        self.window.info_log(message, src)

    def debug_log(self, message: str):
        """Log debug message"""
        self.window.debug_log(message)

    def warning_log(self, message: str):
        """Log warning message"""
        self.window.warning_log(message)

    def error_log(self, message: str):
        """Log error message"""
        self.window.error_log(message)

    def get_icon(self, key: str) -> Optional[QIcon]:
        """Get icon by key"""
        return self.window.get_icon(key)

    def build_button(self, icon: QIcon, callback: Callable[[], None], tooltip: str = "") -> QPushButton:
        """Build a button with the given icon and callback"""
        return self.window.build_button(icon, callback, tooltip)

    def set_button_state(self, button: QPushButton, enabled: bool):
        """Enable/disable a QPushButton."""
        self.window.set_button_state(button, enabled)

    def set_button_icon(self, button: QPushButton, icon: QIcon):
        """Set icon on a QPushButton."""
        self.window.set_button_icon(button, icon)

    def set_button_tooltip(self, button: QPushButton, tooltip: str):
        """Set tooltip for a QPushButton and store it for later use."""
        self.window.set_button_tooltip(button, tooltip)

    def show_success(self, title: str, message: str):
        """Display a success/info message box."""
        self.window.show_success(title, message)

    def show_error(self, title: str, message: str):
        """Display an error message box."""
        self.window.show_error(title, message)

    def _integration_fail(self, message: str):
        """Handle integration test failure by logging and exiting immediately."""
        if not self.integration_test_mode:
            return

        # In integration mode we intentionally hard-exit the app
        # We do NOT attempt graceful Qt shutdown because CI should fail fast
        # and auto-restart must never mask instability.
        self.error_log(f"[INTEGRATION TEST MODE] {message}")
        # os._exit required: child process must terminate immediately without
        # running atexit handlers or flushing stdio buffers from parent.
        os._exit(1)
