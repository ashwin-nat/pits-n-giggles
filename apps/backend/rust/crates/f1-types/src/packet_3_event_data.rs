use crate::PacketHeader;
use crate::errors::PacketParsingError;
use serde::Serialize;
use serde::ser::{SerializeMap, Serializer};
use std::fmt;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum EventPacketType {
    SessionStarted,
    SessionEnded,
    FastestLap,
    Retirement,
    DrsEnabled,
    DrsDisabled,
    TeamMateInPits,
    ChequeredFlag,
    RaceWinner,
    PenaltyIssued,
    SpeedTrapTriggered,
    StartLights,
    LightsOut,
    DriveThroughServed,
    StopGoServed,
    Flashback,
    ButtonStatus,
    RedFlag,
    Overtake,
    SafetyCar,
    Collision,
}

impl EventPacketType {
    pub fn from_code(code: &str) -> Option<Self> {
        match code {
            "SSTA" => Some(Self::SessionStarted),
            "SEND" => Some(Self::SessionEnded),
            "FTLP" => Some(Self::FastestLap),
            "RTMT" => Some(Self::Retirement),
            "DRSE" => Some(Self::DrsEnabled),
            "DRSD" => Some(Self::DrsDisabled),
            "TMPT" => Some(Self::TeamMateInPits),
            "CHQF" => Some(Self::ChequeredFlag),
            "RCWN" => Some(Self::RaceWinner),
            "PENA" => Some(Self::PenaltyIssued),
            "SPTP" => Some(Self::SpeedTrapTriggered),
            "STLG" => Some(Self::StartLights),
            "LGOT" => Some(Self::LightsOut),
            "DTSV" => Some(Self::DriveThroughServed),
            "SGSV" => Some(Self::StopGoServed),
            "FLBK" => Some(Self::Flashback),
            "BUTN" => Some(Self::ButtonStatus),
            "RDFL" => Some(Self::RedFlag),
            "OVTK" => Some(Self::Overtake),
            "SCAR" => Some(Self::SafetyCar),
            "COLL" => Some(Self::Collision),
            _ => None,
        }
    }

    pub fn as_code(self) -> &'static str {
        match self {
            Self::SessionStarted => "SSTA",
            Self::SessionEnded => "SEND",
            Self::FastestLap => "FTLP",
            Self::Retirement => "RTMT",
            Self::DrsEnabled => "DRSE",
            Self::DrsDisabled => "DRSD",
            Self::TeamMateInPits => "TMPT",
            Self::ChequeredFlag => "CHQF",
            Self::RaceWinner => "RCWN",
            Self::PenaltyIssued => "PENA",
            Self::SpeedTrapTriggered => "SPTP",
            Self::StartLights => "STLG",
            Self::LightsOut => "LGOT",
            Self::DriveThroughServed => "DTSV",
            Self::StopGoServed => "SGSV",
            Self::Flashback => "FLBK",
            Self::ButtonStatus => "BUTN",
            Self::RedFlag => "RDFL",
            Self::Overtake => "OVTK",
            Self::SafetyCar => "SCAR",
            Self::Collision => "COLL",
        }
    }
}

#[derive(Clone, Debug, PartialEq)]
pub enum EventDetails {
    FastestLap {
        vehicle_idx: u8,
        lap_time: f32,
    },
    Retirement {
        vehicle_idx: u8,
        reason: Option<u8>,
    },
    TeamMateInPits {
        vehicle_idx: u8,
    },
    RaceWinner {
        vehicle_idx: u8,
    },
    Penalty {
        penalty_type: u8,
        infringement_type: u8,
        vehicle_idx: u8,
        other_vehicle_idx: u8,
        time: u8,
        lap_num: u8,
        places_gained: u8,
    },
    SpeedTrap {
        vehicle_idx: u8,
        speed: f32,
        is_overall_fastest_in_session: bool,
        is_driver_fastest_in_session: bool,
        fastest_vehicle_idx_in_session: u8,
        fastest_speed_in_session: f32,
    },
    StartLights {
        num_lights: u8,
    },
    DriveThroughServed {
        vehicle_idx: u8,
    },
    StopGoServed {
        vehicle_idx: u8,
        stop_time: f32,
    },
    Flashback {
        frame_identifier: u32,
        session_time: f32,
    },
    Buttons {
        button_status: u32,
    },
    Overtake {
        overtaking_vehicle_idx: u8,
        being_overtaken_vehicle_idx: u8,
    },
    SafetyCar {
        safety_car_type: u8,
        event_type: u8,
    },
    Collision {
        vehicle_1_index: u8,
        vehicle_2_index: u8,
    },
}

