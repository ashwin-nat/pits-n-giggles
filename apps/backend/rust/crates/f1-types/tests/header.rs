use f1_types::{F1PacketType, PacketHeader, PacketHeaderError};
use serde_json::json;

#[test]
fn packet_type_validation_matches_python_behavior() {
    assert!(F1PacketType::is_valid(0));
    assert!(F1PacketType::is_valid(15));
    assert!(!F1PacketType::is_valid(99));
    assert_eq!(F1PacketType::try_from(6), Ok(F1PacketType::CarTelemetry));
    assert_eq!(F1PacketType::CarTelemetry.to_string(), "CAR_TELEMETRY");
}

#[test]
fn packet_header_round_trips_through_bytes() {
    let header = PacketHeader::from_values(
        2025,
        25,
        1,
        15,
        3,
        F1PacketType::Motion,
        0x1122_3344_5566_7788,
        123.75,
        42,
        84,
        7,
        255,
    );

    let bytes = header.to_bytes();
    let reparsed = PacketHeader::parse(&bytes).expect("header should parse");

    assert_eq!(PacketHeader::PACKET_LEN, 29);
    assert_eq!(reparsed, header);
    assert!(reparsed.is_supported_packet_type());
}

#[test]
fn packet_header_reports_unknown_packet_types_without_failing_parse() {
    let mut bytes = PacketHeader::from_values(
        2024,
        24,
        1,
        2,
        3,
        F1PacketType::Session,
        99,
        12.5,
        1,
        2,
        3,
        255,
    )
    .to_bytes();
    bytes[6] = 99;

    let header = PacketHeader::parse(&bytes).expect("unknown packet id should still parse");

    assert_eq!(header.packet_id, None);
    assert_eq!(header.packet_id_raw, 99);
    assert!(!header.is_supported_packet_type());
    assert_eq!(header.packet_id_label(), "99");
}

#[test]
fn packet_header_serializes_to_python_compatible_json_shape() {
    let header = PacketHeader::from_values(
        2023,
        23,
        9,
        4,
        1,
        F1PacketType::LapData,
        12345,
        3.25,
        77,
        91,
        11,
        255,
    );

    let value = serde_json::to_value(header).expect("header should serialize");

    assert_eq!(
        value,
        json!({
            "packet-format": 2023,
            "game-year": 23,
            "game-major-version": 9,
            "game-minor-version": 4,
            "packet-version": 1,
            "packet-id": "LAP_DATA",
            "session-uid": 12345,
            "session-time": 3.25,
            "frame-identifier": 77,
            "overall-frame-identifier": 91,
            "player-car-index": 11,
            "secondary-player-car-index": 255
        })
    );
}

#[test]
fn packet_header_rejects_wrong_length() {
    let error = PacketHeader::parse(&[0u8; 10]).expect_err("short header should fail");
    assert_eq!(
        error,
        PacketHeaderError::InvalidLength {
            expected: PacketHeader::PACKET_LEN,
            actual: 10,
        }
    );
}
