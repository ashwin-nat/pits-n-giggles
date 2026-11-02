"""Offline tests for race-control speech: new messages only, id order, no replay."""

from apps.voice.race_control_announcer import RaceControlAnnouncer, describe_message


def _msg(
    mid, kind="SPEED_TRAP_RECORD", name="TSUNODA", lap=29, seg="Rettifilo Tribune"
):
    msg = {
        "id": mid,
        "message-type": kind,
        "lap-number": lap,
        "involved-drivers": [13],
        "timestamp": 1.0,
    }
    if name is not None:
        msg["driver-info"] = {"driver-number": 22, "name": name, "team": "VCARB"}
    if seg is not None:
        msg["segment-info"] = {"name": seg, "type": "straight"}
    return msg


class _Feed:
    def __init__(self):
        self.payload: dict = {"race-control": []}

    def __call__(self):
        return self.payload


def _announcer(feed):
    spoken = []
    ann = RaceControlAnnouncer(spoken.append, "http://unused", fetch=feed)
    return ann, spoken


def test_describe_message_builds_readable_sentence():
    assert describe_message(_msg(23)) == (
        "speed trap record, Tsunoda, lap 29, at Rettifilo Tribune"
    )


def test_describe_message_without_driver_or_segment():
    text = describe_message({"id": 1, "message-type": "RED_FLAG", "lap-number": 3})
    assert text == "red flag, lap 3"


def test_first_poll_adopts_baseline_without_speaking():
    feed = _Feed()
    feed.payload = {"race-control": [_msg(1), _msg(2)]}
    ann, spoken = _announcer(feed)
    assert ann.poll_once() == []
    assert spoken == []


def test_new_messages_are_spoken_in_id_order_once():
    feed = _Feed()
    feed.payload = {"race-control": [_msg(1)]}
    ann, spoken = _announcer(feed)
    ann.poll_once()

    feed.payload = {
        "race-control": [_msg(3, kind="PENALTY"), _msg(1), _msg(2, kind="OVERTAKE")]
    }
    ann.poll_once()
    assert [s.split(",")[0] for s in spoken] == ["overtake", "penalty"]

    ann.poll_once()  # same data again: nothing repeated
    assert len(spoken) == 2


def test_session_reset_rebaselines_without_replay():
    feed = _Feed()
    feed.payload = {"race-control": [_msg(10), _msg(11)]}
    ann, spoken = _announcer(feed)
    ann.poll_once()

    feed.payload = {"race-control": [_msg(1)]}  # new session, lower ids
    assert ann.poll_once() == []
    feed.payload = {"race-control": [_msg(1), _msg(2, kind="RED_FLAG")]}
    ann.poll_once()
    assert spoken == ["red flag, Tsunoda, lap 29, at Rettifilo Tribune"]


def test_missing_or_malformed_payload_is_ignored():
    feed = _Feed()
    ann, spoken = _announcer(feed)
    feed.payload = {"error": "backend unavailable"}
    assert ann.poll_once() == []
    feed.payload = {"race-control": "nope"}
    assert ann.poll_once() == []
    assert spoken == []


def test_fetch_errors_propagate_to_caller_for_the_loop_to_log():
    def boom():
        raise ConnectionError("dashboard down")

    ann = RaceControlAnnouncer(lambda t: None, "http://unused", fetch=boom)
    try:
        ann.poll_once()
    except ConnectionError:
        return
    raise AssertionError("expected ConnectionError")
