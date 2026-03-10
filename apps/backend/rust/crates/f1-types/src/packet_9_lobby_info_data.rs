use crate::errors::InvalidPacketLengthError;
use crate::{PacketHeader, TeamID24, TeamID25};
use serde::Serialize;
use serde::ser::{SerializeMap, Serializer};
use std::fmt;

fn telemetry_setting_label(value: u8) -> &'static str {
    match value {
        1 => "Public",
        _ => "Restricted",
    }
}

fn platform_label(value: u8) -> &'static str {
    match value {
        0 => "N/A",
        1 => "Steam",
        3 => "PlayStation",
        4 => "Xbox",
        6 => "Origin",
        255 => "Unknown",
        _ => "N/A",
    }
}

fn nationality_label(value: u8) -> String {
    match value {
        0 => "Unspecified",
        1 => "American",
        2 => "Argentinean",
        3 => "Australian",
        4 => "Austrian",
        5 => "Azerbaijani",
        6 => "Bahraini",
        7 => "Belgian",
        8 => "Bolivian",
        9 => "Brazilian",
        10 => "British",
        11 => "Bulgarian",
        12 => "Cameroonian",
        13 => "Canadian",
        14 => "Chilean",
        15 => "Chinese",
        16 => "Colombian",
        17 => "Costa Rican",
        18 => "Croatian",
        19 => "Cypriot",
        20 => "Czech",
        21 => "Danish",
        22 => "Dutch",
        23 => "Ecuadorian",
        24 => "English",
        25 => "Emirian",
        26 => "Estonian",
        27 => "Finnish",
        28 => "French",
        29 => "German",
        30 => "Ghanaian",
        31 => "Greek",
        32 => "Guatemalan",
        33 => "Honduran",
        34 => "Hong Konger",
        35 => "Hungarian",
        36 => "Icelander",
        37 => "Indian",
        38 => "Indonesian",
        39 => "Irish",
        40 => "Israeli",
        41 => "Italian",
        42 => "Jamaican",
        43 => "Japanese",
        44 => "Jordanian",
        45 => "Kuwaiti",
        46 => "Latvian",
        47 => "Lebanese",
        48 => "Lithuanian",
        49 => "Luxembourger",
        50 => "Malaysian",
        51 => "Maltese",
        52 => "Mexican",
        53 => "Monegasque",
        54 => "New Zealander",
        55 => "Nicaraguan",
        56 => "Northern Irish",
        57 => "Norwegian",
        58 => "Omani",
        59 => "Pakistani",
        60 => "Panamanian",
        61 => "Paraguayan",
        62 => "Peruvian",
        63 => "Polish",
        64 => "Portuguese",
        65 => "Qatari",
        66 => "Romanian",
        67 => "Russian",
        68 => "Salvadoran",
        69 => "Saudi",
        70 => "Scottish",
        71 => "Serbian",
        72 => "Singaporean",
        73 => "Slovakian",
        74 => "Slovenian",
        75 => "South Korean",
        76 => "South African",
        77 => "Spanish",
        78 => "Swedish",
        79 => "Swiss",
        80 => "Thai",
        81 => "Turkish",
        82 => "Uruguayan",
        83 => "Ukrainian",
        84 => "Venezuelan",
        85 => "Barbadian",
        86 => "Welsh",
        87 => "Vietnamese",
        _ => return value.to_string(),
    }
    .to_string()
}

fn team_label(packet_format: u16, value: u8) -> String {
    if packet_format == 2023 {
        match value {
            0 => "Mercedes",
            1 => "Ferrari",
            2 => "Red Bull Racing",
            3 => "Williams",
            4 => "Aston Martin",
            5 => "Alpine",
            6 => "Alpha Tauri",
            7 => "Haas",
            8 => "McLaren",
            9 => "Alfa Romeo",
            255 => "MY_TEAM",
            _ => return value.to_string(),
        }
        .to_string()
    } else if packet_format == 2024 {
        TeamID24::from_raw(value)
            .map(|team| team.to_string())
            .unwrap_or_else(|| value.to_string())
    } else {
        TeamID25::from_raw(value)
            .map(|team| team.to_string())
            .unwrap_or_else(|| value.to_string())
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ReadyStatus {
    NotReady,
    Ready,
    Spectating,
    Unknown(u8),
}

impl ReadyStatus {
    pub fn from_raw(value: u8) -> Self {
        match value {
            0 => Self::NotReady,
            1 => Self::Ready,
            2 => Self::Spectating,
            _ => Self::Unknown(value),
        }
    }

    pub fn raw(self) -> u8 {
        match self {
            Self::NotReady => 0,
            Self::Ready => 1,
            Self::Spectating => 2,
            Self::Unknown(value) => value,
        }
    }
}

impl fmt::Display for ReadyStatus {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::NotReady => f.write_str("NOT_READY"),
            Self::Ready => f.write_str("READY"),
            Self::Spectating => f.write_str("SPECTATING"),
            Self::Unknown(value) => write!(f, "{value}"),
        }
    }
}

