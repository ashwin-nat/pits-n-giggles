use crate::errors::InvalidPacketLengthError;
use crate::{ActualTyreCompound, PacketHeader, TractionControlAssistMode, VisualTyreCompound};
use serde::Serialize;
use serde::ser::{SerializeMap, Serializer};
use std::fmt;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum VehicleFiaFlags {
    InvalidUnknown = -1,
    None = 0,
    Green = 1,
    Blue = 2,
    Yellow = 3,
}

impl VehicleFiaFlags {
    pub fn from_raw(value: i8) -> Self {
        match value {
            -1 => Self::InvalidUnknown,
            0 => Self::None,
            1 => Self::Green,
            2 => Self::Blue,
            3 => Self::Yellow,
            _ => Self::InvalidUnknown,
        }
    }
}

impl fmt::Display for VehicleFiaFlags {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(match self {
            Self::InvalidUnknown => "Invalid/Unknown",
            Self::None => "None",
            Self::Green => "Green",
            Self::Blue => "Blue",
            Self::Yellow => "Yellow",
        })
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ErsDeployMode {
    None = 0,
    Medium = 1,
    Hotlap = 2,
    Overtake = 3,
}

impl ErsDeployMode {
    pub fn from_raw(value: u8) -> Self {
        match value {
            1 => Self::Medium,
            2 => Self::Hotlap,
            3 => Self::Overtake,
            _ => Self::None,
        }
    }
}

impl fmt::Display for ErsDeployMode {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(match self {
            Self::None => "None",
            Self::Medium => "Medium",
            Self::Hotlap => "Hotlap",
            Self::Overtake => "Overtake",
        })
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum FuelMix {
    Lean = 0,
    Standard = 1,
    Rich = 2,
    Max = 3,
}

impl FuelMix {
    pub fn from_raw(value: u8) -> Self {
        match value {
            1 => Self::Standard,
            2 => Self::Rich,
            3 => Self::Max,
            _ => Self::Lean,
        }
    }
}

impl fmt::Display for FuelMix {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(match self {
            Self::Lean => "Lean",
            Self::Standard => "Standard",
            Self::Rich => "Rich",
            Self::Max => "Max",
        })
    }
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct CarStatusData {
    pub traction_control: TractionControlAssistMode,
    pub anti_lock_brakes: bool,
    pub fuel_mix: FuelMix,
    pub front_brake_bias: u8,
    pub pit_limiter_status: bool,
    pub fuel_in_tank: f32,
    pub fuel_capacity: f32,
    pub fuel_remaining_laps: f32,
    pub max_rpm: u16,
    pub idle_rpm: u16,
    pub max_gears: u8,
    pub drs_allowed: u8,
    pub drs_activation_distance: u16,
    pub actual_tyre_compound: ActualTyreCompound,
    pub visual_tyre_compound: VisualTyreCompound,
    pub tyres_age_laps: u8,
    pub vehicle_fia_flags: VehicleFiaFlags,
    pub engine_power_ice: f32,
    pub engine_power_mguk: f32,
    pub ers_store_energy: f32,
    pub ers_deploy_mode: ErsDeployMode,
    pub ers_harvested_this_lap_mguk: f32,
    pub ers_harvested_this_lap_mguh: f32,
    pub ers_deployed_this_lap: f32,
    pub network_paused: bool,
}

impl CarStatusData {
    pub const MIN_FUEL_KG: f32 = 0.2;
    pub const MAX_ERS_STORE_ENERGY: f32 = 4_000_000.0;
    pub const PACKET_LEN: usize = 55;

