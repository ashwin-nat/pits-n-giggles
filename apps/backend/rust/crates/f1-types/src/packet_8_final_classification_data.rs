use crate::errors::InvalidPacketLengthError;
use crate::{ActualTyreCompound, PacketHeader, ResultReason, ResultStatus, VisualTyreCompound};
use serde::Serialize;
use serde::ser::{SerializeMap, Serializer};
use std::fmt;

fn milliseconds_to_minutes_seconds_milliseconds(milliseconds: u32) -> String {
    let total_seconds = milliseconds / 1_000;
    let milliseconds = milliseconds % 1_000;
    let minutes = total_seconds / 60;
    let seconds = total_seconds % 60;
    format!("{minutes:02}:{seconds:02}.{milliseconds:03}")
}

fn seconds_to_minutes_seconds_milliseconds(seconds: f64) -> String {
    let total_milliseconds = (seconds * 1_000.0) as u64;
    let total_seconds = total_milliseconds / 1_000;
    let milliseconds = total_milliseconds % 1_000;
    let minutes = total_seconds / 60;
    let seconds = total_seconds % 60;
    format!("{minutes:02}:{seconds:02}.{milliseconds:03}")
}

#[derive(Clone, Debug, PartialEq)]
pub struct FinalClassificationData {
    pub packet_format: u16,
    pub position: u8,
    pub num_laps: u8,
    pub grid_position: u8,
    pub points: u8,
    pub num_pit_stops: u8,
    pub result_status: ResultStatus,
    pub result_reason: ResultReason,
    pub best_lap_time_in_ms: u32,
    pub total_race_time: f64,
    pub penalties_time: u8,
    pub num_penalties: u8,
    pub num_tyre_stints: u8,
    pub tyre_stints_actual: Vec<ActualTyreCompound>,
    pub tyre_stints_visual: Vec<VisualTyreCompound>,
    pub tyre_stints_end_laps: Vec<u8>,
}

impl FinalClassificationData {
    pub const MAX_TYRE_STINTS: usize = 8;
    pub const PACKET_LEN: usize = 45;
    pub const PACKET_LEN_25: usize = 46;

    #[allow(clippy::too_many_arguments)]
    pub fn from_values(
        packet_format: u16,
        position: u8,
        num_laps: u8,
        grid_position: u8,
        points: u8,
        num_pit_stops: u8,
        result_status: ResultStatus,
        result_reason: ResultReason,
        best_lap_time_in_ms: u32,
        total_race_time: f64,
        penalties_time: u8,
        num_penalties: u8,
        num_tyre_stints: u8,
        tyre_stints_actual: Vec<ActualTyreCompound>,
        tyre_stints_visual: Vec<VisualTyreCompound>,
        tyre_stints_end_laps: Vec<u8>,
    ) -> Self {
        let trimmed_len = usize::min(num_tyre_stints as usize, Self::MAX_TYRE_STINTS);
        Self {
            packet_format,
            position,
            num_laps,
            grid_position,
            points,
            num_pit_stops,
            result_status,
            result_reason: if packet_format >= 2025 {
                result_reason
            } else {
                ResultReason::INVALID
            },
            best_lap_time_in_ms,
            total_race_time,
            penalties_time,
            num_penalties,
            num_tyre_stints,
            tyre_stints_actual: tyre_stints_actual.into_iter().take(trimmed_len).collect(),
            tyre_stints_visual: tyre_stints_visual.into_iter().take(trimmed_len).collect(),
            tyre_stints_end_laps: tyre_stints_end_laps.into_iter().take(trimmed_len).collect(),
        }
    }

