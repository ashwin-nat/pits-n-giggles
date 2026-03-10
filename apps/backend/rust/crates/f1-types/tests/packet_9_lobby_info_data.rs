use f1_types::{
    F1PacketType, InvalidPacketLengthError, LobbyInfoData, PacketHeader, PacketLobbyInfoData,
    ReadyStatus,
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
        F1PacketType::LobbyInfo,
        909,
        44.0,
        2,
        3,
        0,
        255,
    )
}

fn sample_player(packet_format: u16, index: u8) -> LobbyInfoData {
    let (team_id_raw, platform_raw, your_telemetry_raw, show_online_names, tech_level) =
        match packet_format {
            2023 => (if index == 0 { 4 } else { 8 }, 1, 1, true, 0),
            2024 => (if index == 0 { 2 } else { 8 }, 255, 1, index == 1, 1200),
            _ => (if index == 0 { 3 } else { 8 }, 1, 1, index == 1, 1500),
        };

    LobbyInfoData::from_values(
        packet_format,
        index.is_multiple_of(2),
        team_id_raw,
        if index == 0 { 37 } else { 10 },
        platform_raw,
        if index == 0 {
            "Milk Shake".to_string()
        } else {
            "NORRIS".to_string()
        },
        if index == 0 { 13 } else { 4 },
        your_telemetry_raw,
        show_online_names,
        tech_level,
        if index == 0 {
            ReadyStatus::NotReady
        } else {
            ReadyStatus::Ready
        },
    )
}

fn sample_packet(packet_format: u16, num_players: u8) -> PacketLobbyInfoData {
    let players = (0..num_players)
        .map(|index| sample_player(packet_format, index))
        .collect::<Vec<_>>();

    PacketLobbyInfoData::from_values(sample_header(packet_format), num_players, players)
}

#[test]
fn lobby_info_round_trips_for_2025() {
    let player = sample_player(2025, 1);
    let reparsed = LobbyInfoData::parse(&player.to_bytes(), 2025).expect("parse player");

    assert_eq!(LobbyInfoData::PACKET_LEN_25, 42);
    assert_eq!(reparsed, player);
}

#[test]
fn lobby_info_json_matches_python_shape_for_2023() {
    let value = serde_json::to_value(sample_player(2023, 0)).expect("serialize");

    assert_eq!(
        value,
        json!({
            "ai-controlled": true,
            "team-id": "Aston Martin",
            "nationality": "Indian",
            "platform": "Steam",
            "name": "Milk Shake",
            "car-number": 13,
            "your-telemetry": "Public",
            "show-online-names": true,
            "tech-level": 0,
            "ready-status": "NOT_READY"
        })
    );
}

#[test]
fn lobby_info_json_matches_python_shape_for_2025_team_case() {
    let value = serde_json::to_value(sample_player(2025, 1)).expect("serialize");

    assert_eq!(value["team-id"], json!("Mclaren"));
}

#[test]
fn packet_lobby_info_round_trips() {
    let packet = sample_packet(2024, 2);
    let bytes = packet.to_bytes();
    let header = PacketHeader::parse(&bytes[..PacketHeader::PACKET_LEN]).expect("parse header");
    let parsed = PacketLobbyInfoData::parse(header, &bytes[PacketHeader::PACKET_LEN..])
        .expect("parse packet");

    assert_eq!(parsed, packet);
    assert_eq!(parsed.lobby_players.len(), 2);
}

#[test]
fn packet_lobby_info_parses_fixed_size_payload_with_unused_slots() {
    let packet = sample_packet(2025, 2);
    let bytes = packet.to_bytes();
    let payload = &bytes[PacketHeader::PACKET_LEN..];
    let parsed = PacketLobbyInfoData::parse(sample_header(2025), payload).expect("parse packet");

    assert_eq!(parsed.num_players, 2);
    assert_eq!(parsed.lobby_players.len(), 2);
    assert_eq!(parsed.lobby_players[1].name, "NORRIS");
    assert_eq!(
        payload.len(),
        PacketLobbyInfoData::payload_len_for_format(2025)
    );
}

#[test]
fn packet_lobby_info_json_matches_python_shape() {
    let value = serde_json::to_value(sample_packet(2024, 2)).expect("serialize");

    assert_eq!(value["num-players"], json!(2));
    assert_eq!(
        value["lobby-players"][0]["team-id"],
        json!("Red Bull Racing")
    );
    assert_eq!(
        value["lobby-players"][0]["ready-status"],
        json!("NOT_READY")
    );
    assert_eq!(value["lobby-players"][1]["show-online-names"], json!(true));
}

#[test]
fn packet_lobby_info_rejects_wrong_length() {
    let error =
        PacketLobbyInfoData::parse(sample_header(2024), &[0u8; 100]).expect_err("wrong length");

    assert_eq!(
        error,
        InvalidPacketLengthError::new(format!(
            "Received packet length {} is not equal to expected {}",
            100,
            PacketLobbyInfoData::payload_len_for_format(2024)
        ))
    );
}
