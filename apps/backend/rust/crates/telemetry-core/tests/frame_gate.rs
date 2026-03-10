use f1_types::{
    EventPacketType, F1Packet, F1PacketType, PacketEventData, PacketHeader, PacketTimeTrialData,
    TimeTrialDataSet,
};
use telemetry_core::{FrameGateDropReason, SessionFrameGate};

fn header(
    packet_type: F1PacketType,
    session_uid: u64,
    frame_identifier: u32,
    overall_frame_identifier: u32,
) -> PacketHeader {
    PacketHeader::from_values(
        2025,
        25,
        1,
        0,
        1,
        packet_type,
        session_uid,
        0.0,
        frame_identifier,
        overall_frame_identifier,
        0,
        255,
    )
}

fn event_packet(
    session_uid: u64,
    frame_identifier: u32,
    overall_frame_identifier: u32,
) -> F1Packet {
    F1Packet::Event(PacketEventData::from_values(
        header(
            F1PacketType::Event,
            session_uid,
            frame_identifier,
            overall_frame_identifier,
        ),
        EventPacketType::SessionStarted,
        None,
    ))
}

fn time_trial_packet(
    session_uid: u64,
    frame_identifier: u32,
    overall_frame_identifier: u32,
) -> F1Packet {
    let data_set = TimeTrialDataSet::from_values(
        2025, 1, 3, 70_000, 20_000, 25_000, 25_000, false, true, false, false, true, true,
    );

    F1Packet::TimeTrial(PacketTimeTrialData::from_values(
        header(
            F1PacketType::TimeTrial,
            session_uid,
            frame_identifier,
            overall_frame_identifier,
        ),
        data_set.clone(),
        data_set.clone(),
        data_set,
    ))
}

#[test]
fn first_packet_is_accepted() {
    let mut gate = SessionFrameGate::default();
    let packet = event_packet(1, 10, 10);

    assert!(gate.should_accept(&packet));
    assert_eq!(gate.last_drop_reason(), None);
}

#[test]
fn monotonic_frames_are_accepted() {
    let mut gate = SessionFrameGate::default();

    assert!(gate.should_accept(&event_packet(1, 1, 1)));
    assert!(gate.should_accept(&event_packet(1, 2, 2)));
    assert!(gate.should_accept(&event_packet(1, 3, 3)));
    assert_eq!(gate.last_drop_reason(), None);
}

#[test]
fn out_of_order_packet_is_dropped() {
    let mut gate = SessionFrameGate::default();

    assert!(gate.should_accept(&event_packet(1, 10, 10)));
    assert!(!gate.should_accept(&event_packet(1, 9, 9)));
    assert_eq!(
        gate.last_drop_reason(),
        Some(FrameGateDropReason::OutOfOrderPacket)
    );
}

#[test]
fn duplicate_packet_type_in_same_frame_is_dropped() {
    let mut gate = SessionFrameGate::default();

    assert!(gate.should_accept(&event_packet(1, 100, 100)));
    assert!(!gate.should_accept(&event_packet(1, 100, 100)));
    assert_eq!(
        gate.last_drop_reason(),
        Some(FrameGateDropReason::DuplicatePacketType)
    );
}

#[test]
fn different_packet_types_in_same_frame_are_allowed() {
    let mut gate = SessionFrameGate::default();

    assert!(gate.should_accept(&event_packet(1, 200, 200)));
    assert!(gate.should_accept(&time_trial_packet(1, 200, 200)));
    assert_eq!(gate.last_drop_reason(), None);
}

#[test]
fn new_frame_clears_seen_packet_types() {
    let mut gate = SessionFrameGate::default();

    assert!(gate.should_accept(&event_packet(1, 300, 300)));
    assert!(gate.should_accept(&event_packet(1, 301, 301)));
    assert_eq!(gate.last_drop_reason(), None);
}

#[test]
fn frame_zero_resets_uniqueness_tracking() {
    let mut gate = SessionFrameGate::default();

    assert!(gate.should_accept(&event_packet(1, 50, 50)));
    assert!(gate.should_accept(&event_packet(1, 0, 0)));
    assert!(gate.should_accept(&event_packet(1, 0, 0)));
}

#[test]
fn session_change_resets_state() {
    let mut gate = SessionFrameGate::default();

    assert!(gate.should_accept(&event_packet(1, 400, 400)));
    assert!(gate.should_accept(&event_packet(2, 400, 400)));
    assert_eq!(gate.last_drop_reason(), None);
}

#[test]
fn duplicate_after_session_change_is_isolated() {
    let mut gate = SessionFrameGate::default();

    assert!(gate.should_accept(&event_packet(1, 500, 500)));
    assert!(gate.should_accept(&event_packet(2, 500, 500)));
    assert!(!gate.should_accept(&event_packet(2, 500, 500)));
}

#[test]
fn drop_reason_is_cleared_after_accept() {
    let mut gate = SessionFrameGate::default();

    assert!(gate.should_accept(&event_packet(1, 10, 10)));
    assert!(!gate.should_accept(&event_packet(1, 10, 10)));
    assert!(gate.last_drop_reason().is_some());

    assert!(gate.should_accept(&event_packet(1, 11, 11)));
    assert_eq!(gate.last_drop_reason(), None);
}

#[test]
fn disabled_mode_accepts_everything() {
    let mut gate = SessionFrameGate::new(false);

    assert!(gate.should_accept(&event_packet(1, 10, 10)));
    assert!(gate.should_accept(&event_packet(1, 9, 9)));
    assert!(gate.should_accept(&event_packet(1, 9, 9)));
    assert!(gate.should_accept(&event_packet(2, 5, 5)));
    assert!(gate.should_accept(&event_packet(2, 0, 0)));
    assert_eq!(gate.last_drop_reason(), None);
}

#[test]
fn flashback_does_not_trigger_backward_drop_if_overall_frame_increases() {
    let mut gate = SessionFrameGate::default();

    assert!(gate.should_accept(&event_packet(1, 1000, 1000)));
    assert!(gate.should_accept(&event_packet(1, 1001, 1001)));
    assert!(gate.should_accept(&event_packet(1, 900, 1002)));
    assert!(gate.should_accept(&event_packet(1, 900, 1003)));
}
