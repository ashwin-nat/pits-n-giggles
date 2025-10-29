import logging
import threading
from datetime import datetime
from logging.handlers import RotatingFileHandler

_write_lock = threading.Lock()  # protects file + console writes


# ---------- Custom Formatter ----------
class TestFormatter(logging.Formatter):
    """Formatter that switches output based on log_type."""
    def format(self, record):
        log_type = getattr(record, "log_type", None)

        if log_type == "runner":
            # Example: 2025-10-28 21:49:32,464 [TEST] [runner.py:41] - <Message>
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
            return f"{ts} [TEST] [{record.filename}:{record.lineno}] - {record.getMessage()}"

        elif log_type == "child":
            # Example: [TEST] - <Message>
            return f"[TEST] - {record.getMessage()}"

        # Fallback for unknown log type
        return f"[UNKNOWN] - {record.getMessage()}"


# ---------- Thread-safe Rotating Handler ----------
class ThreadSafeRotatingHandler(RotatingFileHandler):
    """Rotating file handler with thread-safe writes to file and console."""
    def emit(self, record):
        msg = self.format(record)
        with _write_lock:
            # Write to file (via parent handler)
            super().emit(record)
            # Also print to console
            print(msg)

    def format(self, record):
        if self.formatter:
            return self.formatter.format(record)
        return super().format(record)


# ---------- Custom Logger ----------
class TestLogger(logging.Logger):
    """Logger with convenience methods for test and process logs."""

    def test_log(self, message: str):
        """Log a test runner message."""
        self.info(message, extra={"log_type": "runner"})

    def proc_log(self, message: str):
        """Log a child process (stdout) message."""
        self.info(message, extra={"log_type": "child"})


# ---------- Factory Function ----------
def create_logger(
    log_file: str = "integration_test.log",
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 1
) -> TestLogger:
    """
    Create a thread-safe rotating logger for both test runner and child process logs.
    """
    logging.setLoggerClass(TestLogger)
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    handler = ThreadSafeRotatingHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    handler.setFormatter(TestFormatter())
    logger.addHandler(handler)

    return logger
