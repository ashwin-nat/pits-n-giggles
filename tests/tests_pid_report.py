
import contextlib
import io
import os
import re
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests_base import F1TelemetryUnitTestsBase

from lib.child_proc_mgmt import extract_pid_from_line, report_pid_from_child

# ----------------------------------------------------------------------------------------------------------------------

class TestPidReport(F1TelemetryUnitTestsBase):

    def test_extract_pid_from_multiple_tags_in_line(self):
        """Test extracting PID when multiple PID tags are present in a line."""
        line = "<<PNG_LAUNCHER_CHILD_PID:12345>> Some log <<PNG_LAUNCHER_CHILD_PID:67890>> More info"
        # Should return the first PID by default
        self.assertEqual(extract_pid_from_line(line), 12345)

    def test_extract_pid_with_whitespace_variations_invalid(self):
        """Test PID extraction with various whitespace scenarios."""
        test_cases = [
            "<<PNG_LAUNCHER_CHILD_PID:  54321  >>",
            " << PNG_LAUNCHER_CHILD_PID: 54321 >> "
        ]
        for line in test_cases:
            self.assertEqual(extract_pid_from_line(line), None,
                             f"Failed for line: {line}")

    def test_extract_pid_with_zero_pid(self):
        """Test handling of zero as a PID."""
        line = "<<PNG_LAUNCHER_CHILD_PID:0>>"
        self.assertEqual(extract_pid_from_line(line), 0)

    def test_extract_pid_with_large_pid(self):
        """Test handling of very large PIDs."""
        large_pid = 2**31 - 1  # Maximum 32-bit signed integer
        line = f"<<PNG_LAUNCHER_CHILD_PID:{large_pid}>>"
        self.assertEqual(extract_pid_from_line(line), large_pid)

    def test_report_pid_from_child_pid_type(self):
        """Verify that the reported PID is of the correct type."""
        with io.StringIO() as buf, contextlib.redirect_stdout(buf):
            report_pid_from_child()
            output = buf.getvalue().strip()

        # Verify the output format
        match = re.match(r"<<PNG_LAUNCHER_CHILD_PID:(\d+)>>", output)
        self.assertIsNotNone(match, "Output does not match expected format")

        # Extract the PID and verify its type and value
        if match:
            pid = match.group(1)
            # Verify the PID is a string of digits
            self.assertTrue(pid.isdigit(), "PID should be a string of digits")

            # Convert to int and verify it matches os.getpid()
            pid_int = int(pid)
            self.assertEqual(pid_int, os.getpid(), "Reported PID does not match os.getpid()")

    def test_extract_pid_with_non_numeric_pid(self):
        """Test behavior with non-numeric or malformed PID tags."""
        test_cases = [
            "<<PNG_LAUNCHER_CHILD_PID:abc>>",
            "<<PNG_LAUNCHER_CHILD_PID:-123>>",
            "<<PNG_LAUNCHER_CHILD_PID:12.34>>",
        ]
        for line in test_cases:
            self.assertIsNone(extract_pid_from_line(line),
                              f"Should return None for line: {line}")

    def test_extract_pid_case_sensitivity(self):
        """Verify the PID tag extraction is case-sensitive."""
        # Slightly different capitalization should not match
        line = "<<png_launcher_child_pid:12345>>"
        self.assertIsNone(extract_pid_from_line(line))

    def test_report_pid_from_child_output_uniqueness(self):
        """Verify that multiple calls generate unique output."""
        outputs = set()
        for _ in range(5):
            with io.StringIO() as buf, contextlib.redirect_stdout(buf):
                report_pid_from_child()
                output = buf.getvalue().strip()
                outputs.add(output)

        # Verify consistent PID across multiple calls in the same process
        self.assertEqual(len(outputs), 1, "PID should remain consistent within the same process")

    def test_extract_pid_with_additional_delimiters(self):
        """Test PID extraction with various delimiter scenarios."""
        test_cases = [
            "log text[<<PNG_LAUNCHER_CHILD_PID:54321>>]more text",
            "log text{<<PNG_LAUNCHER_CHILD_PID:54321>>}more text",
            "log text(<<PNG_LAUNCHER_CHILD_PID:54321>>)more text"
        ]
        for line in test_cases:
            self.assertEqual(extract_pid_from_line(line), 54321,
                             f"Failed for line: {line}")
