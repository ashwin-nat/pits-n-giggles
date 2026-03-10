use crate::errors::{InvalidPacketLengthError, PacketParsingError};
use crate::{
    F1PacketType, PacketCarDamageData, PacketCarSetupData, PacketCarStatusData,
    PacketCarTelemetryData, PacketEventData, PacketFinalClassificationData, PacketHeader,
    PacketHeaderError, PacketLapData, PacketLapPositionsData, PacketLobbyInfoData,
    PacketMotionData, PacketMotionExData, PacketParticipantsData, PacketSessionData,
    PacketSessionHistoryData, PacketTimeTrialData, PacketTyreSetsData, SessionDataError,
    SessionHistoryError,
};
use serde::Serialize;
use std::fmt;

#[derive(Clone, Debug, PartialEq)]
pub enum F1Packet {
    Motion(PacketMotionData),
    Session(PacketSessionData),
    LapData(PacketLapData),
    Event(PacketEventData),
    Participants(PacketParticipantsData),
    CarSetups(PacketCarSetupData),
    CarTelemetry(PacketCarTelemetryData),
    CarStatus(PacketCarStatusData),
    FinalClassification(PacketFinalClassificationData),
    LobbyInfo(PacketLobbyInfoData),
    CarDamage(PacketCarDamageData),
    SessionHistory(PacketSessionHistoryData),
    TyreSets(PacketTyreSetsData),
    MotionEx(PacketMotionExData),
    TimeTrial(PacketTimeTrialData),
    LapPositions(PacketLapPositionsData),
}

impl F1Packet {
    pub fn parse(data: &[u8]) -> Result<Self, F1PacketParseError> {
        if data.len() < PacketHeader::PACKET_LEN {
            return Err(F1PacketParseError::Header(
                PacketHeaderError::InvalidLength {
                    expected: PacketHeader::PACKET_LEN,
                    actual: data.len(),
                },
            ));
        }

        let header = PacketHeader::parse(&data[..PacketHeader::PACKET_LEN])?;
        Self::parse_payload(header, &data[PacketHeader::PACKET_LEN..])
    }

    pub fn parse_payload(header: PacketHeader, payload: &[u8]) -> Result<Self, F1PacketParseError> {
        match header.packet_id {
            Some(F1PacketType::Motion) => {
                Ok(Self::Motion(PacketMotionData::parse(header, payload)?))
            }
            Some(F1PacketType::Session) => {
                Ok(Self::Session(PacketSessionData::parse(header, payload)?))
            }
            Some(F1PacketType::LapData) => {
                Ok(Self::LapData(PacketLapData::parse(header, payload)?))
            }
            Some(F1PacketType::Event) => Ok(Self::Event(PacketEventData::parse(header, payload)?)),
            Some(F1PacketType::Participants) => Ok(Self::Participants(
                PacketParticipantsData::parse(header, payload)?,
            )),
            Some(F1PacketType::CarSetups) => {
                Ok(Self::CarSetups(PacketCarSetupData::parse(header, payload)?))
            }
            Some(F1PacketType::CarTelemetry) => Ok(Self::CarTelemetry(
                PacketCarTelemetryData::parse(header, payload)?,
            )),
            Some(F1PacketType::CarStatus) => Ok(Self::CarStatus(PacketCarStatusData::parse(
                header, payload,
            )?)),
            Some(F1PacketType::FinalClassification) => Ok(Self::FinalClassification(
                PacketFinalClassificationData::parse(header, payload)?,
            )),
            Some(F1PacketType::LobbyInfo) => Ok(Self::LobbyInfo(PacketLobbyInfoData::parse(
                header, payload,
            )?)),
            Some(F1PacketType::CarDamage) => Ok(Self::CarDamage(PacketCarDamageData::parse(
                header, payload,
            )?)),
            Some(F1PacketType::SessionHistory) => Ok(Self::SessionHistory(
                PacketSessionHistoryData::parse(header, payload)?,
            )),
            Some(F1PacketType::TyreSets) => {
                Ok(Self::TyreSets(PacketTyreSetsData::parse(header, payload)?))
            }
            Some(F1PacketType::MotionEx) => {
                Ok(Self::MotionEx(PacketMotionExData::parse(header, payload)?))
            }
            Some(F1PacketType::TimeTrial) => Ok(Self::TimeTrial(PacketTimeTrialData::parse(
                header, payload,
            )?)),
            Some(F1PacketType::LapPositions) => Ok(Self::LapPositions(
                PacketLapPositionsData::parse(header, payload)?,
            )),
            None => Err(F1PacketParseError::UnsupportedPacketType(
                header.packet_id_raw,
            )),
        }
    }

    pub fn header(&self) -> &PacketHeader {
        match self {
            Self::Motion(packet) => &packet.header,
            Self::Session(packet) => &packet.header,
            Self::LapData(packet) => &packet.header,
            Self::Event(packet) => &packet.header,
            Self::Participants(packet) => &packet.header,
            Self::CarSetups(packet) => &packet.header,
            Self::CarTelemetry(packet) => &packet.header,
            Self::CarStatus(packet) => &packet.header,
            Self::FinalClassification(packet) => &packet.header,
            Self::LobbyInfo(packet) => &packet.header,
            Self::CarDamage(packet) => &packet.header,
            Self::SessionHistory(packet) => &packet.header,
            Self::TyreSets(packet) => &packet.header,
            Self::MotionEx(packet) => &packet.header,
            Self::TimeTrial(packet) => &packet.header,
            Self::LapPositions(packet) => &packet.header,
        }
    }