impl EventDetails {
    pub fn parse(event_type: EventPacketType, packet_format: u16, data: &[u8]) -> Option<Self> {
        Some(match event_type {
            EventPacketType::FastestLap => Self::FastestLap {
                vehicle_idx: data[0],
                lap_time: f32::from_le_bytes(data[1..5].try_into().expect("fixed slice length")),
            },
            EventPacketType::Retirement => Self::Retirement {
                vehicle_idx: data[0],
                reason: if packet_format >= 2025 {
                    Some(data[1])
                } else {
                    None
                },
            },
            EventPacketType::TeamMateInPits => Self::TeamMateInPits {
                vehicle_idx: data[0],
            },
            EventPacketType::RaceWinner => Self::RaceWinner {
                vehicle_idx: data[0],
            },
            EventPacketType::PenaltyIssued => Self::Penalty {
                penalty_type: data[0],
                infringement_type: data[1],
                vehicle_idx: data[2],
                other_vehicle_idx: data[3],
                time: data[4],
                lap_num: data[5],
                places_gained: data[6],
            },
            EventPacketType::SpeedTrapTriggered => Self::SpeedTrap {
                vehicle_idx: data[0],
                speed: f32::from_le_bytes(data[1..5].try_into().expect("fixed slice length")),
                is_overall_fastest_in_session: data[5] != 0,
                is_driver_fastest_in_session: data[6] != 0,
                fastest_vehicle_idx_in_session: data[7],
                fastest_speed_in_session: f32::from_le_bytes(
                    data[8..12].try_into().expect("fixed slice length"),
                ),
            },
            EventPacketType::StartLights => Self::StartLights {
                num_lights: data[0],
            },
            EventPacketType::DriveThroughServed => Self::DriveThroughServed {
                vehicle_idx: data[0],
            },
            EventPacketType::StopGoServed => Self::StopGoServed {
                vehicle_idx: data[0],
                stop_time: if packet_format > 2025 {
                    f32::from_le_bytes(data[1..5].try_into().expect("fixed slice length"))
                } else {
                    0.0
                },
            },
            EventPacketType::Flashback => Self::Flashback {
                frame_identifier: u32::from_le_bytes(
                    data[0..4].try_into().expect("fixed slice length"),
                ),
                session_time: f32::from_le_bytes(
                    data[4..8].try_into().expect("fixed slice length"),
                ),
            },
            EventPacketType::ButtonStatus => Self::Buttons {
                button_status: u32::from_le_bytes(
                    data[0..4].try_into().expect("fixed slice length"),
                ),
            },
            EventPacketType::Overtake => Self::Overtake {
                overtaking_vehicle_idx: data[0],
                being_overtaken_vehicle_idx: data[1],
            },
            EventPacketType::SafetyCar => Self::SafetyCar {
                safety_car_type: data[0],
                event_type: data[1],
            },
            EventPacketType::Collision => Self::Collision {
                vehicle_1_index: data[0],
                vehicle_2_index: data[1],
            },
            EventPacketType::SessionStarted
            | EventPacketType::SessionEnded
            | EventPacketType::DrsEnabled
            | EventPacketType::DrsDisabled
            | EventPacketType::ChequeredFlag
            | EventPacketType::LightsOut
            | EventPacketType::RedFlag => return None,
        })
    }

