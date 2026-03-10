use crate::PacketHeader;
use crate::errors::InvalidPacketLengthError;
use serde::Serialize;
use serde::ser::{SerializeMap, Serializer};
use std::fmt;

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct CarTelemetryData {
    pub speed: u16,
    pub throttle: f32,
    pub steer: f32,
    pub brake: f32,
    pub clutch: u8,
    pub gear: i8,
    pub engine_rpm: u16,
    pub drs: bool,
    pub rev_lights_percent: u8,
    pub rev_lights_bit_value: u16,
    pub brakes_temperature: [u16; 4],
    pub tyres_surface_temperature: [u8; 4],
    pub tyres_inner_temperature: [u8; 4],
    pub engine_temperature: u16,
    pub tyres_pressure: [f32; 4],
    pub surface_type: [u8; 4],
}

impl CarTelemetryData {
    pub const PACKET_LEN: usize = 60;

    #[allow(clippy::too_many_arguments)]
    pub fn from_values(
        speed: u16,
        throttle: f32,
        steer: f32,
        brake: f32,
        clutch: u8,
        gear: i8,
        engine_rpm: u16,
        drs: bool,
        rev_lights_percent: u8,
        rev_lights_bit_value: u16,
        brakes_temperature: [u16; 4],
        tyres_surface_temperature: [u8; 4],
        tyres_inner_temperature: [u8; 4],
        engine_temperature: u16,
        tyres_pressure: [f32; 4],
        surface_type: [u8; 4],
    ) -> Self {
        Self {
            speed,
            throttle,
            steer,
            brake,
            clutch,
            gear,
            engine_rpm,
            drs,
            rev_lights_percent,
            rev_lights_bit_value,
            brakes_temperature,
            tyres_surface_temperature,
            tyres_inner_temperature,
            engine_temperature,
            tyres_pressure,
            surface_type,
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

        let mut offset = 0usize;
        let read_u8 = |data: &[u8], offset: &mut usize| {
            let value = data[*offset];
            *offset += 1;
            value
        };
        let read_i8 = |data: &[u8], offset: &mut usize| {
            let value = data[*offset] as i8;
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
        let read_f32 = |data: &[u8], offset: &mut usize| {
            let value = f32::from_le_bytes(
                data[*offset..*offset + 4]
                    .try_into()
                    .expect("fixed slice length"),
            );
            *offset += 4;
            value
        };

        Ok(Self {
            speed: read_u16(data, &mut offset),
            throttle: read_f32(data, &mut offset),
            steer: read_f32(data, &mut offset),
            brake: read_f32(data, &mut offset),
            clutch: read_u8(data, &mut offset),
            gear: read_i8(data, &mut offset),
            engine_rpm: read_u16(data, &mut offset),
            drs: read_u8(data, &mut offset) != 0,
            rev_lights_percent: read_u8(data, &mut offset),
            rev_lights_bit_value: read_u16(data, &mut offset),
            brakes_temperature: [
                read_u16(data, &mut offset),
                read_u16(data, &mut offset),
                read_u16(data, &mut offset),
                read_u16(data, &mut offset),
            ],
            tyres_surface_temperature: [
                read_u8(data, &mut offset),
                read_u8(data, &mut offset),
                read_u8(data, &mut offset),
                read_u8(data, &mut offset),
            ],
            tyres_inner_temperature: [
                read_u8(data, &mut offset),
                read_u8(data, &mut offset),
                read_u8(data, &mut offset),
                read_u8(data, &mut offset),
            ],
            engine_temperature: read_u16(data, &mut offset),
            tyres_pressure: [
                read_f32(data, &mut offset),
                read_f32(data, &mut offset),
                read_f32(data, &mut offset),
                read_f32(data, &mut offset),
            ],
            surface_type: [
                read_u8(data, &mut offset),
                read_u8(data, &mut offset),
                read_u8(data, &mut offset),
                read_u8(data, &mut offset),
            ],
        })
    }

    pub fn to_bytes(&self) -> [u8; Self::PACKET_LEN] {
        let mut bytes = [0u8; Self::PACKET_LEN];
        let mut offset = 0usize;
        let write_u8 = |bytes: &mut [u8], offset: &mut usize, value: u8| {
            bytes[*offset] = value;
            *offset += 1;
        };
        let write_i8 = |bytes: &mut [u8], offset: &mut usize, value: i8| {
            bytes[*offset] = value as u8;
            *offset += 1;
        };
        let write_u16 = |bytes: &mut [u8], offset: &mut usize, value: u16| {
            bytes[*offset..*offset + 2].copy_from_slice(&value.to_le_bytes());
            *offset += 2;
        };
        let write_f32 = |bytes: &mut [u8], offset: &mut usize, value: f32| {
            bytes[*offset..*offset + 4].copy_from_slice(&value.to_le_bytes());
            *offset += 4;
        };

        write_u16(&mut bytes, &mut offset, self.speed);
        write_f32(&mut bytes, &mut offset, self.throttle);
        write_f32(&mut bytes, &mut offset, self.steer);
        write_f32(&mut bytes, &mut offset, self.brake);
        write_u8(&mut bytes, &mut offset, self.clutch);
        write_i8(&mut bytes, &mut offset, self.gear);
        write_u16(&mut bytes, &mut offset, self.engine_rpm);
        write_u8(&mut bytes, &mut offset, self.drs as u8);
        write_u8(&mut bytes, &mut offset, self.rev_lights_percent);
        write_u16(&mut bytes, &mut offset, self.rev_lights_bit_value);
        for value in self.brakes_temperature {
            write_u16(&mut bytes, &mut offset, value);
        }
        for value in self.tyres_surface_temperature {
            write_u8(&mut bytes, &mut offset, value);
        }
        for value in self.tyres_inner_temperature {
            write_u8(&mut bytes, &mut offset, value);
        }
        write_u16(&mut bytes, &mut offset, self.engine_temperature);
        for value in self.tyres_pressure {
            write_f32(&mut bytes, &mut offset, value);
        }
        for value in self.surface_type {
            write_u8(&mut bytes, &mut offset, value);
        }
        bytes
    }
}

impl fmt::Display for CarTelemetryData {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "CarTelemetryData(Speed: {}, Throttle: {}, Steer: {}, Brake: {}, Clutch: {}, Gear: {}, Engine RPM: {}, DRS: {}, Rev Lights Percent: {}, Brakes Temperature: {:?}, Tyres Surface Temperature: {:?}, Tyres Inner Temperature: {:?}, Engine Temperature: {}, Tyres Pressure: {:?})",
            self.speed,
            self.throttle,
            self.steer,
            self.brake,
            self.clutch,
            self.gear,
            self.engine_rpm,
            self.drs,
            self.rev_lights_percent,
            self.brakes_temperature,
            self.tyres_surface_temperature,
            self.tyres_inner_temperature,
            self.engine_temperature,
            self.tyres_pressure
        )
    }
}

