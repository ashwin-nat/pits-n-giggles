use f1_types::{
    F1PacketType, InvalidPacketLengthError, PacketHeader, PacketSessionData, SessionDataError,
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
        F1PacketType::Session,
        111,
        22.0,
        2,
        3,
        0,
        255,
    )
}

fn build_payload(packet_format: u16) -> Vec<u8> {
    let mut payload = vec![0u8; PacketSessionData::payload_len_for_format(packet_format)];
    payload[0] = if packet_format == 2025 { 0 } else { 1 };
    payload[1] = if packet_format == 2025 { 0 } else { 30 };
    payload[2] = if packet_format == 2025 { 0 } else { 22 };
    payload[3] = 25u8.min(5);
    payload[4..6].copy_from_slice(&4323u16.to_le_bytes());
    payload[6] = if packet_format == 2023 { 10 } else { 15 };
    payload[7] = match packet_format {
        2023 => 17i8 as u8,
        2024 => 10i8 as u8,
        _ => 40i8 as u8,
    };
    payload[8] = 0;
    payload[9..11].copy_from_slice(&7200u16.to_le_bytes());
    payload[11..13].copy_from_slice(&7200u16.to_le_bytes());
    payload[13] = 80;
    payload[18] = if packet_format == 2023 { 1 } else { 0 };

    let marshal_offset = PacketSessionData::SECTION_0_LEN;
    if packet_format == 2023 {
        payload[marshal_offset..marshal_offset + 4].copy_from_slice(&0.99f32.to_le_bytes());
        payload[marshal_offset + 4] = 3u8;
    }

    let section_2_offset =
        PacketSessionData::SECTION_0_LEN + (PacketSessionData::MAX_MARSHAL_ZONES * 5);
    payload[section_2_offset] = if packet_format == 2023 { 2 } else { 0 };
    payload[section_2_offset + 1] = if packet_format == 2023 { 1 } else { 0 };
    payload[section_2_offset + 2] = if packet_format == 2023 { 1 } else { 0 };

    let weather_offset = section_2_offset + 3;
    if packet_format == 2023 {
        payload[weather_offset] = 10;
        payload[weather_offset + 1] = 0;
        payload[weather_offset + 2] = 1;
        payload[weather_offset + 3] = 31u8;
        payload[weather_offset + 4] = 2u8;
        payload[weather_offset + 5] = 22u8;
        payload[weather_offset + 6] = 2u8;
        payload[weather_offset + 7] = 12u8;
    }

    let section_4_offset = weather_offset + (if packet_format == 2023 { 56 } else { 64 }) * 8;
    payload[section_4_offset] = 1;
    payload[section_4_offset + 1] = if packet_format == 2023 { 95 } else { 0 };
    payload[section_4_offset + 2..section_4_offset + 6]
        .copy_from_slice(&1137458632u32.to_le_bytes());
    payload[section_4_offset + 6..section_4_offset + 10]
        .copy_from_slice(&1137458632u32.to_le_bytes());
    payload[section_4_offset + 10..section_4_offset + 14]
        .copy_from_slice(&1137458632u32.to_le_bytes());
    payload[section_4_offset + 19] = if packet_format == 2023 { 1 } else { 0 };
    payload[section_4_offset + 26] = if packet_format == 2025 { 0 } else { 7 };
    payload[section_4_offset + 27] = 1;
    payload[section_4_offset + 32] = if packet_format == 2023 { 5 } else { 3 };

    if packet_format == 2024 {
        let section_5_offset = section_4_offset + 40;
        payload[section_5_offset + 37..section_5_offset + 41]
            .copy_from_slice(&2323.7588f32.to_le_bytes());
        payload[section_5_offset + 41..section_5_offset + 45]
            .copy_from_slice(&5065.0088f32.to_le_bytes());
    }

    if packet_format == 2025 {
        let section_5_offset = section_4_offset + 40;
        for (index, byte) in payload[section_5_offset..section_5_offset + 45]
            .iter_mut()
            .enumerate()
        {
            *byte = (index as u8).wrapping_add(1);
        }
    }

    payload
}

#[test]
fn packet_session_data_json_matches_python_shape_for_2023() {
    let packet =
        PacketSessionData::parse(sample_header(2023), &build_payload(2023)).expect("parse");
    let value = serde_json::to_value(packet).expect("serialize");

    assert_eq!(value["weather"], json!("Light Cloud"));
    assert_eq!(value["track-id"], json!("Austria"));
    assert_eq!(value["session-type"], json!("Race"));
    assert_eq!(value["safety-car-status"], json!("VIRTUAL_SAFETY_CAR"));
    assert_eq!(value["gearbox-assist"], json!("Manual"));
    assert_eq!(value["marshal-zones"][0]["zone-flag"], json!("YELLOW_FLAG"));
    assert_eq!(value["weekend-structure"].as_array().unwrap().len(), 12);
}

#[test]
fn packet_session_data_json_matches_python_shape_for_2024() {
    let packet =
        PacketSessionData::parse(sample_header(2024), &build_payload(2024)).expect("parse");
    let value = serde_json::to_value(packet).expect("serialize");

    assert_eq!(value["track-id"], json!("Spa"));
    assert_eq!(value["session-type"], json!("Race"));
    assert_eq!(value["game-mode"], json!("Online Custom"));
    assert_eq!(value["weekend-structure"], json!([]));
    assert_eq!(value["sector-2-lap-distance-start"], json!("2323.7588"));
    assert_eq!(value["sector-3-lap-distance-start"], json!("5065.009"));
}

#[test]
fn packet_session_data_2025_ignores_section5_for_json_but_preserves_length() {
    let payload = build_payload(2025);
    let packet = PacketSessionData::parse(sample_header(2025), &payload).expect("parse");
    let value = serde_json::to_value(&packet).expect("serialize");

    assert_eq!(value["track-id"], json!("Austria_Reverse"));
    assert_eq!(value["game-mode"], json!("Event Mode"));
    assert_eq!(value["equal-car-performance"], json!("0"));
    assert_eq!(value["weekend-structure"], json!(vec!["0"; 12]));
    assert_eq!(packet.to_bytes()[PacketHeader::PACKET_LEN..], payload);
}

#[test]
fn packet_session_data_rejects_wrong_length() {
    let error =
        PacketSessionData::parse(sample_header(2024), &[0u8; 100]).expect_err("wrong length");

    assert_eq!(
        error,
        SessionDataError::InvalidPacketLength(InvalidPacketLengthError::new(format!(
            "Received packet length {} is not equal to expected {}",
            100,
            PacketSessionData::payload_len_for_format(2024)
        )))
    );
}
