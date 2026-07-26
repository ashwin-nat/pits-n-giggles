# MIT License
#
# Copyright (c) [2026] [Ashwin Natarajan]
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

import pytest

from lib.event_counter import EventCounter
from lib.mailbox import LatestSlot

# -------------------------------------- FIXTURES -----------------------------------------------------------------------

@pytest.fixture
def stats():
    return EventCounter()

@pytest.fixture
def slot(stats):
    return LatestSlot("test-topic", stats)

# -------------------------------------- TESTS: take() --------------------------------------------------------------------------

def test_take_before_any_publish_returns_none(slot):
    assert slot.take() is None

def test_publish_then_take_returns_payload_and_seq(slot):
    seq = slot.publish("hello")
    assert seq == 1
    assert slot.take() == ("hello", 1)

def test_seq_increments_monotonically_across_publishes(slot):
    seqs = [slot.publish(f"payload-{i}") for i in range(5)]
    assert seqs == [1, 2, 3, 4, 5]

def test_take_returns_only_the_latest_publish(slot):
    slot.publish("first")
    slot.publish("second")
    payload, seq = slot.take()
    assert payload == "second"
    assert seq == 2

def test_take_is_repeatable_without_consuming(slot):
    slot.publish("value")
    assert slot.take() == slot.take()

def test_slots_are_independent(stats):
    slot_a = LatestSlot("topic-a", stats)
    slot_b = LatestSlot("topic-b", stats)
    slot_a.publish("a-value")
    assert slot_b.take() is None

# -------------------------------------- TESTS: take_if_new() ---------------------------------------------------------------

def test_take_if_new_before_any_publish_returns_none(slot):
    assert slot.take_if_new(last_seq=0) is None

def test_take_if_new_returns_value_when_seq_differs(slot):
    slot.publish("value")
    assert slot.take_if_new(last_seq=0) == ("value", 1)

def test_take_if_new_returns_none_when_seq_unchanged(slot):
    slot.publish("value")
    assert slot.take_if_new(last_seq=1) is None

def test_take_if_new_collapses_a_publish_backlog_to_the_latest_value(slot):
    for i in range(5):
        slot.publish(f"payload-{i}")
    # A reader that missed every intermediate publish still gets exactly the latest one.
    assert slot.take_if_new(last_seq=0) == ("payload-4", 5)

# -------------------------------------- TESTS: stats ------------------------------------------------------------------------

def test_publish_is_tracked_in_shared_stats(stats, slot):
    slot.publish("a")
    slot.publish("b")
    counters = stats.get_stats()
    assert counters["test-topic"]["__MAILBOX_PUBLISHED__"]["count"] == 2

def test_coalesced_skip_is_tracked_in_shared_stats(stats, slot):
    slot.publish("value")
    slot.take_if_new(last_seq=1)  # unchanged -> coalesced
    slot.take_if_new(last_seq=1)  # unchanged -> coalesced
    counters = stats.get_stats()
    assert counters["test-topic"]["__MAILBOX_COALESCED__"]["count"] == 2

def test_delivered_take_if_new_does_not_count_as_coalesced(stats, slot):
    slot.publish("value")
    slot.take_if_new(last_seq=0)  # delivered, not coalesced
    counters = stats.get_stats()
    assert "__MAILBOX_COALESCED__" not in counters["test-topic"]

def test_slots_sharing_one_event_counter_report_stats_under_their_own_name(stats):
    slot_a = LatestSlot("topic-a", stats)
    slot_b = LatestSlot("topic-b", stats)
    slot_a.publish("a-value")
    slot_b.publish("b-value")
    slot_b.publish("b-value-2")
    counters = stats.get_stats()
    assert counters["topic-a"]["__MAILBOX_PUBLISHED__"]["count"] == 1
    assert counters["topic-b"]["__MAILBOX_PUBLISHED__"]["count"] == 2
