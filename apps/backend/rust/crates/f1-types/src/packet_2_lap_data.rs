use crate::errors::InvalidPacketLengthError;
use crate::{PacketHeader, ResultStatus};
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

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum DriverStatus {
    InGarage,
    FlyingLap,
    InLap,
    OutLap,
    OnTrack,
    Unknown(u8),
}

impl DriverStatus {
    pub fn from_raw(value: u8) -> Self {
        match value {
            0 => Self::InGarage,
            1 => Self::FlyingLap,
            2 => Self::InLap,
            3 => Self::OutLap,
            4 => Self::OnTrack,
            _ => Self::Unknown(value),
        }
    }

    pub fn raw(self) -> u8 {
        match self {
            Self::InGarage => 0,
            Self::FlyingLap => 1,
            Self::InLap => 2,
            Self::OutLap => 3,
            Self::OnTrack => 4,
            Self::Unknown(value) => value,
        }
    }
}

impl fmt::Display for DriverStatus {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::InGarage => f.write_str("IN_GARAGE"),
            Self::FlyingLap => f.write_str("FLYING_LAP"),
            Self::InLap => f.write_str("IN_LAP"),
            Self::OutLap => f.write_str("OUT_LAP"),
            Self::OnTrack => f.write_str("ON_TRACK"),
            Self::Unknown(value) => write!(f, "{value}"),
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum PitStatus {
    None,
    Pitting,
    InPitArea,
    Unknown(u8),
}

impl PitStatus {
    pub fn from_raw(value: u8) -> Self {
        match value {
            0 => Self::None,
            1 => Self::Pitting,
            2 => Self::InPitArea,
            _ => Self::Unknown(value),
        }
    }

    pub fn raw(self) -> u8 {
        match self {
            Self::None => 0,
            Self::Pitting => 1,
            Self::InPitArea => 2,
            Self::Unknown(value) => value,
        }
    }
}

impl fmt::Display for PitStatus {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::None => f.write_str("NONE"),
            Self::Pitting => f.write_str("PITTING"),
            Self::InPitArea => f.write_str("IN_PIT_AREA"),
            Self::Unknown(value) => write!(f, "{value}"),
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub enum Sector {
    Sector1,
    Sector2,
    Sector3,
    Unknown(u8),
}

impl Sector {
    pub fn from_raw(value: u8) -> Self {
        match value {
            0 => Self::Sector1,
            1 => Self::Sector2,
            2 => Self::Sector3,
            _ => Self::Unknown(value),
        }
    }

