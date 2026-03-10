use serde::Serialize;
use serde::ser::{SerializeMap, Serializer};
use std::fmt;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize)]
#[repr(u8)]
pub enum F1PacketType {
    Motion = 0,
    Session = 1,
    LapData = 2,
    Event = 3,
    Participants = 4,
    CarSetups = 5,
    CarTelemetry = 6,
    CarStatus = 7,
    FinalClassification = 8,
    LobbyInfo = 9,
    CarDamage = 10,
    SessionHistory = 11,
    TyreSets = 12,
    MotionEx = 13,
    TimeTrial = 14,
    LapPositions = 15,
}

impl F1PacketType {
    pub fn is_valid(value: u8) -> bool {
        Self::try_from(value).is_ok()
    }

    fn as_name(self) -> &'static str {
        match self {
            Self::Motion => "MOTION",
            Self::Session => "SESSION",
            Self::LapData => "LAP_DATA",
            Self::Event => "EVENT",
            Self::Participants => "PARTICIPANTS",
            Self::CarSetups => "CAR_SETUPS",
            Self::CarTelemetry => "CAR_TELEMETRY",
            Self::CarStatus => "CAR_STATUS",
            Self::FinalClassification => "FINAL_CLASSIFICATION",
            Self::LobbyInfo => "LOBBY_INFO",
            Self::CarDamage => "CAR_DAMAGE",
            Self::SessionHistory => "SESSION_HISTORY",
            Self::TyreSets => "TYRE_SETS",
            Self::MotionEx => "MOTION_EX",
            Self::TimeTrial => "TIME_TRIAL",
            Self::LapPositions => "LAP_POSITIONS",
        }
    }
}

impl fmt::Display for F1PacketType {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(self.as_name())
    }
}

impl TryFrom<u8> for F1PacketType {
    type Error = u8;

    fn try_from(value: u8) -> Result<Self, Self::Error> {
        match value {
            0 => Ok(Self::Motion),
            1 => Ok(Self::Session),
            2 => Ok(Self::LapData),
            3 => Ok(Self::Event),
            4 => Ok(Self::Participants),
            5 => Ok(Self::CarSetups),
            6 => Ok(Self::CarTelemetry),
            7 => Ok(Self::CarStatus),
            8 => Ok(Self::FinalClassification),
            9 => Ok(Self::LobbyInfo),
            10 => Ok(Self::CarDamage),
            11 => Ok(Self::SessionHistory),
            12 => Ok(Self::TyreSets),
            13 => Ok(Self::MotionEx),
            14 => Ok(Self::TimeTrial),
            15 => Ok(Self::LapPositions),
            _ => Err(value),
        }
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum PacketHeaderError {
    InvalidLength { expected: usize, actual: usize },
}

impl fmt::Display for PacketHeaderError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::InvalidLength { expected, actual } => {
                write!(
                    f,
                    "invalid packet header length: expected {expected} bytes, got {actual}"
                )
            }
        }
    }
}

impl std::error::Error for PacketHeaderError {}

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct PacketHeader {
    pub packet_format: u16,
    pub game_year: u8,
    pub game_major_version: u8,
    pub game_minor_version: u8,
    pub packet_version: u8,
    pub packet_id_raw: u8,
    pub packet_id: Option<F1PacketType>,
    pub session_uid: u64,
    pub session_time: f32,
    pub frame_identifier: u32,
    pub overall_frame_identifier: u32,
    pub player_car_index: u8,
    pub secondary_player_car_index: u8,
}

impl PacketHeader {
    pub const PACKET_LEN: usize = 29;

    pub fn parse(data: &[u8]) -> Result<Self, PacketHeaderError> {
        if data.len() != Self::PACKET_LEN {
            return Err(PacketHeaderError::InvalidLength {
                expected: Self::PACKET_LEN,
                actual: data.len(),
            });
        }

        let packet_format = u16::from_le_bytes([data[0], data[1]]);
        let game_year = data[2];
        let game_major_version = data[3];
        let game_minor_version = data[4];
        let packet_version = data[5];
        let packet_id_raw = data[6];
        let session_uid = u64::from_le_bytes(data[7..15].try_into().expect("fixed slice length"));
        let session_time = f32::from_le_bytes(data[15..19].try_into().expect("fixed slice length"));
        let frame_identifier =
            u32::from_le_bytes(data[19..23].try_into().expect("fixed slice length"));
        let overall_frame_identifier =
            u32::from_le_bytes(data[23..27].try_into().expect("fixed slice length"));
        let player_car_index = data[27];
        let secondary_player_car_index = data[28];

        Ok(Self {
            packet_format,
            game_year,
            game_major_version,
            game_minor_version,
            packet_version,
            packet_id_raw,
            packet_id: F1PacketType::try_from(packet_id_raw).ok(),
            session_uid,
            session_time,
            frame_identifier,
            overall_frame_identifier,
            player_car_index,
            secondary_player_car_index,
        })
    }

