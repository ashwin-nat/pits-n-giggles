use f1_types::{
    F1PacketType, InvalidPacketLengthError, LiveryColour, PacketHeader, PacketParticipantsData,
    ParticipantData,
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
        F1PacketType::Participants,
        808,
        33.0,
        2,
        3,
        0,
        255,
    )
}

fn sample_participant(packet_format: u16, index: u8) -> ParticipantData {
    let team = match packet_format {
        2023 => {
            if index == 0 {
                2
            } else {
                8
            }
        }
        2024 => {
            if index == 0 {
                2
            } else {
                8
            }
        }
        _ => {
            if index == 0 {
                3
            } else {
                8
            }
        }
    };

    ParticipantData::from_values(
        packet_format,
        index.is_multiple_of(2),
        if index == 0 { 9 } else { 54 },
        255,
        team,
        false,
        if index == 0 { 33 } else { 4 },
        if index == 0 { 22 } else { 10 },
        if index == 0 {
            "VERSTAPPEN".to_string()
        } else {
            "NORRIS".to_string()
        },
        1,
        index == 1,
        if index == 1 { 1 } else { 255 },
        0,
        4,
        vec![
            LiveryColour::from_values(1, 2, 3),
            LiveryColour::from_values(4, 5, 6),
            LiveryColour::from_values(7, 8, 9),
            LiveryColour::from_values(10, 11, 12),
        ],
    )
}

fn sample_packet(packet_format: u16) -> PacketParticipantsData {
    let mut participants = vec![
        sample_participant(packet_format, 0),
        sample_participant(packet_format, 1),
    ];
    while participants.len() < PacketParticipantsData::MAX_PARTICIPANTS {
        participants.push(ParticipantData::from_values(
            packet_format,
            false,
            255,
            255,
            255,
            false,
            0,
            255,
            String::new(),
            0,
            false,
            0,
            0,
            0,
            vec![],
        ));
    }

    PacketParticipantsData::from_values(sample_header(packet_format), 2, participants)
}

#[test]
fn participant_round_trips_for_2025() {
    let participant = sample_participant(2025, 0);
    let reparsed =
        ParticipantData::parse(&participant.to_bytes(), 2025).expect("parse participant");

    assert_eq!(ParticipantData::PACKET_LEN_25, 57);
    assert_eq!(reparsed, participant);
}

#[test]
fn participant_json_matches_python_shape_for_2024() {
    let value = serde_json::to_value(sample_participant(2024, 1)).expect("serialize");

    assert_eq!(
        value,
        json!({
            "ai-controlled": false,
            "driver-id": 54,
            "network-id": 255,
            "team-id": "McLaren",
            "my-team": false,
            "race-number": 4,
            "nationality": "British",
            "name": "NORRIS",
            "telemetry-setting": "Public",
            "show-online-names": true,
            "tech-level": 0,
            "platform": "Steam"
        })
    );
}

#[test]
fn participant_json_matches_python_shape_for_2025_team_case() {
    let value = serde_json::to_value(sample_participant(2025, 1)).expect("serialize");

    assert_eq!(value["team-id"], json!("Mclaren"));
}

#[test]
fn packet_participants_round_trips() {
    let packet = sample_packet(2025);
    let bytes = packet.to_bytes();
    let header = PacketHeader::parse(&bytes[..PacketHeader::PACKET_LEN]).expect("parse header");
    let parsed = PacketParticipantsData::parse(header, &bytes[PacketHeader::PACKET_LEN..])
        .expect("parse packet");

    assert_eq!(parsed, packet);
    assert_eq!(
        parsed.participants.len(),
        PacketParticipantsData::MAX_PARTICIPANTS
    );
}

#[test]
fn packet_participants_json_matches_python_shape() {
    let value = serde_json::to_value(sample_packet(2023)).expect("serialize");

    assert_eq!(value["num-active-cars"], json!(2));
    assert_eq!(
        value["participants"][0]["team-id"],
        json!("Red Bull Racing")
    );
    assert_eq!(value["participants"][1]["platform"], json!("Steam"));
}

#[test]
fn packet_participants_reject_wrong_length() {
    let error =
        PacketParticipantsData::parse(sample_header(2024), &[0u8; 100]).expect_err("wrong length");

    assert_eq!(
        error,
        InvalidPacketLengthError::new(format!(
            "Received packet length {} is not equal to expected {}",
            100,
            PacketParticipantsData::payload_len_for_format(2024)
        ))
    );
}