    pub fn to_bytes(&self, packet_format: u16) -> Vec<u8> {
        match self {
            Self::FastestLap {
                vehicle_idx,
                lap_time,
            } => {
                let mut bytes = Vec::with_capacity(5);
                bytes.push(*vehicle_idx);
                bytes.extend_from_slice(&lap_time.to_le_bytes());
                bytes
            }
            Self::Retirement {
                vehicle_idx,
                reason,
            } => {
                let mut bytes = vec![*vehicle_idx];
                if packet_format >= 2025 {
                    bytes.push(reason.unwrap_or(0));
                }
                bytes
            }
            Self::TeamMateInPits { vehicle_idx }
            | Self::RaceWinner { vehicle_idx }
            | Self::DriveThroughServed { vehicle_idx } => vec![*vehicle_idx],
            Self::Penalty {
                penalty_type,
                infringement_type,
                vehicle_idx,
                other_vehicle_idx,
                time,
                lap_num,
                places_gained,
            } => vec![
                *penalty_type,
                *infringement_type,
                *vehicle_idx,
                *other_vehicle_idx,
                *time,
                *lap_num,
                *places_gained,
            ],
            Self::SpeedTrap {
                vehicle_idx,
                speed,
                is_overall_fastest_in_session,
                is_driver_fastest_in_session,
                fastest_vehicle_idx_in_session,
                fastest_speed_in_session,
            } => {
                let mut bytes = vec![*vehicle_idx];
                bytes.extend_from_slice(&speed.to_le_bytes());
                bytes.push(*is_overall_fastest_in_session as u8);
                bytes.push(*is_driver_fastest_in_session as u8);
                bytes.push(*fastest_vehicle_idx_in_session);
                bytes.extend_from_slice(&fastest_speed_in_session.to_le_bytes());
                bytes
            }
            Self::StartLights { num_lights } => vec![*num_lights],
            Self::StopGoServed {
                vehicle_idx,
                stop_time,
            } => {
                let mut bytes = vec![*vehicle_idx];
                if packet_format > 2025 {
                    bytes.extend_from_slice(&stop_time.to_le_bytes());
                }
                bytes
            }
            Self::Flashback {
                frame_identifier,
                session_time,
            } => {
                let mut bytes = Vec::with_capacity(8);
                bytes.extend_from_slice(&frame_identifier.to_le_bytes());
                bytes.extend_from_slice(&session_time.to_le_bytes());
                bytes
            }
            Self::Buttons { button_status } => button_status.to_le_bytes().to_vec(),
            Self::Overtake {
                overtaking_vehicle_idx,
                being_overtaken_vehicle_idx,
            } => vec![*overtaking_vehicle_idx, *being_overtaken_vehicle_idx],
            Self::SafetyCar {
                safety_car_type,
                event_type,
            } => vec![*safety_car_type, *event_type],
            Self::Collision {
                vehicle_1_index,
                vehicle_2_index,
            } => vec![*vehicle_1_index, *vehicle_2_index],
        }
    }
}

