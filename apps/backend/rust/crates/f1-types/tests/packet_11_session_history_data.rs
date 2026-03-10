use f1_types::{
    ActualTyreCompound, F1PacketType, InvalidPacketLengthError, LapHistoryData, PacketHeader,
    PacketSessionHistoryData, SessionHistoryError, TyreStintHistoryData, VisualTyreCompound,
};
use serde_json::json;

fn sample_header(packet_format: u16) -> PacketHeader {
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
        F1PacketType::SessionHistory,
        1111,
        55.0,
        2,
        3,
        0,
        255,
    )
}

fn sample_lap(index: u8) -> LapHistoryData {
    LapHistoryData::from_values(
        if index == 0 { 76_823 } else { 68_894 },
        if index == 0 { 27_620 } else { 20_341 },
        0,
        if index == 0 { 32_097 } else { 31_207 },
        0,
        if index == 0 { 17_105 } else { 17_345 },
        0,
        15,
    )
}

fn sample_packet(packet_format: u16) -> PacketSessionHistoryData {
    PacketSessionHistoryData::from_values(
        sample_header(packet_format),
        14,
        2,
        1,
        2,
        2,
        2,
        1,
        vec![sample_lap(0), sample_lap(1)],
        vec![TyreStintHistoryData::from_values(
            255,
            if packet_format == 2024 {
                ActualTyreCompound::C3
            } else {
                ActualTyreCompound::C5
            },
            VisualTyreCompound::Soft,
        )],
    )
}

#[test]
fn lap_history_round_trips() {
    let lap = sample_lap(0);
    let reparsed = LapHistoryData::parse(&lap.to_bytes()).expect("parse lap");

    assert_eq!(reparsed, lap);
}

#[test]
fn packet_session_history_round_trips() {
    let packet = sample_packet(2025);
    let bytes = packet.to_bytes();
    let header = PacketHeader::parse(&bytes[..PacketHeader::PACKET_LEN]).expect("parse header");
    let parsed = PacketSessionHistoryData::parse(header, &bytes[PacketHeader::PACKET_LEN..])
        .expect("parse packet");

    assert_eq!(parsed, packet);
}

#[test]
fn packet_session_history_json_matches_python_shape() {
    let value = serde_json::to_value(sample_packet(2024)).expect("serialize");

    assert_eq!(value["car-index"], json!(14));
    assert_eq!(value["num-laps"], json!(2));
    assert_eq!(value["best-sector-3-lap-num"], json!(1));
    assert_eq!(
        value["lap-history-data"][0]["lap-time-str"],
        json!("01:16.823")
    );
    assert_eq!(
        value["tyre-stints-history-data"][0]["tyre-actual-compound"],
        json!("C3")
    );
}

#[test]
fn packet_session_history_rejects_wrong_length() {
    let error = PacketSessionHistoryData::parse(sample_header(2024), &[0u8; 100])
        .expect_err("wrong length");

    assert_eq!(
        error,
        SessionHistoryError::InvalidPacketLength(InvalidPacketLengthError::new(format!(
            "Received packet length {} is not equal to expected {}",
            100,
            PacketSessionHistoryData::PAYLOAD_LEN
        )))
    );
}

#[test]
fn packet_session_history_rejects_invalid_tyre_stint_count() {
    let mut payload = vec![0u8; PacketSessionHistoryData::PAYLOAD_LEN];
    payload[0] = 2;
    payload[1] = 1;
    payload[2] = 9;

    let error = PacketSessionHistoryData::parse(sample_header(2025), &payload)
        .expect_err("invalid tyre stint count");

    assert_eq!(
        error.to_string(),
        "Packet count validation error. Too many TyreStintHistoryData items: 9 > 8"
    );
}
