use f1_types::{
    CarSetupData, F1PacketType, InvalidPacketLengthError, PacketCarSetupData, PacketHeader,
};
use serde_json::json;

fn header_for_format(packet_format: u16) -> PacketHeader {
    PacketHeader::from_values(
        packet_format,
        (packet_format - 2000) as u8,
        1,
        2,
        1,
        F1PacketType::CarSetups,
        77,
        9.0,
        3,
        4,
        5,
        255,
    )
}

fn sample_setup(packet_format: u16, seed: u8) -> CarSetupData {
    CarSetupData::from_values(
        packet_format,
        1 + seed,
        2 + seed,
        3 + seed,
        4 + seed,
        -3.5 + seed as f32,
        -2.0 + seed as f32,
        0.02 + seed as f32,
        0.12 + seed as f32,
        5 + seed,
        6 + seed,
        7 + seed,
        8 + seed,
        9 + seed,
        10 + seed,
        11 + seed,
        12 + seed,
        21.5 + seed as f32,
        21.6 + seed as f32,
        24.3 + seed as f32,
        24.4 + seed as f32,
        13 + seed,
        14.0 + seed as f32,
        15 + seed,
    )
}

fn zero_setup(packet_format: u16) -> CarSetupData {
    CarSetupData::from_values(
        packet_format,
        0,
        0,
        0,
        0,
        0.0,
        0.0,
        0.0,
        0.0,
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
        0.0,
        0,
        0.0,
        0,
    )
}

fn setup_packet_fixture(packet_format: u16) -> PacketCarSetupData {
    let setups = (0..PacketCarSetupData::MAX_CARS as u8)
        .map(|seed| sample_setup(packet_format, seed))
        .collect::<Vec<_>>();
    PacketCarSetupData::from_values(header_for_format(packet_format), setups, 41.25)
}

#[test]
fn car_setup_data_round_trips_for_f1_23_layout() {
    let setup = sample_setup(2023, 0);
    let reparsed = CarSetupData::parse(&setup.to_bytes(), 2023).expect("parse setup");

    assert_eq!(CarSetupData::PACKET_LEN_23, 49);
    assert_eq!(reparsed, setup);
    assert_eq!(reparsed.engine_braking, 0);
}

#[test]
fn car_setup_data_round_trips_for_f1_25_layout() {
    let setup = sample_setup(2025, 0);
    let reparsed = CarSetupData::parse(&setup.to_bytes(), 2025).expect("parse setup");

    assert_eq!(CarSetupData::PACKET_LEN_24, 50);
    assert_eq!(reparsed, setup);
    assert_eq!(reparsed.engine_braking, 15);
}

#[test]
fn car_setup_json_matches_python_shape() {
    let setup = sample_setup(2025, 0);
    let value = serde_json::to_value(setup).expect("serialize");

    assert_eq!(
        value,
        json!({
            "front-wing": 1,
            "rear-wing": 2,
            "on-throttle": 3,
            "off-throttle": 4,
            "front-camber": -3.5,
            "rear-camber": -2.0,
            "front-toe": 0.019999999552965164,
            "rear-toe": 0.11999999731779099,
            "front-suspension": 5,
            "rear-suspension": 6,
            "front-anti-roll-bar": 7,
            "rear-anti-roll-bar": 8,
            "front-suspension-height": 9,
            "rear-suspension-height": 10,
            "brake-pressure": 11,
            "brake-bias": 12,
            "engine-braking": 15,
            "rear-left-tyre-pressure": 21.5,
            "rear-right-tyre-pressure": 21.600000381469727,
            "front-left-tyre-pressure": 24.299999237060547,
            "front-right-tyre-pressure": 24.399999618530273,
            "ballast": 13,
            "fuel-load": 14.0,
            "is-valid": true
        })
    );
}

#[test]
fn car_setup_validity_matches_python_behavior() {
    assert!(!zero_setup(2023).is_valid());
    assert!(sample_setup(2023, 0).is_valid());
}

#[test]
fn packet_car_setups_round_trip_for_f1_25_with_next_front_wing_value() {
    let packet = setup_packet_fixture(2025);
    let bytes = packet.to_bytes();
    let header = PacketHeader::parse(&bytes[..PacketHeader::PACKET_LEN]).expect("parse header");
    let parsed = PacketCarSetupData::parse(header, &bytes[PacketHeader::PACKET_LEN..])
        .expect("parse packet");

    assert_eq!(parsed, packet);
    assert_eq!(parsed.next_front_wing_value, 41.25);
}

#[test]
fn packet_car_setups_round_trip_for_f1_23_without_extra_float() {
    let packet = setup_packet_fixture(2023);
    let bytes = packet.to_bytes();
    let header = PacketHeader::parse(&bytes[..PacketHeader::PACKET_LEN]).expect("parse header");
    let parsed = PacketCarSetupData::parse(header, &bytes[PacketHeader::PACKET_LEN..])
        .expect("parse packet");

    assert_eq!(parsed, packet);
    assert_eq!(parsed.next_front_wing_value, 0.0);
}

#[test]
fn packet_car_setups_reject_wrong_length() {
    let header = header_for_format(2025);
    let error = PacketCarSetupData::parse(header, &[0u8; 100]).expect_err("wrong length");

    assert_eq!(
        error,
        InvalidPacketLengthError::new(format!(
            "Received packet length {} is not equal to expected {}",
            100,
            PacketCarSetupData::MAX_CARS * CarSetupData::PACKET_LEN_24 + 4
        ))
    );
}
