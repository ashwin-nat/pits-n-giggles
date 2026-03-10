use crate::errors::InvalidPacketLengthError;
use crate::{ActualTyreCompound, PacketHeader, SessionType23, SessionType24, VisualTyreCompound};
use serde::Serialize;
use serde::ser::{SerializeMap, Serializer};
use std::fmt;

#[derive(Clone, Debug, PartialEq)]
pub struct TyreSetData {
    pub packet_format: u16,
    pub actual_tyre_compound: ActualTyreCompound,
    pub visual_tyre_compound: VisualTyreCompound,
    pub wear: u8,
    pub available: bool,
    pub recommended_session: u8,
    pub life_span: u8,
    pub usable_life: u8,
    pub lap_delta_time: i16,
    pub fitted: bool,
}

impl TyreSetData {
    pub const PACKET_LEN: usize = 10;

    pub fn from_values(
        packet_format: u16,
        actual_tyre_compound: ActualTyreCompound,
        visual_tyre_compound: VisualTyreCompound,
        wear: u8,
        available: bool,
        recommended_session: u8,
        life_span: u8,
        usable_life: u8,
        lap_delta_time: i16,
        fitted: bool,
    ) -> Self {
        Self {
            packet_format,
            actual_tyre_compound,
            visual_tyre_compound,
            wear,
            available,
            recommended_session,
            life_span,
            usable_life,
            lap_delta_time,
            fitted,
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
            actual_tyre_compound: ActualTyreCompound::from_raw(data[0]),
            visual_tyre_compound: VisualTyreCompound::from_raw(data[1]),
            wear: data[2],
            available: data[3] != 0,
            recommended_session: data[4],
            life_span: data[5],
            usable_life: data[6],
            lap_delta_time: i16::from_le_bytes([data[7], data[8]]),
            fitted: data[9] != 0,
        })
    }

    pub fn recommended_session_label(&self) -> String {
        if self.packet_format == 2023 {
            SessionType23::try_from(self.recommended_session)
                .map(|value| value.to_string())
                .unwrap_or_else(|value| value.to_string())
        } else {
            SessionType24::try_from(self.recommended_session)
                .map(|value| value.to_string())
                .unwrap_or_else(|value| value.to_string())
        }
    }

    pub fn to_bytes(&self) -> [u8; Self::PACKET_LEN] {
        let mut bytes = [0u8; Self::PACKET_LEN];
        bytes[0] = self.actual_tyre_compound as u8;
        bytes[1] = self.visual_tyre_compound as u8;
        bytes[2] = self.wear;
        bytes[3] = self.available as u8;
        bytes[4] = self.recommended_session;
        bytes[5] = self.life_span;
        bytes[6] = self.usable_life;
        bytes[7..9].copy_from_slice(&self.lap_delta_time.to_le_bytes());
        bytes[9] = self.fitted as u8;
        bytes
    }
}

impl fmt::Display for TyreSetData {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "TyreSetData(Actual Tyre Compound: {}, Visual Tyre Compound: {}, Wear: {}%, Available: {}, Recommended Session: {}, Life Span: {}, Usable Life: {}, Lap Delta Time: {} ms, Fitted: {})",
            self.actual_tyre_compound,
            self.visual_tyre_compound,
            self.wear,
            self.available,
            self.recommended_session_label(),
            self.life_span,
            self.usable_life,
            self.lap_delta_time,
            self.fitted
        )
    }
}

