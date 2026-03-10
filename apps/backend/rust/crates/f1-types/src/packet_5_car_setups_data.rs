use crate::PacketHeader;
use crate::errors::InvalidPacketLengthError;
use serde::Serialize;
use serde::ser::{SerializeMap, Serializer};
use std::fmt;

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct CarSetupData {
    pub packet_format: u16,
    pub front_wing: u8,
    pub rear_wing: u8,
    pub on_throttle: u8,
    pub off_throttle: u8,
    pub front_camber: f32,
    pub rear_camber: f32,
    pub front_toe: f32,
    pub rear_toe: f32,
    pub front_suspension: u8,
    pub rear_suspension: u8,
    pub front_anti_roll_bar: u8,
    pub rear_anti_roll_bar: u8,
    pub front_suspension_height: u8,
    pub rear_suspension_height: u8,
    pub brake_pressure: u8,
    pub brake_bias: u8,
    pub engine_braking: u8,
    pub rear_left_tyre_pressure: f32,
    pub rear_right_tyre_pressure: f32,
    pub front_left_tyre_pressure: f32,
    pub front_right_tyre_pressure: f32,
    pub ballast: u8,
    pub fuel_load: f32,
}

impl CarSetupData {
    pub const PACKET_LEN_23: usize = 49;
    pub const PACKET_LEN_24: usize = 50;

