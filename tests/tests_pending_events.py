# ----------------------------------------------------------------------------------------------------------------------

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
from enum import auto
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests_base import F1TelemetryUnitTestsBase

from lib.pending_events import PendingEventsManager, PendingEventType

# -------------------------------------- TEST EVENT TYPES --------------------------------------------------------------

class TestEventType(PendingEventType):
    """
    Dummy event types for testing purposes.
    """
    EVENT_A = auto()
    EVENT_B = auto()
    EVENT_C = auto()
    EVENT_D = auto()
    EVENT_E = auto()

# -------------------------------------- TEST CLASS --------------------------------------------------------------------

class TestPendingEventsManager(F1TelemetryUnitTestsBase):
    """Tests for the PendingEventsManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.callback_triggered = False
        self.callback_count = 0

    def _callback(self):
        """Test callback that updates status variables."""
        self.callback_triggered = True
        self.callback_count += 1

    # -------------------------------------- Basic Functionality Tests -------------------------------------------------

    def test_initialization_default(self):
        """Test default initialization with in_order=False."""
        manager = PendingEventsManager(self._callback)
        self.assertTrue(manager.areEventsPending() is False)

    def test_initialization_in_order(self):
        """Test initialization with in_order=True."""
        manager = PendingEventsManager(self._callback, in_order=True)
        self.assertTrue(manager.areEventsPending() is False)

    def test_register_events(self):
        """Test registering events."""
        manager = PendingEventsManager(self._callback)
        events = [TestEventType.EVENT_A, TestEventType.EVENT_B]
        manager.register(events)
        self.assertTrue(manager.areEventsPending())

    def test_register_empty_list(self):
        """Test registering an empty list of events."""
        manager = PendingEventsManager(self._callback)
        manager.register([])
        self.assertFalse(manager.areEventsPending())

    # -------------------------------------- Any Order Mode Tests ------------------------------------------------------

    def test_any_order_single_event(self):
        """Test completion with a single event in any order mode."""
        manager = PendingEventsManager(self._callback, in_order=False)
        manager.register([TestEventType.EVENT_A])

        manager.onEvent(TestEventType.EVENT_A)

        self.assertTrue(self.callback_triggered)
        self.assertEqual(self.callback_count, 1)
        self.assertFalse(manager.areEventsPending())

    def test_any_order_multiple_events_sequential(self):
        """Test completion with multiple events in sequential order (any order mode)."""
        manager = PendingEventsManager(self._callback, in_order=False)
        events = [TestEventType.EVENT_A, TestEventType.EVENT_B]
        manager.register(events)

        manager.onEvent(TestEventType.EVENT_A)
        self.assertFalse(self.callback_triggered)
        self.assertEqual(self.callback_count, 0)
        self.assertTrue(manager.areEventsPending())

        manager.onEvent(TestEventType.EVENT_B)
        self.assertTrue(self.callback_triggered)
        self.assertEqual(self.callback_count, 1)
        self.assertFalse(manager.areEventsPending())

    def test_any_order_multiple_events_reverse(self):
        """Test completion with multiple events in reverse order (any order mode)."""
        manager = PendingEventsManager(self._callback, in_order=False)
        events = [TestEventType.EVENT_A, TestEventType.EVENT_B]
        manager.register(events)

        manager.onEvent(TestEventType.EVENT_B)
        self.assertFalse(self.callback_triggered)
        self.assertEqual(self.callback_count, 0)
        self.assertTrue(manager.areEventsPending())

        manager.onEvent(TestEventType.EVENT_A)
        self.assertTrue(self.callback_triggered)
        self.assertEqual(self.callback_count, 1)
        self.assertFalse(manager.areEventsPending())

    def test_any_order_duplicate_events(self):
        """Test with duplicate events in the registration list (any order mode)."""
        manager = PendingEventsManager(self._callback, in_order=False)
        events = [
            TestEventType.EVENT_A,
            TestEventType.EVENT_A,
            TestEventType.EVENT_B
        ]
        manager.register(events)

        # First occurrence removes first duplicate
        manager.onEvent(TestEventType.EVENT_A)
        self.assertFalse(self.callback_triggered)
        self.assertEqual(self.callback_count, 0)
        self.assertTrue(manager.areEventsPending())

        # Second occurrence removes second duplicate
        manager.onEvent(TestEventType.EVENT_A)
        self.assertFalse(self.callback_triggered)
        self.assertEqual(self.callback_count, 0)
        self.assertTrue(manager.areEventsPending())

        # Final event triggers callback
        manager.onEvent(TestEventType.EVENT_B)
        self.assertTrue(self.callback_triggered)
        self.assertEqual(self.callback_count, 1)
        self.assertFalse(manager.areEventsPending())

    # -------------------------------------- In Order Mode Tests -------------------------------------------------------

    def test_in_order_single_event(self):
        """Test completion with a single event in order mode."""
        manager = PendingEventsManager(self._callback, in_order=True)
        manager.register([TestEventType.EVENT_A])

        manager.onEvent(TestEventType.EVENT_A)

        self.assertTrue(self.callback_triggered)
        self.assertEqual(self.callback_count, 1)
        self.assertFalse(manager.areEventsPending())

    def test_in_order_correct_sequence(self):
        """Test completion with events in correct order (in order mode)."""
        manager = PendingEventsManager(self._callback, in_order=True)
        events = [TestEventType.EVENT_A, TestEventType.EVENT_B]
        manager.register(events)

        manager.onEvent(TestEventType.EVENT_A)
        self.assertFalse(self.callback_triggered)
        self.assertEqual(self.callback_count, 0)
        self.assertTrue(manager.areEventsPending())

        manager.onEvent(TestEventType.EVENT_B)
        self.assertTrue(self.callback_triggered)
        self.assertEqual(self.callback_count, 1)
        self.assertFalse(manager.areEventsPending())

    def test_in_order_wrong_sequence(self):
        """Test that wrong order doesn't trigger completion (in order mode)."""
        manager = PendingEventsManager(self._callback, in_order=True)
        events = [TestEventType.EVENT_A, TestEventType.EVENT_B]
        manager.register(events)

        # Event arrives out of order - should be ignored
        manager.onEvent(TestEventType.EVENT_B)
        self.assertFalse(self.callback_triggered)
        self.assertEqual(self.callback_count, 0)
        self.assertTrue(manager.areEventsPending())

        # Correct first event
        manager.onEvent(TestEventType.EVENT_A)
        self.assertFalse(self.callback_triggered)
        self.assertEqual(self.callback_count, 0)
        self.assertTrue(manager.areEventsPending())

        # Correct second event now triggers
        manager.onEvent(TestEventType.EVENT_B)
        self.assertTrue(self.callback_triggered)
        self.assertEqual(self.callback_count, 1)
        self.assertFalse(manager.areEventsPending())

    def test_in_order_duplicate_events(self):
        """Test duplicate events in correct order (in order mode)."""
        manager = PendingEventsManager(self._callback, in_order=True)
        events = [
            TestEventType.EVENT_A,
            TestEventType.EVENT_A,
            TestEventType.EVENT_B
        ]
        manager.register(events)

        manager.onEvent(TestEventType.EVENT_A)
        self.assertTrue(manager.areEventsPending())

        manager.onEvent(TestEventType.EVENT_A)
        self.assertTrue(manager.areEventsPending())

        manager.onEvent(TestEventType.EVENT_B)
        self.assertTrue(self.callback_triggered)
        self.assertEqual(self.callback_count, 1)
        self.assertFalse(manager.areEventsPending())

    # -------------------------------------- Edge Cases ----------------------------------------------------------------

    def test_unregistered_event(self):
        """Test that unregistered events are ignored."""
        manager = PendingEventsManager(self._callback, in_order=False)
        manager.register([TestEventType.EVENT_A])

        # This event is not in the pending list
        manager.onEvent(TestEventType.EVENT_B)

        self.assertFalse(self.callback_triggered)
        self.assertEqual(self.callback_count, 0)
        self.assertTrue(manager.areEventsPending())

    def test_event_after_completion(self):
        """Test that events after completion don't trigger callback again."""
        manager = PendingEventsManager(self._callback, in_order=False)
        manager.register([TestEventType.EVENT_A])

        manager.onEvent(TestEventType.EVENT_A)
        self.assertTrue(self.callback_triggered)
        self.assertEqual(self.callback_count, 1)

        # Send another event after completion
        manager.onEvent(TestEventType.EVENT_B)

        # Callback should still only be called once
        self.assertEqual(self.callback_count, 1)

    def test_reregister_after_completion(self):
        """Test re-registering events after completion."""
        manager = PendingEventsManager(self._callback, in_order=False)

        # First registration and completion
        manager.register([TestEventType.EVENT_A])
        manager.onEvent(TestEventType.EVENT_A)
        self.assertTrue(self.callback_triggered)
        self.assertEqual(self.callback_count, 1)

        # Re-register with different events
        manager.register([TestEventType.EVENT_B])
        self.assertTrue(manager.areEventsPending())

        manager.onEvent(TestEventType.EVENT_B)

        # Callback should be called twice total
        self.assertEqual(self.callback_count, 2)

    def test_empty_event_list_triggers_immediately(self):
        """Test that registering empty list means no pending events."""
        manager = PendingEventsManager(self._callback, in_order=False)
        manager.register([])

        # With no pending events, callback should not be triggered
        self.assertFalse(manager.areEventsPending())
        self.assertFalse(self.callback_triggered)
        self.assertEqual(self.callback_count, 0)

    def test_same_event_multiple_times_any_order(self):
        """Test sending the same event multiple times in any order mode."""
        manager = PendingEventsManager(self._callback, in_order=False)
        events = [
            TestEventType.EVENT_A,
            TestEventType.EVENT_A
        ]
        manager.register(events)

        # Send same event twice
        manager.onEvent(TestEventType.EVENT_A)
        self.assertTrue(manager.areEventsPending())

        manager.onEvent(TestEventType.EVENT_A)
        self.assertTrue(self.callback_triggered)
        self.assertEqual(self.callback_count, 1)
        self.assertFalse(manager.areEventsPending())

    def test_same_event_multiple_times_in_order(self):
        """Test sending the same event multiple times in order mode."""
        manager = PendingEventsManager(self._callback, in_order=True)
        events = [
            TestEventType.EVENT_A,
            TestEventType.EVENT_A
        ]
        manager.register(events)

        manager.onEvent(TestEventType.EVENT_A)
        self.assertTrue(manager.areEventsPending())

        manager.onEvent(TestEventType.EVENT_A)
        self.assertTrue(self.callback_triggered)
        self.assertEqual(self.callback_count, 1)
        self.assertFalse(manager.areEventsPending())

    def test_interleaved_events_in_order(self):
        """Test interleaved correct and incorrect events in order mode."""
        manager = PendingEventsManager(self._callback, in_order=True)
        events = [
            TestEventType.EVENT_A,
            TestEventType.EVENT_B
        ]
        manager.register(events)

        # Wrong event - ignored
        manager.onEvent(TestEventType.EVENT_B)
        self.assertTrue(manager.areEventsPending())

        # Wrong event again - still ignored
        manager.onEvent(TestEventType.EVENT_B)
        self.assertTrue(manager.areEventsPending())

        # Correct event
        manager.onEvent(TestEventType.EVENT_A)
        self.assertTrue(manager.areEventsPending())

        # Now correct second event
        manager.onEvent(TestEventType.EVENT_B)
        self.assertTrue(self.callback_triggered)
        self.assertEqual(self.callback_count, 1)
        self.assertFalse(manager.areEventsPending())

    def test_callback_not_called_prematurely(self):
        """Test that callback is not called before all events occur."""
        manager = PendingEventsManager(self._callback, in_order=False)
        events = [
            TestEventType.EVENT_A,
            TestEventType.EVENT_B
        ]
        manager.register(events)

        # Send multiple unregistered events
        for _ in range(5):
            manager.onEvent(TestEventType.EVENT_A)

        self.assertFalse(self.callback_triggered)
        self.assertEqual(self.callback_count, 0)

    def test_multiple_managers_independent(self):
        """Test that multiple managers operate independently."""
        callback1_triggered = False
        callback1_count = 0
        callback2_triggered = False
        callback2_count = 0

        def callback1():
            nonlocal callback1_triggered, callback1_count
            callback1_triggered = True
            callback1_count += 1

        def callback2():
            nonlocal callback2_triggered, callback2_count
            callback2_triggered = True
            callback2_count += 1

        manager1 = PendingEventsManager(callback1, in_order=False)
        manager2 = PendingEventsManager(callback2, in_order=False)

        manager1.register([TestEventType.EVENT_A])
        manager2.register([TestEventType.EVENT_B])

        manager1.onEvent(TestEventType.EVENT_A)
        self.assertTrue(callback1_triggered)
        self.assertEqual(callback1_count, 1)
        self.assertFalse(callback2_triggered)
        self.assertEqual(callback2_count, 0)

        manager2.onEvent(TestEventType.EVENT_B)
        self.assertEqual(callback1_count, 1)
        self.assertTrue(callback2_triggered)
        self.assertEqual(callback2_count, 1)

    def test_many_events_any_order(self):
        """Test with more than 2 events in any order mode."""
        manager = PendingEventsManager(self._callback, in_order=False)
        events = [
            TestEventType.EVENT_A,
            TestEventType.EVENT_B,
            TestEventType.EVENT_C,
            TestEventType.EVENT_D,
            TestEventType.EVENT_E
        ]
        manager.register(events)

        # Send events in random order
        manager.onEvent(TestEventType.EVENT_C)
        self.assertFalse(self.callback_triggered)

        manager.onEvent(TestEventType.EVENT_A)
        self.assertFalse(self.callback_triggered)

        manager.onEvent(TestEventType.EVENT_E)
        self.assertFalse(self.callback_triggered)

        manager.onEvent(TestEventType.EVENT_B)
        self.assertFalse(self.callback_triggered)

        manager.onEvent(TestEventType.EVENT_D)
        self.assertTrue(self.callback_triggered)
        self.assertEqual(self.callback_count, 1)
        self.assertFalse(manager.areEventsPending())

    def test_many_events_in_order(self):
        """Test with more than 2 events in order mode."""
        manager = PendingEventsManager(self._callback, in_order=True)
        events = [
            TestEventType.EVENT_A,
            TestEventType.EVENT_B,
            TestEventType.EVENT_C,
            TestEventType.EVENT_D
        ]
        manager.register(events)

        # Send wrong event - should be ignored
        manager.onEvent(TestEventType.EVENT_C)
        self.assertFalse(self.callback_triggered)
        self.assertTrue(manager.areEventsPending())

        # Send in correct order
        manager.onEvent(TestEventType.EVENT_A)
        self.assertFalse(self.callback_triggered)

        manager.onEvent(TestEventType.EVENT_B)
        self.assertFalse(self.callback_triggered)

        manager.onEvent(TestEventType.EVENT_C)
        self.assertFalse(self.callback_triggered)

        manager.onEvent(TestEventType.EVENT_D)
        self.assertTrue(self.callback_triggered)
        self.assertEqual(self.callback_count, 1)
        self.assertFalse(manager.areEventsPending())

    def test_mixed_event_types_any_order(self):
        """Test with a mix of different event types in any order."""
        manager = PendingEventsManager(self._callback, in_order=False)
        events = [
            TestEventType.EVENT_A,
            TestEventType.EVENT_C,
            TestEventType.EVENT_E,
        ]
        manager.register(events)

        manager.onEvent(TestEventType.EVENT_E)
        self.assertTrue(manager.areEventsPending())

        manager.onEvent(TestEventType.EVENT_A)
        self.assertTrue(manager.areEventsPending())

        manager.onEvent(TestEventType.EVENT_C)
        self.assertTrue(self.callback_triggered)
        self.assertFalse(manager.areEventsPending())
