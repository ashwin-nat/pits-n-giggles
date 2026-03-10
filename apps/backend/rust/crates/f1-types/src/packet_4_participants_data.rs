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
pub struct LiveryColour {
    pub red: u8,
    pub green: u8,
    pub blue: u8,
}

impl LiveryColour {
    pub const PACKET_LEN: usize = 3;

    pub fn from_values(red: u8, green: u8, blue: u8) -> Self {
        Self { red, green, blue }
    }

    pub fn parse(data: &[u8]) -> Result<Self, InvalidPacketLengthError> {
        if data.len() != Self::PACKET_LEN {
            return Err(InvalidPacketLengthError::new(format!(
                "Received packet length {} expected {}",
                data.len(),
                Self::PACKET_LEN
            )));
        }
        Ok(Self {
            red: data[0],
            green: data[1],
            blue: data[2],
        })
    }

    pub fn to_bytes(&self) -> [u8; Self::PACKET_LEN] {
        [self.red, self.green, self.blue]
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct ParticipantData {
    pub packet_format: u16,
    pub ai_controlled: bool,
    pub driver_id: u8,
    pub network_id: u8,
    pub team_id_raw: u8,
    pub my_team: bool,
    pub race_number: u8,
    pub nationality_raw: u8,
    pub name: String,
    pub your_telemetry_raw: u8,
    pub show_online_names: bool,
    pub platform_raw: u8,
    pub tech_level: u16,
    pub num_colours: u8,
    pub livery_colours: Vec<LiveryColour>,
}

impl ParticipantData {
    pub const PACKET_LEN_23: usize = 58;
    pub const PACKET_LEN_24: usize = 60;
    pub const PACKET_LEN_25_BASE: usize = 45;
    pub const MAX_LIVERY_COLOURS: usize = 4;
    pub const PACKET_LEN_25: usize =
        Self::PACKET_LEN_25_BASE + (LiveryColour::PACKET_LEN * Self::MAX_LIVERY_COLOURS);

    #[allow(clippy::too_many_arguments)]
    pub fn from_values(
        packet_format: u16,
        ai_controlled: bool,
        driver_id: u8,
        network_id: u8,
        team_id_raw: u8,
        my_team: bool,
        race_number: u8,
        nationality_raw: u8,
        name: String,
        your_telemetry_raw: u8,
        show_online_names: bool,
        platform_raw: u8,
        tech_level: u16,
        num_colours: u8,
        livery_colours: Vec<LiveryColour>,
    ) -> Self {
        Self {
            packet_format,
            ai_controlled,
            driver_id,
            network_id,
            team_id_raw,
            my_team,
            race_number,
            nationality_raw,
            name,
            your_telemetry_raw,
            show_online_names,
            platform_raw,
            tech_level: if packet_format >= 2024 { tech_level } else { 0 },
            num_colours: if packet_format >= 2025 {
                num_colours
            } else {
                0
            },
            livery_colours: if packet_format >= 2025 {
                livery_colours
                    .into_iter()
                    .take(num_colours as usize)
                    .collect()
            } else {
                Vec::new()
            },
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
                "Received packet length {} expected {}",
                data.len(),
                expected_len
            )));
        }

        let name_len = if packet_format >= 2025 { 32 } else { 48 };
        let mut offset = 0usize;
        let read_u8 = |data: &[u8], offset: &mut usize| {
            let value = data[*offset];
            *offset += 1;
            value
        };
        let read_u16 = |data: &[u8], offset: &mut usize| {
            let value = u16::from_le_bytes(
                data[*offset..*offset + 2]
                    .try_into()
                    .expect("fixed slice length"),
            );
            *offset += 2;
            value
        };

        let ai_controlled = read_u8(data, &mut offset) != 0;
        let driver_id = read_u8(data, &mut offset);
        let network_id = read_u8(data, &mut offset);
        let team_id_raw = read_u8(data, &mut offset);
        let my_team = read_u8(data, &mut offset) != 0;
        let race_number = read_u8(data, &mut offset);
        let nationality_raw = read_u8(data, &mut offset);
        let name = String::from_utf8_lossy(&data[offset..offset + name_len])
            .trim_end_matches('\0')
            .to_string();
        offset += name_len;
        let your_telemetry_raw = read_u8(data, &mut offset);
        let show_online_names = read_u8(data, &mut offset) != 0;

        let (tech_level, platform_raw, num_colours, livery_colours) = if packet_format == 2023 {
            (0, read_u8(data, &mut offset), 0, Vec::new())
        } else if packet_format == 2024 {
            let tech_level = read_u16(data, &mut offset);
            (tech_level, read_u8(data, &mut offset), 0, Vec::new())
        } else {
            let tech_level = read_u16(data, &mut offset);
            let platform_raw = read_u8(data, &mut offset);
            let num_colours = read_u8(data, &mut offset);
            let mut colours = Vec::with_capacity(num_colours as usize);
            for index in 0..Self::MAX_LIVERY_COLOURS {
                let start = offset + (index * LiveryColour::PACKET_LEN);
                let end = start + LiveryColour::PACKET_LEN;
                if index < num_colours as usize {
                    colours.push(LiveryColour::parse(&data[start..end])?);
                }
            }
            (tech_level, platform_raw, num_colours, colours)
        };