    #[allow(clippy::too_many_arguments)]
    pub fn from_values(
        packet_format: u16,
        front_wing: u8,
        rear_wing: u8,
        on_throttle: u8,
        off_throttle: u8,
        front_camber: f32,
        rear_camber: f32,
        front_toe: f32,
        rear_toe: f32,
        front_suspension: u8,
        rear_suspension: u8,
        front_anti_roll_bar: u8,
        rear_anti_roll_bar: u8,
        front_suspension_height: u8,
        rear_suspension_height: u8,
        brake_pressure: u8,
        brake_bias: u8,
        rear_left_tyre_pressure: f32,
        rear_right_tyre_pressure: f32,
        front_left_tyre_pressure: f32,
        front_right_tyre_pressure: f32,
        ballast: u8,
        fuel_load: f32,
        engine_braking: u8,
    ) -> Self {
        Self {
            packet_format,
            front_wing,
            rear_wing,
            on_throttle,
            off_throttle,
            front_camber,
            rear_camber,
            front_toe,
            rear_toe,
            front_suspension,
            rear_suspension,
            front_anti_roll_bar,
            rear_anti_roll_bar,
            front_suspension_height,
            rear_suspension_height,
            brake_pressure,
            brake_bias,
            engine_braking: if packet_format == 2023 {
                0
            } else {
                engine_braking
            },
            rear_left_tyre_pressure,
            rear_right_tyre_pressure,
            front_left_tyre_pressure,
            front_right_tyre_pressure,
            ballast,
            fuel_load,
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
        let read_f32 = |data: &[u8], offset: &mut usize| {
            let value = f32::from_le_bytes(
                data[*offset..*offset + 4]
                    .try_into()
                    .expect("fixed slice length"),
            );
            *offset += 4;
            value
        };

        let front_wing = read_u8(data, &mut offset);
        let rear_wing = read_u8(data, &mut offset);
        let on_throttle = read_u8(data, &mut offset);
        let off_throttle = read_u8(data, &mut offset);
        let front_camber = read_f32(data, &mut offset);
        let rear_camber = read_f32(data, &mut offset);
        let front_toe = read_f32(data, &mut offset);
        let rear_toe = read_f32(data, &mut offset);
        let front_suspension = read_u8(data, &mut offset);
        let rear_suspension = read_u8(data, &mut offset);
        let front_anti_roll_bar = read_u8(data, &mut offset);
        let rear_anti_roll_bar = read_u8(data, &mut offset);
        let front_suspension_height = read_u8(data, &mut offset);
        let rear_suspension_height = read_u8(data, &mut offset);
        let brake_pressure = read_u8(data, &mut offset);
        let brake_bias = read_u8(data, &mut offset);
        let engine_braking = if packet_format == 2023 {
            0
        } else {
            read_u8(data, &mut offset)
        };
        let rear_left_tyre_pressure = read_f32(data, &mut offset);
        let rear_right_tyre_pressure = read_f32(data, &mut offset);
        let front_left_tyre_pressure = read_f32(data, &mut offset);
        let front_right_tyre_pressure = read_f32(data, &mut offset);
        let ballast = read_u8(data, &mut offset);
        let fuel_load = read_f32(data, &mut offset);

        Ok(Self {
            packet_format,
            front_wing,
            rear_wing,
            on_throttle,
            off_throttle,
            front_camber,
            rear_camber,
            front_toe,
            rear_toe,
            front_suspension,
            rear_suspension,
            front_anti_roll_bar,
            rear_anti_roll_bar,
            front_suspension_height,
            rear_suspension_height,
            brake_pressure,
            brake_bias,
            engine_braking,
            rear_left_tyre_pressure,
            rear_right_tyre_pressure,
            front_left_tyre_pressure,
            front_right_tyre_pressure,
            ballast,
            fuel_load,
        })
    }

    pub fn is_valid(&self) -> bool {
        !(self.front_wing == 0
            && self.rear_wing == 0
            && self.on_throttle == 0
            && self.off_throttle == 0
            && self.front_camber == 0.0
            && self.rear_camber == 0.0
            && self.front_toe == 0.0
            && self.rear_toe == 0.0
            && self.front_suspension == 0
            && self.rear_suspension == 0
            && self.front_anti_roll_bar == 0
            && self.rear_anti_roll_bar == 0
            && self.front_suspension_height == 0
            && self.rear_suspension_height == 0
            && self.brake_pressure == 0
            && self.brake_bias == 0
            && self.rear_left_tyre_pressure == 0.0
            && self.rear_right_tyre_pressure == 0.0
            && self.front_left_tyre_pressure == 0.0
            && self.front_right_tyre_pressure == 0.0
            && self.ballast == 0
            && self.fuel_load == 0.0)
    }

    pub fn to_bytes(&self) -> Vec<u8> {
        let mut bytes = Vec::with_capacity(Self::packet_len_for_format(self.packet_format));
        bytes.push(self.front_wing);
        bytes.push(self.rear_wing);
        bytes.push(self.on_throttle);
        bytes.push(self.off_throttle);
        bytes.extend_from_slice(&self.front_camber.to_le_bytes());
        bytes.extend_from_slice(&self.rear_camber.to_le_bytes());
        bytes.extend_from_slice(&self.front_toe.to_le_bytes());
        bytes.extend_from_slice(&self.rear_toe.to_le_bytes());
        bytes.push(self.front_suspension);
        bytes.push(self.rear_suspension);
        bytes.push(self.front_anti_roll_bar);
        bytes.push(self.rear_anti_roll_bar);
        bytes.push(self.front_suspension_height);
        bytes.push(self.rear_suspension_height);
        bytes.push(self.brake_pressure);
        bytes.push(self.brake_bias);
        if self.packet_format != 2023 {
            bytes.push(self.engine_braking);
        }
        bytes.extend_from_slice(&self.rear_left_tyre_pressure.to_le_bytes());
        bytes.extend_from_slice(&self.rear_right_tyre_pressure.to_le_bytes());
        bytes.extend_from_slice(&self.front_left_tyre_pressure.to_le_bytes());
        bytes.extend_from_slice(&self.front_right_tyre_pressure.to_le_bytes());
        bytes.push(self.ballast);
        bytes.extend_from_slice(&self.fuel_load.to_le_bytes());
        bytes
    }
}

impl fmt::Display for CarSetupData {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "CarSetupData(Front Wing: {}, Rear Wing: {}, On Throttle: {}, Off Throttle: {}, Front Camber: {}, Rear Camber: {}, Front Toe: {}, Rear Toe: {}, Front Suspension: {}, Rear Suspension: {}, Front Anti-Roll Bar: {}, Rear Anti-Roll Bar: {}, Front Suspension Height: {}, Rear Suspension Height: {}, Brake Pressure: {}, Brake Bias: {}, Rear Left Tyre Pressure: {}, Rear Right Tyre Pressure: {}, Front Left Tyre Pressure: {}, Front Right Tyre Pressure: {}, Ballast: {}, Fuel Load: {})",
            self.front_wing,
            self.rear_wing,
            self.on_throttle,
            self.off_throttle,
            self.front_camber,
            self.rear_camber,
            self.front_toe,
            self.rear_toe,
            self.front_suspension,
            self.rear_suspension,
            self.front_anti_roll_bar,
            self.rear_anti_roll_bar,
            self.front_suspension_height,
            self.rear_suspension_height,
            self.brake_pressure,
            self.brake_bias,
            self.rear_left_tyre_pressure,
            self.rear_right_tyre_pressure,
            self.front_left_tyre_pressure,
            self.front_right_tyre_pressure,
            self.ballast,
            self.fuel_load
        )
    }
}