impl Serialize for TyreSetData {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let mut map = serializer.serialize_map(Some(9))?;
        map.serialize_entry(
            "actual-tyre-compound",
            &self.actual_tyre_compound.to_string(),
        )?;
        map.serialize_entry(
            "visual-tyre-compound",
            &self.visual_tyre_compound.to_string(),
        )?;
        map.serialize_entry("wear", &self.wear)?;
        map.serialize_entry("available", &self.available)?;
        map.serialize_entry("recommended-session", &self.recommended_session_label())?;
        map.serialize_entry("life-span", &self.life_span)?;
        map.serialize_entry("usable-life", &self.usable_life)?;
        map.serialize_entry("lap-delta-time", &self.lap_delta_time)?;
        map.serialize_entry("fitted", &self.fitted)?;
        map.end()
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct PacketTyreSetsData {
    pub header: PacketHeader,
    pub car_index: u8,
    pub tyre_set_data: Vec<TyreSetData>,
    pub fitted_index: u8,
}

impl PacketTyreSetsData {
    pub const MAX_TYRE_SETS: usize = 20;
    pub const PAYLOAD_LEN: usize = 1 + (Self::MAX_TYRE_SETS * TyreSetData::PACKET_LEN) + 1;

    pub fn parse(header: PacketHeader, data: &[u8]) -> Result<Self, InvalidPacketLengthError> {
        if data.len() != Self::PAYLOAD_LEN {
            return Err(InvalidPacketLengthError::new(format!(
                "Received packet length {} is not equal to expected {}",
                data.len(),
                Self::PAYLOAD_LEN
            )));
        }

        let car_index = data[0];
        let tyre_set_data = data[1..1 + (Self::MAX_TYRE_SETS * TyreSetData::PACKET_LEN)]
            .chunks_exact(TyreSetData::PACKET_LEN)
            .map(|chunk| TyreSetData::parse(chunk, header.packet_format))
            .collect::<Result<Vec<_>, _>>()?;
        let fitted_index = data[Self::PAYLOAD_LEN - 1];

        Ok(Self {
            header,
            car_index,
            tyre_set_data,
            fitted_index,
        })
    }

    pub fn from_values(
        header: PacketHeader,
        car_index: u8,
        tyre_set_data: Vec<TyreSetData>,
        fitted_index: u8,
    ) -> Self {
        Self {
            header,
            car_index,
            tyre_set_data,
            fitted_index,
        }
    }

    pub fn get_tyre_set(&self, index: usize) -> Option<&TyreSetData> {
        self.tyre_set_data.get(index)
    }

    pub fn get_tyre_set_key(&self, index: usize) -> Option<String> {
        self.get_tyre_set(index)
            .map(|tyre_set| format!("{index}.{}", tyre_set.actual_tyre_compound))
    }

    pub fn fitted_tyre_set(&self) -> Option<&TyreSetData> {
        let index = usize::from(self.fitted_index);
        self.tyre_set_data.get(index)
    }

    pub fn fitted_tyre_set_key(&self) -> Option<String> {
        if self.fitted_index == u8::MAX {
            return None;
        }
        self.fitted_tyre_set()
            .map(|tyre_set| format!("{}.{}", self.fitted_index, tyre_set.actual_tyre_compound))
    }

    pub fn to_bytes(&self) -> Vec<u8> {
        let mut bytes = Vec::with_capacity(PacketHeader::PACKET_LEN + Self::PAYLOAD_LEN);
        bytes.extend_from_slice(&self.header.to_bytes());
        bytes.push(self.car_index);
        for tyre_set in &self.tyre_set_data {
            bytes.extend_from_slice(&tyre_set.to_bytes());
        }
        bytes.push(self.fitted_index);
        bytes
    }
}

impl fmt::Display for PacketTyreSetsData {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "PacketTyreSetsData(Car Index: {}, Fitted Index: {}, Tyre Set Data: {:?})",
            self.car_index, self.fitted_index, self.tyre_set_data
        )
    }
}

impl Serialize for PacketTyreSetsData {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let mut map = serializer.serialize_map(Some(3))?;
        map.serialize_entry("car-index", &self.car_index)?;
        map.serialize_entry("tyre-set-data", &self.tyre_set_data)?;
        map.serialize_entry("fitted-index", &self.fitted_index)?;
        map.end()
    }
}
