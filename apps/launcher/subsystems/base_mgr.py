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

import random
import subprocess
import sys
import threading
import time
from typing import TYPE_CHECKING, Callable, List, Optional

import psutil
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QPushButton

from lib.child_proc_mgmt import extract_pid_from_line, is_init_complete
from lib.config import PngSettings
from lib.error_status import (PNG_ERROR_CODE_HTTP_PORT_IN_USE,
                              PNG_ERROR_CODE_UDP_TELEMETRY_PORT_IN_USE,
                              PNG_ERROR_CODE_UNKNOWN, PNG_LOST_CONN_TO_PARENT)
from lib.ipc import IpcParent, get_free_tcp_port

if TYPE_CHECKING:
    from apps.launcher.gui import PngLauncherWindow

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class PngAppMgrBase(QObject):
    """Base class for managing subsystem processes"""

    # Qt signals
    status_changed = Signal(str)
    post_start_signal = Signal()
    post_stop_signal = Signal()

    EXIT_ERRORS = {
        PNG_ERROR_CODE_HTTP_PORT_IN_USE: {
            "title": "HTTP Port In Use",
            "message": (
                "failed to start because the required port is already in use.\n"
                "Please close the conflicting app or change the port in settings."
            ),
            "status": "HTTP Port Conflict",
        },
        PNG_ERROR_CODE_UDP_TELEMETRY_PORT_IN_USE: {
            "title": "Telemetry Port In Use",
            "message": (
                "failed to start because the required UDP port is already in use.\n"
                "Please close the conflicting app or setup forwarding to the current port in settings."
            ),
            "status": "UDP Port Conflict",
        },
        PNG_ERROR_CODE_UNKNOWN: {
            "title": "Unknown Error",
            "message": (
                "failed to start due to an unknown error.\n"
                "Please check the logs for more details."
            ),
            "status": "Crashed",
        },
        PNG_LOST_CONN_TO_PARENT: {
            "title": "Lost Connection to Parent",
            "message": (
                "lost connection to the parent process.\n"
                "Please check the logs for more details."
            ),
            "status": "Timed out",
        }
    }
    DEFAULT_EXIT = EXIT_ERRORS[PNG_ERROR_CODE_UNKNOWN]

    def __init__(self,
                 window: "PngLauncherWindow",
                 module_path: str,
                 display_name: str,
                 short_name: str,
                 settings: PngSettings,
                 start_by_default: bool = False,
                 args: Optional[List[str]] = None,
                 debug_mode: bool = False,
                 coverage_enabled: bool = False,
                 http_port_conflict_settings_field: Optional[str] = None,
                 udp_port_conflict_settings_field: Optional[str] = None,
                 post_start_cb: Optional[Callable[[], None]] = None,
                 post_stop_cb: Optional[Callable[[], None]] = None,
                 auto_restart: bool = True,
                 max_restart_attempts: int = 3,
                 restart_delay: float = 2.0):
        """
        Initialize the subsystem manager

        Args:
            module_path: Python module path to run (e.g., 'my_app.server')
            display_name: Human-readable name for UI display
            short_name: Short name for logging
            start_by_default: Whether to auto-start this subsystem
            args: Additional command-line arguments
            debug_mode: Enable debug mode (disables heartbeat timeout)
            coverage_enabled: Enable code coverage tracking
            http_port_conflict_settings_field: Settings field to check for HTTP port conflicts
            udp_port_conflict_settings_field: Settings field to check for UDP port conflicts
            auto_restart: Enable automatic restart on unexpected exits
            max_restart_attempts: Maximum number of restart attempts (default: 3)
            restart_delay: Delay in seconds between restart attempts (default: 2.0)
        """
        super().__init__()


        self.window = window
        self.module_path = module_path
        self.display_name = display_name
        self.short_name = short_name
        self.start_by_default = start_by_default
        self.args = args or []
        self.debug_mode = debug_mode
        self.coverage_enabled = coverage_enabled
        self.http_port_conflict_field = http_port_conflict_settings_field
        self.udp_port_conflict_field = udp_port_conflict_settings_field
        self.curr_settings = settings

        # Process management
        self.process: Optional[subprocess.Popen] = None
        self._process_lock = threading.Lock()
        self.child_pid: Optional[int] = None
        self.is_running = False
        self._is_restarting = threading.Event()
        self._is_stopping = threading.Event()

        # Status tracking
        self.status = "Stopped"

        # Auto-restart configuration
        self.auto_restart = auto_restart
        self.max_restart_attempts = max_restart_attempts
        self.restart_delay = restart_delay
        self._restart_count = 0
        self._last_crash_time: Optional[float] = None
        self._restart_window = 60.0  # Reset counter if stable for 60 seconds

        # Hooks
        self._post_start_hook: Optional[Callable[[], None]] = post_start_cb
        self._post_stop_hook: Optional[Callable[[], None]] = post_stop_cb
        if self._post_start_hook:
            self.post_start_signal.connect(self._post_start_hook)

        if self._post_stop_hook:
            self.post_stop_signal.connect(self._post_stop_hook)

        # IPC and heartbeat settings
        self.ipc_port: Optional[int] = None
        self.heartbeat_interval: float = 5.0  # seconds
        self.num_missable_heartbeats: int = 3
        self._stop_heartbeat = threading.Event()

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

    def get_launch_command(self) -> List[str]:
        """Build the subprocess launch command"""
        if getattr(sys, "frozen", False):
            # PyInstaller frozen executable
            cmd = [sys.executable, "--module", self.module_path]
        elif self.coverage_enabled:
            # Coverage mode
            cmd = [
                sys.executable,
                '-m', 'coverage',
                'run',
                '--parallel-mode',
                '--rcfile', 'scripts/.coveragerc_integration',
                '-m', self.module_path
            ]
        else:
            # Normal Python execution
            cmd = [sys.executable, "-m", self.module_path]

        # Add additional arguments
        cmd.extend(self.args)

        # Add IPC port if available
        if self.ipc_port:
            cmd.extend(["--ipc-port", str(self.ipc_port)])

        return cmd

    def start(self, reason: str):
        """Start the subsystem process"""

        with self._process_lock:
            if self.is_running:
                self.debug_log(f"{self.display_name} is already running")
                return

            self.info_log(f"Starting {self.display_name}... Reason: {reason}")
            self._update_status("Starting")

            self.ipc_port = get_free_tcp_port()

            # Build and execute launch command
            launch_cmd = self.get_launch_command()
            self.debug_log(f"Launch command: {' '.join(launch_cmd)}")

            try:
                # Start the subprocess
                # pylint: disable=consider-using-with
                self.process = subprocess.Popen(
                    launch_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    stdin=subprocess.PIPE
                )

                self.is_running = True
                self.child_pid = self.process.pid

                # Start monitoring threads
                threading.Thread(
                    target=self._capture_output,
                    daemon=True,
                    name=f"{self.display_name}-output"
                ).start()

                threading.Thread(
                    target=self._monitor_exit,
                    daemon=True,
                    name=f"{self.display_name}-monitor"
                ).start()

                threading.Thread(
                    target=self._send_heartbeat,
                    daemon=True,
                    name=f"{self.display_name}-heartbeat"
                ).start()

                self.info_log(f"{self.display_name} started (PID: {self.child_pid})")

            except Exception as e: # pylint: disable=broad-exception-caught
                self.error_log(f"Failed to start {self.display_name}: {e}")
                self._update_status("Crashed")
                self.is_running = False

    def stop(self, reason: str):
        """Stop the subsystem process"""
        with self._process_lock:
            if not self.is_running:
                self.debug_log(f"{self.display_name} is not running")
                return

            self.info_log(f"Stopping {self.display_name}...")
            self._is_stopping.set()
            self._update_status("Stopping")

            # Force Qt to update UI now
            self.window.process_events()

            # Try graceful shutdown first (IPC would go here)
            if self._send_ipc_shutdown(reason):
                try:
                    self.process.wait(timeout=10)
                    self.debug_log(f"{self.display_name} exited gracefully")
                except subprocess.TimeoutExpired:
                    self.debug_log(f"{self.display_name} did not exit in time, forcing...")
                    self._terminate_process()
            else:
                self._terminate_process()

            # Clean up state
            self.process = None
            self.child_pid = None
            self.is_running = False
            self._update_status("Stopped")
            self._is_stopping.clear()

            # Run post-stop hook
            if self._post_stop_hook:
                try:
                    self.post_stop_signal.emit()
                except Exception as e: # pylint: disable=broad-exception-caught
                    self.error_log(f"Post-stop hook error: {e}")

    def restart(self, reason: str):
        """Restart the subsystem"""
        self._is_restarting.set()
        self.info_log(f"Restarting {self.display_name}...")
        _reason = f"Restarting: {reason}"

        if self.is_running:
            self.stop(_reason)

        time.sleep(1)  # Brief pause
        self.start(_reason)
        self._is_restarting.clear()

    def start_stop(self, reason: str):
        """Toggle between start and stop"""
        if self.is_running:
            self.stop(reason)
        else:
            # Reset restart counter on manual stop
            self._restart_count = 0
            self.debug_log(f"{self.display_name} Reset restart counter on manual stop")
            self.start(reason)

    def _should_auto_restart(self) -> bool:
        """Determine if auto-restart should be attempted"""
        if not self.auto_restart:
            return False

        if self._restart_count >= self.max_restart_attempts:
            self.error_log(
                f"{self.display_name} has reached maximum restart attempts ({self.max_restart_attempts})"
            )
            return False

        return True

    def _auto_restart(self):
        """Attempt automatic restart after unexpected exit"""
        self._restart_count += 1

        self.warning_log(
            f"{self.display_name} auto-restart attempt {self._restart_count}/{self.max_restart_attempts}"
        )
        self._update_status(f"Restarting ({self._restart_count}/{self.max_restart_attempts})")

        # Wait before restarting
        time.sleep(self.restart_delay)

        # Attempt restart
        self._is_restarting.set()
        try:
            self.start(f"Auto-restart attempt {self._restart_count}")
        finally:
            self._is_restarting.clear()

    def _capture_output(self):
        """Capture subprocess output"""

        # Snapshot process and stdout once under the lock
        with self._process_lock:
            process = self.process
            # If process or its stdout isn't available, exit immediately.
            if not process or not process.stdout:
                return
            stdout = process.stdout

        self.debug_log(f"Capturing {self.display_name} output...")
        for line in stdout:
            if not line:
                # EOF reached
                break

            line = line.rstrip()

            if pid := extract_pid_from_line(line):
                with self._process_lock:
                    # Check current PID safely in case process changed meanwhile
                    current_pid = self.process.pid if self.process else None
                    changed = current_pid is not None and current_pid != pid
                    self.child_pid = pid
                self.debug_log(f"{self.display_name} PID update: {pid} changed = {changed}")
            elif is_init_complete(line):
                self.debug_log(f"{self.display_name} initialization complete")
                with self._process_lock:
                    self._update_status("Running")
                if self._post_start_hook:
                    try:
                        self.post_start_signal.emit()
                    except Exception as e: # pylint: disable=broad-exception-caught
                        self.error_log(f"{self.display_name}: Error in post-start hook: {e}")

            else:
                self.info_log(line, src=self.short_name)


    def _monitor_exit(self):
        """Monitor for unexpected process exit"""
        process = self.process

        try:
            if not process:
                return

            ret_code = process.wait()

            # Check if this is still the current process
            if self.process is not process:
                return

            # Check for expected exits
            if self._is_restarting.is_set() or self._is_stopping.is_set():
                return

            if ret_code == 15:  # SIGTERM during restart
                return

            # Unexpected exit
            if self.is_running:
                self._handle_unexpected_exit(ret_code)

        finally:
            self._stop_heartbeat.set()

    def _handle_unexpected_exit(self, ret_code: int):
        """Handle unexpected process termination"""
        self.error_log(f"{self.display_name} exited unexpectedly (code: {ret_code})")

        with self._process_lock:
            self.is_running = False
            self.child_pid = None
            self.process = None

        # Get error info
        error_info = self.EXIT_ERRORS.get(ret_code, self.DEFAULT_EXIT)
        status = error_info.get("status", "Crashed")
        self._update_status(status)

        # Run post-stop hook
        if self._post_stop_hook:
            try:
                self.post_stop_signal.emit()
            except Exception as e: # pylint: disable=broad-exception-caught
                self.error_log(f"Post-stop hook error: {e}")

        # Attempt auto-restart if enabled
        if self._should_auto_restart():
            threading.Thread(
                target=self._auto_restart,
                daemon=True,
                name=f"{self.display_name}-auto-restart"
            ).start()
        elif self.auto_restart:
            self.error_log(
                f"{self.display_name} will not auto-restart (max attempts reached)"
            )

    def _send_heartbeat(self):
        """Send periodic heartbeat to child process"""
        # Initial random delay
        time.sleep(random.uniform(0, 2.0))

        failed_count = 0
        self.debug_log(f"{self.display_name}: Starting heartbeat job to port {self.ipc_port}...")
        timeout_ms = (int(self.heartbeat_interval) - 2) * 1000
        assert timeout_ms > 0

        while not self._stop_heartbeat.is_set():
            self.debug_log(f"{self.display_name}: Sending heartbeat to port {self.ipc_port}...")
            try:
                rsp = IpcParent(self.ipc_port, timeout_ms).heartbeat()
                if rsp.get("status") == "success":
                    failed_count = 0
                    self.debug_log(f"{self.display_name}: Heartbeat success response: {rsp} on port {self.ipc_port}")
                else:
                    self.debug_log(
                        f"{self.display_name}: Heartbeat failed with response: {rsp} on port {self.ipc_port}"
                    )
                    failed_count += 1

            except Exception as e: # pylint: disable=broad-exception-caught
                self.debug_log(f"Heartbeat error: {e}")
                failed_count += 1

            # Check for excessive failures
            if failed_count > self.num_missable_heartbeats and not self.debug_mode:
                self.error_log(
                    f"{self.display_name} missed {failed_count} heartbeats, stopping..."
                )
                self.stop("Heartbeat failure")
                break

            self._stop_heartbeat.wait(self.heartbeat_interval)

        self._stop_heartbeat.clear()

    def _send_ipc_shutdown(self, reason: str) -> bool:
        """Send IPC shutdown command"""
        try:
            rsp = IpcParent(self.ipc_port).shutdown_child(reason)
            return rsp.get("status") == "success"
        except Exception as e: # pylint: disable=broad-exception-caught
            self.debug_log(f"IPC shutdown failed: {e}")
            return False


    def _terminate_process(self):
        """Force-terminate the process and all its subprocesses"""

        target_pid = None
        if self.child_pid and self.child_pid != (self.process.pid if self.process else None):
            # Terminate actual child (PyInstaller case)
            target_pid = self.child_pid
        elif self.process:
            target_pid = self.process.pid

        if target_pid:
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

    def _update_status(self, status: str):
        """Update status and emit signal"""
        self.status = status
        self.status_changed.emit(status)

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

    def select_file(self, title="Select File", file_filter="All Files (*.*)") -> str:
        """Open a file dialog and return path or None."""
        return self.window.select_file(title, file_filter)
