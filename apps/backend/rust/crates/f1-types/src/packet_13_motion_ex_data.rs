use crate::PacketHeader;
use crate::errors::InvalidPacketLengthError;
use serde::Serialize;
use serde::ser::{SerializeMap, Serializer};
use std::fmt;

#[derive(Clone, Copy, Serialize)]
struct AxisTriplet {
    x: f32,
    y: f32,
    z: f32,
}

#[derive(Clone, Debug, PartialEq)]
pub struct PacketMotionExData {
    pub header: PacketHeader,
    pub suspension_position: [f32; 4],
    pub suspension_velocity: [f32; 4],
    pub suspension_acceleration: [f32; 4],
    pub wheel_speed: [f32; 4],
    pub wheel_slip_ratio: [f32; 4],
    pub wheel_slip_angle: [f32; 4],
    pub wheel_lat_force: [f32; 4],
    pub wheel_long_force: [f32; 4],
    pub wheel_vert_force: [f32; 4],
    pub front_aero_height: f32,
    pub rear_aero_height: f32,
    pub front_roll_angle: f32,
    pub rear_roll_angle: f32,
    pub chassis_yaw: f32,
    pub chassis_pitch: f32,
    pub wheel_camber: [f32; 4],
    pub wheel_camber_gain: [f32; 4],
    pub height_of_cog_above_ground: f32,
    pub local_velocity_x: f32,
    pub local_velocity_y: f32,
    pub local_velocity_z: f32,
    pub angular_velocity_x: f32,
    pub angular_velocity_y: f32,
    pub angular_velocity_z: f32,
    pub angular_acceleration_x: f32,
    pub angular_acceleration_y: f32,
    pub angular_acceleration_z: f32,
    pub front_wheels_angle: f32,
}

impl PacketMotionExData {
    pub const PACKET_LEN_23: usize = 188;
    pub const PACKET_LEN_EXTRA_24: usize = 20;
    pub const PACKET_LEN_EXTRA_25: usize = 36;
    pub const PACKET_LEN_24: usize = Self::PACKET_LEN_23 + Self::PACKET_LEN_EXTRA_24;
    pub const PACKET_LEN_25: usize = Self::PACKET_LEN_24 + Self::PACKET_LEN_EXTRA_25;

    #[allow(clippy::too_many_arguments)]
    pub fn from_values(
        header: PacketHeader,
        suspension_position: [f32; 4],
        suspension_velocity: [f32; 4],
        suspension_acceleration: [f32; 4],
        wheel_speed: [f32; 4],
        wheel_slip_ratio: [f32; 4],
        wheel_slip_angle: [f32; 4],
        wheel_lat_force: [f32; 4],
        wheel_long_force: [f32; 4],
        wheel_vert_force: [f32; 4],
        front_aero_height: f32,
        rear_aero_height: f32,
        front_roll_angle: f32,
        rear_roll_angle: f32,
        chassis_yaw: f32,
        chassis_pitch: f32,
        wheel_camber: [f32; 4],
        wheel_camber_gain: [f32; 4],
        height_of_cog_above_ground: f32,
        local_velocity_x: f32,
        local_velocity_y: f32,
        local_velocity_z: f32,
        angular_velocity_x: f32,
        angular_velocity_y: f32,
        angular_velocity_z: f32,
        angular_acceleration_x: f32,
        angular_acceleration_y: f32,
        angular_acceleration_z: f32,
        front_wheels_angle: f32,
    ) -> Self {
        Self {
            header,
            suspension_position,
            suspension_velocity,
            suspension_acceleration,
            wheel_speed,
            wheel_slip_ratio,
            wheel_slip_angle,
            wheel_lat_force,
            wheel_long_force,
            wheel_vert_force,
            front_aero_height: if header.packet_format >= 2024 {
                front_aero_height
            } else {
                0.0
            },
            rear_aero_height: if header.packet_format >= 2024 {
                rear_aero_height
            } else {
                0.0
            },
            front_roll_angle: if header.packet_format >= 2024 {
                front_roll_angle
            } else {
                0.0
            },
            rear_roll_angle: if header.packet_format >= 2024 {
                rear_roll_angle
            } else {
                0.0
            },
            chassis_yaw: if header.packet_format >= 2024 {
                chassis_yaw
            } else {
                0.0
            },
            chassis_pitch: if header.packet_format >= 2025 {
                chassis_pitch
            } else {
                0.0
            },
            wheel_camber: if header.packet_format >= 2025 {
                wheel_camber
            } else {
                [0.0; 4]
            },
            wheel_camber_gain: if header.packet_format >= 2025 {
                wheel_camber_gain
            } else {
                [0.0; 4]
            },
            height_of_cog_above_ground,
            local_velocity_x,
            local_velocity_y,
            local_velocity_z,
            angular_velocity_x,
            angular_velocity_y,
            angular_velocity_z,
            angular_acceleration_x,
            angular_acceleration_y,
            angular_acceleration_z,
            front_wheels_angle,
        }
    }

