use f1_types::{
    ActualTyreCompound, CarStatusData, F1PacketType, InvalidPacketLengthError, PacketCarStatusData,
    PacketHeader, TractionControlAssistMode, VisualTyreCompound,
};
use serde_json::json;

fn sample_header() -> PacketHeader {
    PacketHeader::from_values(
        2025,
        25,
        1,
        2,
        1,
        F1PacketType::CarStatus,
        101,
        7.0,
        3,
        4,
        5,
        255,
    )
}

fn sample_status(index: u8) -> CarStatusData {
    use f1_types::packet_7_car_status_data::{ErsDeployMode, FuelMix, VehicleFiaFlags};

    CarStatusData::from_values(
        if index.is_multiple_of(2) {
            TractionControlAssistMode::Full
        } else {
            TractionControlAssistMode::Medium
        },
        index.is_multiple_of(2),
        FuelMix::Standard,
        58,
        false,
        13.4 + index as f32,
        110.0,
        2.3 + index as f32,
        13_999,
        3_499,
        9,
        1,
        216,
        ActualTyreCompound::C3,
        VisualTyreCompound::Soft,
        index,
        if index == 0 {
            VehicleFiaFlags::None
        } else {
            VehicleFiaFlags::Green
        },
        543_265.7,
        92_318.04,
        1_187_635.0,
        ErsDeployMode::Overtake,
        1_498_400.0,
        1_321_435.1,
        2_028_127.3,
        false,
    )
}

fn packet_fixture() -> PacketCarStatusData {
    let cars = (0..PacketCarStatusData::MAX_CARS as u8)
        .map(sample_status)
        .collect::<Vec<_>>();
    PacketCarStatusData::from_values(sample_header(), cars)
}

#[test]
fn car_status_round_trips_through_bytes() {
    let status = sample_status(0);
    let reparsed = CarStatusData::parse(&status.to_bytes()).expect("parse status");

    assert_eq!(CarStatusData::PACKET_LEN, 55);
    assert_eq!(reparsed, status);
}

#[test]
fn car_status_json_matches_python_shape() {
    let value = serde_json::to_value(sample_status(0)).expect("serialize");

    assert_eq!(
        value,
        json!({
            "traction-control": "FULL",
            "anti-lock-brakes": true,
            "fuel-mix": "Standard",
            "front-brake-bias": 58,
            "pit-limiter-status": false,
            "fuel-in-tank": 13.399999618530273,
            "fuel-capacity": 110.0,
            "fuel-remaining-laps": 2.299999952316284,
            "max-rpm": 13999,
            "idle-rpm": 3499,
            "max-gears": 9,
            "drs-allowed": 1,
            "drs-activation-distance": 216,
            "actual-tyre-compound": "C3",
            "visual-tyre-compound": "Soft",
            "tyres-age-laps": 0,
            "vehicle-fia-flags": "None",
            "engine-power-ice": 543265.6875,
            "engine-power-mguk": 92318.0390625,
            "ers-store-energy": 1187635.0,
            "ers-deploy-mode": "Overtake",
            "ers-harvested-this-lap-mguk": 1498400.0,
            "ers-harvested-this-lap-mguh": 1321435.125,
            "ers-deployed-this-lap": 2028127.25,
            "ers-max-capacity": 4000000.0,
            "network-paused": false
        })
    );
}

#[test]
fn packet_car_status_round_trips() {
    let packet = packet_fixture();
    let bytes = packet.to_bytes();
    let header = PacketHeader::parse(&bytes[..PacketHeader::PACKET_LEN]).expect("parse header");
    let parsed = PacketCarStatusData::parse(header, &bytes[PacketHeader::PACKET_LEN..])
        .expect("parse packet");

    assert_eq!(parsed, packet);
    assert_eq!(parsed.car_status_data.len(), PacketCarStatusData::MAX_CARS);
}

#[test]
fn packet_car_status_json_matches_python_shape() {
    let value = serde_json::to_value(packet_fixture()).expect("serialize");

    assert_eq!(
        value["car-status-data"].as_array().map(Vec::len),
        Some(PacketCarStatusData::MAX_CARS)
    );
    assert_eq!(
        value["car-status-data"][0]["traction-control"],
        json!("FULL")
    );
    assert_eq!(
        value["car-status-data"][0]["actual-tyre-compound"],
        json!("C3")
    );
}

#[test]
fn packet_car_status_rejects_wrong_length() {
    let error = PacketCarStatusData::parse(sample_header(), &[0u8; 100]).expect_err("wrong length");

    assert_eq!(
        error,
        InvalidPacketLengthError::new(format!(
            "Received packet length {} is not equal to expected {}",
            100,
            PacketCarStatusData::PAYLOAD_LEN
        ))
    );
}