    #[allow(clippy::too_many_arguments)]
    pub fn from_values(
        traction_control: TractionControlAssistMode,
        anti_lock_brakes: bool,
        fuel_mix: FuelMix,
        front_brake_bias: u8,
        pit_limiter_status: bool,
        fuel_in_tank: f32,
        fuel_capacity: f32,
        fuel_remaining_laps: f32,
        max_rpm: u16,
        idle_rpm: u16,
        max_gears: u8,
        drs_allowed: u8,
        drs_activation_distance: u16,
        actual_tyre_compound: ActualTyreCompound,
        visual_tyre_compound: VisualTyreCompound,
        tyres_age_laps: u8,
        vehicle_fia_flags: VehicleFiaFlags,
        engine_power_ice: f32,
        engine_power_mguk: f32,
        ers_store_energy: f32,
        ers_deploy_mode: ErsDeployMode,
        ers_harvested_this_lap_mguk: f32,
        ers_harvested_this_lap_mguh: f32,
        ers_deployed_this_lap: f32,
        network_paused: bool,
    ) -> Self {
        Self {
            traction_control,
            anti_lock_brakes,
            fuel_mix,
            front_brake_bias,
            pit_limiter_status,
            fuel_in_tank,
            fuel_capacity,
            fuel_remaining_laps,
            max_rpm,
            idle_rpm,
            max_gears,
            drs_allowed,
            drs_activation_distance,
            actual_tyre_compound,
            visual_tyre_compound,
            tyres_age_laps,
            vehicle_fia_flags,
            engine_power_ice,
            engine_power_mguk,
            ers_store_energy,
            ers_deploy_mode,
            ers_harvested_this_lap_mguk,
            ers_harvested_this_lap_mguh,
            ers_deployed_this_lap,
            network_paused,
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
            traction_control: TractionControlAssistMode::try_from(read_u8(data, &mut offset))
                .unwrap_or(TractionControlAssistMode::Off),
            anti_lock_brakes: read_u8(data, &mut offset) != 0,
            fuel_mix: FuelMix::from_raw(read_u8(data, &mut offset)),
            front_brake_bias: read_u8(data, &mut offset),
            pit_limiter_status: read_u8(data, &mut offset) != 0,
            fuel_in_tank: read_f32(data, &mut offset),
            fuel_capacity: read_f32(data, &mut offset),
            fuel_remaining_laps: read_f32(data, &mut offset),
            max_rpm: read_u16(data, &mut offset),
            idle_rpm: read_u16(data, &mut offset),
            max_gears: read_u8(data, &mut offset),
            drs_allowed: read_u8(data, &mut offset),
            drs_activation_distance: read_u16(data, &mut offset),
            actual_tyre_compound: ActualTyreCompound::from_raw(read_u8(data, &mut offset)),
            visual_tyre_compound: VisualTyreCompound::from_raw(read_u8(data, &mut offset)),
            tyres_age_laps: read_u8(data, &mut offset),
            vehicle_fia_flags: VehicleFiaFlags::from_raw(read_i8(data, &mut offset)),
            engine_power_ice: read_f32(data, &mut offset),
            engine_power_mguk: read_f32(data, &mut offset),
            ers_store_energy: read_f32(data, &mut offset),
            ers_deploy_mode: ErsDeployMode::from_raw(read_u8(data, &mut offset)),
            ers_harvested_this_lap_mguk: read_f32(data, &mut offset),
            ers_harvested_this_lap_mguh: read_f32(data, &mut offset),
            ers_deployed_this_lap: read_f32(data, &mut offset),
            network_paused: read_u8(data, &mut offset) != 0,
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

        write_u8(&mut bytes, &mut offset, self.traction_control as u8);
        write_u8(&mut bytes, &mut offset, self.anti_lock_brakes as u8);
        write_u8(&mut bytes, &mut offset, self.fuel_mix as u8);
        write_u8(&mut bytes, &mut offset, self.front_brake_bias);
        write_u8(&mut bytes, &mut offset, self.pit_limiter_status as u8);
        write_f32(&mut bytes, &mut offset, self.fuel_in_tank);
        write_f32(&mut bytes, &mut offset, self.fuel_capacity);
        write_f32(&mut bytes, &mut offset, self.fuel_remaining_laps);
        write_u16(&mut bytes, &mut offset, self.max_rpm);
        write_u16(&mut bytes, &mut offset, self.idle_rpm);
        write_u8(&mut bytes, &mut offset, self.max_gears);
        write_u8(&mut bytes, &mut offset, self.drs_allowed);
        write_u16(&mut bytes, &mut offset, self.drs_activation_distance);
        write_u8(&mut bytes, &mut offset, self.actual_tyre_compound as u8);
        write_u8(&mut bytes, &mut offset, self.visual_tyre_compound as u8);
        write_u8(&mut bytes, &mut offset, self.tyres_age_laps);
        write_i8(&mut bytes, &mut offset, self.vehicle_fia_flags as i8);
        write_f32(&mut bytes, &mut offset, self.engine_power_ice);
        write_f32(&mut bytes, &mut offset, self.engine_power_mguk);
        write_f32(&mut bytes, &mut offset, self.ers_store_energy);
        write_u8(&mut bytes, &mut offset, self.ers_deploy_mode as u8);
        write_f32(&mut bytes, &mut offset, self.ers_harvested_this_lap_mguk);
        write_f32(&mut bytes, &mut offset, self.ers_harvested_this_lap_mguh);
        write_f32(&mut bytes, &mut offset, self.ers_deployed_this_lap);
        write_u8(&mut bytes, &mut offset, self.network_paused as u8);
        bytes
    }
}

impl fmt::Display for CarStatusData {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "CarStatusData(m_tractionControl={}, m_antiLockBrakes={}, m_fuelMix={}, m_frontBrakeBias={}, m_pitLimiterStatus={}, m_fuelInTank={}, m_fuelCapacity={}, m_fuelRemainingLaps={}, m_maxRPM={}, m_idleRPM={}, m_maxGears={}, m_drsAllowed={}, m_drsActivationDistance={}, m_actualTyreCompound={}, m_visualTyreCompound={}, m_tyresAgeLaps={}, m_vehicleFiaFlags={}, m_enginePowerICE={}, m_enginePowerMGUK={}, m_ersStoreEnergy={}, m_ersDeployMode={}, m_ersHarvestedThisLapMGUK={}, m_ersHarvestedThisLapMGUH={}, m_ersDeployedThisLap={}, m_networkPaused={})",
            self.traction_control,
            self.anti_lock_brakes,
            self.fuel_mix,
            self.front_brake_bias,
            self.pit_limiter_status,
            self.fuel_in_tank,
            self.fuel_capacity,
            self.fuel_remaining_laps,
            self.max_rpm,
            self.idle_rpm,
            self.max_gears,
            self.drs_allowed,
            self.drs_activation_distance,
            self.actual_tyre_compound,
            self.visual_tyre_compound,
            self.tyres_age_laps,
            self.vehicle_fia_flags,
            self.engine_power_ice,
            self.engine_power_mguk,
            self.ers_store_energy,
            self.ers_deploy_mode,
            self.ers_harvested_this_lap_mguk,
            self.ers_harvested_this_lap_mguh,
            self.ers_deployed_this_lap,
            self.network_paused
        )
    }
}

impl Serialize for CarStatusData {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let mut map = serializer.serialize_map(Some(26))?;
        map.serialize_entry("traction-control", &self.traction_control.to_string())?;
        map.serialize_entry("anti-lock-brakes", &self.anti_lock_brakes)?;
        map.serialize_entry("fuel-mix", &self.fuel_mix.to_string())?;
        map.serialize_entry("front-brake-bias", &self.front_brake_bias)?;
        map.serialize_entry("pit-limiter-status", &self.pit_limiter_status)?;
        map.serialize_entry("fuel-in-tank", &self.fuel_in_tank)?;
        map.serialize_entry("fuel-capacity", &self.fuel_capacity)?;
        map.serialize_entry("fuel-remaining-laps", &self.fuel_remaining_laps)?;
        map.serialize_entry("max-rpm", &self.max_rpm)?;
        map.serialize_entry("idle-rpm", &self.idle_rpm)?;
        map.serialize_entry("max-gears", &self.max_gears)?;
        map.serialize_entry("drs-allowed", &self.drs_allowed)?;
        map.serialize_entry("drs-activation-distance", &self.drs_activation_distance)?;
        map.serialize_entry(
            "actual-tyre-compound",
            &self.actual_tyre_compound.to_string(),
        )?;
        map.serialize_entry(
            "visual-tyre-compound",
            &self.visual_tyre_compound.to_string(),
        )?;
        map.serialize_entry("tyres-age-laps", &self.tyres_age_laps)?;
        map.serialize_entry("vehicle-fia-flags", &self.vehicle_fia_flags.to_string())?;
        map.serialize_entry("engine-power-ice", &self.engine_power_ice)?;
        map.serialize_entry("engine-power-mguk", &self.engine_power_mguk)?;
        map.serialize_entry("ers-store-energy", &self.ers_store_energy)?;
        map.serialize_entry("ers-deploy-mode", &self.ers_deploy_mode.to_string())?;
        map.serialize_entry(
            "ers-harvested-this-lap-mguk",
            &self.ers_harvested_this_lap_mguk,
        )?;
        map.serialize_entry(
            "ers-harvested-this-lap-mguh",
            &self.ers_harvested_this_lap_mguh,
        )?;
        map.serialize_entry("ers-deployed-this-lap", &self.ers_deployed_this_lap)?;
        map.serialize_entry("ers-max-capacity", &Self::MAX_ERS_STORE_ENERGY)?;
        map.serialize_entry("network-paused", &self.network_paused)?;
        map.end()
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct PacketCarStatusData {
    pub header: PacketHeader,
    pub car_status_data: Vec<CarStatusData>,
}

impl PacketCarStatusData {
    pub const MAX_CARS: usize = 22;
    pub const PAYLOAD_LEN: usize = Self::MAX_CARS * CarStatusData::PACKET_LEN;