impl Serialize for ReadyStatus {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        serializer.serialize_str(&self.to_string())
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct LobbyInfoData {
    pub packet_format: u16,
    pub ai_controlled: bool,
    pub team_id_raw: u8,
    pub nationality_raw: u8,
    pub platform_raw: u8,
    pub name: String,
    pub car_number: u8,
    pub your_telemetry_raw: u8,
    pub show_online_names: bool,
    pub tech_level: u16,
    pub ready_status: ReadyStatus,
}

impl LobbyInfoData {
    pub const PACKET_LEN_23: usize = 54;
    pub const PACKET_LEN_24: usize = 58;
    pub const PACKET_LEN_25: usize = 42;

    #[allow(clippy::too_many_arguments)]
    pub fn from_values(
        packet_format: u16,
        ai_controlled: bool,
        team_id_raw: u8,
        nationality_raw: u8,
        platform_raw: u8,
        name: String,
        car_number: u8,
        your_telemetry_raw: u8,
        show_online_names: bool,
        tech_level: u16,
        ready_status: ReadyStatus,
    ) -> Self {
        Self {
            packet_format,
            ai_controlled,
            team_id_raw,
            nationality_raw,
            platform_raw,
            name,
            car_number,
            your_telemetry_raw: if packet_format == 2023 {
                1
            } else {
                your_telemetry_raw
            },
            show_online_names: if packet_format == 2023 {
                true
            } else {
                show_online_names
            },
            tech_level: if packet_format == 2023 { 0 } else { tech_level },
            ready_status,
        }
    }

    pub fn packet_len_for_format(packet_format: u16) -> usize {
        match packet_format {
            2023 => Self::PACKET_LEN_23,
            2024 => Self::PACKET_LEN_24,
            _ => Self::PACKET_LEN_25,
        }
    }

    pub fn parse(data: &[u8], packet_format: u16) -> Result<Self, InvalidPacketLengthError> {
        let expected_len = Self::packet_len_for_format(packet_format);
        if data.len() != expected_len {
            return Err(InvalidPacketLengthError::new(format!(
                "Received packet length {} is not equal to expected {}",
                data.len(),
                expected_len
            )));
        }

        let ai_controlled = data[0] != 0;
        let team_id_raw = data[1];
        let nationality_raw = data[2];
        let platform_raw = data[3];
        let (name_len, offset_after_name) = if packet_format == 2025 {
            (32usize, 36usize)
        } else {
            (48usize, 52usize)
        };
        let name_bytes = &data[4..4 + name_len];
        let name = String::from_utf8_lossy(name_bytes)
            .trim_end_matches('\0')
            .to_string();
        let car_number = data[offset_after_name];

        let (your_telemetry_raw, show_online_names, tech_level, ready_status_raw) =
            if packet_format == 2023 {
                (1, true, 0, data[offset_after_name + 1])
            } else {
                (
                    data[offset_after_name + 1],
                    data[offset_after_name + 2] != 0,
                    u16::from_le_bytes([data[offset_after_name + 3], data[offset_after_name + 4]]),
                    data[offset_after_name + 5],
                )
            };

        Ok(Self::from_values(
            packet_format,
            ai_controlled,
            team_id_raw,
            nationality_raw,
            platform_raw,
            name,
            car_number,
            your_telemetry_raw,
            show_online_names,
            tech_level,
            ReadyStatus::from_raw(ready_status_raw),
        ))
    }

