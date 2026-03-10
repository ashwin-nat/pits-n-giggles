use f1_types::{
    DriverStatus, F1PacketType, InvalidPacketLengthError, LapData, PacketHeader, PacketLapData,
    PitStatus, ResultStatus, Sector,
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
        F1PacketType::LapData,
        2222,
        66.0,
        2,
        3,
        0,
        255,
    )
}

fn sample_lap(packet_format: u16, index: u8) -> LapData {
    LapData::from_values(
        packet_format,
        if index == 0 { 70_687 } else { 70_475 },
        if index == 0 { 33_841 } else { 33_748 },
        if index == 0 { 20_525 } else { 20_948 },
        0,
        0,
        0,
        if index == 0 { 367 } else { 567 },
        0,
        if index == 0 { 13_500 } else { 14_100 },
        0,
        if index == 0 { 2124.3691 } else { 2103.7285 },
        if index == 0 { 19_418.309 } else { 19_397.668 },
        -0.0,
        if index == 0 { 16 } else { 17 },
        5,
        PitStatus::None,
        0,
        Sector::Sector2,
        false,
        0,
        0,
        0,
        0,
        0,
        if index == 0 { 16 } else { 19 },
        DriverStatus::OnTrack,
        ResultStatus::ACTIVE,
        false,
        0,
        0,
        0,
        if packet_format == 2023 {
            0.0
        } else if index == 0 {
            318.5956
        } else {
            320.0920
        },
        if packet_format == 2023 { 0 } else { 3 },
    )
}

fn sample_packet(packet_format: u16) -> PacketLapData {
    let mut laps = vec![sample_lap(packet_format, 0), sample_lap(packet_format, 1)];
    while laps.len() < PacketLapData::MAX_CARS {
        laps.push(LapData::from_values(
            packet_format,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0.0,
            0.0,
            0.0,
            0,
            0,
            PitStatus::None,
            0,
            Sector::Sector1,
            false,
            0,
            0,
            0,
            0,
            0,
            0,
            DriverStatus::InGarage,
            ResultStatus::INVALID,
            false,
            0,
            0,
            0,
            0.0,
            0,
        ));
    }

    PacketLapData::from_values(sample_header(packet_format), laps, -1, -1)
}

#[test]
fn lap_data_round_trips_for_2024() {
    let lap = sample_lap(2024, 0);
    let reparsed = LapData::parse(&lap.to_bytes(), 2024).expect("parse lap");

    assert_eq!(reparsed, lap);
}

#[test]
fn lap_data_json_matches_python_shape_for_2023() {
    let value = serde_json::to_value(sample_lap(2023, 0)).expect("serialize");

    assert_eq!(value["last-lap-time-str"], json!("01:10.687"));
    assert_eq!(value["pit-status"], json!("NONE"));
    assert_eq!(value["sector"], json!("1"));
    assert_eq!(value["driver-status"], json!("ON_TRACK"));
    assert_eq!(value["speed-trap-fastest-speed"], json!(0.0));
}

#[test]
fn packet_lap_data_round_trips() {
    let packet = sample_packet(2025);
    let bytes = packet.to_bytes();
    let header = PacketHeader::parse(&bytes[..PacketHeader::PACKET_LEN]).expect("parse header");
    let parsed =
        PacketLapData::parse(header, &bytes[PacketHeader::PACKET_LEN..]).expect("parse packet");

    assert_eq!(parsed, packet);
    assert_eq!(parsed.time_trial_pb_car_idx, -1);
    assert_eq!(parsed.time_trial_rival_car_idx, -1);
}

#[test]
fn packet_lap_data_json_matches_python_shape() {
    let value = serde_json::to_value(sample_packet(2024)).expect("serialize");

    assert_eq!(value["lap-data-count"], json!(22));
    assert_eq!(value["time-trial-pb-car-idx"], json!(-1));
    assert_eq!(
        value["lap-data"][0]["speed-trap-fastest-speed"],
        json!(318.5956_f32)
    );
}

#[test]
fn packet_lap_data_rejects_wrong_length() {
    let error = PacketLapData::parse(sample_header(2024), &[0u8; 100]).expect_err("wrong length");

    assert_eq!(
        error,
        InvalidPacketLengthError::new(format!(
            "Received packet length {} is not equal to expected {}",
            100,
            PacketLapData::payload_len_for_format(2024)
        ))
    );
}
