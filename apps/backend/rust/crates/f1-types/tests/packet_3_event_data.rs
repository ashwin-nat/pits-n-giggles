use f1_types::{F1PacketType, PacketEventData, PacketHeader};
use serde_json::json;

fn sample_header(packet_format: u16) -> PacketHeader {
    PacketHeader::from_values(
        packet_format,
        if packet_format >= 2025 { 25 } else { 24 },
        1,
        2,
        1,
        F1PacketType::Event,
        333,
        19.0,
        6,
        7,
        0,
        255,
    )
}

#[test]
fn event_packet_parses_session_started() {
    let packet = PacketEventData::parse(
        sample_header(2024),
        b"SSTA\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
    )
    .expect("parse");

    let value = serde_json::to_value(packet).expect("serialize");
    assert_eq!(
        value,
        json!({
            "event-string-code": "SSTA",
            "event-details": null
        })
    );
}

#[test]
fn event_packet_parses_fastest_lap_2024() {
    let packet = PacketEventData::parse(
        sample_header(2024),
        b"FTLP\x04\x11X\xdcB\x00\x00\x00\x00\x00\x00\x00",
    )
    .expect("parse");

    let value = serde_json::to_value(packet).expect("serialize");
    assert_eq!(
        value,
        json!({
            "event-string-code": "FTLP",
            "event-details": {
                "vehicle-idx": 4,
                "lap-time": 110.17200469970703
            }
        })
    );
}

#[test]
fn event_packet_parses_fastest_lap_2025() {
    let packet = PacketEventData::parse(
        sample_header(2025),
        b"FTLP\x07\x14.\x89B\x00\x00\x00\x02\x1amP",
    )
    .expect("parse");

    let value = serde_json::to_value(packet).expect("serialize");
    assert_eq!(
        value,
        json!({
            "event-string-code": "FTLP",
            "event-details": {
                "vehicle-idx": 7,
                "lap-time": 68.58999633789062
            }
        })
    );
}