    pub fn packet_len_for_format(packet_format: u16) -> usize {
        if packet_format >= 2025 {
            Self::PACKET_LEN_25
        } else {
            Self::PACKET_LEN
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

        let mut offset = 0usize;
        let read_u8 = |data: &[u8], offset: &mut usize| {
            let value = data[*offset];
            *offset += 1;
            value
        };
        let read_u32 = |data: &[u8], offset: &mut usize| {
            let value = u32::from_le_bytes(
                data[*offset..*offset + 4]
                    .try_into()
                    .expect("fixed slice length"),
            );
            *offset += 4;
            value
        };
        let read_f64 = |data: &[u8], offset: &mut usize| {
            let value = f64::from_le_bytes(
                data[*offset..*offset + 8]
                    .try_into()
                    .expect("fixed slice length"),
            );
            *offset += 8;
            value
        };

        let position = read_u8(data, &mut offset);
        let num_laps = read_u8(data, &mut offset);
        let grid_position = read_u8(data, &mut offset);
        let points = read_u8(data, &mut offset);
        let num_pit_stops = read_u8(data, &mut offset);
        let result_status = ResultStatus::from_raw(read_u8(data, &mut offset));
        let result_reason = if packet_format >= 2025 {
            ResultReason::from_raw(read_u8(data, &mut offset))
        } else {
            ResultReason::INVALID
        };
        let best_lap_time_in_ms = read_u32(data, &mut offset);
        let total_race_time = read_f64(data, &mut offset);
        let penalties_time = read_u8(data, &mut offset);
        let num_penalties = read_u8(data, &mut offset);
        let num_tyre_stints = read_u8(data, &mut offset);

        let tyre_stints_actual = (0..Self::MAX_TYRE_STINTS)
            .map(|_| ActualTyreCompound::from_raw(read_u8(data, &mut offset)))
            .collect::<Vec<_>>();
        let tyre_stints_visual = (0..Self::MAX_TYRE_STINTS)
            .map(|_| VisualTyreCompound::from_raw(read_u8(data, &mut offset)))
            .collect::<Vec<_>>();
        let tyre_stints_end_laps = (0..Self::MAX_TYRE_STINTS)
            .map(|_| read_u8(data, &mut offset))
            .collect::<Vec<_>>();

        Ok(Self::from_values(
            packet_format,
            position,
            num_laps,
            grid_position,
            points,
            num_pit_stops,
            result_status,
            result_reason,
            best_lap_time_in_ms,
            total_race_time,
            penalties_time,
            num_penalties,
            num_tyre_stints,
            tyre_stints_actual,
            tyre_stints_visual,
            tyre_stints_end_laps,
        ))
    }

    pub fn to_bytes(&self) -> Vec<u8> {
        let mut bytes = Vec::with_capacity(Self::packet_len_for_format(self.packet_format));
        bytes.push(self.position);
        bytes.push(self.num_laps);
        bytes.push(self.grid_position);
        bytes.push(self.points);
        bytes.push(self.num_pit_stops);
        bytes.push(self.result_status as u8);
        if self.packet_format >= 2025 {
            bytes.push(self.result_reason as u8);
        }
        bytes.extend_from_slice(&self.best_lap_time_in_ms.to_le_bytes());
        bytes.extend_from_slice(&self.total_race_time.to_le_bytes());
        bytes.push(self.penalties_time);
        bytes.push(self.num_penalties);
        bytes.push(self.num_tyre_stints);

        let mut actual = [0u8; Self::MAX_TYRE_STINTS];
        for (index, compound) in self
            .tyre_stints_actual
            .iter()
            .take(Self::MAX_TYRE_STINTS)
            .enumerate()
        {
            actual[index] = *compound as u8;
        }
        bytes.extend_from_slice(&actual);

        let mut visual = [0u8; Self::MAX_TYRE_STINTS];
        for (index, compound) in self
            .tyre_stints_visual
            .iter()
            .take(Self::MAX_TYRE_STINTS)
            .enumerate()
        {
            visual[index] = *compound as u8;
        }
        bytes.extend_from_slice(&visual);

        let mut end_laps = [0u8; Self::MAX_TYRE_STINTS];
        for (index, lap) in self
            .tyre_stints_end_laps
            .iter()
            .take(Self::MAX_TYRE_STINTS)
            .enumerate()
        {
            end_laps[index] = *lap;
        }
        bytes.extend_from_slice(&end_laps);
        bytes
    }
}

impl fmt::Display for FinalClassificationData {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "FinalClassificationData(Position: {}, Num Laps: {}, Grid Position: {}, Points: {}, Num Pit Stops: {}, Result Status: {}, Best Lap Time In MS: {}, Total Race Time: {}, Penalties Time: {}, Num Penalties: {}, Num Tyre Stints: {})",
            self.position,
            self.num_laps,
            self.grid_position,
            self.points,
            self.num_pit_stops,
            self.result_status,
            self.best_lap_time_in_ms,
            self.total_race_time,
            self.penalties_time,
            self.num_penalties,
            self.num_tyre_stints
        )
    }
}

