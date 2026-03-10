use f1_types::{
    CarDamageData, F1PacketType, InvalidPacketLengthError, PacketCarDamageData, PacketHeader,
};
use serde_json::json;

fn header_for_format(packet_format: u16) -> PacketHeader {
    PacketHeader::from_values(
        packet_format,
        (packet_format - 2000) as u8,
        1,
        2,
        1,
        F1PacketType::CarDamage,
        88,
        4.0,
        1,
        2,
        3,
        255,
    )
}

fn sample_damage(packet_format: u16, seed: u8) -> CarDamageData {
    let tyre_blisters = if packet_format >= 2025 {
        [9 + seed, 10 + seed, 11 + seed, 12 + seed]
    } else {
        [0, 0, 0, 0]
    };

    CarDamageData::from_values(
        packet_format,
        [
            0.1 + seed as f32,
            0.2 + seed as f32,
            0.3 + seed as f32,
            0.4 + seed as f32,
        ],
        [1 + seed, 2 + seed, 3 + seed, 4 + seed],
        [5 + seed, 6 + seed, 7 + seed, 8 + seed],
        tyre_blisters,
        13 + seed,
        14 + seed,
        15 + seed,
        16 + seed,
        17 + seed,
        18 + seed,
        seed % 2 == 0,
        seed % 2 == 1,
        19 + seed,
        20 + seed,
        21 + seed,
        22 + seed,
        23 + seed,
        24 + seed,
        25 + seed,
        26 + seed,
        true,
        false,
    )
}

fn packet_fixture(packet_format: u16) -> PacketCarDamageData {
    let cars = (0..PacketCarDamageData::MAX_CARS as u8)
        .map(|seed| sample_damage(packet_format, seed))
        .collect::<Vec<_>>();
    PacketCarDamageData::from_values(header_for_format(packet_format), cars)
}

#[test]
fn car_damage_data_round_trips_for_f1_24_layout() {
    let car = sample_damage(2024, 0);
    let reparsed = CarDamageData::parse(&car.to_bytes(), 2024).expect("car parse");

    assert_eq!(CarDamageData::PACKET_LEN, 42);
    assert_eq!(reparsed, car);
    assert_eq!(reparsed.tyre_blisters, [0, 0, 0, 0]);
}

#[test]
fn car_damage_data_round_trips_for_f1_25_layout() {
    let car = sample_damage(2025, 0);
    let reparsed = CarDamageData::parse(&car.to_bytes(), 2025).expect("car parse");

    assert_eq!(CarDamageData::PACKET_LEN_25, 46);
    assert_eq!(reparsed, car);
    assert_eq!(reparsed.tyre_blisters, [9, 10, 11, 12]);
}

#[test]
fn car_damage_json_matches_python_shape_and_omits_tyre_blisters() {
    let car = sample_damage(2025, 0);
    let value = serde_json::to_value(car).expect("serialize");

    assert_eq!(
        value,
        json!({
            "tyres-wear": [
                0.10000000149011612,
                0.20000000298023224,
                0.30000001192092896,
                0.4000000059604645
            ],
            "tyres-damage": [1, 2, 3, 4],
            "brakes-damage": [5, 6, 7, 8],
            "front-left-wing-damage": 13,
            "front-right-wing-damage": 14,
            "rear-wing-damage": 15,
            "floor-damage": 16,
            "diffuser-damage": 17,
            "sidepod-damage": 18,
            "drs-fault": true,
            "ers-fault": false,
            "gear-box-damage": 19,
            "engine-damage": 20,
            "engine-mguh-wear": 21,
            "engine-es-wear": 22,
            "engine-ce-wear": 23,
            "engine-ice-wear": 24,
            "engine-mguk-wear": 25,
            "engine-tc-wear": 26,
            "engine-blown": true,
            "engine-seized": false
        })
    );
    assert!(value.get("tyre-blisters").is_none());
}

#[test]
fn packet_car_damage_data_round_trips_for_f1_25() {
    let packet = packet_fixture(2025);
    let bytes = packet.to_bytes();
    let header = PacketHeader::parse(&bytes[..PacketHeader::PACKET_LEN]).expect("header parse");
    let parsed = PacketCarDamageData::parse(header, &bytes[PacketHeader::PACKET_LEN..])
        .expect("packet parse");

    assert_eq!(parsed, packet);
    assert_eq!(parsed.car_damage_data.len(), PacketCarDamageData::MAX_CARS);
}

#[test]
fn packet_car_damage_data_rejects_wrong_length() {
    let header = header_for_format(2024);
    let error = PacketCarDamageData::parse(header, &[0u8; 84]).expect_err("wrong length");

    assert_eq!(
        error,
        InvalidPacketLengthError::new(format!(
            "Received packet length {} is not equal to expected {}",
            84,
            PacketCarDamageData::MAX_CARS * CarDamageData::PACKET_LEN
        ))
    );
}