    #[allow(clippy::too_many_arguments)]
    pub fn from_values(
        packet_format: u16,
        game_year: u8,
        game_major_version: u8,
        game_minor_version: u8,
        packet_version: u8,
        packet_type: F1PacketType,
        session_uid: u64,
        session_time: f32,
        frame_identifier: u32,
        overall_frame_identifier: u32,
        player_car_index: u8,
        secondary_player_car_index: u8,
    ) -> Self {
        Self {
            packet_format,
            game_year,
            game_major_version,
            game_minor_version,
            packet_version,
            packet_id_raw: packet_type as u8,
            packet_id: Some(packet_type),
            session_uid,
            session_time,
            frame_identifier,
            overall_frame_identifier,
            player_car_index,
            secondary_player_car_index,
        }
    }

    pub fn is_supported_packet_type(&self) -> bool {
        self.packet_id.is_some()
    }

    pub fn packet_id_label(&self) -> String {
        match self.packet_id {
            Some(packet_type) => packet_type.to_string(),
            None => self.packet_id_raw.to_string(),
        }
    }

    pub fn to_bytes(&self) -> [u8; Self::PACKET_LEN] {
        let mut bytes = [0u8; Self::PACKET_LEN];
        bytes[0..2].copy_from_slice(&self.packet_format.to_le_bytes());
        bytes[2] = self.game_year;
        bytes[3] = self.game_major_version;
        bytes[4] = self.game_minor_version;
        bytes[5] = self.packet_version;
        bytes[6] = self.packet_id_raw;
        bytes[7..15].copy_from_slice(&self.session_uid.to_le_bytes());
        bytes[15..19].copy_from_slice(&self.session_time.to_le_bytes());
        bytes[19..23].copy_from_slice(&self.frame_identifier.to_le_bytes());
        bytes[23..27].copy_from_slice(&self.overall_frame_identifier.to_le_bytes());
        bytes[27] = self.player_car_index;
        bytes[28] = self.secondary_player_car_index;
        bytes
    }
}

impl TryFrom<&[u8]> for PacketHeader {
    type Error = PacketHeaderError;

    fn try_from(value: &[u8]) -> Result<Self, Self::Error> {
        Self::parse(value)
    }
}

impl fmt::Display for PacketHeader {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "PacketHeader(Format: {}, Year: {}, Major Version: {}, Minor Version: {}, Packet Version: {}, Packet ID: {}, Session UID: {}, Session Time: {}, Frame Identifier: {}, Overall Frame Identifier: {}, Player Car Index: {}, Secondary Player Car Index: {})",
            self.packet_format,
            self.game_year,
            self.game_major_version,
            self.game_minor_version,
            self.packet_version,
            self.packet_id_label(),
            self.session_uid,
            self.session_time,
            self.frame_identifier,
            self.overall_frame_identifier,
            self.player_car_index,
            self.secondary_player_car_index
        )
    }
}

impl Serialize for PacketHeader {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let mut map = serializer.serialize_map(Some(12))?;
        map.serialize_entry("packet-format", &self.packet_format)?;
        map.serialize_entry("game-year", &self.game_year)?;
        map.serialize_entry("game-major-version", &self.game_major_version)?;
        map.serialize_entry("game-minor-version", &self.game_minor_version)?;
        map.serialize_entry("packet-version", &self.packet_version)?;
        map.serialize_entry("packet-id", &self.packet_id_label())?;
        map.serialize_entry("session-uid", &self.session_uid)?;
        map.serialize_entry("session-time", &self.session_time)?;
        map.serialize_entry("frame-identifier", &self.frame_identifier)?;
        map.serialize_entry("overall-frame-identifier", &self.overall_frame_identifier)?;
        map.serialize_entry("player-car-index", &self.player_car_index)?;
        map.serialize_entry(
            "secondary-player-car-index",
            &self.secondary_player_car_index,
        )?;
        map.end()
    }
}
