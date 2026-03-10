use crate::errors::InvalidPacketLengthError;
use crate::{PacketHeader, TeamID24, TeamID25};
use serde::Serialize;
use serde::ser::{SerializeMap, Serializer};
use std::fmt;

fn lap_time_string(milliseconds: u32) -> String {
    let seconds = milliseconds / 1_000;
    let ms = milliseconds % 1_000;
    let minutes = seconds / 60;
    let seconds = seconds % 60;
    if minutes > 0 {
        format!("{minutes:02}:{seconds:02}.{ms:03}")
    } else {
        format!("{seconds:02}.{ms:03}")
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct TimeTrialDataSet {
    pub packet_format: u16,
    pub car_index: u8,
    pub team_id_raw: u8,
    pub lap_time_in_ms: u32,
    pub sector1_time_in_ms: u32,
    pub sector2_time_in_ms: u32,
    pub sector3_time_in_ms: u32,
    pub traction_control: bool,
    pub gearbox_assist: bool,
    pub anti_lock_brakes: bool,
    pub equal_car_performance: bool,
    pub custom_setup: bool,
    pub is_valid: bool,
}

impl TimeTrialDataSet {
    pub const PACKET_LEN: usize = 24;

    #[allow(clippy::too_many_arguments)]
    pub fn from_values(
        packet_format: u16,
        car_index: u8,
        team_id_raw: u8,
        lap_time_in_ms: u32,
        sector1_time_in_ms: u32,
        sector2_time_in_ms: u32,
        sector3_time_in_ms: u32,
        traction_control: bool,
        gearbox_assist: bool,
        anti_lock_brakes: bool,
        equal_car_performance: bool,
        custom_setup: bool,
        is_valid: bool,
    ) -> Self {
        Self {
            packet_format,
            car_index,
            team_id_raw,
            lap_time_in_ms,
            sector1_time_in_ms,
            sector2_time_in_ms,
            sector3_time_in_ms,
            traction_control,
            gearbox_assist,
            anti_lock_brakes,
            equal_car_performance,
            custom_setup,
            is_valid,
        }
    }

    pub fn parse(data: &[u8], packet_format: u16) -> Result<Self, InvalidPacketLengthError> {
        if data.len() != Self::PACKET_LEN {
            return Err(InvalidPacketLengthError::new(format!(
                "Received packet length {} expected {}",
                data.len(),
                Self::PACKET_LEN
            )));
        }

        Ok(Self {
            packet_format,
            car_index: data[0],
            team_id_raw: data[1],
            lap_time_in_ms: u32::from_le_bytes(data[2..6].try_into().expect("fixed slice length")),
            sector1_time_in_ms: u32::from_le_bytes(
                data[6..10].try_into().expect("fixed slice length"),
            ),
            sector2_time_in_ms: u32::from_le_bytes(
                data[10..14].try_into().expect("fixed slice length"),
            ),
            sector3_time_in_ms: u32::from_le_bytes(
                data[14..18].try_into().expect("fixed slice length"),
            ),
            traction_control: data[18] != 0,
            gearbox_assist: data[19] != 0,
            anti_lock_brakes: data[20] != 0,
            equal_car_performance: data[21] != 0,
            custom_setup: data[22] != 0,
            is_valid: data[23] != 0,
        })
    }

    pub fn team_label(&self) -> String {
        if self.packet_format >= 2025 {
            TeamID25::from_raw(self.team_id_raw)
                .map(|team| team.to_string())
                .unwrap_or_else(|| self.team_id_raw.to_string())
        } else {
            TeamID24::from_raw(self.team_id_raw)
                .map(|team| team.to_string())
                .unwrap_or_else(|| self.team_id_raw.to_string())
        }
    }

    pub fn to_bytes(&self) -> [u8; Self::PACKET_LEN] {
        let mut bytes = [0u8; Self::PACKET_LEN];
        bytes[0] = self.car_index;
        bytes[1] = self.team_id_raw;
        bytes[2..6].copy_from_slice(&self.lap_time_in_ms.to_le_bytes());
        bytes[6..10].copy_from_slice(&self.sector1_time_in_ms.to_le_bytes());
        bytes[10..14].copy_from_slice(&self.sector2_time_in_ms.to_le_bytes());
        bytes[14..18].copy_from_slice(&self.sector3_time_in_ms.to_le_bytes());
        bytes[18] = self.traction_control as u8;
        bytes[19] = self.gearbox_assist as u8;
        bytes[20] = self.anti_lock_brakes as u8;
        bytes[21] = self.equal_car_performance as u8;
        bytes[22] = self.custom_setup as u8;
        bytes[23] = self.is_valid as u8;
        bytes
    }
}

impl Serialize for TimeTrialDataSet {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let mut map = serializer.serialize_map(Some(16))?;
        map.serialize_entry("car-index", &self.car_index)?;
        map.serialize_entry("team", &self.team_label())?;
        map.serialize_entry("lap-time-ms", &self.lap_time_in_ms)?;
        map.serialize_entry("lap-time-str", &lap_time_string(self.lap_time_in_ms))?;
        map.serialize_entry("sector-1-time-ms", &self.sector1_time_in_ms)?;
        map.serialize_entry(
            "sector-1-time-str",
            &lap_time_string(self.sector1_time_in_ms),
        )?;
        map.serialize_entry("sector-2-time-in-ms", &self.sector2_time_in_ms)?;
        map.serialize_entry(
            "sector-2-time-str",
            &lap_time_string(self.sector2_time_in_ms),
        )?;
        map.serialize_entry("sector3-time-in-ms", &self.sector3_time_in_ms)?;
        map.serialize_entry(
            "sector-3-time-str",
            &lap_time_string(self.sector3_time_in_ms),
        )?;
        map.serialize_entry("traction-control", &self.traction_control)?;
        map.serialize_entry("gearbox-assist", &self.gearbox_assist)?;
        map.serialize_entry("anti-lock-brakes", &self.anti_lock_brakes)?;
        map.serialize_entry("equal-car-performance", &self.equal_car_performance)?;
        map.serialize_entry("custom-setup", &self.custom_setup)?;
        map.serialize_entry("is-valid", &self.is_valid)?;
        map.end()
    }
}

impl fmt::Display for TimeTrialDataSet {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "TimeTrialDataSet(Car Index: {}, Team: {})",
            self.car_index,
            self.team_label()
        )
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct PacketTimeTrialData {
    pub header: PacketHeader,
    pub player_session_best_data_set: TimeTrialDataSet,
    pub personal_best_data_set: TimeTrialDataSet,
    pub rival_session_best_data_set: TimeTrialDataSet,
}

impl PacketTimeTrialData {
    pub const PAYLOAD_LEN: usize = TimeTrialDataSet::PACKET_LEN * 3;

    pub fn parse(header: PacketHeader, data: &[u8]) -> Result<Self, InvalidPacketLengthError> {
        if data.len() != Self::PAYLOAD_LEN {
            return Err(InvalidPacketLengthError::new(format!(
                "Received packet length {} is not equal to expected {}",
                data.len(),
                Self::PAYLOAD_LEN
            )));
        }

        Ok(Self {
            player_session_best_data_set: TimeTrialDataSet::parse(
                &data[..TimeTrialDataSet::PACKET_LEN],
                header.packet_format,
            )?,
            personal_best_data_set: TimeTrialDataSet::parse(
                &data[TimeTrialDataSet::PACKET_LEN..TimeTrialDataSet::PACKET_LEN * 2],
                header.packet_format,
            )?,
            rival_session_best_data_set: TimeTrialDataSet::parse(
                &data[TimeTrialDataSet::PACKET_LEN * 2..],
                header.packet_format,
            )?,
            header,
        })
    }

    pub fn from_values(
        header: PacketHeader,
        player_session_best_data_set: TimeTrialDataSet,
        personal_best_data_set: TimeTrialDataSet,
        rival_session_best_data_set: TimeTrialDataSet,
    ) -> Self {
        Self {
            header,
            player_session_best_data_set,
            personal_best_data_set,
            rival_session_best_data_set,
        }
    }

    pub fn to_bytes(&self) -> Vec<u8> {
        let mut bytes = Vec::with_capacity(PacketHeader::PACKET_LEN + Self::PAYLOAD_LEN);
        bytes.extend_from_slice(&self.header.to_bytes());
        bytes.extend_from_slice(&self.player_session_best_data_set.to_bytes());
        bytes.extend_from_slice(&self.personal_best_data_set.to_bytes());
        bytes.extend_from_slice(&self.rival_session_best_data_set.to_bytes());
        bytes
    }
}

impl Serialize for PacketTimeTrialData {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let mut map = serializer.serialize_map(Some(3))?;
        map.serialize_entry(
            "player-session-best-data-set",
            &self.player_session_best_data_set,
        )?;
        map.serialize_entry("personal-best-data-set", &self.personal_best_data_set)?;
        map.serialize_entry(
            "rival-session-best-data-set",
            &self.rival_session_best_data_set,
        )?;
        map.end()
    }
}

impl fmt::Display for PacketTimeTrialData {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "PacketTimeTrialData(Header: {})", self.header)
    }
}
