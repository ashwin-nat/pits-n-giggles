use f1_types::{
    CarTelemetryData, F1PacketType, InvalidPacketLengthError, PacketCarTelemetryData, PacketHeader,
};
use serde_json::json;

fn sample_header() -> PacketHeader {
    PacketHeader::from_values(
        2025,
        25,
        1,
        2,
        1,
        F1PacketType::CarTelemetry,
        99,
        12.0,
        1,
        2,
        3,
        255,
    )
}

fn sample_telemetry(seed: u8) -> CarTelemetryData {
    CarTelemetryData::from_values(
        300 + seed as u16,
        1.0,
        -0.01 - seed as f32,
        0.25 + seed as f32,
        seed,
        8 - (seed as i8 % 3),
        11000 + seed as u16,
        seed % 2 == 0,
        80 + seed,
        0b1010101010101010u16.saturating_add(seed as u16),
        [
            400 + seed as u16,
            401 + seed as u16,
            500 + seed as u16,
            501 + seed as u16,
        ],
        [80 + seed, 81 + seed, 82 + seed, 83 + seed],
        [90 + seed, 91 + seed, 92 + seed, 93 + seed],
        110 + seed as u16,
        [
            21.5 + seed as f32,
            21.6 + seed as f32,
            24.3 + seed as f32,
            24.4 + seed as f32,
        ],
        [0, 1, 0, 1],
    )
}

fn telemetry_packet_fixture() -> PacketCarTelemetryData {
    let telemetry = (0..PacketCarTelemetryData::MAX_CARS as u8)
        .map(sample_telemetry)
        .collect::<Vec<_>>();
    PacketCarTelemetryData::from_values(sample_header(), telemetry, 255, 2, 6)
}

#[test]
fn car_telemetry_data_round_trips_through_bytes() {
    let telemetry = sample_telemetry(0);
    let reparsed = CarTelemetryData::parse(&telemetry.to_bytes()).expect("parse telemetry");

    assert_eq!(CarTelemetryData::PACKET_LEN, 60);
    assert_eq!(reparsed, telemetry);
}

#[test]
fn car_telemetry_json_matches_python_shape() {
    let telemetry = sample_telemetry(0);
    let value = serde_json::to_value(telemetry).expect("serialize");

    assert_eq!(
        value,
        json!({
            "speed": 300,
            "throttle": 1.0,
            "steer": -0.009999999776482582,
            "brake": 0.25,
            "clutch": 0,
            "gear": 8,
            "engine-rpm": 11000,
            "drs": true,
            "rev-lights-percent": 80,
            "brakes-temperature": [400, 401, 500, 501],
            "tyres-surface-temperature": [80, 81, 82, 83],
            "tyres-inner-temperature": [90, 91, 92, 93],
            "engine-temperature": 110,
            "tyres-pressure": [21.5, 21.600000381469727, 24.299999237060547, 24.399999618530273],
            "surface-type": [0, 1, 0, 1]
        })
    );
}

#[test]
fn packet_car_telemetry_round_trips_with_extra_fields() {
    let packet = telemetry_packet_fixture();
    let bytes = packet.to_bytes();
    let header = PacketHeader::parse(&bytes[..PacketHeader::PACKET_LEN]).expect("parse header");
    let parsed = PacketCarTelemetryData::parse(header, &bytes[PacketHeader::PACKET_LEN..])
        .expect("parse packet");

    assert_eq!(parsed, packet);
    assert_eq!(
        parsed.car_telemetry_data.len(),
        PacketCarTelemetryData::MAX_CARS
    );
}

#[test]
fn packet_car_telemetry_json_matches_python_shape() {
    let packet = telemetry_packet_fixture();
    let value = serde_json::to_value(packet).expect("serialize");

    assert_eq!(
        value["car-telemetry-data"].as_array().map(Vec::len),
        Some(PacketCarTelemetryData::MAX_CARS)
    );
    assert_eq!(value["mfd-panel-index"], json!(255));
    assert_eq!(value["mfd-panel-index-secondary"], json!(2));
    assert_eq!(value["suggested-gear"], json!(6));
}

#[test]
fn packet_car_telemetry_rejects_wrong_length() {
    let error =
        PacketCarTelemetryData::parse(sample_header(), &[0u8; 10]).expect_err("wrong length");

    assert_eq!(
        error,
        InvalidPacketLengthError::new(format!(
            "Received packet length {} is not equal to expected {}",
            10,
            PacketCarTelemetryData::PAYLOAD_LEN
        ))
    );
}
