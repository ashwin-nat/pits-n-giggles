use f1_types::{F1PacketType, InvalidPacketLengthError, PacketHeader, PacketLapPositionsData};
use serde_json::json;

fn sample_header() -> PacketHeader {
    PacketHeader::from_values(
        2025,
        25,
        1,
        2,
        1,
        F1PacketType::LapPositions,
        88,
        12.0,
        7,
        8,
        0,
        255,
    )
}

fn sample_packet() -> PacketLapPositionsData {
    PacketLapPositionsData::from_values(
        sample_header(),
        2,
        5,
        vec![
            vec![
                16, 17, 13, 2, 12, 8, 6, 1, 9, 10, 19, 5, 18, 11, 3, 14, 4, 15, 7, 20, 0, 0,
            ],
            vec![
                11, 17, 1, 2, 19, 9, 10, 16, 15, 13, 14, 8, 7, 5, 18, 20, 6, 12, 3, 4, 0, 0,
            ],
        ],
    )
}

#[test]
fn lap_positions_round_trip() {
    let packet = sample_packet();
    let bytes = packet.to_bytes();
    let header = PacketHeader::parse(&bytes[..PacketHeader::PACKET_LEN]).expect("parse header");
    let parsed = PacketLapPositionsData::parse(header, &bytes[PacketHeader::PACKET_LEN..])
        .expect("parse packet");

    assert_eq!(parsed, packet);
    assert_eq!(PacketLapPositionsData::PAYLOAD_LEN, 1102);
}

#[test]
fn lap_positions_json_matches_python_shape() {
    let value = serde_json::to_value(sample_packet()).expect("serialize");

    assert_eq!(
        value,
        json!({
            "num-laps": 2,
            "lap-start": 5,
            "lap-positions": [
                [16, 17, 13, 2, 12, 8, 6, 1, 9, 10, 19, 5, 18, 11, 3, 14, 4, 15, 7, 20, 0, 0],
                [11, 17, 1, 2, 19, 9, 10, 16, 15, 13, 14, 8, 7, 5, 18, 20, 6, 12, 3, 4, 0, 0]
            ]
        })
    );
}

#[test]
fn lap_positions_reject_wrong_length() {
    let error =
        PacketLapPositionsData::parse(sample_header(), &[0u8; 100]).expect_err("wrong length");

    assert_eq!(
        error,
        InvalidPacketLengthError::new(format!(
            "Received packet length {} is not equal to expected {}",
            100,
            PacketLapPositionsData::PAYLOAD_LEN
        ))
    );
}

#[test]
fn lap_positions_reject_num_laps_above_max() {
    let mut payload = vec![0u8; PacketLapPositionsData::PAYLOAD_LEN];
    payload[0] = (PacketLapPositionsData::MAX_LAPS as u8).saturating_add(1);
    payload[1] = 3;

    let error =
        PacketLapPositionsData::parse(sample_header(), &payload).expect_err("invalid num_laps");

    assert_eq!(
        error,
        InvalidPacketLengthError::new(format!(
            "Received num laps {} exceeds max {}",
            PacketLapPositionsData::MAX_LAPS as u8 + 1,
            PacketLapPositionsData::MAX_LAPS
        ))
    );
}