impl Serialize for CarTelemetryData {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let mut map = serializer.serialize_map(Some(15))?;
        map.serialize_entry("speed", &self.speed)?;
        map.serialize_entry("throttle", &self.throttle)?;
        map.serialize_entry("steer", &self.steer)?;
        map.serialize_entry("brake", &self.brake)?;
        map.serialize_entry("clutch", &self.clutch)?;
        map.serialize_entry("gear", &self.gear)?;
        map.serialize_entry("engine-rpm", &self.engine_rpm)?;
        map.serialize_entry("drs", &self.drs)?;
        map.serialize_entry("rev-lights-percent", &self.rev_lights_percent)?;
        map.serialize_entry("brakes-temperature", &self.brakes_temperature)?;
        map.serialize_entry("tyres-surface-temperature", &self.tyres_surface_temperature)?;
        map.serialize_entry("tyres-inner-temperature", &self.tyres_inner_temperature)?;
        map.serialize_entry("engine-temperature", &self.engine_temperature)?;
        map.serialize_entry("tyres-pressure", &self.tyres_pressure)?;
        map.serialize_entry("surface-type", &self.surface_type)?;
        map.end()
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct PacketCarTelemetryData {
    pub header: PacketHeader,
    pub car_telemetry_data: Vec<CarTelemetryData>,
    pub mfd_panel_index: u8,
    pub mfd_panel_index_secondary_player: u8,
    pub suggested_gear: i8,
}

impl PacketCarTelemetryData {
    pub const MAX_CARS: usize = 22;
    pub const PACKET_LEN_EXTRA: usize = 3;
    pub const PAYLOAD_LEN: usize =
        (Self::MAX_CARS * CarTelemetryData::PACKET_LEN) + Self::PACKET_LEN_EXTRA;

