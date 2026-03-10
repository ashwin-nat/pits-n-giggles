use f1_types::{
    CarMotionData, F1Packet, F1PacketParseError, F1PacketType, PacketEventData, PacketHeader,
    PacketMotionData, PacketTimeTrialData, TimeTrialDataSet,
};
use serde_json::json;

fn header(packet_type: F1PacketType, packet_format: u16) -> PacketHeader {
    PacketHeader::from_values(
        packet_format,
        if packet_format >= 2025 {
            25
        } else if packet_format == 2024 {
            24
        } else {
            23
        },
        1,
        2,
        1,
        packet_type,
        999,
        12.0,
        4,
        5,
        0,
        255,
    )
}

fn sample_motion_packet() -> PacketMotionData {
    PacketMotionData::from_values(
        header(F1PacketType::Motion, 2024),
        vec![
            CarMotionData::from_values(
                1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7, 8, 9, 10, 11, 12, 13.0, 14.0, 15.0, 16.0, 17.0,
                18.0,
            );
            PacketMotionData::MAX_CARS
        ],
    )
}

fn sample_time_trial_packet() -> PacketTimeTrialData {
    let dataset = TimeTrialDataSet::from_values(
        2025, 1, 3, 70_000, 20_000, 25_000, 25_000, false, true, false, false, true, true,
    );
    PacketTimeTrialData::from_values(
        header(F1PacketType::TimeTrial, 2025),
        dataset.clone(),
        dataset.clone(),
        dataset,
    )
}

#[test]
fn dispatcher_parses_motion_packet() {
    let bytes = sample_motion_packet().to_bytes();
    let packet = F1Packet::parse(&bytes).expect("parse dispatch");

    assert_eq!(packet.packet_type(), F1PacketType::Motion);
    assert_eq!(packet.to_bytes(), bytes);
}

#[test]
fn dispatcher_parses_time_trial_packet() {
    let bytes = sample_time_trial_packet().to_bytes();
    let packet = F1Packet::parse(&bytes).expect("parse dispatch");
    let value = serde_json::to_value(packet).expect("serialize");

    assert_eq!(
        value["player-session-best-data-set"]["team"],
        json!("Williams")
    );
}

#[test]
fn dispatcher_reports_unsupported_packet_type() {
    let mut bytes = header(F1PacketType::Motion, 2024).to_bytes().to_vec();
    bytes[6] = 99;
    bytes.resize(PacketHeader::PACKET_LEN, 0);

    let error = F1Packet::parse(&bytes).expect_err("unsupported packet id");
    assert_eq!(error, F1PacketParseError::UnsupportedPacketType(99));
}

#[test]
fn dispatcher_wraps_event_parse_errors() {
    let mut bytes = header(F1PacketType::Event, 2024).to_bytes().to_vec();
    bytes.extend_from_slice(b"XXXX\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00");

    let error = F1Packet::parse(&bytes).expect_err("invalid event");
    assert_eq!(
        error.to_string(),
        "Malformed packet. Unsupported Event Type XXXX"
    );
}

#[test]
fn event_packet_parse_uses_typed_error() {
    let error = PacketEventData::parse(header(F1PacketType::Event, 2024), b"XXXX")
        .expect_err("typed error");

    assert_eq!(
        error.to_string(),
        "Malformed packet. Invalid packet length. Received packet length 4 is not equal to expected 16"
    );
}