impl Serialize for CarSetupData {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let mut map = serializer.serialize_map(Some(24))?;
        map.serialize_entry("front-wing", &self.front_wing)?;
        map.serialize_entry("rear-wing", &self.rear_wing)?;
        map.serialize_entry("on-throttle", &self.on_throttle)?;
        map.serialize_entry("off-throttle", &self.off_throttle)?;
        map.serialize_entry("front-camber", &self.front_camber)?;
        map.serialize_entry("rear-camber", &self.rear_camber)?;
        map.serialize_entry("front-toe", &self.front_toe)?;
        map.serialize_entry("rear-toe", &self.rear_toe)?;
        map.serialize_entry("front-suspension", &self.front_suspension)?;
        map.serialize_entry("rear-suspension", &self.rear_suspension)?;
        map.serialize_entry("front-anti-roll-bar", &self.front_anti_roll_bar)?;
        map.serialize_entry("rear-anti-roll-bar", &self.rear_anti_roll_bar)?;
        map.serialize_entry("front-suspension-height", &self.front_suspension_height)?;
        map.serialize_entry("rear-suspension-height", &self.rear_suspension_height)?;
        map.serialize_entry("brake-pressure", &self.brake_pressure)?;
        map.serialize_entry("brake-bias", &self.brake_bias)?;
        map.serialize_entry("engine-braking", &self.engine_braking)?;
        map.serialize_entry("rear-left-tyre-pressure", &self.rear_left_tyre_pressure)?;
        map.serialize_entry("rear-right-tyre-pressure", &self.rear_right_tyre_pressure)?;
        map.serialize_entry("front-left-tyre-pressure", &self.front_left_tyre_pressure)?;
        map.serialize_entry("front-right-tyre-pressure", &self.front_right_tyre_pressure)?;
        map.serialize_entry("ballast", &self.ballast)?;
        map.serialize_entry("fuel-load", &self.fuel_load)?;
        map.serialize_entry("is-valid", &self.is_valid())?;
        map.end()
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct PacketCarSetupData {
    pub header: PacketHeader,
    pub car_setups: Vec<CarSetupData>,
    pub next_front_wing_value: f32,
}

impl PacketCarSetupData {
    pub const MAX_CARS: usize = 22;

    pub fn parse(header: PacketHeader, packet: &[u8]) -> Result<Self, InvalidPacketLengthError> {
        let setup_len = CarSetupData::packet_len_for_format(header.packet_format);
        let expected_payload = if header.packet_format == 2023 {
            Self::MAX_CARS * setup_len
        } else {
            (Self::MAX_CARS * setup_len) + 4
        };

        if packet.len() != expected_payload {
            return Err(InvalidPacketLengthError::new(format!(
                "Received packet length {} is not equal to expected {}",
                packet.len(),
                expected_payload
            )));
        }

        let setups_bytes = Self::MAX_CARS * setup_len;
        let car_setups = packet[..setups_bytes]
            .chunks_exact(setup_len)
            .map(|chunk| CarSetupData::parse(chunk, header.packet_format))
            .collect::<Result<Vec<_>, _>>()?;

        let next_front_wing_value = if header.packet_format == 2023 {
            0.0
        } else {
            f32::from_le_bytes(
                packet[setups_bytes..setups_bytes + 4]
                    .try_into()
                    .expect("fixed slice length"),
            )
        };

        Ok(Self {
            header,
            car_setups,
            next_front_wing_value,
        })
    }

    pub fn from_values(
        header: PacketHeader,
        car_setups: Vec<CarSetupData>,
        next_front_wing_value: f32,
    ) -> Self {
        Self {
            header,
            car_setups,
            next_front_wing_value: if header.packet_format == 2023 {
                0.0
            } else {
                next_front_wing_value
            },
        }
    }

    pub fn to_bytes(&self) -> Vec<u8> {
        let setup_len = CarSetupData::packet_len_for_format(self.header.packet_format);
        let mut bytes = Vec::with_capacity(
            PacketHeader::PACKET_LEN
                + (self.car_setups.len() * setup_len)
                + if self.header.packet_format == 2023 {
                    0
                } else {
                    4
                },
        );
        bytes.extend_from_slice(&self.header.to_bytes());
        for setup in &self.car_setups {
            bytes.extend_from_slice(&setup.to_bytes());
        }
        if self.header.packet_format != 2023 {
            bytes.extend_from_slice(&self.next_front_wing_value.to_le_bytes());
        }
        bytes
    }
}

impl fmt::Display for PacketCarSetupData {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let setups = self
            .car_setups
            .iter()
            .map(ToString::to_string)
            .collect::<Vec<_>>()
            .join(", ");
        write!(
            f,
            "PacketCarSetupData(Header: {}, Car Setups: [{}])",
            self.header, setups
        )
    }
}

impl Serialize for PacketCarSetupData {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let mut map = serializer.serialize_map(Some(1))?;
        map.serialize_entry("car-setups", &self.car_setups)?;
        map.end()
    }
}
