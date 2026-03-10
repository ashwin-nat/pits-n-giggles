use f1_types::{
    F1PacketType, InvalidPacketLengthError, PacketHeader, PacketTimeTrialData, TeamID24, TeamID25,
    TimeTrialDataSet,
};
use serde_json::json;

fn sample_header(packet_format: u16) -> PacketHeader {
    PacketHeader::from_values(
        packet_format,
        if packet_format >= 2025 { 25 } else { 24 },
        1,
        2,
        1,
        F1PacketType::TimeTrial,
        77,
        90.0,
        4,
        5,
        0,
        255,
    )
}

fn sample_dataset(packet_format: u16, index: u8) -> TimeTrialDataSet {
    TimeTrialDataSet::from_values(
        packet_format,
        index,
        if packet_format >= 2025 {
            if index == 0 {
                TeamID25::WILLIAMS as u8
            } else {
                TeamID25::MERCEDES as u8
            }
        } else if index == 0 {
            TeamID24::RED_BULL_RACING as u8
        } else {
            TeamID24::ASTON_MARTIN as u8
        },
        if index == 0 {
            0
        } else {
            93_691 + u32::from(index)
        },
        if index == 0 { 0 } else { 24_300 },
        if index == 0 { 0 } else { 28_112 },
        if index == 0 { 0 } else { 41_278 },
        index.is_multiple_of(2),
        false,
        index == 2,
        index == 0,
        index == 1,
        true,
    )
}

fn sample_packet(packet_format: u16) -> PacketTimeTrialData {
    PacketTimeTrialData::from_values(
        sample_header(packet_format),
        sample_dataset(packet_format, 0),
        sample_dataset(packet_format, 1),
        sample_dataset(packet_format, 2),
    )
}

#[test]
fn time_trial_dataset_round_trips() {
    let data_set = sample_dataset(2024, 1);
    let reparsed =
        TimeTrialDataSet::parse(&data_set.to_bytes(), 2024).expect("parse time-trial data set");

    assert_eq!(TimeTrialDataSet::PACKET_LEN, 24);
    assert_eq!(reparsed, data_set);
}

#[test]
fn time_trial_dataset_json_matches_python_shape() {
    let value = serde_json::to_value(sample_dataset(2024, 1)).expect("serialize");

    assert_eq!(
        value,
        json!({
            "car-index": 1,
            "team": "Aston Martin",
            "lap-time-ms": 93692,
            "lap-time-str": "01:33.692",
            "sector-1-time-ms": 24300,
            "sector-1-time-str": "24.300",
            "sector-2-time-in-ms": 28112,
            "sector-2-time-str": "28.112",
            "sector3-time-in-ms": 41278,
            "sector-3-time-str": "41.278",
            "traction-control": false,
            "gearbox-assist": false,
            "anti-lock-brakes": false,
            "equal-car-performance": false,
            "custom-setup": true,
            "is-valid": true
        })
    );
}

#[test]
fn packet_time_trial_round_trips() {
    let packet = sample_packet(2025);
    let bytes = packet.to_bytes();
    let header = PacketHeader::parse(&bytes[..PacketHeader::PACKET_LEN]).expect("parse header");
    let parsed = PacketTimeTrialData::parse(header, &bytes[PacketHeader::PACKET_LEN..])
        .expect("parse packet");

    assert_eq!(parsed, packet);
    assert_eq!(PacketTimeTrialData::PAYLOAD_LEN, 72);
}

#[test]
fn packet_time_trial_json_matches_python_shape() {
    let value = serde_json::to_value(sample_packet(2025)).expect("serialize");

    assert_eq!(
        value["player-session-best-data-set"]["team"],
        json!("Williams")
    );
    assert_eq!(
        value["player-session-best-data-set"]["lap-time-str"],
        json!("00.000")
    );
    assert_eq!(value["personal-best-data-set"]["team"], json!("Mercedes"));
    assert_eq!(
        value["rival-session-best-data-set"]["anti-lock-brakes"],
        json!(true)
    );
}

#[test]
fn packet_time_trial_rejects_wrong_length() {
    let error =
        PacketTimeTrialData::parse(sample_header(2025), &[0u8; 12]).expect_err("wrong length");

    assert_eq!(
        error,
        InvalidPacketLengthError::new(format!(
            "Received packet length {} is not equal to expected {}",
            12,
            PacketTimeTrialData::PAYLOAD_LEN
        ))
    );
}
