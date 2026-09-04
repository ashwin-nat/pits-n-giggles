
import contextlib
import io
import os
import re
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from tests_base import F1TelemetryUnitTestsBase

from lib.child_proc_mgmt import (_INTEGRATION_FAIL_TAG_PREFIX,
                                 _INTEGRATION_TEST_ENV_VAR,
                                 _SESSION_SAVE_SKIPPED_TAG_PREFIX,
                                 _SESSION_SAVED_TAG_PREFIX,
                                 enable_integration_test_mode,
                                 extract_integration_fail_from_line,
                                 extract_ipc_port_from_line,
                                 extract_pid_from_line,
                                 extract_save_skipped_from_line,
                                 extract_saved_path_from_line,
                                 is_init_complete, is_integration_test_mode,
                                 notify_parent_init_complete,
                                 report_integration_fail,
                                 report_ipc_port_from_child,
                                 report_pid_from_child,
                                 report_session_save_skipped_from_child,
                                 report_session_saved_from_child)

pytestmark = pytest.mark.serial

# ----------------------------------------------------------------------------------------------------------------------

class TestChildProcMgmt(F1TelemetryUnitTestsBase):
    pass

class TestPidReport(TestChildProcMgmt):

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

class TestIsInitComplete(TestChildProcMgmt):

    def test_contains_init_complete(self):
        # Test case where the line contains _INIT_COMPLETE_STR
        line = "Some random text <<__PNG_SUBSYSTEM_INIT_COMPLETE__>> more text"
        self.assertTrue(is_init_complete(line))

    def test_does_not_contain_init_complete(self):
        # Test case where the line does not contain _INIT_COMPLETE_STR
        line = "Some random text without the init complete"
        self.assertFalse(is_init_complete(line))

    def test_empty_string(self):
        # Test case where the line is empty
        line = ""
        self.assertFalse(is_init_complete(line))

    def test_only_init_complete(self):
        # Test case where the line is exactly _INIT_COMPLETE_STR
        line = "<<__PNG_SUBSYSTEM_INIT_COMPLETE__>>"
        self.assertTrue(is_init_complete(line))

    def test_case_sensitivity(self):
        # Test case where _INIT_COMPLETE_STR is in a different case (should fail)
        line = "<<__png_subsystem_init_complete__>>"
        self.assertFalse(is_init_complete(line))

    def test_whitespace_before_init_complete(self):
        # Test case where there is leading whitespace before _INIT_COMPLETE_STR
        line = "    <<__PNG_SUBSYSTEM_INIT_COMPLETE__>>"
        self.assertTrue(is_init_complete(line))

    def test_whitespace_after_init_complete(self):
        # Test case where there is trailing whitespace after _INIT_COMPLETE_STR
        line = "<<__PNG_SUBSYSTEM_INIT_COMPLETE__>>    "
        self.assertTrue(is_init_complete(line))

    def test_partial_string(self):
        # Test case where a substring of _INIT_COMPLETE_STR is present (should fail)
        line = "<<__PNG_SUBSYSTEM_INIT_COMPL>>"
        self.assertFalse(is_init_complete(line))

class TestIpcPortExtraction(TestChildProcMgmt):

    def test_valid_ipc_port(self):
        line = "<<PNG_LAUNCHER_IPC_PORT:5555>>"
        self.assertEqual(extract_ipc_port_from_line(line), 5555)

    def test_invalid_no_tag(self):
        self.assertIsNone(extract_ipc_port_from_line("nothing here"))

    def test_invalid_wrong_tag(self):
        self.assertIsNone(extract_ipc_port_from_line("<<PNG_LAUNCHER_CHILD_PID:1234>>"))

    def test_valid_ipc_port_with_noise(self):
        line = "log info: starting... <<PNG_LAUNCHER_IPC_PORT:7777>> ready"
        self.assertEqual(extract_ipc_port_from_line(line), 7777)

    def test_multiple_tags_uses_first_match(self):
        line = "<<PNG_LAUNCHER_IPC_PORT:1111>> something <<PNG_LAUNCHER_IPC_PORT:2222>>"
        self.assertEqual(extract_ipc_port_from_line(line), 1111)

    def test_non_numeric_port(self):
        # Should return None because regex requires digits
        line = "<<PNG_LAUNCHER_IPC_PORT:abcd>>"
        self.assertIsNone(extract_ipc_port_from_line(line))


