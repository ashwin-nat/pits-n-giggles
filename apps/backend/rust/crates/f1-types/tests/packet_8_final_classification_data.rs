use f1_types::{
    ActualTyreCompound, F1PacketType, FinalClassificationData, InvalidPacketLengthError,
    PacketFinalClassificationData, PacketHeader, ResultReason, ResultStatus, VisualTyreCompound,
};
use serde_json::json;

fn sample_header(packet_format: u16) -> PacketHeader {
    PacketHeader::from_values(
        packet_format,
        if packet_format >= 2025 { 25 } else { 24 },
        1,
        2,
        1,
        F1PacketType::FinalClassification,
        404,
        91.5,
        11,
        12,
        13,
        255,
    )
}

fn sample_classification(packet_format: u16, index: u8) -> FinalClassificationData {
    FinalClassificationData::from_values(
        packet_format,
        index + 1,
        5,
        index + 3,
        if index == 0 { 25 } else { 18 },
        index,
        ResultStatus::FINISHED,
        ResultReason::FINISHED,
        93_413 + (u32::from(index) * 17),
        485.195 + f64::from(index),
        0,
        0,
        2,
        vec![ActualTyreCompound::C3, ActualTyreCompound::C2],
        vec![VisualTyreCompound::Soft, VisualTyreCompound::Medium],
        vec![12, 255],
    )
}

fn sample_packet(packet_format: u16) -> PacketFinalClassificationData {
    PacketFinalClassificationData::from_values(
        sample_header(packet_format),
        2,
        vec![
            sample_classification(packet_format, 0),
            sample_classification(packet_format, 1),
        ],
    )
}

#[test]
fn final_classification_round_trips_for_2024_layout() {
    let classification = sample_classification(2024, 0);
    let reparsed = FinalClassificationData::parse(&classification.to_bytes(), 2024)
        .expect("parse classification");

    assert_eq!(FinalClassificationData::PACKET_LEN, 45);
    assert_eq!(reparsed, classification);
    assert_eq!(reparsed.result_reason, ResultReason::INVALID);
}

#[test]
fn final_classification_round_trips_for_2025_layout() {
    let classification = sample_classification(2025, 0);
    let reparsed = FinalClassificationData::parse(&classification.to_bytes(), 2025)
        .expect("parse classification");

    assert_eq!(FinalClassificationData::PACKET_LEN_25, 46);
    assert_eq!(reparsed, classification);
    assert_eq!(reparsed.result_reason, ResultReason::FINISHED);
}

#[test]
fn packet_final_classification_round_trips() {
    let packet = sample_packet(2025);
    let bytes = packet.to_bytes();
    let header = PacketHeader::parse(&bytes[..PacketHeader::PACKET_LEN]).expect("parse header");
    let parsed = PacketFinalClassificationData::parse(header, &bytes[PacketHeader::PACKET_LEN..])
        .expect("parse packet");

    assert_eq!(parsed, packet);
    assert_eq!(parsed.num_cars, 2);
    assert_eq!(
        bytes.len(),
        PacketHeader::PACKET_LEN
            + 1
            + (PacketFinalClassificationData::MAX_CARS * FinalClassificationData::PACKET_LEN_25)
    );
}

#[test]
fn packet_final_classification_supports_empty_payload() {
    let packet = PacketFinalClassificationData::from_values(sample_header(2024), 0, vec![]);
    let bytes = packet.to_bytes();
    let header = PacketHeader::parse(&bytes[..PacketHeader::PACKET_LEN]).expect("parse header");
    let parsed = PacketFinalClassificationData::parse(header, &bytes[PacketHeader::PACKET_LEN..])
        .expect("parse packet");

    assert_eq!(parsed.num_cars, 0);
    assert!(parsed.classification_data.is_empty());
}

#[test]
fn packet_final_classification_parses_fixed_size_payload_with_unused_slots() {
    let header = sample_header(2025);
    let mut payload = Vec::with_capacity(
        1 + (PacketFinalClassificationData::MAX_CARS * FinalClassificationData::PACKET_LEN_25),
    );
    payload.push(2);
    payload.extend_from_slice(&sample_classification(2025, 0).to_bytes());
    payload.extend_from_slice(&sample_classification(2025, 1).to_bytes());
    payload.resize(
        1 + (PacketFinalClassificationData::MAX_CARS * FinalClassificationData::PACKET_LEN_25),
        0,
    );

    let parsed = PacketFinalClassificationData::parse(header, &payload).expect("parse packet");

    assert_eq!(parsed.num_cars, 2);
    assert_eq!(
        parsed.classification_data,
        vec![
            sample_classification(2025, 0),
            sample_classification(2025, 1)
        ]
    );
}

#[test]
fn final_classification_json_matches_python_shape() {
    let value = serde_json::to_value(sample_classification(2025, 0)).expect("serialize");

    assert_eq!(
        value,
        json!({
            "position": 1,
            "num-laps": 5,
            "grid-position": 3,
            "points": 25,
            "num-pit-stops": 0,
            "result-status": "FINISHED",
            "result-reason": "finished",
            "best-lap-time-ms": 93413,
            "best-lap-time-str": "01:33.413",
            "total-race-time": 485.195,
            "total-race-time-str": "08:05.195",
            "penalties-time": 0,
            "num-penalties": 0,
            "num-tyre-stints": 2,
            "tyre-stints-actual": ["C3", "C2"],
            "tyre-stints-visual": ["Soft", "Medium"],
            "tyre-stints-end-laps": [12, 255]
        })
    );
}

#[test]
fn packet_final_classification_json_matches_python_shape() {
    let value = serde_json::to_value(sample_packet(2024)).expect("serialize");

    assert_eq!(value["num-cars"], json!(2));
    assert_eq!(
        value["classification-data"][0]["result-status"],
        json!("FINISHED")
    );
    assert_eq!(
        value["classification-data"][0]["best-lap-time-str"],
        json!("01:33.413")
    );
    assert_eq!(value["classification-data"][0].get("result-reason"), None);
}

#[test]
fn packet_final_classification_rejects_wrong_length() {
    let error = PacketFinalClassificationData::parse(sample_header(2025), &[2u8; 12])
        .expect_err("wrong length");

    assert_eq!(
        error,
        InvalidPacketLengthError::new(format!(
            "Received packet length {} is not equal to expected {}",
            12,
            1 + (PacketFinalClassificationData::MAX_CARS * FinalClassificationData::PACKET_LEN_25)
        ))
    );
}
