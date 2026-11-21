"""Bounded radio scheduling, with no wall clock or I/O."""

from dataclasses import replace

import pytest

from apps.voice.contracts import Answer, CalloutCondition, Evidence, RadioWork
from apps.voice.radio_queue import RadioQueue


def work(kind="question", id="q", **kwargs):
    evidence = Evidence("tyres", 1, 0, 0, 20, 20, None, {}, (), ())
    defaults = dict(
        id=id,
        kind=kind,
        text=id,
        generation=0,
        created_mono=0,
        expires_mono=20,
    )
    if kind == "callout":
        defaults.update(
            answer=Answer("wear", "fact", evidence, (), ()),
            condition=CalloutCondition("tyre_wear", {}),
        )
    defaults.update(kwargs)
    return RadioWork(**defaults)


def drain(queue, now=0):
    result = []
    while (item := queue.take(now_mono=now)) is not None:
        result.append(item)
    return result


def test_quotas_priorities_fifo():
    queue = RadioQueue()
    assert queue.submit(work("greeting"), now_mono=0)
    for i in range(3):
        assert queue.submit(work("callout", str(i)), now_mono=0)
    assert not queue.submit(work("callout", "extra"), now_mono=0)
    for i in range(4):
        assert queue.submit(work(id=f"q{i}"), now_mono=0)
    assert not queue.submit(work(id="newest"), now_mono=0)
    items = drain(queue)
    assert [w.id for w in items[:4]] == [f"q{i}" for i in range(4)]
    assert len(items) <= 8
    assert items[-1].kind == "greeting"


@pytest.mark.parametrize(
    "kind,ttl",
    [
        ("question", 10),
        ("callout", 3),
        ("ack", 2),
        ("greeting", 2),
    ],
)
def test_expiry_boundary(kind, ttl):
    queue = RadioQueue()
    item = work(kind)
    assert not queue.submit(item, now_mono=ttl)
    assert queue.submit(item, now_mono=ttl - 0.001)
    assert queue.take(now_mono=ttl) is None


def test_coalescing_replaces_event():
    queue = RadioQueue()
    assert queue.submit(work("callout", "old", dedupe_key="wear"), now_mono=0)
    assert queue.submit(work("callout", "new", dedupe_key="wear"), now_mono=0)
    assert [w.id for w in drain(queue)] == ["new"]


def test_missing_condition_or_evidence_is_rejected():
    queue = RadioQueue()
    item = work("callout")
    assert not queue.submit(replace(item, condition=None), now_mono=0)
    assert not queue.submit(replace(item, answer=None), now_mono=0)


def test_reset_discards_pending_and_old_generation():
    queue = RadioQueue()
    queue.submit(work(), now_mono=0)
    queue.reset(1)
    assert queue.take(now_mono=0) is None
    assert not queue.submit(work(), now_mono=0)
    assert queue.submit(work(generation=1), now_mono=0)


def test_callout_can_refresh_within_original_ttl_after_old_evidence_expires():
    queue = RadioQueue()
    item = work("callout")
    item = replace(
        item,
        answer=replace(
            item.answer, evidence=replace(item.answer.evidence, expires_mono=1)
        ),
    )
    assert queue.submit(item, now_mono=0)
    assert queue.take(now_mono=2) is not None


def test_ack_greeting_share_one_slot():
    queue = RadioQueue()
    queue.submit(work("greeting"), now_mono=0)
    assert queue.submit(work("ack", "ack"), now_mono=0)
    assert [w.kind for w in drain(queue)] == ["ack"]
