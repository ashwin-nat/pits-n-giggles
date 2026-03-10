use f1_types::{
    ActualTyreCompound, F1PacketType, InvalidPacketLengthError, PacketHeader, PacketTyreSetsData,
    SessionType23, SessionType24, TyreSetData, VisualTyreCompound,
};
use serde_json::json;

fn sample_header(packet_format: u16) -> PacketHeader {
    PacketHeader::from_values(
        packet_format,
        if packet_format >= 2025 { 25 } else { 24 },
        1,
        2,
        1,
        F1PacketType::TyreSets,
        909,
        44.0,
        21,
        22,
        3,
        255,
    )
}

fn sample_tyre_set(packet_format: u16, index: u8) -> TyreSetData {
    TyreSetData::from_values(
        packet_format,
        if index.is_multiple_of(2) {
            ActualTyreCompound::C3
        } else {
            ActualTyreCompound::C2
        },
        if index.is_multiple_of(2) {
            VisualTyreCompound::Soft
        } else {
            VisualTyreCompound::Medium
        },
        10 + index,
        !index.is_multiple_of(3),
        if packet_format == 2023 {
            SessionType23::RACE as u8
        } else {
            SessionType24::RACE as u8
        },
        18 + index,
        22 + index,
        -3 + i16::from(index),
        index == 6,
    )
}

fn sample_packet(packet_format: u16) -> PacketTyreSetsData {
    let tyre_set_data = (0..PacketTyreSetsData::MAX_TYRE_SETS as u8)
        .map(|index| sample_tyre_set(packet_format, index))
        .collect::<Vec<_>>();

    PacketTyreSetsData::from_values(sample_header(packet_format), 6, tyre_set_data, 6)
}

#[test]
fn tyre_set_data_round_trips_through_bytes() {
    let tyre_set = sample_tyre_set(2024, 0);
    let reparsed = TyreSetData::parse(&tyre_set.to_bytes(), 2024).expect("parse tyre set");

    assert_eq!(TyreSetData::PACKET_LEN, 10);
    assert_eq!(reparsed, tyre_set);
}

#[test]
fn tyre_set_data_json_matches_python_shape() {
    let value = serde_json::to_value(sample_tyre_set(2024, 0)).expect("serialize");

    assert_eq!(
        value,
        json!({
            "actual-tyre-compound": "C3",
            "visual-tyre-compound": "Soft",
            "wear": 10,
            "available": false,
            "recommended-session": "Race",
            "life-span": 18,
            "usable-life": 22,
            "lap-delta-time": -3,
            "fitted": false
        })
    );
}

#[test]
fn tyre_set_data_uses_2023_session_labels() {
    let value = serde_json::to_value(sample_tyre_set(2023, 0)).expect("serialize");

    assert_eq!(value["recommended-session"], json!("Race"));
}

#[test]
fn packet_tyre_sets_round_trips() {
    let packet = sample_packet(2025);
    let bytes = packet.to_bytes();
    let header = PacketHeader::parse(&bytes[..PacketHeader::PACKET_LEN]).expect("parse header");
    let parsed = PacketTyreSetsData::parse(header, &bytes[PacketHeader::PACKET_LEN..])
        .expect("parse packet");

    assert_eq!(parsed, packet);
    assert_eq!(parsed.fitted_tyre_set_key().as_deref(), Some("6.C3"));
    assert_eq!(parsed.get_tyre_set_key(1).as_deref(), Some("1.C2"));
}

#[test]
fn packet_tyre_sets_json_matches_python_shape() {
    let value = serde_json::to_value(sample_packet(2024)).expect("serialize");

    assert_eq!(value["car-index"], json!(6));
    assert_eq!(
        value["tyre-set-data"].as_array().map(Vec::len),
        Some(PacketTyreSetsData::MAX_TYRE_SETS)
    );
    assert_eq!(
        value["tyre-set-data"][0]["recommended-session"],
        json!("Race")
    );
    assert_eq!(value["fitted-index"], json!(6));
}

#[test]
fn packet_tyre_sets_rejects_wrong_length() {
    let error =
        PacketTyreSetsData::parse(sample_header(2025), &[0u8; 100]).expect_err("wrong length");

    assert_eq!(
        error,
        InvalidPacketLengthError::new(format!(
            "Received packet length {} is not equal to expected {}",
            100,
            PacketTyreSetsData::PAYLOAD_LEN
        ))
    );
}