        Ok(Self::from_values(
            packet_format,
            ai_controlled,
            driver_id,
            network_id,
            team_id_raw,
            my_team,
            race_number,
            nationality_raw,
            name,
            your_telemetry_raw,
            show_online_names,
            platform_raw,
            tech_level,
            num_colours,
            livery_colours,
        ))
    }

    pub fn to_bytes(&self) -> Vec<u8> {
        let expected_len = Self::packet_len_for_format(self.packet_format);
        let mut bytes = Vec::with_capacity(expected_len);
        bytes.push(self.ai_controlled as u8);
        bytes.push(self.driver_id);
        bytes.push(self.network_id);
        bytes.push(self.team_id_raw);
        bytes.push(self.my_team as u8);
        bytes.push(self.race_number);
        bytes.push(self.nationality_raw);

        let name_len = if self.packet_format >= 2025 { 32 } else { 48 };
        let mut name_bytes = vec![0u8; name_len];
        let encoded = self.name.as_bytes();
        let copy_len = encoded.len().min(name_len);
        name_bytes[..copy_len].copy_from_slice(&encoded[..copy_len]);
        bytes.extend_from_slice(&name_bytes);

        bytes.push(self.your_telemetry_raw);
        bytes.push(self.show_online_names as u8);

        if self.packet_format >= 2024 {
            bytes.extend_from_slice(&self.tech_level.to_le_bytes());
        }

        bytes.push(self.platform_raw);

        if self.packet_format >= 2025 {
            bytes.push(self.num_colours);
            for colour in self.livery_colours.iter().take(Self::MAX_LIVERY_COLOURS) {
                bytes.extend_from_slice(&colour.to_bytes());
            }
            let remaining = Self::MAX_LIVERY_COLOURS.saturating_sub(self.livery_colours.len());
            bytes.resize(bytes.len() + (remaining * LiveryColour::PACKET_LEN), 0);
        }

        bytes
    }
}

impl Serialize for ParticipantData {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let mut map = serializer.serialize_map(Some(12))?;
        map.serialize_entry("ai-controlled", &self.ai_controlled)?;
        map.serialize_entry("driver-id", &self.driver_id)?;
        map.serialize_entry("network-id", &self.network_id)?;
        map.serialize_entry("team-id", &team_label(self.packet_format, self.team_id_raw))?;
        map.serialize_entry("my-team", &self.my_team)?;
        map.serialize_entry("race-number", &self.race_number)?;
        map.serialize_entry("nationality", &nationality_label(self.nationality_raw))?;
        map.serialize_entry("name", &self.name)?;
        map.serialize_entry(
            "telemetry-setting",
            &telemetry_setting_label(self.your_telemetry_raw),
        )?;
        map.serialize_entry("show-online-names", &self.show_online_names)?;
        map.serialize_entry("tech-level", &self.tech_level)?;
        map.serialize_entry("platform", &platform_label(self.platform_raw))?;
        map.end()
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct PacketParticipantsData {
    pub header: PacketHeader,
    pub num_active_cars: u8,
    pub participants: Vec<ParticipantData>,
}

impl PacketParticipantsData {
    pub const MAX_PARTICIPANTS: usize = 22;

    pub fn payload_len_for_format(packet_format: u16) -> usize {
        1 + (Self::MAX_PARTICIPANTS * ParticipantData::packet_len_for_format(packet_format))
    }

    pub fn parse(header: PacketHeader, packet: &[u8]) -> Result<Self, InvalidPacketLengthError> {
        let expected_len = Self::payload_len_for_format(header.packet_format);
        if packet.len() != expected_len {
            return Err(InvalidPacketLengthError::new(format!(
                "Received packet length {} is not equal to expected {}",
                packet.len(),
                expected_len
            )));
        }

        let participant_len = ParticipantData::packet_len_for_format(header.packet_format);
        let participants = packet[1..]
            .chunks_exact(participant_len)
            .map(|chunk| ParticipantData::parse(chunk, header.packet_format))
            .collect::<Result<Vec<_>, _>>()?;

        Ok(Self {
            header,
            num_active_cars: packet[0],
            participants,
        })
    }

    pub fn from_values(
        header: PacketHeader,
        num_active_cars: u8,
        participants: Vec<ParticipantData>,
    ) -> Self {
        Self {
            header,
            num_active_cars,
            participants,
        }
    }

    pub fn to_bytes(&self) -> Vec<u8> {
        let participant_len = ParticipantData::packet_len_for_format(self.header.packet_format);
        let mut bytes = Vec::with_capacity(
            PacketHeader::PACKET_LEN + 1 + (Self::MAX_PARTICIPANTS * participant_len),
        );
        bytes.extend_from_slice(&self.header.to_bytes());
        bytes.push(self.num_active_cars);
        for participant in self.participants.iter().take(Self::MAX_PARTICIPANTS) {
            bytes.extend_from_slice(&participant.to_bytes());
        }
        let remaining = Self::MAX_PARTICIPANTS.saturating_sub(self.participants.len());
        bytes.resize(bytes.len() + (remaining * participant_len), 0);
        bytes
    }
}

impl Serialize for PacketParticipantsData {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let mut map = serializer.serialize_map(Some(2))?;
        map.serialize_entry("num-active-cars", &self.num_active_cars)?;
        map.serialize_entry("participants", &self.participants)?;
        map.end()
    }
}

impl fmt::Display for PacketParticipantsData {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "PacketParticipantsData(Num Active Cars: {})",
            self.num_active_cars
        )
    }
}