# ----------------------------------------------------------------------------------------------------------------------

# Stdout tokens the child emits for the integration runner, as
# (prefix, reporter, extractor, payload). Lines are built from the module's own prefix, so a
# renamed tag fails here rather than silently passing against a literal nothing emits any more.
TOKENS = [
    (_SESSION_SAVED_TAG_PREFIX, report_session_saved_from_child, extract_saved_path_from_line,
     "data/2026_01_01/race-info/Race_Monza.json"),
    (_SESSION_SAVE_SKIPPED_TAG_PREFIX, report_session_save_skipped_from_child,
     extract_save_skipped_from_line, "no-lap-data"),
    # Free-form message with punctuation - the non-greedy match has to return all of it.
    (_INTEGRATION_FAIL_TAG_PREFIX, report_integration_fail, extract_integration_fail_from_line,
     "HUD exited unexpectedly (code: 3221225477) | exiting with code -1073741819"),
]

TOKEN_IDS = [p.strip("<:") for p, _, _, _ in TOKENS]


@pytest.mark.parametrize("prefix, report_fn, extract_fn, payload", TOKENS, ids=TOKEN_IDS)
def test_token_round_trip(prefix, report_fn, extract_fn, payload):
    """What the child prints is what the parent parses back out."""
    assert extract_fn(f"{prefix}{payload}>>") == payload


@pytest.mark.parametrize("prefix, report_fn, extract_fn, payload", TOKENS, ids=TOKEN_IDS)
def test_token_extraction_ignores_unrelated_lines(prefix, report_fn, extract_fn, payload):
    """Noise, and the other tokens - the runner dispatches on these separately."""
    assert extract_fn("just a normal log line") is None
    assert extract_fn("") is None

    for other_prefix, _, _, other_payload in TOKENS:
        if other_prefix != prefix:
            assert extract_fn(f"{other_prefix}{other_payload}>>") is None


@pytest.mark.parametrize("prefix, report_fn, extract_fn, payload", TOKENS, ids=TOKEN_IDS)
def test_reporters_are_silent_outside_integration_mode(monkeypatch, capsys, prefix, report_fn,
                                                       extract_fn, payload):
    """A normal build must print nothing: report_integration_fail runs on the crash path."""
    monkeypatch.delenv(_INTEGRATION_TEST_ENV_VAR, raising=False)
    report_fn(payload)
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("prefix, report_fn, extract_fn, payload", TOKENS, ids=TOKEN_IDS)
def test_reporters_emit_inside_integration_mode(monkeypatch, capsys, prefix, report_fn,
                                                extract_fn, payload):
    """The emit half of the round trip - what the runner's output pump actually reads.

    The silence test above only pins the early return, so without this the print itself is
    never executed and a broken token would ship green.
    """
    monkeypatch.setenv(_INTEGRATION_TEST_ENV_VAR, "1")
    report_fn(payload)
    line = capsys.readouterr().out.strip()
    assert line == f"{prefix}{payload}>>"
    assert extract_fn(line) == payload


def test_enable_integration_test_mode_is_visible_to_the_reporters(monkeypatch):
    """The runner sets this before spawning the app; children inherit it via the environment."""
    monkeypatch.delenv(_INTEGRATION_TEST_ENV_VAR, raising=False)
    assert not is_integration_test_mode()
    enable_integration_test_mode()
    assert is_integration_test_mode()


def test_ipc_port_round_trip(capsys):
    """Reported unconditionally - the launcher needs the port whatever the mode."""
    report_ipc_port_from_child(5555)
    assert extract_ipc_port_from_line(capsys.readouterr().out.strip()) == 5555


def test_init_complete_round_trip(capsys):
    """Also unconditional: the launcher blocks on this before marking a subsystem up."""
    notify_parent_init_complete()
    assert is_init_complete(capsys.readouterr().out.strip())
