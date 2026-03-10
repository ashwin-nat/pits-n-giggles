use f1_types::{F1PacketType, InvalidPacketLengthError, PacketHeader, PacketMotionExData};
use serde_json::json;

fn sample_header(packet_format: u16) -> PacketHeader {
    PacketHeader::from_values(
        packet_format,
        if packet_format >= 2025 { 25 } else { 24 },
        1,
        2,
        1,
        F1PacketType::MotionEx,
        1_234,
        55.0,
        9,
        10,
        0,
        255,
    )
}

fn sample_motion_ex(packet_format: u16) -> PacketMotionExData {
    PacketMotionExData::from_values(
        sample_header(packet_format),
        [1.0, 2.0, 3.0, 4.0],
        [5.0, 6.0, 7.0, 8.0],
        [9.0, 10.0, 11.0, 12.0],
        [13.0, 14.0, 15.0, 16.0],
        [0.1, 0.2, 0.3, 0.4],
        [0.5, 0.6, 0.7, 0.8],
        [17.0, 18.0, 19.0, 20.0],
        [21.0, 22.0, 23.0, 24.0],
        [25.0, 26.0, 27.0, 28.0],
        0.9,
        1.1,
        1.2,
        1.3,
        1.4,
        1.5,
        [-0.03, -0.03, -0.05, -0.05],
        [0.004, 0.004, 0.0, 0.0],
        0.35,
        2.1,
        2.2,
        2.3,
        3.1,
        3.2,
        3.3,
        4.1,
        4.2,
        4.3,
        -0.2,
    )
}

#[test]
fn motion_ex_round_trips_for_2023_layout() {
    let packet = sample_motion_ex(2023);
    let bytes = packet.to_bytes();
    let parsed = PacketMotionExData::parse(sample_header(2023), &bytes).expect("parse packet");

    assert_eq!(PacketMotionExData::PACKET_LEN_23, 188);
    assert_eq!(parsed, packet);
    assert_eq!(parsed.front_aero_height, 0.0);
    assert_eq!(parsed.chassis_pitch, 0.0);
}

#[test]
fn motion_ex_round_trips_for_2025_layout() {
    let packet = sample_motion_ex(2025);
    let bytes = packet.to_bytes();
    let parsed = PacketMotionExData::parse(sample_header(2025), &bytes).expect("parse packet");

    assert_eq!(PacketMotionExData::PACKET_LEN_25, 244);
    assert_eq!(parsed, packet);
}

#[test]
fn motion_ex_json_matches_python_shape() {
    let value = serde_json::to_value(sample_motion_ex(2025)).expect("serialize");

    assert_eq!(
        value,
        json!({
            "suspension-position": [1.0, 2.0, 3.0, 4.0],
            "suspension-velocity": [5.0, 6.0, 7.0, 8.0],
            "suspension-acceleration": [9.0, 10.0, 11.0, 12.0],
            "wheel-speed": [13.0, 14.0, 15.0, 16.0],
            "wheel-slip-ratio": [0.10000000149011612, 0.20000000298023224, 0.30000001192092896, 0.4000000059604645],
            "wheel-slip-angle": [0.5, 0.6000000238418579, 0.699999988079071, 0.800000011920929],
            "wheel-lat-force": [17.0, 18.0, 19.0, 20.0],
            "wheel-long-force": [21.0, 22.0, 23.0, 24.0],
            "height-of-cog-above-ground": 0.3499999940395355,
            "local-velocity": { "x": 2.0999999046325684, "y": 2.200000047683716, "z": 2.299999952316284 },
            "angular-velocity": { "x": 3.0999999046325684, "y": 3.200000047683716, "z": 3.299999952316284 },
            "angular-acceleration": { "x": 4.099999904632568, "y": 4.199999809265137, "z": 4.300000190734863 },
            "front-wheels-angle": -0.20000000298023224,
            "wheel-vert-force": [25.0, 26.0, 27.0, 28.0],
            "front-aero-height": 0.8999999761581421,
            "rear-aero-height": 1.100000023841858,
            "front-roll-angle": 1.2000000476837158,
            "rear-roll-angle": 1.2999999523162842,
            "chassis-yaw": 1.399999976158142,
            "chassis-pitch": 1.5,
            "wheel-camber": [-0.029999999329447746, -0.029999999329447746, -0.05000000074505806, -0.05000000074505806],
            "wheel-camber-gain": [0.004000000189989805, 0.004000000189989805, 0.0, 0.0]
        })
    );
}

#[test]
fn motion_ex_rejects_wrong_length() {
    let error =
        PacketMotionExData::parse(sample_header(2024), &[0u8; 100]).expect_err("wrong length");

    assert_eq!(
        error,
        InvalidPacketLengthError::new(format!(
            "Received packet length {} is not equal to expected {}",
            100,
            PacketMotionExData::PACKET_LEN_24
        ))
    );
}