impl Serialize for EventDetails {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let mut map = serializer.serialize_map(None)?;
        match self {
            Self::FastestLap {
                vehicle_idx,
                lap_time,
            } => {
                map.serialize_entry("vehicle-idx", vehicle_idx)?;
                map.serialize_entry("lap-time", lap_time)?;
            }
            Self::Retirement { vehicle_idx, .. }
            | Self::TeamMateInPits { vehicle_idx }
            | Self::RaceWinner { vehicle_idx }
            | Self::DriveThroughServed { vehicle_idx } => {
                map.serialize_entry("vehicle-idx", vehicle_idx)?;
            }
            Self::Penalty {
                penalty_type,
                infringement_type,
                vehicle_idx,
                other_vehicle_idx,
                time,
                lap_num,
                places_gained,
            } => {
                map.serialize_entry("penalty-type", penalty_type)?;
                map.serialize_entry("infringement-type", infringement_type)?;
                map.serialize_entry("vehicle-idx", vehicle_idx)?;
                map.serialize_entry("other-vehicle-idx", other_vehicle_idx)?;
                map.serialize_entry("time", time)?;
                map.serialize_entry("lap-num", lap_num)?;
                map.serialize_entry("places-gained", places_gained)?;
            }
            Self::SpeedTrap {
                vehicle_idx,
                speed,
                is_overall_fastest_in_session,
                is_driver_fastest_in_session,
                fastest_vehicle_idx_in_session,
                fastest_speed_in_session,
            } => {
                map.serialize_entry("vehicle-idx", vehicle_idx)?;
                map.serialize_entry("speed", speed)?;
                map.serialize_entry(
                    "is-overall-fastest-in-session",
                    is_overall_fastest_in_session,
                )?;
                map.serialize_entry("is-driver-fastest-in-session", is_driver_fastest_in_session)?;
                map.serialize_entry(
                    "fastest-vehicle-idx-in-session",
                    fastest_vehicle_idx_in_session,
                )?;
                map.serialize_entry("fastest-speed-in-session", fastest_speed_in_session)?;
            }
            Self::StartLights { num_lights } => {
                map.serialize_entry("num-lights", num_lights)?;
            }
            Self::StopGoServed {
                vehicle_idx,
                stop_time,
            } => {
                map.serialize_entry("vehicle-idx", vehicle_idx)?;
                map.serialize_entry("stop-time", stop_time)?;
            }
            Self::Flashback {
                frame_identifier,
                session_time,
            } => {
                map.serialize_entry("flashback-frame-identifier", frame_identifier)?;
                map.serialize_entry("flashback-session-time", session_time)?;
            }
            Self::Buttons { button_status } => {
                map.serialize_entry("button-status", button_status)?;
            }
            Self::Overtake {
                overtaking_vehicle_idx,
                being_overtaken_vehicle_idx,
            } => {
                map.serialize_entry("overtaking-vehicle-idx", overtaking_vehicle_idx)?;
                map.serialize_entry("being-overtaken-vehicle-idx", being_overtaken_vehicle_idx)?;
            }
            Self::SafetyCar {
                safety_car_type,
                event_type,
            } => {
                map.serialize_entry("safety-car-type", safety_car_type)?;
                map.serialize_entry("safety-car-event-type", event_type)?;
            }
            Self::Collision {
                vehicle_1_index,
                vehicle_2_index,
            } => {
                map.serialize_entry("vehicle-1-index", vehicle_1_index)?;
                map.serialize_entry("vehicle-2-index", vehicle_2_index)?;
            }
        }
        map.end()
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct PacketEventData {
    pub header: PacketHeader,
    pub event_string_code: String,
    pub event_code: EventPacketType,
    pub event_details: Option<EventDetails>,
}

impl PacketEventData {
    pub const PACKET_LEN: usize = 16;

    pub fn parse(header: PacketHeader, packet: &[u8]) -> Result<Self, PacketParsingError> {
        if packet.len() != Self::PACKET_LEN {
            return Err(PacketParsingError::new(format!(
                "Invalid packet length. Received packet length {} is not equal to expected {}",
                packet.len(),
                Self::PACKET_LEN
            )));
        }

        let event_string_code = String::from_utf8_lossy(&packet[..4]).to_string();
        let event_code = EventPacketType::from_code(&event_string_code).ok_or_else(|| {
            PacketParsingError::new(format!("Unsupported Event Type {}", event_string_code))
        })?;
        let event_details = EventDetails::parse(event_code, header.packet_format, &packet[4..]);

        Ok(Self {
            header,
            event_string_code,
            event_code,
            event_details,
        })
    }

    pub fn from_values(
        header: PacketHeader,
        event_code: EventPacketType,
        event_details: Option<EventDetails>,
    ) -> Self {
        Self {
            header,
            event_string_code: event_code.as_code().to_string(),
            event_code,
            event_details,
        }
    }

    pub fn to_bytes(&self) -> Vec<u8> {
        let mut bytes = Vec::with_capacity(PacketHeader::PACKET_LEN + Self::PACKET_LEN);
        bytes.extend_from_slice(&self.header.to_bytes());
        bytes.extend_from_slice(self.event_string_code.as_bytes());
        if let Some(details) = &self.event_details {
            bytes.extend_from_slice(&details.to_bytes(self.header.packet_format));
        }
        bytes.resize(PacketHeader::PACKET_LEN + Self::PACKET_LEN, 0);
        bytes
    }
}

impl fmt::Display for PacketEventData {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "PacketEventData(Event String Code: {})",
            self.event_string_code
        )
    }
}

impl Serialize for PacketEventData {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let mut map = serializer.serialize_map(Some(2))?;
        map.serialize_entry("event-string-code", &self.event_string_code)?;
        map.serialize_entry("event-details", &self.event_details)?;
        map.end()
    }
}
