use crate::errors::{InvalidPacketLengthError, PacketCountValidationError};
use crate::{ActualTyreCompound, PacketHeader, VisualTyreCompound};
use serde::Serialize;
use serde::ser::{SerializeMap, Serializer};
use std::fmt;

fn lap_time_string(milliseconds: u32) -> String {
    let total_seconds = milliseconds / 1_000;
    let milliseconds = milliseconds % 1_000;
    let minutes = total_seconds / 60;
    let seconds = total_seconds % 60;
    format!("{minutes:02}:{seconds:02}.{milliseconds:03}")
}

fn lap_time_split_string(minutes: u8, milliseconds: u16) -> String {
    if minutes > 0 {
        let total_seconds = milliseconds / 1_000;
        let milliseconds = milliseconds % 1_000;
        format!("{minutes}:{total_seconds:02}.{milliseconds:03}")
    } else {
        let seconds = milliseconds / 1_000;
        let milliseconds = milliseconds % 1_000;
        format!("{seconds}.{milliseconds:03}")
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum SessionHistoryError {
    InvalidPacketLength(InvalidPacketLengthError),
    InvalidCount(PacketCountValidationError),
}

impl fmt::Display for SessionHistoryError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::InvalidPacketLength(error) => write!(f, "{error}"),
            Self::InvalidCount(error) => write!(f, "{error}"),
        }
    }
}

impl std::error::Error for SessionHistoryError {}

impl From<InvalidPacketLengthError> for SessionHistoryError {
    fn from(value: InvalidPacketLengthError) -> Self {
        Self::InvalidPacketLength(value)
    }
}

impl From<PacketCountValidationError> for SessionHistoryError {
    fn from(value: PacketCountValidationError) -> Self {
        Self::InvalidCount(value)
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct LapHistoryData {
    pub lap_time_in_ms: u32,
    pub sector1_time_in_ms: u16,
    pub sector1_time_minutes: u8,
    pub sector2_time_in_ms: u16,
    pub sector2_time_minutes: u8,
    pub sector3_time_in_ms: u16,
    pub sector3_time_minutes: u8,
    pub lap_valid_bit_flags: u8,
}

impl LapHistoryData {
    pub const PACKET_LEN: usize = 14;

    #[allow(clippy::too_many_arguments)]
    pub fn from_values(
        lap_time_in_ms: u32,
        sector1_time_in_ms: u16,
        sector1_time_minutes: u8,
        sector2_time_in_ms: u16,
        sector2_time_minutes: u8,
        sector3_time_in_ms: u16,
        sector3_time_minutes: u8,
        lap_valid_bit_flags: u8,
    ) -> Self {
        Self {
            lap_time_in_ms,
            sector1_time_in_ms,
            sector1_time_minutes,
            sector2_time_in_ms,
            sector2_time_minutes,
            sector3_time_in_ms,
            sector3_time_minutes,
            lap_valid_bit_flags,
        }
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
            lap_time_in_ms: u32::from_le_bytes(data[0..4].try_into().expect("fixed slice length")),
            sector1_time_in_ms: u16::from_le_bytes(
                data[4..6].try_into().expect("fixed slice length"),
            ),
            sector1_time_minutes: data[6],
            sector2_time_in_ms: u16::from_le_bytes(
                data[7..9].try_into().expect("fixed slice length"),
            ),
            sector2_time_minutes: data[9],
            sector3_time_in_ms: u16::from_le_bytes(
                data[10..12].try_into().expect("fixed slice length"),
            ),
            sector3_time_minutes: data[12],
            lap_valid_bit_flags: data[13],
        })
    }

    pub fn to_bytes(&self) -> [u8; Self::PACKET_LEN] {
        let mut bytes = [0u8; Self::PACKET_LEN];
        bytes[0..4].copy_from_slice(&self.lap_time_in_ms.to_le_bytes());
        bytes[4..6].copy_from_slice(&self.sector1_time_in_ms.to_le_bytes());
        bytes[6] = self.sector1_time_minutes;
        bytes[7..9].copy_from_slice(&self.sector2_time_in_ms.to_le_bytes());
        bytes[9] = self.sector2_time_minutes;
        bytes[10..12].copy_from_slice(&self.sector3_time_in_ms.to_le_bytes());
        bytes[12] = self.sector3_time_minutes;
        bytes[13] = self.lap_valid_bit_flags;
        bytes
    }
}

