
import contextlib
import io
import os
import re
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests_base import F1TelemetryUnitTestsBase

from lib.pid_report import extract_pid_from_line, report_pid_from_child

# ----------------------------------------------------------------------------------------------------------------------

class TestPidReport(F1TelemetryUnitTestsBase):

    def test_extract_pid_from_valid_line(self):
        line = "<<PNG_LAUNCHER_CHILD_PID:12345>>"
        self.assertEqual(extract_pid_from_line(line), 12345)

    def test_extract_pid_from_line_with_extra_text(self):
        line = "2025-05-11 12:00:00 INFO <<PNG_LAUNCHER_CHILD_PID:9876>> More logs"
        self.assertEqual(extract_pid_from_line(line), 9876)

    def test_extract_pid_from_line_without_pid(self):
        line = "Just a normal log line"
        self.assertIsNone(extract_pid_from_line(line))

    def test_extract_pid_from_malformed_tag(self):
        # Missing closing >>
        line = "<<PNG_LAUNCHER_CHILD_PID:5678>"
        self.assertIsNone(extract_pid_from_line(line))

    def test_report_pid_from_child_output(self):
        # Capture printed output
        with io.StringIO() as buf, contextlib.redirect_stdout(buf):
            report_pid_from_child()
            output = buf.getvalue().strip()

        # Match expected format
        match = re.match(r"<<PNG_LAUNCHER_CHILD_PID:(\d+)>>", output)
        self.assertIsNotNone(match)
        if match:
            pid = int(match.group(1))
            self.assertEqual(pid, os.getpid())
