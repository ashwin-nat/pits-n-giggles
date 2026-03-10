use crate::PacketHeader;
use crate::errors::InvalidPacketLengthError;
use serde::Serialize;
use serde::ser::{SerializeMap, Serializer};
use std::fmt;

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct CarMotionData {
    pub world_position_x: f32,
    pub world_position_y: f32,
    pub world_position_z: f32,
    pub world_velocity_x: f32,
    pub world_velocity_y: f32,
    pub world_velocity_z: f32,
    pub world_forward_dir_x: i16,
    pub world_forward_dir_y: i16,
    pub world_forward_dir_z: i16,
    pub world_right_dir_x: i16,
    pub world_right_dir_y: i16,
    pub world_right_dir_z: i16,
    pub g_force_lateral: f32,
    pub g_force_longitudinal: f32,
    pub g_force_vertical: f32,
    pub yaw: f32,
    pub pitch: f32,
    pub roll: f32,
}

impl CarMotionData {
    pub const PACKET_LEN: usize = 60;

    #[allow(clippy::too_many_arguments)]
    pub fn from_values(
        world_position_x: f32,
        world_position_y: f32,
        world_position_z: f32,
        world_velocity_x: f32,
        world_velocity_y: f32,
        world_velocity_z: f32,
        world_forward_dir_x: i16,
        world_forward_dir_y: i16,
        world_forward_dir_z: i16,
        world_right_dir_x: i16,
        world_right_dir_y: i16,
        world_right_dir_z: i16,
        g_force_lateral: f32,
        g_force_longitudinal: f32,
        g_force_vertical: f32,
        yaw: f32,
        pitch: f32,
        roll: f32,
    ) -> Self {
        Self {
            world_position_x,
            world_position_y,
            world_position_z,
            world_velocity_x,
            world_velocity_y,
            world_velocity_z,
            world_forward_dir_x,
            world_forward_dir_y,
            world_forward_dir_z,
            world_right_dir_x,
            world_right_dir_y,
            world_right_dir_z,
            g_force_lateral,
            g_force_longitudinal,
            g_force_vertical,
            yaw,
            pitch,
            roll,
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
            world_position_x: f32::from_le_bytes(
                data[0..4].try_into().expect("fixed slice length"),
            ),
            world_position_y: f32::from_le_bytes(
                data[4..8].try_into().expect("fixed slice length"),
            ),
            world_position_z: f32::from_le_bytes(
                data[8..12].try_into().expect("fixed slice length"),
            ),
            world_velocity_x: f32::from_le_bytes(
                data[12..16].try_into().expect("fixed slice length"),
            ),
            world_velocity_y: f32::from_le_bytes(
                data[16..20].try_into().expect("fixed slice length"),
            ),
            world_velocity_z: f32::from_le_bytes(
                data[20..24].try_into().expect("fixed slice length"),
            ),
            world_forward_dir_x: i16::from_le_bytes(
                data[24..26].try_into().expect("fixed slice length"),
            ),
            world_forward_dir_y: i16::from_le_bytes(
                data[26..28].try_into().expect("fixed slice length"),
            ),
            world_forward_dir_z: i16::from_le_bytes(
                data[28..30].try_into().expect("fixed slice length"),
            ),
            world_right_dir_x: i16::from_le_bytes(
                data[30..32].try_into().expect("fixed slice length"),
            ),
            world_right_dir_y: i16::from_le_bytes(
                data[32..34].try_into().expect("fixed slice length"),
            ),
            world_right_dir_z: i16::from_le_bytes(
                data[34..36].try_into().expect("fixed slice length"),
            ),
            g_force_lateral: f32::from_le_bytes(
                data[36..40].try_into().expect("fixed slice length"),
            ),
            g_force_longitudinal: f32::from_le_bytes(
                data[40..44].try_into().expect("fixed slice length"),
            ),
            g_force_vertical: f32::from_le_bytes(
                data[44..48].try_into().expect("fixed slice length"),
            ),
            yaw: f32::from_le_bytes(data[48..52].try_into().expect("fixed slice length")),
            pitch: f32::from_le_bytes(data[52..56].try_into().expect("fixed slice length")),
            roll: f32::from_le_bytes(data[56..60].try_into().expect("fixed slice length")),
        })
    }

    pub fn to_bytes(&self) -> [u8; Self::PACKET_LEN] {
        let mut bytes = [0u8; Self::PACKET_LEN];
        bytes[0..4].copy_from_slice(&self.world_position_x.to_le_bytes());
        bytes[4..8].copy_from_slice(&self.world_position_y.to_le_bytes());
        bytes[8..12].copy_from_slice(&self.world_position_z.to_le_bytes());
        bytes[12..16].copy_from_slice(&self.world_velocity_x.to_le_bytes());
        bytes[16..20].copy_from_slice(&self.world_velocity_y.to_le_bytes());
        bytes[20..24].copy_from_slice(&self.world_velocity_z.to_le_bytes());
        bytes[24..26].copy_from_slice(&self.world_forward_dir_x.to_le_bytes());
        bytes[26..28].copy_from_slice(&self.world_forward_dir_y.to_le_bytes());
        bytes[28..30].copy_from_slice(&self.world_forward_dir_z.to_le_bytes());
        bytes[30..32].copy_from_slice(&self.world_right_dir_x.to_le_bytes());
        bytes[32..34].copy_from_slice(&self.world_right_dir_y.to_le_bytes());
        bytes[34..36].copy_from_slice(&self.world_right_dir_z.to_le_bytes());
        bytes[36..40].copy_from_slice(&self.g_force_lateral.to_le_bytes());
        bytes[40..44].copy_from_slice(&self.g_force_longitudinal.to_le_bytes());
        bytes[44..48].copy_from_slice(&self.g_force_vertical.to_le_bytes());
        bytes[48..52].copy_from_slice(&self.yaw.to_le_bytes());
        bytes[52..56].copy_from_slice(&self.pitch.to_le_bytes());
        bytes[56..60].copy_from_slice(&self.roll.to_le_bytes());
        bytes
    }
}