    pub fn packet_len_for_format(packet_format: u16) -> usize {
        if packet_format >= 2025 {
            Self::PACKET_LEN_25
        } else if packet_format >= 2024 {
            Self::PACKET_LEN_24
        } else {
            Self::PACKET_LEN_23
        }
    }

    pub fn parse(header: PacketHeader, data: &[u8]) -> Result<Self, InvalidPacketLengthError> {
        let expected_len = Self::packet_len_for_format(header.packet_format);
        if data.len() != expected_len {
            return Err(InvalidPacketLengthError::new(format!(
                "Received packet length {} is not equal to expected {}",
                data.len(),
                expected_len
            )));
        }

        let mut offset = 0usize;
        let read_f32 = |data: &[u8], offset: &mut usize| {
            let value = f32::from_le_bytes(
                data[*offset..*offset + 4]
                    .try_into()
                    .expect("fixed slice length"),
            );
            *offset += 4;
            value
        };
        let read_array4 = |data: &[u8], offset: &mut usize| {
            [
                read_f32(data, offset),
                read_f32(data, offset),
                read_f32(data, offset),
                read_f32(data, offset),
            ]
        };

        let suspension_position = read_array4(data, &mut offset);
        let suspension_velocity = read_array4(data, &mut offset);
        let suspension_acceleration = read_array4(data, &mut offset);
        let wheel_speed = read_array4(data, &mut offset);
        let wheel_slip_ratio = read_array4(data, &mut offset);
        let wheel_slip_angle = read_array4(data, &mut offset);
        let wheel_lat_force = read_array4(data, &mut offset);
        let wheel_long_force = read_array4(data, &mut offset);
        let height_of_cog_above_ground = read_f32(data, &mut offset);
        let local_velocity_x = read_f32(data, &mut offset);
        let local_velocity_y = read_f32(data, &mut offset);
        let local_velocity_z = read_f32(data, &mut offset);
        let angular_velocity_x = read_f32(data, &mut offset);
        let angular_velocity_y = read_f32(data, &mut offset);
        let angular_velocity_z = read_f32(data, &mut offset);
        let angular_acceleration_x = read_f32(data, &mut offset);
        let angular_acceleration_y = read_f32(data, &mut offset);
        let angular_acceleration_z = read_f32(data, &mut offset);
        let front_wheels_angle = read_f32(data, &mut offset);
        let wheel_vert_force = read_array4(data, &mut offset);

        let (front_aero_height, rear_aero_height, front_roll_angle, rear_roll_angle, chassis_yaw) =
            if header.packet_format >= 2024 {
                (
                    read_f32(data, &mut offset),
                    read_f32(data, &mut offset),
                    read_f32(data, &mut offset),
                    read_f32(data, &mut offset),
                    read_f32(data, &mut offset),
                )
            } else {
                (0.0, 0.0, 0.0, 0.0, 0.0)
            };

        let (chassis_pitch, wheel_camber, wheel_camber_gain) = if header.packet_format >= 2025 {
            (
                read_f32(data, &mut offset),
                read_array4(data, &mut offset),
                read_array4(data, &mut offset),
            )
        } else {
            (0.0, [0.0; 4], [0.0; 4])
        };

        Ok(Self::from_values(
            header,
            suspension_position,
            suspension_velocity,
            suspension_acceleration,
            wheel_speed,
            wheel_slip_ratio,
            wheel_slip_angle,
            wheel_lat_force,
            wheel_long_force,
            wheel_vert_force,
            front_aero_height,
            rear_aero_height,
            front_roll_angle,
            rear_roll_angle,
            chassis_yaw,
            chassis_pitch,
            wheel_camber,
            wheel_camber_gain,
            height_of_cog_above_ground,
            local_velocity_x,
            local_velocity_y,
            local_velocity_z,
            angular_velocity_x,
            angular_velocity_y,
            angular_velocity_z,
            angular_acceleration_x,
            angular_acceleration_y,
            angular_acceleration_z,
            front_wheels_angle,
        ))
    }