    pub fn raw(self) -> u8 {
        match self {
            Self::Sector1 => 0,
            Self::Sector2 => 1,
            Self::Sector3 => 2,
            Self::Unknown(value) => value,
        }
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct LapData {
    pub packet_format: u16,
    pub last_lap_time_in_ms: u32,
    pub current_lap_time_in_ms: u32,
    pub sector1_time_in_ms: u16,
    pub sector1_time_minutes: u8,
    pub sector2_time_in_ms: u16,
    pub sector2_time_minutes: u8,
    pub delta_to_car_in_front_in_ms: u16,
    pub delta_to_car_in_front_minutes: u8,
    pub delta_to_race_leader_in_ms: u16,
    pub delta_to_race_leader_minutes: u8,
    pub lap_distance: f32,
    pub total_distance: f32,
    pub safety_car_delta: f32,
    pub car_position: u8,
    pub current_lap_num: u8,
    pub pit_status: PitStatus,
    pub num_pit_stops: u8,
    pub sector: Sector,
    pub current_lap_invalid: bool,
    pub penalties: u8,
    pub total_warnings: u8,
    pub corner_cutting_warnings: u8,
    pub num_unserved_drive_through_pens: u8,
    pub num_unserved_stop_go_pens: u8,
    pub grid_position: u8,
    pub driver_status: DriverStatus,
    pub result_status: ResultStatus,
    pub pit_lane_timer_active: bool,
    pub pit_lane_time_in_lane_in_ms: u16,
    pub pit_stop_timer_in_ms: u16,
    pub pit_stop_should_serve_pen: u8,
    pub speed_trap_fastest_speed: f32,
    pub speed_trap_fastest_lap: u8,
}

impl LapData {
    pub const PACKET_LEN_23: usize = 50;
    pub const PACKET_LEN_24: usize = 57;

    #[allow(clippy::too_many_arguments)]
    pub fn from_values(
        packet_format: u16,
        last_lap_time_in_ms: u32,
        current_lap_time_in_ms: u32,
        sector1_time_in_ms: u16,
        sector1_time_minutes: u8,
        sector2_time_in_ms: u16,
        sector2_time_minutes: u8,
        delta_to_car_in_front_in_ms: u16,
        delta_to_car_in_front_minutes: u8,
        delta_to_race_leader_in_ms: u16,
        delta_to_race_leader_minutes: u8,
        lap_distance: f32,
        total_distance: f32,
        safety_car_delta: f32,
        car_position: u8,
        current_lap_num: u8,
        pit_status: PitStatus,
        num_pit_stops: u8,
        sector: Sector,
        current_lap_invalid: bool,
        penalties: u8,
        total_warnings: u8,
        corner_cutting_warnings: u8,
        num_unserved_drive_through_pens: u8,
        num_unserved_stop_go_pens: u8,
        grid_position: u8,
        driver_status: DriverStatus,
        result_status: ResultStatus,
        pit_lane_timer_active: bool,
        pit_lane_time_in_lane_in_ms: u16,
        pit_stop_timer_in_ms: u16,
        pit_stop_should_serve_pen: u8,
        speed_trap_fastest_speed: f32,
        speed_trap_fastest_lap: u8,
    ) -> Self {
        Self {
            packet_format,
            last_lap_time_in_ms,
            current_lap_time_in_ms,
            sector1_time_in_ms,
            sector1_time_minutes,
            sector2_time_in_ms,
            sector2_time_minutes,
            delta_to_car_in_front_in_ms,
            delta_to_car_in_front_minutes: if packet_format == 2023 {
                0
            } else {
                delta_to_car_in_front_minutes
            },
            delta_to_race_leader_in_ms,
            delta_to_race_leader_minutes: if packet_format == 2023 {
                0
            } else {
                delta_to_race_leader_minutes
            },
            lap_distance,
            total_distance,
            safety_car_delta,
            car_position,
            current_lap_num,
            pit_status,
            num_pit_stops,
            sector,
            current_lap_invalid,
            penalties,
            total_warnings,
            corner_cutting_warnings,
            num_unserved_drive_through_pens,
            num_unserved_stop_go_pens,
            grid_position,
            driver_status,
            result_status,
            pit_lane_timer_active,
            pit_lane_time_in_lane_in_ms,
            pit_stop_timer_in_ms,
            pit_stop_should_serve_pen,
            speed_trap_fastest_speed: if packet_format == 2023 {
                0.0
            } else {
                speed_trap_fastest_speed
            },
            speed_trap_fastest_lap: if packet_format == 2023 {
                0
            } else {
                speed_trap_fastest_lap
            },
        }
    }

    pub fn packet_len_for_format(packet_format: u16) -> usize {
        if packet_format == 2023 {
            Self::PACKET_LEN_23
        } else {
            Self::PACKET_LEN_24
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
        let read_u16 = |data: &[u8], offset: &mut usize| {
            let value = u16::from_le_bytes(
                data[*offset..*offset + 2]
                    .try_into()
                    .expect("fixed slice length"),
            );
            *offset += 2;
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
        let read_f32 = |data: &[u8], offset: &mut usize| {
            let value = f32::from_le_bytes(
                data[*offset..*offset + 4]
                    .try_into()
                    .expect("fixed slice length"),
            );
            *offset += 4;
            value
        };

        let last_lap_time_in_ms = read_u32(data, &mut offset);
        let current_lap_time_in_ms = read_u32(data, &mut offset);
        let sector1_time_in_ms = read_u16(data, &mut offset);
        let sector1_time_minutes = read_u8(data, &mut offset);
        let sector2_time_in_ms = read_u16(data, &mut offset);
        let sector2_time_minutes = read_u8(data, &mut offset);
        let delta_to_car_in_front_in_ms = read_u16(data, &mut offset);
        let delta_to_car_in_front_minutes = if packet_format == 2023 {
            0
        } else {
            read_u8(data, &mut offset)
        };
        let delta_to_race_leader_in_ms = read_u16(data, &mut offset);
        let delta_to_race_leader_minutes = if packet_format == 2023 {
            0
        } else {
            read_u8(data, &mut offset)
        };
        let lap_distance = read_f32(data, &mut offset);
        let total_distance = read_f32(data, &mut offset);
        let safety_car_delta = read_f32(data, &mut offset);
        let car_position = read_u8(data, &mut offset);
        let current_lap_num = read_u8(data, &mut offset);
        let pit_status = PitStatus::from_raw(read_u8(data, &mut offset));
        let num_pit_stops = read_u8(data, &mut offset);
        let sector = Sector::from_raw(read_u8(data, &mut offset));
        let current_lap_invalid = read_u8(data, &mut offset) != 0;
        let penalties = read_u8(data, &mut offset);
        let total_warnings = read_u8(data, &mut offset);
        let corner_cutting_warnings = read_u8(data, &mut offset);
        let num_unserved_drive_through_pens = read_u8(data, &mut offset);
        let num_unserved_stop_go_pens = read_u8(data, &mut offset);
        let grid_position = read_u8(data, &mut offset);
        let driver_status = DriverStatus::from_raw(read_u8(data, &mut offset));
        let result_status = ResultStatus::from_raw(read_u8(data, &mut offset));
        let pit_lane_timer_active = read_u8(data, &mut offset) != 0;
        let pit_lane_time_in_lane_in_ms = read_u16(data, &mut offset);
        let pit_stop_timer_in_ms = read_u16(data, &mut offset);
        let pit_stop_should_serve_pen = read_u8(data, &mut offset);
        let speed_trap_fastest_speed = if packet_format == 2023 {
            0.0
        } else {
            read_f32(data, &mut offset)
        };
        let speed_trap_fastest_lap = if packet_format == 2023 {
            0
        } else {
            read_u8(data, &mut offset)
        };

        Ok(Self::from_values(
            packet_format,
            last_lap_time_in_ms,
            current_lap_time_in_ms,
            sector1_time_in_ms,
            sector1_time_minutes,
            sector2_time_in_ms,
            sector2_time_minutes,
            delta_to_car_in_front_in_ms,
            delta_to_car_in_front_minutes,
            delta_to_race_leader_in_ms,
            delta_to_race_leader_minutes,
            lap_distance,
            total_distance,
            safety_car_delta,
            car_position,
            current_lap_num,
            pit_status,
            num_pit_stops,
            sector,
            current_lap_invalid,
            penalties,
            total_warnings,
            corner_cutting_warnings,
            num_unserved_drive_through_pens,
            num_unserved_stop_go_pens,
            grid_position,
            driver_status,
            result_status,
            pit_lane_timer_active,
            pit_lane_time_in_lane_in_ms,
            pit_stop_timer_in_ms,
            pit_stop_should_serve_pen,
            speed_trap_fastest_speed,
            speed_trap_fastest_lap,
        ))
    }

    pub fn to_bytes(&self) -> Vec<u8> {
        let mut bytes = Vec::with_capacity(Self::packet_len_for_format(self.packet_format));
        bytes.extend_from_slice(&self.last_lap_time_in_ms.to_le_bytes());
        bytes.extend_from_slice(&self.current_lap_time_in_ms.to_le_bytes());
        bytes.extend_from_slice(&self.sector1_time_in_ms.to_le_bytes());
        bytes.push(self.sector1_time_minutes);
        bytes.extend_from_slice(&self.sector2_time_in_ms.to_le_bytes());
        bytes.push(self.sector2_time_minutes);
        bytes.extend_from_slice(&self.delta_to_car_in_front_in_ms.to_le_bytes());
        if self.packet_format != 2023 {
            bytes.push(self.delta_to_car_in_front_minutes);
        }
        bytes.extend_from_slice(&self.delta_to_race_leader_in_ms.to_le_bytes());
        if self.packet_format != 2023 {
            bytes.push(self.delta_to_race_leader_minutes);
        }
        bytes.extend_from_slice(&self.lap_distance.to_le_bytes());
        bytes.extend_from_slice(&self.total_distance.to_le_bytes());
        bytes.extend_from_slice(&self.safety_car_delta.to_le_bytes());
        bytes.push(self.car_position);
        bytes.push(self.current_lap_num);
        bytes.push(self.pit_status.raw());
        bytes.push(self.num_pit_stops);
        bytes.push(self.sector.raw());
        bytes.push(u8::from(self.current_lap_invalid));
        bytes.push(self.penalties);
        bytes.push(self.total_warnings);
        bytes.push(self.corner_cutting_warnings);
        bytes.push(self.num_unserved_drive_through_pens);
        bytes.push(self.num_unserved_stop_go_pens);
        bytes.push(self.grid_position);
        bytes.push(self.driver_status.raw());
        bytes.push(self.result_status as u8);
        bytes.push(u8::from(self.pit_lane_timer_active));
        bytes.extend_from_slice(&self.pit_lane_time_in_lane_in_ms.to_le_bytes());
        bytes.extend_from_slice(&self.pit_stop_timer_in_ms.to_le_bytes());
        bytes.push(self.pit_stop_should_serve_pen);
        if self.packet_format != 2023 {
            bytes.extend_from_slice(&self.speed_trap_fastest_speed.to_le_bytes());
            bytes.push(self.speed_trap_fastest_lap);
        }
        bytes
    }
}

impl Serialize for LapData {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let mut map = serializer.serialize_map(Some(33))?;
        map.serialize_entry("last-lap-time-in-ms", &self.last_lap_time_in_ms)?;
        map.serialize_entry(
            "last-lap-time-str",
            &lap_time_string(self.last_lap_time_in_ms),
        )?;
        map.serialize_entry("current-lap-time-in-ms", &self.current_lap_time_in_ms)?;
        map.serialize_entry(
            "current-lap-time-str",
            &lap_time_string(self.current_lap_time_in_ms),
        )?;
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
        map.serialize_entry(
            "delta-to-car-in-front-in-ms",
            &self.delta_to_car_in_front_in_ms,
        )?;
        map.serialize_entry(
            "delta-to-race-leader-in-ms",
            &self.delta_to_race_leader_in_ms,
        )?;
        map.serialize_entry("lap-distance", &self.lap_distance)?;
        map.serialize_entry("total-distance", &self.total_distance)?;
        map.serialize_entry("safety-car-delta", &self.safety_car_delta)?;
        map.serialize_entry("car-position", &self.car_position)?;
        map.serialize_entry("current-lap-num", &self.current_lap_num)?;
        map.serialize_entry("pit-status", &self.pit_status.to_string())?;
        map.serialize_entry("num-pit-stops", &self.num_pit_stops)?;
        map.serialize_entry("sector", &self.sector.raw().to_string())?;
        map.serialize_entry("current-lap-invalid", &self.current_lap_invalid)?;
        map.serialize_entry("penalties", &self.penalties)?;
        map.serialize_entry("total-warnings", &self.total_warnings)?;
        map.serialize_entry("corner-cutting-warnings", &self.corner_cutting_warnings)?;
        map.serialize_entry(
            "num-unserved-drive-through-pens",
            &self.num_unserved_drive_through_pens,
        )?;
        map.serialize_entry("num-unserved-stop-go-pens", &self.num_unserved_stop_go_pens)?;
        map.serialize_entry("grid-position", &self.grid_position)?;
        map.serialize_entry("driver-status", &self.driver_status.to_string())?;
        map.serialize_entry("result-status", &self.result_status.to_string())?;
        map.serialize_entry("pit-lane-timer-active", &self.pit_lane_timer_active)?;
        map.serialize_entry(
            "pit-lane-time-in-lane-in-ms",
            &self.pit_lane_time_in_lane_in_ms,
        )?;
        map.serialize_entry("pit-stop-timer-in-ms", &self.pit_stop_timer_in_ms)?;
        map.serialize_entry("pit-stop-should-serve-pen", &self.pit_stop_should_serve_pen)?;
        map.serialize_entry("speed-trap-fastest-speed", &self.speed_trap_fastest_speed)?;
        map.serialize_entry("speed-trap-fastest-lap", &self.speed_trap_fastest_lap)?;
        map.end()
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct PacketLapData {
    pub header: PacketHeader,
    pub lap_data: Vec<LapData>,
    pub time_trial_pb_car_idx: i8,
    pub time_trial_rival_car_idx: i8,
}

impl PacketLapData {
    pub const MAX_CARS: usize = 22;
    pub const EXTRA_LEN: usize = 2;

    pub fn payload_len_for_format(packet_format: u16) -> usize {
        (Self::MAX_CARS * LapData::packet_len_for_format(packet_format)) + Self::EXTRA_LEN
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

        let item_len = LapData::packet_len_for_format(header.packet_format);
        let lap_data = packet[..Self::MAX_CARS * item_len]
            .chunks_exact(item_len)
            .map(|chunk| LapData::parse(chunk, header.packet_format))
            .collect::<Result<Vec<_>, _>>()?;
        let extra = &packet[Self::MAX_CARS * item_len..];

        Ok(Self {
            header,
            lap_data,
            time_trial_pb_car_idx: i8::from_le_bytes([extra[0]]),
            time_trial_rival_car_idx: i8::from_le_bytes([extra[1]]),
        })
    }

    pub fn from_values(
        header: PacketHeader,
        lap_data: Vec<LapData>,
        time_trial_pb_car_idx: i8,
        time_trial_rival_car_idx: i8,
    ) -> Self {
        Self {
            header,
            lap_data,
            time_trial_pb_car_idx,
            time_trial_rival_car_idx,
        }
    }

    pub fn to_bytes(&self) -> Vec<u8> {
        let item_len = LapData::packet_len_for_format(self.header.packet_format);
        let mut bytes = Vec::with_capacity(
            PacketHeader::PACKET_LEN + Self::payload_len_for_format(self.header.packet_format),
        );
        bytes.extend_from_slice(&self.header.to_bytes());
        for lap in self.lap_data.iter().take(Self::MAX_CARS) {
            bytes.extend_from_slice(&lap.to_bytes());
        }
        let remaining = Self::MAX_CARS.saturating_sub(self.lap_data.len());
        if remaining > 0 {
            bytes.resize(bytes.len() + (remaining * item_len), 0);
        }
        bytes.push(self.time_trial_pb_car_idx as u8);
        bytes.push(self.time_trial_rival_car_idx as u8);
        bytes
    }
}

impl Serialize for PacketLapData {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let mut map = serializer.serialize_map(Some(4))?;
        map.serialize_entry("lap-data", &self.lap_data)?;
        map.serialize_entry("lap-data-count", &Self::MAX_CARS)?;
        map.serialize_entry("time-trial-pb-car-idx", &self.time_trial_pb_car_idx)?;
        map.serialize_entry("time-trial-rival-car-idx", &self.time_trial_rival_car_idx)?;
        map.end()
    }
}