    pub fn parse(header: PacketHeader, packet: &[u8]) -> Result<Self, InvalidPacketLengthError> {
        if packet.len() != Self::PAYLOAD_LEN {
            return Err(InvalidPacketLengthError::new(format!(
                "Received packet length {} is not equal to expected {}",
                packet.len(),
                Self::PAYLOAD_LEN
            )));
        }

        let car_status_data = packet
            .chunks_exact(CarStatusData::PACKET_LEN)
            .map(CarStatusData::parse)
            .collect::<Result<Vec<_>, _>>()?;

        Ok(Self {
            header,
            car_status_data,
        })
    }

    pub fn from_values(header: PacketHeader, car_status_data: Vec<CarStatusData>) -> Self {
        Self {
            header,
            car_status_data,
        }
    }

    pub fn to_bytes(&self) -> Vec<u8> {
        let mut bytes = Vec::with_capacity(PacketHeader::PACKET_LEN + Self::PAYLOAD_LEN);
        bytes.extend_from_slice(&self.header.to_bytes());
        for car in &self.car_status_data {
            bytes.extend_from_slice(&car.to_bytes());
        }
        bytes
    }
}

impl fmt::Display for PacketCarStatusData {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let status = self
            .car_status_data
            .iter()
            .map(ToString::to_string)
            .collect::<Vec<_>>()
            .join(", ");
        write!(
            f,
            "PacketCarStatusData(Header: {}, Car Status Data: [{}])",
            self.header, status
        )
    }
}

impl Serialize for PacketCarStatusData {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let mut map = serializer.serialize_map(Some(1))?;
        map.serialize_entry("car-status-data", &self.car_status_data)?;
        map.end()
    }
}