    pub fn to_bytes(&self) -> Vec<u8> {
        let packet_len = Self::packet_len_for_format(self.packet_format);
        let mut bytes = vec![0u8; packet_len];
        bytes[0] = u8::from(self.ai_controlled);
        bytes[1] = self.team_id_raw;
        bytes[2] = self.nationality_raw;
        bytes[3] = self.platform_raw;

        let name_len = if self.packet_format == 2025 { 32 } else { 48 };
        let name_bytes = self.name.as_bytes();
        let copied_len = usize::min(name_bytes.len(), name_len);
        bytes[4..4 + copied_len].copy_from_slice(&name_bytes[..copied_len]);

        let offset_after_name = if self.packet_format == 2025 { 36 } else { 52 };
        bytes[offset_after_name] = self.car_number;

        if self.packet_format == 2023 {
            bytes[offset_after_name + 1] = self.ready_status.raw();
        } else {
            bytes[offset_after_name + 1] = self.your_telemetry_raw;
            bytes[offset_after_name + 2] = u8::from(self.show_online_names);
            bytes[offset_after_name + 3..offset_after_name + 5]
                .copy_from_slice(&self.tech_level.to_le_bytes());
            bytes[offset_after_name + 5] = self.ready_status.raw();
        }

        bytes
    }
}

impl Serialize for LobbyInfoData {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let mut map = serializer.serialize_map(Some(10))?;
        map.serialize_entry("ai-controlled", &self.ai_controlled)?;
        map.serialize_entry("team-id", &team_label(self.packet_format, self.team_id_raw))?;
        map.serialize_entry("nationality", &nationality_label(self.nationality_raw))?;
        map.serialize_entry("platform", platform_label(self.platform_raw))?;
        map.serialize_entry("name", &self.name)?;
        map.serialize_entry("car-number", &self.car_number)?;
        map.serialize_entry(
            "your-telemetry",
            telemetry_setting_label(self.your_telemetry_raw),
        )?;
        map.serialize_entry("show-online-names", &self.show_online_names)?;
        map.serialize_entry("tech-level", &self.tech_level)?;
        map.serialize_entry("ready-status", &self.ready_status)?;
        map.end()
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct PacketLobbyInfoData {
    pub header: PacketHeader,
    pub num_players: u8,
    pub lobby_players: Vec<LobbyInfoData>,
}

impl PacketLobbyInfoData {
    pub const MAX_PLAYERS: usize = 22;

    pub fn payload_len_for_format(packet_format: u16) -> usize {
        1 + (Self::MAX_PLAYERS * LobbyInfoData::packet_len_for_format(packet_format))
    }

    pub fn parse(header: PacketHeader, packet: &[u8]) -> Result<Self, InvalidPacketLengthError> {
        if packet.is_empty() {
            return Err(InvalidPacketLengthError::new(
                "Received packet length 0 is not equal to expected at least 1",
            ));
        }

        let num_players = packet[0];
        if usize::from(num_players) > Self::MAX_PLAYERS {
            return Err(InvalidPacketLengthError::new(format!(
                "Received player count {} exceeds maximum {}",
                num_players,
                Self::MAX_PLAYERS
            )));
        }

        let expected_len = Self::payload_len_for_format(header.packet_format);
        if packet.len() != expected_len {
            return Err(InvalidPacketLengthError::new(format!(
                "Received packet length {} is not equal to expected {}",
                packet.len(),
                expected_len
            )));
        }

        let item_len = LobbyInfoData::packet_len_for_format(header.packet_format);
        let lobby_players = packet[1..]
            .chunks_exact(item_len)
            .take(usize::from(num_players))
            .map(|chunk| LobbyInfoData::parse(chunk, header.packet_format))
            .collect::<Result<Vec<_>, _>>()?;

        Ok(Self {
            header,
            num_players,
            lobby_players,
        })
    }

    pub fn from_values(
        header: PacketHeader,
        num_players: u8,
        lobby_players: Vec<LobbyInfoData>,
    ) -> Self {
        Self {
            header,
            num_players,
            lobby_players,
        }
    }

    pub fn to_bytes(&self) -> Vec<u8> {
        let item_len = LobbyInfoData::packet_len_for_format(self.header.packet_format);
        let mut bytes = Vec::with_capacity(Self::payload_len_for_format(self.header.packet_format));
        bytes.extend_from_slice(&self.header.to_bytes());
        bytes.push(self.num_players);

        for player in self.lobby_players.iter().take(Self::MAX_PLAYERS) {
            bytes.extend_from_slice(&player.to_bytes());
        }

        let remaining = Self::MAX_PLAYERS.saturating_sub(self.lobby_players.len());
        if remaining > 0 {
            bytes.resize(bytes.len() + (remaining * item_len), 0);
        }

        bytes
    }
}

impl Serialize for PacketLobbyInfoData {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let mut map = serializer.serialize_map(Some(2))?;
        map.serialize_entry("num-players", &self.num_players)?;
        map.serialize_entry("lobby-players", &self.lobby_players)?;
        map.end()
    }
}