impl Serialize for LapHistoryData {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let mut map = serializer.serialize_map(Some(11))?;
        map.serialize_entry("lap-time-in-ms", &self.lap_time_in_ms)?;
        map.serialize_entry("lap-time-str", &lap_time_string(self.lap_time_in_ms))?;
        map.serialize_entry("sector-1-time-in-ms", &self.sector1_time_in_ms)?;
        map.serialize_entry("sector-1-time-minutes", &self.sector1_time_minutes)?;
        map.serialize_entry(
            "sector-1-time-str",
            &lap_time_split_string(self.sector1_time_minutes, self.sector1_time_in_ms),
        )?;
        map.serialize_entry("sector-2-time-in-ms", &self.sector2_time_in_ms)?;
        map.serialize_entry("sector-2-time-minutes", &self.sector2_time_minutes)?;
        map.serialize_entry(
            "sector-2-time-str",
            &lap_time_split_string(self.sector2_time_minutes, self.sector2_time_in_ms),
        )?;
        map.serialize_entry("sector-3-time-in-ms", &self.sector3_time_in_ms)?;
        map.serialize_entry("sector-3-time-minutes", &self.sector3_time_minutes)?;
        map.serialize_entry(
            "sector-3-time-str",
            &lap_time_split_string(self.sector3_time_minutes, self.sector3_time_in_ms),
        )?;
        map.serialize_entry("lap-valid-bit-flags", &self.lap_valid_bit_flags)?;
        map.end()
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct TyreStintHistoryData {
    pub end_lap: u8,
    pub tyre_actual_compound: ActualTyreCompound,
    pub tyre_visual_compound: VisualTyreCompound,
}

impl TyreStintHistoryData {
    pub const PACKET_LEN: usize = 3;

    pub fn from_values(
        end_lap: u8,
        tyre_actual_compound: ActualTyreCompound,
        tyre_visual_compound: VisualTyreCompound,
    ) -> Self {
        Self {
            end_lap,
            tyre_actual_compound,
            tyre_visual_compound,
        }
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
            end_lap: data[0],
            tyre_actual_compound: ActualTyreCompound::from_raw(data[1]),
            tyre_visual_compound: VisualTyreCompound::from_raw(data[2]),
        })
    }

    pub fn to_bytes(&self) -> [u8; Self::PACKET_LEN] {
        [
            self.end_lap,
            self.tyre_actual_compound as u8,
            self.tyre_visual_compound as u8,
        ]
    }
}

impl Serialize for TyreStintHistoryData {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let mut map = serializer.serialize_map(Some(3))?;
        map.serialize_entry("end-lap", &self.end_lap)?;
        map.serialize_entry(
            "tyre-actual-compound",
            &self.tyre_actual_compound.to_string(),
        )?;
        map.serialize_entry(
            "tyre-visual-compound",
            &self.tyre_visual_compound.to_string(),
        )?;
        map.end()
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct PacketSessionHistoryData {
    pub header: PacketHeader,
    pub car_index: u8,
    pub num_laps: u8,
    pub num_tyre_stints: u8,
    pub best_lap_time_lap_num: u8,
    pub best_sector1_lap_num: u8,
    pub best_sector2_lap_num: u8,
    pub best_sector3_lap_num: u8,
    pub lap_history_data: Vec<LapHistoryData>,
    pub tyre_stints_history_data: Vec<TyreStintHistoryData>,
}

impl PacketSessionHistoryData {
    pub const MAX_LAPS: usize = 100;
    pub const MAX_TYRE_STINT_COUNT: usize = 8;
    pub const PREFIX_LEN: usize = 7;
    pub const PAYLOAD_LEN: usize = Self::PREFIX_LEN
        + (Self::MAX_LAPS * LapHistoryData::PACKET_LEN)
        + (Self::MAX_TYRE_STINT_COUNT * TyreStintHistoryData::PACKET_LEN);

    #[allow(clippy::too_many_arguments)]
    pub fn from_values(
        header: PacketHeader,
        car_index: u8,
        num_laps: u8,
        num_tyre_stints: u8,
        best_lap_time_lap_num: u8,
        best_sector1_lap_num: u8,
        best_sector2_lap_num: u8,
        best_sector3_lap_num: u8,
        lap_history_data: Vec<LapHistoryData>,
        tyre_stints_history_data: Vec<TyreStintHistoryData>,
    ) -> Self {
        Self {
            header,
            car_index,
            num_laps,
            num_tyre_stints,
            best_lap_time_lap_num,
            best_sector1_lap_num,
            best_sector2_lap_num,
            best_sector3_lap_num,
            lap_history_data: lap_history_data
                .into_iter()
                .take(num_laps as usize)
                .collect(),
            tyre_stints_history_data: tyre_stints_history_data
                .into_iter()
                .take(num_tyre_stints as usize)
                .collect(),
        }
    }

