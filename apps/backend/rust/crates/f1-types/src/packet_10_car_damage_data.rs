use crate::PacketHeader;
use crate::errors::InvalidPacketLengthError;
use serde::Serialize;
use serde::ser::{SerializeMap, Serializer};
use std::fmt;

#[derive(Clone, Debug, PartialEq)]
pub struct CarDamageData {
    pub packet_format: u16,
    pub tyres_wear: [f32; 4],
    pub tyres_damage: [u8; 4],
    pub brakes_damage: [u8; 4],
    pub tyre_blisters: [u8; 4],
    pub front_left_wing_damage: u8,
    pub front_right_wing_damage: u8,
    pub rear_wing_damage: u8,
    pub floor_damage: u8,
    pub diffuser_damage: u8,
    pub sidepod_damage: u8,
    pub drs_fault: bool,
    pub ers_fault: bool,
    pub gear_box_damage: u8,
    pub engine_damage: u8,
    pub engine_mguh_wear: u8,
    pub engine_es_wear: u8,
    pub engine_ce_wear: u8,
    pub engine_ice_wear: u8,
    pub engine_mguk_wear: u8,
    pub engine_tc_wear: u8,
    pub engine_blown: bool,
    pub engine_seized: bool,
}

impl CarDamageData {
    pub const PACKET_LEN: usize = 42;
    pub const PACKET_LEN_25: usize = 46;