    pub fn to_bytes(&self) -> Vec<u8> {
        let mut bytes = Vec::with_capacity(Self::packet_len_for_format(self.header.packet_format));

        for values in [
            &self.suspension_position,
            &self.suspension_velocity,
            &self.suspension_acceleration,
            &self.wheel_speed,
            &self.wheel_slip_ratio,
            &self.wheel_slip_angle,
            &self.wheel_lat_force,
            &self.wheel_long_force,
        ] {
            for value in *values {
                bytes.extend_from_slice(&value.to_le_bytes());
            }
        }

        for value in [
            self.height_of_cog_above_ground,
            self.local_velocity_x,
            self.local_velocity_y,
            self.local_velocity_z,
            self.angular_velocity_x,
            self.angular_velocity_y,
            self.angular_velocity_z,
            self.angular_acceleration_x,
            self.angular_acceleration_y,
            self.angular_acceleration_z,
            self.front_wheels_angle,
        ] {
            bytes.extend_from_slice(&value.to_le_bytes());
        }

        for value in self.wheel_vert_force {
            bytes.extend_from_slice(&value.to_le_bytes());
        }

        if self.header.packet_format >= 2024 {
            for value in [
                self.front_aero_height,
                self.rear_aero_height,
                self.front_roll_angle,
                self.rear_roll_angle,
                self.chassis_yaw,
            ] {
                bytes.extend_from_slice(&value.to_le_bytes());
            }
        }

        if self.header.packet_format >= 2025 {
            bytes.extend_from_slice(&self.chassis_pitch.to_le_bytes());
            for value in self.wheel_camber {
                bytes.extend_from_slice(&value.to_le_bytes());
            }
            for value in self.wheel_camber_gain {
                bytes.extend_from_slice(&value.to_le_bytes());
            }
        }

        bytes
    }
}

impl fmt::Display for PacketMotionExData {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "PacketMotionExData(Header: {})", self.header)
    }
}

impl Serialize for PacketMotionExData {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let mut map = serializer.serialize_map(Some(21))?;
        map.serialize_entry("suspension-position", &self.suspension_position)?;
        map.serialize_entry("suspension-velocity", &self.suspension_velocity)?;
        map.serialize_entry("suspension-acceleration", &self.suspension_acceleration)?;
        map.serialize_entry("wheel-speed", &self.wheel_speed)?;
        map.serialize_entry("wheel-slip-ratio", &self.wheel_slip_ratio)?;
        map.serialize_entry("wheel-slip-angle", &self.wheel_slip_angle)?;
        map.serialize_entry("wheel-lat-force", &self.wheel_lat_force)?;
        map.serialize_entry("wheel-long-force", &self.wheel_long_force)?;
        map.serialize_entry(
            "height-of-cog-above-ground",
            &self.height_of_cog_above_ground,
        )?;
        map.serialize_entry(
            "local-velocity",
            &AxisTriplet {
                x: self.local_velocity_x,
                y: self.local_velocity_y,
                z: self.local_velocity_z,
            },
        )?;
        map.serialize_entry(
            "angular-velocity",
            &AxisTriplet {
                x: self.angular_velocity_x,
                y: self.angular_velocity_y,
                z: self.angular_velocity_z,
            },
        )?;
        map.serialize_entry(
            "angular-acceleration",
            &AxisTriplet {
                x: self.angular_acceleration_x,
                y: self.angular_acceleration_y,
                z: self.angular_acceleration_z,
            },
        )?;
        map.serialize_entry("front-wheels-angle", &self.front_wheels_angle)?;
        map.serialize_entry("wheel-vert-force", &self.wheel_vert_force)?;
        map.serialize_entry("front-aero-height", &self.front_aero_height)?;
        map.serialize_entry("rear-aero-height", &self.rear_aero_height)?;
        map.serialize_entry("front-roll-angle", &self.front_roll_angle)?;
        map.serialize_entry("rear-roll-angle", &self.rear_roll_angle)?;
        map.serialize_entry("chassis-yaw", &self.chassis_yaw)?;
        map.serialize_entry("chassis-pitch", &self.chassis_pitch)?;
        map.serialize_entry("wheel-camber", &self.wheel_camber)?;
        map.serialize_entry("wheel-camber-gain", &self.wheel_camber_gain)?;
        map.end()
    }
}