    pub fn parse(header: PacketHeader, packet: &[u8]) -> Result<Self, InvalidPacketLengthError> {
        if packet.len() != Self::PAYLOAD_LEN {
            return Err(InvalidPacketLengthError::new(format!(
                "Received packet length {} is not equal to expected {}",
                packet.len(),
                Self::PAYLOAD_LEN
            )));
        }

        let telemetry_bytes = Self::MAX_CARS * CarTelemetryData::PACKET_LEN;
        let car_telemetry_data = packet[..telemetry_bytes]
            .chunks_exact(CarTelemetryData::PACKET_LEN)
            .map(CarTelemetryData::parse)
            .collect::<Result<Vec<_>, _>>()?;

        Ok(Self {
            header,
            car_telemetry_data,
            mfd_panel_index: packet[telemetry_bytes],
            mfd_panel_index_secondary_player: packet[telemetry_bytes + 1],
            suggested_gear: packet[telemetry_bytes + 2] as i8,
        })
    }

    pub fn from_values(
        header: PacketHeader,
        car_telemetry_data: Vec<CarTelemetryData>,
        mfd_panel_index: u8,
        mfd_panel_index_secondary_player: u8,
        suggested_gear: i8,
    ) -> Self {
        Self {
            header,
            car_telemetry_data,
            mfd_panel_index,
            mfd_panel_index_secondary_player,
            suggested_gear,
        }
    }

    pub fn to_bytes(&self) -> Vec<u8> {
        let mut bytes = Vec::with_capacity(PacketHeader::PACKET_LEN + Self::PAYLOAD_LEN);
        bytes.extend_from_slice(&self.header.to_bytes());
        for telemetry in &self.car_telemetry_data {
            bytes.extend_from_slice(&telemetry.to_bytes());
        }
        bytes.push(self.mfd_panel_index);
        bytes.push(self.mfd_panel_index_secondary_player);
        bytes.push(self.suggested_gear as u8);
        bytes
    }
}

impl fmt::Display for PacketCarTelemetryData {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let telemetry = self
            .car_telemetry_data
            .iter()
            .map(ToString::to_string)
            .collect::<Vec<_>>()
            .join(", ");
        write!(
            f,
            "PacketCarTelemetryData(Header: {}, Car Telemetry Data: [{}], MFD Panel Index: {}, MFD Panel Index Secondary: {}, Suggested Gear: {})",
            self.header,
            telemetry,
            self.mfd_panel_index,
            self.mfd_panel_index_secondary_player,
            self.suggested_gear
        )
    }
}

impl Serialize for PacketCarTelemetryData {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let mut map = serializer.serialize_map(Some(4))?;
        map.serialize_entry("car-telemetry-data", &self.car_telemetry_data)?;
        map.serialize_entry("mfd-panel-index", &self.mfd_panel_index)?;
        map.serialize_entry(
            "mfd-panel-index-secondary",
            &self.mfd_panel_index_secondary_player,
        )?;
        map.serialize_entry("suggested-gear", &self.suggested_gear)?;
        map.end()
    }
}