    #[allow(clippy::too_many_arguments)]
    pub fn from_values(
        packet_format: u16,
        tyres_wear: [f32; 4],
        tyres_damage: [u8; 4],
        brakes_damage: [u8; 4],
        tyre_blisters: [u8; 4],
        front_left_wing_damage: u8,
        front_right_wing_damage: u8,
        rear_wing_damage: u8,
        floor_damage: u8,
        diffuser_damage: u8,
        sidepod_damage: u8,
        drs_fault: bool,
        ers_fault: bool,
        gear_box_damage: u8,
        engine_damage: u8,
        engine_mguh_wear: u8,
        engine_es_wear: u8,
        engine_ce_wear: u8,
        engine_ice_wear: u8,
        engine_mguk_wear: u8,
        engine_tc_wear: u8,
        engine_blown: bool,
        engine_seized: bool,
    ) -> Self {
        Self {
            packet_format,
            tyres_wear,
            tyres_damage,
            brakes_damage,
            tyre_blisters,
            front_left_wing_damage,
            front_right_wing_damage,
            rear_wing_damage,
            floor_damage,
            diffuser_damage,
            sidepod_damage,
            drs_fault,
            ers_fault,
            gear_box_damage,
            engine_damage,
            engine_mguh_wear,
            engine_es_wear,
            engine_ce_wear,
            engine_ice_wear,
            engine_mguk_wear,
            engine_tc_wear,
            engine_blown,
            engine_seized,
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
        let read_f32 = |data: &[u8], offset: &mut usize| {
            let value = f32::from_le_bytes(
                data[*offset..*offset + 4]
                    .try_into()
                    .expect("fixed slice length"),
            );
            *offset += 4;
            value
        };
        let read_u8 = |data: &[u8], offset: &mut usize| {
            let value = data[*offset];
            *offset += 1;
            value
        };

        let tyres_wear = [
            read_f32(data, &mut offset),
            read_f32(data, &mut offset),
            read_f32(data, &mut offset),
            read_f32(data, &mut offset),
        ];
        let tyres_damage = [
            read_u8(data, &mut offset),
            read_u8(data, &mut offset),
            read_u8(data, &mut offset),
            read_u8(data, &mut offset),
        ];
        let brakes_damage = [
            read_u8(data, &mut offset),
            read_u8(data, &mut offset),
            read_u8(data, &mut offset),
            read_u8(data, &mut offset),
        ];
        let tyre_blisters = if packet_format >= 2025 {
            [
                read_u8(data, &mut offset),
                read_u8(data, &mut offset),
                read_u8(data, &mut offset),
                read_u8(data, &mut offset),
            ]
        } else {
            [0; 4]
        };

        Ok(Self {
            packet_format,
            tyres_wear,
            tyres_damage,
            brakes_damage,
            tyre_blisters,
            front_left_wing_damage: read_u8(data, &mut offset),
            front_right_wing_damage: read_u8(data, &mut offset),
            rear_wing_damage: read_u8(data, &mut offset),
            floor_damage: read_u8(data, &mut offset),
            diffuser_damage: read_u8(data, &mut offset),
            sidepod_damage: read_u8(data, &mut offset),
            drs_fault: read_u8(data, &mut offset) != 0,
            ers_fault: read_u8(data, &mut offset) != 0,
            gear_box_damage: read_u8(data, &mut offset),
            engine_damage: read_u8(data, &mut offset),
            engine_mguh_wear: read_u8(data, &mut offset),
            engine_es_wear: read_u8(data, &mut offset),
            engine_ce_wear: read_u8(data, &mut offset),
            engine_ice_wear: read_u8(data, &mut offset),
            engine_mguk_wear: read_u8(data, &mut offset),
            engine_tc_wear: read_u8(data, &mut offset),
            engine_blown: read_u8(data, &mut offset) != 0,
            engine_seized: read_u8(data, &mut offset) != 0,
        })
    }

    pub fn to_bytes(&self) -> Vec<u8> {
        let mut bytes = Vec::with_capacity(Self::packet_len_for_format(self.packet_format));
        for value in self.tyres_wear {
            bytes.extend_from_slice(&value.to_le_bytes());
        }
        bytes.extend_from_slice(&self.tyres_damage);
        bytes.extend_from_slice(&self.brakes_damage);
        if self.packet_format >= 2025 {
            bytes.extend_from_slice(&self.tyre_blisters);
        }
        bytes.push(self.front_left_wing_damage);
        bytes.push(self.front_right_wing_damage);
        bytes.push(self.rear_wing_damage);
        bytes.push(self.floor_damage);
        bytes.push(self.diffuser_damage);
        bytes.push(self.sidepod_damage);
        bytes.push(self.drs_fault as u8);
        bytes.push(self.ers_fault as u8);
        bytes.push(self.gear_box_damage);
        bytes.push(self.engine_damage);
        bytes.push(self.engine_mguh_wear);
        bytes.push(self.engine_es_wear);
        bytes.push(self.engine_ce_wear);
        bytes.push(self.engine_ice_wear);
        bytes.push(self.engine_mguk_wear);
        bytes.push(self.engine_tc_wear);
        bytes.push(self.engine_blown as u8);
        bytes.push(self.engine_seized as u8);
        bytes
    }
}

impl fmt::Display for CarDamageData {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "Tyres Wear: {:?}, Tyres Damage: {:?}, Brakes Damage: {:?}, Front Left Wing Damage: {}, Front Right Wing Damage: {}, Rear Wing Damage: {}, Floor Damage: {}, Diffuser Damage: {}, Sidepod Damage: {}, DRS Fault: {}, ERS Fault: {}, Gear Box Damage: {}, Engine Damage: {}, Engine MGU-H Wear: {}, Engine ES Wear: {}, Engine CE Wear: {}, Engine ICE Wear: {}, Engine MGU-K Wear: {}, Engine TC Wear: {}, Engine Blown: {}, Engine Seized: {}",
            self.tyres_wear,
            self.tyres_damage,
            self.brakes_damage,
            self.front_left_wing_damage,
            self.front_right_wing_damage,
            self.rear_wing_damage,
            self.floor_damage,
            self.diffuser_damage,
            self.sidepod_damage,
            self.drs_fault,
            self.ers_fault,
            self.gear_box_damage,
            self.engine_damage,
            self.engine_mguh_wear,
            self.engine_es_wear,
            self.engine_ce_wear,
            self.engine_ice_wear,
            self.engine_mguk_wear,
            self.engine_tc_wear,
            self.engine_blown,
            self.engine_seized
        )
    }
}