impl fmt::Display for CarMotionData {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "CarMotionData(World Position: ({}, {}, {}), World Velocity: ({}, {}, {}), World Forward Dir: ({}, {}, {}), World Right Dir: ({}, {}, {}), G-Force Lateral: {}, G-Force Longitudinal: {}, G-Force Vertical: {}, Yaw: {}, Pitch: {}, Roll: {})",
            self.world_position_x,
            self.world_position_y,
            self.world_position_z,
            self.world_velocity_x,
            self.world_velocity_y,
            self.world_velocity_z,
            self.world_forward_dir_x,
            self.world_forward_dir_y,
            self.world_forward_dir_z,
            self.world_right_dir_x,
            self.world_right_dir_y,
            self.world_right_dir_z,
            self.g_force_lateral,
            self.g_force_longitudinal,
            self.g_force_vertical,
            self.yaw,
            self.pitch,
            self.roll
        )
    }
}

impl Serialize for CarMotionData {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let mut map = serializer.serialize_map(Some(6))?;
        map.serialize_entry(
            "world-position",
            &Axis3f {
                x: self.world_position_x,
                y: self.world_position_y,
                z: self.world_position_z,
            },
        )?;
        map.serialize_entry(
            "world-velocity",
            &Axis3f {
                x: self.world_velocity_x,
                y: self.world_velocity_y,
                z: self.world_velocity_z,
            },
        )?;
        map.serialize_entry(
            "world-forward-dir",
            &Axis3i16 {
                x: self.world_forward_dir_x,
                y: self.world_forward_dir_y,
                z: self.world_forward_dir_z,
            },
        )?;
        map.serialize_entry(
            "world-right-dir",
            &Axis3i16 {
                x: self.world_right_dir_x,
                y: self.world_right_dir_y,
                z: self.world_right_dir_z,
            },
        )?;
        map.serialize_entry(
            "g-force",
            &GForce {
                lateral: self.g_force_lateral,
                longitudinal: self.g_force_longitudinal,
                vertical: self.g_force_vertical,
            },
        )?;
        map.serialize_entry(
            "orientation",
            &Orientation {
                yaw: self.yaw,
                pitch: self.pitch,
                roll: self.roll,
            },
        )?;
        map.end()
    }
}

#[derive(Serialize)]
struct Axis3f {
    x: f32,
    y: f32,
    z: f32,
}

#[derive(Serialize)]
struct Axis3i16 {
    x: i16,
    y: i16,
    z: i16,
}

#[derive(Serialize)]
struct GForce {
    lateral: f32,
    longitudinal: f32,
    vertical: f32,
}

#[derive(Serialize)]
struct Orientation {
    yaw: f32,
    pitch: f32,
    roll: f32,
}

#[derive(Clone, Debug, PartialEq)]
pub struct PacketMotionData {
    pub header: PacketHeader,
    pub car_motion_data: Vec<CarMotionData>,
}

impl PacketMotionData {
    pub const MAX_CARS: usize = 22;
    pub const PAYLOAD_LEN: usize = Self::MAX_CARS * CarMotionData::PACKET_LEN;

    pub fn parse(header: PacketHeader, packet: &[u8]) -> Result<Self, InvalidPacketLengthError> {
        if packet.len() != Self::PAYLOAD_LEN {
            return Err(InvalidPacketLengthError::new(format!(
                "Received packet length {} is not equal to expected {}",
                packet.len(),
                Self::PAYLOAD_LEN
            )));
        }

        let car_motion_data = packet
            .chunks_exact(CarMotionData::PACKET_LEN)
            .map(CarMotionData::parse)
            .collect::<Result<Vec<_>, _>>()?;

        Ok(Self {
            header,
            car_motion_data,
        })
    }

    pub fn from_values(header: PacketHeader, car_motion_data: Vec<CarMotionData>) -> Self {
        Self {
            header,
            car_motion_data,
        }
    }

    pub fn to_bytes(&self) -> Vec<u8> {
        let mut bytes = Vec::with_capacity(PacketHeader::PACKET_LEN + Self::PAYLOAD_LEN);
        bytes.extend_from_slice(&self.header.to_bytes());
        for car in &self.car_motion_data {
            bytes.extend_from_slice(&car.to_bytes());
        }
        bytes
    }
}

impl fmt::Display for PacketMotionData {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let car_motion_data = self
            .car_motion_data
            .iter()
            .map(ToString::to_string)
            .collect::<Vec<_>>()
            .join(", ");
        write!(
            f,
            "PacketMotionData(Header: {}, CarMotionData: [{}])",
            self.header, car_motion_data
        )
    }
}

impl Serialize for PacketMotionData {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let mut map = serializer.serialize_map(Some(1))?;
        map.serialize_entry("car-motion-data", &self.car_motion_data)?;
        map.end()
    }
}
