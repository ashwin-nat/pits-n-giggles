"""
Subsystem Manager Base Class
Manages subprocess lifecycle, monitoring, and IPC
"""

import copy
import random
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Optional, Callable, List, Dict, Any
from PySide6.QtCore import QObject, Signal

import psutil


class SubsystemManager(QObject):
    """Base class for managing subsystem processes"""

    # Qt signals for thread-safe UI updates
    status_changed = Signal(str)

    # Exit error codes (matching your original implementation)
    PNG_ERROR_CODE_HTTP_PORT_IN_USE = 100
    PNG_ERROR_CODE_UDP_TELEMETRY_PORT_IN_USE = 101
    PNG_ERROR_CODE_UNKNOWN = 102
    PNG_LOST_CONN_TO_PARENT = 103

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
                 module_path: str,
                 display_name: str,
                 start_by_default: bool = False,
                 args: Optional[List[str]] = None,
                 debug_mode: bool = False,
                 coverage_enabled: bool = False,
                 http_port_conflict_field: Optional[str] = None,
                 udp_port_conflict_field: Optional[str] = None):
        """
        Initialize the subsystem manager

        Args:
            module_path: Python module path to run (e.g., 'my_app.server')
            display_name: Human-readable name for UI display
            start_by_default: Whether to auto-start this subsystem
            args: Additional command-line arguments
            debug_mode: Enable debug mode (disables heartbeat timeout)
            coverage_enabled: Enable code coverage tracking
            http_port_conflict_field: Settings field name for HTTP port conflicts
            udp_port_conflict_field: Settings field name for UDP port conflicts
        """
        super().__init__()

        self.module_path = module_path
        self.display_name = display_name
        self.start_by_default = start_by_default
        self.args = args or []
        self.debug_mode = debug_mode
        self.coverage_enabled = coverage_enabled
        self.http_port_conflict_field = http_port_conflict_field
        self.udp_port_conflict_field = udp_port_conflict_field

        # Process management
        self.process: Optional[subprocess.Popen] = None
        self._process_lock = threading.Lock()
        self.child_pid: Optional[int] = None
        self.is_running = False
        self._is_restarting = threading.Event()
        self._is_stopping = threading.Event()

        # Status tracking
        self.status = "Stopped"

        # Console interface (set by launcher)
        self.console = None

        # Hooks
        self._post_start_hook: Optional[Callable[[], None]] = None
        self._post_stop_hook: Optional[Callable[[], None]] = None

        # IPC and heartbeat settings
        self.ipc_port: Optional[int] = None
        self.heartbeat_interval: float = 5.0  # seconds
        self.num_missable_heartbeats: int = 3
        self._stop_heartbeat = threading.Event()

    def set_console(self, console):
        """Set the console interface for logging"""
        self.console = console

    def get_buttons(self) -> List[Dict[str, Any]]:
        """
        Return button definitions for this subsystem's UI panel

        Returns:
            List of button dicts with keys:
                - text: Button label
                - command: Callback function
                - primary: (optional) True for primary button styling

        Example:
            return [
                {'text': 'Start', 'command': self.start, 'primary': True},
                {'text': 'Stop', 'command': self.stop},
                {'text': 'Restart', 'command': self.restart},
            ]
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

    def start(self):
        """Start the subsystem process"""
        with self._process_lock:
            if self.is_running:
                self._log_debug(f"{self.display_name} is already running")
                return

            self._log_info(f"Starting {self.display_name}...")
            self._update_status("Starting")

            # Get a free port for IPC (stubbed for now)
            self.ipc_port = self._get_free_port()

            # Build and execute launch command
            launch_cmd = self.get_launch_command()
            self._log_debug(f"Launch command: {' '.join(launch_cmd)}")

            try:
                # Start the subprocess
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

                self._log_info(f"{self.display_name} started (PID: {self.child_pid})")

            except Exception as e:
                self._log_error(f"Failed to start {self.display_name}: {e}")
                self._update_status("Crashed")
                self.is_running = False

    def stop(self):
        """Stop the subsystem process"""
        with self._process_lock:
            if not self.is_running:
                self._log_debug(f"{self.display_name} is not running")
                return

            self._log_info(f"Stopping {self.display_name}...")
            self._is_stopping.set()
            self._update_status("Stopping")

            # Try graceful shutdown first (IPC would go here)
            if self._send_ipc_shutdown():
                try:
                    self.process.wait(timeout=10)
                    self._log_debug(f"{self.display_name} exited gracefully")
                except subprocess.TimeoutExpired:
                    self._log_debug(f"{self.display_name} did not exit in time, forcing...")
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
                    self._post_stop_hook()
                except Exception as e:
                    self._log_error(f"Post-stop hook error: {e}")

    def restart(self):
        """Restart the subsystem"""
        self._is_restarting.set()
        self._log_info(f"Restarting {self.display_name}...")

        if self.is_running:
            self.stop()

        time.sleep(1)  # Brief pause
        self.start()
        self._is_restarting.clear()

    def toggle(self):
        """Toggle between start and stop"""
        if self.is_running:
            self.stop()
        else:
            self.start()

    def _capture_output(self):
        """Capture subprocess output"""
        with self._process_lock:
            if not self.process or not self.process.stdout:
                return
            stdout = self.process.stdout

        try:
            for line in stdout:
                if not line:
                    break

                line = line.rstrip()

                # Check for PID update
                if "PID:" in line:
                    try:
                        pid = int(line.split("PID:")[1].strip())
                        with self._process_lock:
                            self.child_pid = pid
                        self._log_debug(f"Updated PID to {pid}")
                    except (ValueError, IndexError):
                        pass

                # Check for initialization complete
                elif "initialization complete" in line.lower():
                    self._log_debug(f"{self.display_name} initialization complete")
                    self._update_status("Running")

                    # Run post-start hook
                    if self._post_start_hook:
                        try:
                            self._post_start_hook()
                        except Exception as e:
                            self._log_error(f"Post-start hook error: {e}")
                else:
                    # Regular log message from child
                    self._log_info(line, is_child_message=True)

        except Exception as e:
            self._log_error(f"Output capture error: {e}")

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
        self._log_error(f"{self.display_name} exited unexpectedly (code: {ret_code})")

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
                self._post_stop_hook()
            except Exception as e:
                self._log_error(f"Post-stop hook error: {e}")

    def _send_heartbeat(self):
        """Send periodic heartbeat to child process"""
        # Initial random delay
        time.sleep(random.uniform(0, 2.0))

        failed_count = 0

        while not self._stop_heartbeat.is_set():
            try:
                # Stub: In real implementation, send IPC heartbeat
                # For now, just check if process is alive
                if self.process and self.process.poll() is None:
                    failed_count = 0
                else:
                    failed_count += 1

            except Exception as e:
                self._log_debug(f"Heartbeat error: {e}")
                failed_count += 1

            # Check for excessive failures
            if failed_count > self.num_missable_heartbeats and not self.debug_mode:
                self._log_error(
                    f"{self.display_name} missed {failed_count} heartbeats, stopping..."
                )
                self.stop()
                break

            self._stop_heartbeat.wait(self.heartbeat_interval)

        self._stop_heartbeat.clear()

    def _send_ipc_shutdown(self) -> bool:
        """Send IPC shutdown command (stub)"""
        # Stub: Real implementation would use IPC
        return False

    def _terminate_process(self):
        """Force-terminate the process"""
        if self.child_pid and self.child_pid != (self.process.pid if self.process else None):
            # Terminate actual child (PyInstaller case)
            try:
                psutil.Process(self.child_pid).kill()
                self._log_debug(f"Killed child PID {self.child_pid}")
            except psutil.NoSuchProcess:
                self._log_debug(f"Child PID {self.child_pid} already gone")
        elif self.process:
            # Terminate subprocess
            self.process.kill()
            self.process.wait()
            self._log_debug(f"Killed subprocess PID {self.process.pid}")

    def _get_free_port(self) -> int:
        """Get a free TCP port (stub)"""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            return s.getsockname()[1]

    def _update_status(self, status: str):
        """Update status and emit signal"""
        self.status = status
        self.status_changed.emit(status)

    # Logging methods
    def _log_info(self, message: str, is_child_message: bool = False):
        """Log info message"""
        if self.console:
            self.console.info_log(message, is_child_message)

    def _log_debug(self, message: str):
        """Log debug message"""
        if self.console:
            self.console.debug_log(message)

    def _log_warning(self, message: str):
        """Log warning message"""
        if self.console:
            self.console.warning_log(message)

    def _log_error(self, message: str):
        """Log error message"""
        if self.console:
            self.console.error_log(message)

    # Hook registration
    def register_post_start(self, func: Callable[[], None]):
        """Register a post-start callback"""
        self._post_start_hook = func
        return func

    def register_post_stop(self, func: Callable[[], None]):
        """Register a post-stop callback"""
        self._post_stop_hook = func
        return func