    pub fn packet_type(&self) -> F1PacketType {
        match self {
            Self::Motion(_) => F1PacketType::Motion,
            Self::Session(_) => F1PacketType::Session,
            Self::LapData(_) => F1PacketType::LapData,
            Self::Event(_) => F1PacketType::Event,
            Self::Participants(_) => F1PacketType::Participants,
            Self::CarSetups(_) => F1PacketType::CarSetups,
            Self::CarTelemetry(_) => F1PacketType::CarTelemetry,
            Self::CarStatus(_) => F1PacketType::CarStatus,
            Self::FinalClassification(_) => F1PacketType::FinalClassification,
            Self::LobbyInfo(_) => F1PacketType::LobbyInfo,
            Self::CarDamage(_) => F1PacketType::CarDamage,
            Self::SessionHistory(_) => F1PacketType::SessionHistory,
            Self::TyreSets(_) => F1PacketType::TyreSets,
            Self::MotionEx(_) => F1PacketType::MotionEx,
            Self::TimeTrial(_) => F1PacketType::TimeTrial,
            Self::LapPositions(_) => F1PacketType::LapPositions,
        }
    }

    pub fn to_bytes(&self) -> Vec<u8> {
        match self {
            Self::Motion(packet) => packet.to_bytes(),
            Self::Session(packet) => packet.to_bytes(),
            Self::LapData(packet) => packet.to_bytes(),
            Self::Event(packet) => packet.to_bytes(),
            Self::Participants(packet) => packet.to_bytes(),
            Self::CarSetups(packet) => packet.to_bytes(),
            Self::CarTelemetry(packet) => packet.to_bytes(),
            Self::CarStatus(packet) => packet.to_bytes(),
            Self::FinalClassification(packet) => packet.to_bytes(),
            Self::LobbyInfo(packet) => packet.to_bytes(),
            Self::CarDamage(packet) => packet.to_bytes(),
            Self::SessionHistory(packet) => packet.to_bytes(),
            Self::TyreSets(packet) => packet.to_bytes(),
            Self::MotionEx(packet) => packet.to_bytes(),
            Self::TimeTrial(packet) => packet.to_bytes(),
            Self::LapPositions(packet) => packet.to_bytes(),
        }
    }
}

impl Serialize for F1Packet {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        match self {
            Self::Motion(packet) => packet.serialize(serializer),
            Self::Session(packet) => packet.serialize(serializer),
            Self::LapData(packet) => packet.serialize(serializer),
            Self::Event(packet) => packet.serialize(serializer),
            Self::Participants(packet) => packet.serialize(serializer),
            Self::CarSetups(packet) => packet.serialize(serializer),
            Self::CarTelemetry(packet) => packet.serialize(serializer),
            Self::CarStatus(packet) => packet.serialize(serializer),
            Self::FinalClassification(packet) => packet.serialize(serializer),
            Self::LobbyInfo(packet) => packet.serialize(serializer),
            Self::CarDamage(packet) => packet.serialize(serializer),
            Self::SessionHistory(packet) => packet.serialize(serializer),
            Self::TyreSets(packet) => packet.serialize(serializer),
            Self::MotionEx(packet) => packet.serialize(serializer),
            Self::TimeTrial(packet) => packet.serialize(serializer),
            Self::LapPositions(packet) => packet.serialize(serializer),
        }
    }
}

#[derive(Clone, Debug, PartialEq)]
pub enum F1PacketParseError {
    Header(PacketHeaderError),
    UnsupportedPacketType(u8),
    InvalidPacketLength(InvalidPacketLengthError),
    PacketParsing(PacketParsingError),
    SessionData(SessionDataError),
    SessionHistory(SessionHistoryError),
}

impl fmt::Display for F1PacketParseError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Header(error) => write!(f, "{error}"),
            Self::UnsupportedPacketType(packet_id) => {
                write!(f, "unsupported packet type: {packet_id}")
            }
            Self::InvalidPacketLength(error) => write!(f, "{error}"),
            Self::PacketParsing(error) => write!(f, "{error}"),
            Self::SessionData(error) => write!(f, "{error}"),
            Self::SessionHistory(error) => write!(f, "{error}"),
        }
    }
}

impl std::error::Error for F1PacketParseError {}

impl From<PacketHeaderError> for F1PacketParseError {
    fn from(value: PacketHeaderError) -> Self {
        Self::Header(value)
    }
}

impl From<InvalidPacketLengthError> for F1PacketParseError {
    fn from(value: InvalidPacketLengthError) -> Self {
        Self::InvalidPacketLength(value)
    }
}

impl From<PacketParsingError> for F1PacketParseError {
    fn from(value: PacketParsingError) -> Self {
        Self::PacketParsing(value)
    }
}

impl From<SessionDataError> for F1PacketParseError {
    fn from(value: SessionDataError) -> Self {
        Self::SessionData(value)
    }
}

impl From<SessionHistoryError> for F1PacketParseError {
    fn from(value: SessionHistoryError) -> Self {
        Self::SessionHistory(value)
    }
}