impl Serialize for FinalClassificationData {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let field_count = if self.packet_format >= 2025 { 17 } else { 16 };
        let mut map = serializer.serialize_map(Some(field_count))?;
        map.serialize_entry("position", &self.position)?;
        map.serialize_entry("num-laps", &self.num_laps)?;
        map.serialize_entry("grid-position", &self.grid_position)?;
        map.serialize_entry("points", &self.points)?;
        map.serialize_entry("num-pit-stops", &self.num_pit_stops)?;
        map.serialize_entry("result-status", &self.result_status.to_string())?;
        if self.packet_format >= 2025 {
            map.serialize_entry("result-reason", &self.result_reason.to_string())?;
        }
        map.serialize_entry("best-lap-time-ms", &self.best_lap_time_in_ms)?;
        map.serialize_entry(
            "best-lap-time-str",
            &milliseconds_to_minutes_seconds_milliseconds(self.best_lap_time_in_ms),
        )?;
        map.serialize_entry("total-race-time", &self.total_race_time)?;
        map.serialize_entry(
            "total-race-time-str",
            &seconds_to_minutes_seconds_milliseconds(self.total_race_time),
        )?;
        map.serialize_entry("penalties-time", &self.penalties_time)?;
        map.serialize_entry("num-penalties", &self.num_penalties)?;
        map.serialize_entry("num-tyre-stints", &self.num_tyre_stints)?;
        map.serialize_entry(
            "tyre-stints-actual",
            &self
                .tyre_stints_actual
                .iter()
                .map(ToString::to_string)
                .collect::<Vec<_>>(),
        )?;
        map.serialize_entry(
            "tyre-stints-visual",
            &self
                .tyre_stints_visual
                .iter()
                .map(ToString::to_string)
                .collect::<Vec<_>>(),
        )?;
        map.serialize_entry("tyre-stints-end-laps", &self.tyre_stints_end_laps)?;
        map.end()
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct PacketFinalClassificationData {
    pub header: PacketHeader,
    pub num_cars: u8,
    pub classification_data: Vec<FinalClassificationData>,
}

impl PacketFinalClassificationData {
    pub const MAX_CARS: usize = 22;

    pub fn parse(header: PacketHeader, packet: &[u8]) -> Result<Self, InvalidPacketLengthError> {
        if packet.is_empty() {
            return Err(InvalidPacketLengthError::new(
                "Received packet length 0 is not equal to expected at least 1",
            ));
        }

        let num_cars = packet[0];
        if usize::from(num_cars) > Self::MAX_CARS {
            return Err(InvalidPacketLengthError::new(format!(
                "Received car count {} exceeds maximum {}",
                num_cars,
                Self::MAX_CARS
            )));
        }

        let item_len = FinalClassificationData::packet_len_for_format(header.packet_format);
        let expected_payload = 1 + (Self::MAX_CARS * item_len);

        if packet.len() != expected_payload {
            return Err(InvalidPacketLengthError::new(format!(
                "Received packet length {} is not equal to expected {}",
                packet.len(),
                expected_payload
            )));
        }
        let classification_data = packet[1..]
            .chunks_exact(item_len)
            .take(usize::from(num_cars))
            .map(|chunk| FinalClassificationData::parse(chunk, header.packet_format))
            .collect::<Result<Vec<_>, _>>()?;

        Ok(Self {
            header,
            num_cars,
            classification_data,
        })
    }

    pub fn from_values(
        header: PacketHeader,
        num_cars: u8,
        classification_data: Vec<FinalClassificationData>,
    ) -> Self {
        Self {
            header,
            num_cars,
            classification_data,
        }
    }

    pub fn to_bytes(&self) -> Vec<u8> {
        let item_len = FinalClassificationData::packet_len_for_format(self.header.packet_format);
        let mut bytes =
            Vec::with_capacity(PacketHeader::PACKET_LEN + 1 + (Self::MAX_CARS * item_len));
        bytes.extend_from_slice(&self.header.to_bytes());
        bytes.push(self.num_cars);

        for item in self.classification_data.iter().take(Self::MAX_CARS) {
            bytes.extend_from_slice(&item.to_bytes());
        }

        let remaining_slots = Self::MAX_CARS.saturating_sub(self.classification_data.len());
        if remaining_slots > 0 {
            bytes.resize(bytes.len() + (remaining_slots * item_len), 0);
        }

        bytes
    }
}

impl fmt::Display for PacketFinalClassificationData {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "PacketFinalClassificationData(Num Cars: {}, Classification Data: {:?})",
            self.num_cars, self.classification_data
        )
    }
}

impl Serialize for PacketFinalClassificationData {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let mut map = serializer.serialize_map(Some(2))?;
        map.serialize_entry("num-cars", &self.num_cars)?;
        map.serialize_entry("classification-data", &self.classification_data)?;
        map.end()
    }
}