impl Serialize for CarDamageData {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let mut map = serializer.serialize_map(Some(21))?;
        map.serialize_entry("tyres-wear", &self.tyres_wear)?;
        map.serialize_entry("tyres-damage", &self.tyres_damage)?;
        map.serialize_entry("brakes-damage", &self.brakes_damage)?;
        map.serialize_entry("front-left-wing-damage", &self.front_left_wing_damage)?;
        map.serialize_entry("front-right-wing-damage", &self.front_right_wing_damage)?;
        map.serialize_entry("rear-wing-damage", &self.rear_wing_damage)?;
        map.serialize_entry("floor-damage", &self.floor_damage)?;
        map.serialize_entry("diffuser-damage", &self.diffuser_damage)?;
        map.serialize_entry("sidepod-damage", &self.sidepod_damage)?;
        map.serialize_entry("drs-fault", &self.drs_fault)?;
        map.serialize_entry("ers-fault", &self.ers_fault)?;
        map.serialize_entry("gear-box-damage", &self.gear_box_damage)?;
        map.serialize_entry("engine-damage", &self.engine_damage)?;
        map.serialize_entry("engine-mguh-wear", &self.engine_mguh_wear)?;
        map.serialize_entry("engine-es-wear", &self.engine_es_wear)?;
        map.serialize_entry("engine-ce-wear", &self.engine_ce_wear)?;
        map.serialize_entry("engine-ice-wear", &self.engine_ice_wear)?;
        map.serialize_entry("engine-mguk-wear", &self.engine_mguk_wear)?;
        map.serialize_entry("engine-tc-wear", &self.engine_tc_wear)?;
        map.serialize_entry("engine-blown", &self.engine_blown)?;
        map.serialize_entry("engine-seized", &self.engine_seized)?;
        map.end()
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct PacketCarDamageData {
    pub header: PacketHeader,
    pub car_damage_data: Vec<CarDamageData>,
}

impl PacketCarDamageData {
    pub const MAX_CARS: usize = 22;

    pub fn parse(header: PacketHeader, data: &[u8]) -> Result<Self, InvalidPacketLengthError> {
        let packet_len = CarDamageData::packet_len_for_format(header.packet_format);
        let expected_len = Self::MAX_CARS * packet_len;
        if data.len() != expected_len {
            return Err(InvalidPacketLengthError::new(format!(
                "Received packet length {} is not equal to expected {}",
                data.len(),
                expected_len
            )));
        }

        let car_damage_data = data
            .chunks_exact(packet_len)
            .map(|chunk| CarDamageData::parse(chunk, header.packet_format))
            .collect::<Result<Vec<_>, _>>()?;

        Ok(Self {
            header,
            car_damage_data,
        })
    }

    pub fn from_values(header: PacketHeader, car_damage_data: Vec<CarDamageData>) -> Self {
        Self {
            header,
            car_damage_data,
        }
    }

    pub fn to_bytes(&self) -> Vec<u8> {
        let packet_len = CarDamageData::packet_len_for_format(self.header.packet_format);
        let mut bytes = Vec::with_capacity(
            PacketHeader::PACKET_LEN + (self.car_damage_data.len() * packet_len),
        );
        bytes.extend_from_slice(&self.header.to_bytes());
        for car in &self.car_damage_data {
            bytes.extend_from_slice(&car.to_bytes());
        }
        bytes
    }
}

impl fmt::Display for PacketCarDamageData {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "Header: {}, Car Damage Data: {:?}",
            self.header, self.car_damage_data
        )
    }
}

impl Serialize for PacketCarDamageData {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let mut map = serializer.serialize_map(Some(1))?;
        map.serialize_entry("car-damage-data", &self.car_damage_data)?;
        map.end()
    }
}