    pub fn parse(header: PacketHeader, data: &[u8]) -> Result<Self, SessionHistoryError> {
        if data.len() != Self::PAYLOAD_LEN {
            return Err(InvalidPacketLengthError::new(format!(
                "Received packet length {} is not equal to expected {}",
                data.len(),
                Self::PAYLOAD_LEN
            ))
            .into());
        }

        let car_index = data[0];
        let num_laps = data[1];
        let num_tyre_stints = data[2];
        let best_lap_time_lap_num = data[3];
        let best_sector1_lap_num = data[4];
        let best_sector2_lap_num = data[5];
        let best_sector3_lap_num = data[6];

        if usize::from(num_laps) > Self::MAX_LAPS {
            return Err(PacketCountValidationError::new(format!(
                "Too many LapHistoryData items: {} > {}",
                num_laps,
                Self::MAX_LAPS
            ))
            .into());
        }
        if usize::from(num_tyre_stints) > Self::MAX_TYRE_STINT_COUNT {
            return Err(PacketCountValidationError::new(format!(
                "Too many TyreStintHistoryData items: {} > {}",
                num_tyre_stints,
                Self::MAX_TYRE_STINT_COUNT
            ))
            .into());
        }

        let lap_offset = Self::PREFIX_LEN;
        let lap_bytes =
            &data[lap_offset..lap_offset + (Self::MAX_LAPS * LapHistoryData::PACKET_LEN)];
        let lap_history_data = lap_bytes
            .chunks_exact(LapHistoryData::PACKET_LEN)
            .take(usize::from(num_laps))
            .map(LapHistoryData::parse)
            .collect::<Result<Vec<_>, _>>()?;

        let tyre_offset = lap_offset + (Self::MAX_LAPS * LapHistoryData::PACKET_LEN);
        let tyre_bytes = &data[tyre_offset
            ..tyre_offset + (Self::MAX_TYRE_STINT_COUNT * TyreStintHistoryData::PACKET_LEN)];
        let tyre_stints_history_data = tyre_bytes
            .chunks_exact(TyreStintHistoryData::PACKET_LEN)
            .take(usize::from(num_tyre_stints))
            .map(TyreStintHistoryData::parse)
            .collect::<Result<Vec<_>, _>>()?;

        Ok(Self {
            header,
            car_index,
            num_laps,
            num_tyre_stints,
            best_lap_time_lap_num,
            best_sector1_lap_num,
            best_sector2_lap_num,
            best_sector3_lap_num,
            lap_history_data,
            tyre_stints_history_data,
        })
    }

    pub fn to_bytes(&self) -> Vec<u8> {
        let mut bytes = Vec::with_capacity(PacketHeader::PACKET_LEN + Self::PAYLOAD_LEN);
        bytes.extend_from_slice(&self.header.to_bytes());
        bytes.push(self.car_index);
        bytes.push(self.num_laps);
        bytes.push(self.num_tyre_stints);
        bytes.push(self.best_lap_time_lap_num);
        bytes.push(self.best_sector1_lap_num);
        bytes.push(self.best_sector2_lap_num);
        bytes.push(self.best_sector3_lap_num);

        for lap in self.lap_history_data.iter().take(Self::MAX_LAPS) {
            bytes.extend_from_slice(&lap.to_bytes());
        }
        let remaining_laps = Self::MAX_LAPS.saturating_sub(self.lap_history_data.len());
        if remaining_laps > 0 {
            bytes.resize(
                bytes.len() + (remaining_laps * LapHistoryData::PACKET_LEN),
                0,
            );
        }

        for stint in self
            .tyre_stints_history_data
            .iter()
            .take(Self::MAX_TYRE_STINT_COUNT)
        {
            bytes.extend_from_slice(&stint.to_bytes());
        }
        let remaining_stints =
            Self::MAX_TYRE_STINT_COUNT.saturating_sub(self.tyre_stints_history_data.len());
        if remaining_stints > 0 {
            bytes.resize(
                bytes.len() + (remaining_stints * TyreStintHistoryData::PACKET_LEN),
                0,
            );
        }

        bytes
    }
}

impl Serialize for PacketSessionHistoryData {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let mut map = serializer.serialize_map(Some(9))?;
        map.serialize_entry("car-index", &self.car_index)?;
        map.serialize_entry("num-laps", &self.num_laps)?;
        map.serialize_entry("num-tyre-stints", &self.num_tyre_stints)?;
        map.serialize_entry("best-lap-time-lap-num", &self.best_lap_time_lap_num)?;
        map.serialize_entry("best-sector-1-lap-num", &self.best_sector1_lap_num)?;
        map.serialize_entry("best-sector-2-lap-num", &self.best_sector2_lap_num)?;
        map.serialize_entry("best-sector-3-lap-num", &self.best_sector3_lap_num)?;
        map.serialize_entry("lap-history-data", &self.lap_history_data)?;
        map.serialize_entry("tyre-stints-history-data", &self.tyre_stints_history_data)?;
        map.end()
    }
}
