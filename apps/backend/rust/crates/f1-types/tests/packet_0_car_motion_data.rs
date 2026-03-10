use f1_types::{
    CarMotionData, F1PacketType, InvalidPacketLengthError, PacketHeader, PacketMotionData,
};
use serde_json::json;

fn sample_header() -> PacketHeader {
    PacketHeader::from_values(
        2025,
        25,
        1,
        15,
        3,
        F1PacketType::Motion,
        55,
        10.5,
        7,
        8,
        1,
        255,
    )
}

fn sample_car(index: i16) -> CarMotionData {
    let n = index as f32;
    CarMotionData::from_values(
        1.0 + n,
        2.0 + n,
        3.0 + n,
        4.0 + n,
        5.0 + n,
        6.0 + n,
        10 + index,
        20 + index,
        30 + index,
        40 + index,
        50 + index,
        60 + index,
        7.0 + n,
        8.0 + n,
        9.0 + n,
        10.0 + n,
        11.0 + n,
        12.0 + n,
    )
}

fn motion_packet_fixture() -> PacketMotionData {
    let cars = (0..PacketMotionData::MAX_CARS as i16)
        .map(sample_car)
        .collect::<Vec<_>>();
    PacketMotionData::from_values(sample_header(), cars)
}

#[test]
fn car_motion_data_round_trips_through_bytes() {
    let car = sample_car(3);
    let reparsed = CarMotionData::parse(&car.to_bytes()).expect("car should parse");

    assert_eq!(CarMotionData::PACKET_LEN, 60);
    assert_eq!(reparsed, car);
}

#[test]
fn car_motion_data_serializes_to_python_compatible_shape() {
    let car = sample_car(0);
    let value = serde_json::to_value(car).expect("car should serialize");

    assert_eq!(
        value,
        json!({
            "world-position": {"x": 1.0, "y": 2.0, "z": 3.0},
            "world-velocity": {"x": 4.0, "y": 5.0, "z": 6.0},
            "world-forward-dir": {"x": 10, "y": 20, "z": 30},
            "world-right-dir": {"x": 40, "y": 50, "z": 60},
            "g-force": {"lateral": 7.0, "longitudinal": 8.0, "vertical": 9.0},
            "orientation": {"yaw": 10.0, "pitch": 11.0, "roll": 12.0}
        })
    );
}

#[test]
fn packet_motion_data_round_trips_with_header_and_payload() {
    let packet = motion_packet_fixture();
    let bytes = packet.to_bytes();
    let parsed_header =
        PacketHeader::parse(&bytes[..PacketHeader::PACKET_LEN]).expect("header parse");
    let parsed_packet = PacketMotionData::parse(parsed_header, &bytes[PacketHeader::PACKET_LEN..])
        .expect("packet parse");

    assert_eq!(parsed_packet, packet);
    assert_eq!(
        parsed_packet.car_motion_data.len(),
        PacketMotionData::MAX_CARS
    );
}

#[test]
fn packet_motion_data_rejects_wrong_payload_length() {
    let error = PacketMotionData::parse(sample_header(), &[0u8; 120])
        .expect_err("wrong payload should fail");

    assert_eq!(
        error,
        InvalidPacketLengthError::new(format!(
            "Received packet length {} is not equal to expected {}",
            120,
            PacketMotionData::PAYLOAD_LEN
        ))
    );
}

#[test]
fn packet_motion_data_serializes_to_python_compatible_shape() {
    let packet = motion_packet_fixture();
    let value = serde_json::to_value(packet).expect("packet should serialize");

    assert_eq!(
        value["car-motion-data"].as_array().map(Vec::len),
        Some(PacketMotionData::MAX_CARS)
    );
    assert_eq!(
        value["car-motion-data"][0],
        json!({
            "world-position": {"x": 1.0, "y": 2.0, "z": 3.0},
            "world-velocity": {"x": 4.0, "y": 5.0, "z": 6.0},
            "world-forward-dir": {"x": 10, "y": 20, "z": 30},
            "world-right-dir": {"x": 40, "y": 50, "z": 60},
            "g-force": {"lateral": 7.0, "longitudinal": 8.0, "vertical": 9.0},
            "orientation": {"yaw": 10.0, "pitch": 11.0, "roll": 12.0}
        })
    );
}
