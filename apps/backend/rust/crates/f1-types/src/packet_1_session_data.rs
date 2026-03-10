use crate::errors::{InvalidPacketLengthError, PacketCountValidationError};
use crate::{PacketHeader, SessionType23, SessionType24};
use serde::Serialize;
use serde::ser::{SerializeMap, Serializer};
use std::fmt;

fn session_type_label(packet_format: u16, value: u8) -> String {
    if packet_format == 2023 {
        SessionType23::try_from(value)
            .map(|session| session.to_string())
            .unwrap_or_else(|_| value.to_string())
    } else {
        SessionType24::try_from(value)
            .map(|session| session.to_string())
            .unwrap_or_else(|_| value.to_string())
    }
}

fn weather_label(value: u8) -> String {
    match value {
        0 => "Clear",
        1 => "Light Cloud",
        2 => "Overcast",
        3 => "Light Rain",
        4 => "Heavy Rain",
        5 => "Storm",
        6 => "Thunderstorm",
        _ => return value.to_string(),
    }
    .to_string()
}

fn temperature_change_label(value: i8) -> String {
    match value {
        0 => "Temperature Up",
        1 => "Temperature Down",
        2 => "No Temperature Change",
        _ => return value.to_string(),
    }
    .to_string()
}

fn marshal_zone_flag_label(value: i8) -> String {
    match value {
        -1 => "INVALID_UNKNOWN",
        0 => "NONE",
        1 => "GREEN_FLAG",
        2 => "BLUE_FLAG",
        3 => "YELLOW_FLAG",
        _ => return value.to_string(),
    }
    .to_string()
}

fn safety_car_type_label(value: u8) -> String {
    match value {
        0 => "NO_SAFETY_CAR",
        1 => "FULL_SAFETY_CAR",
        2 => "VIRTUAL_SAFETY_CAR",
        3 => "FORMATION_LAP",
        _ => return value.to_string(),
    }
    .to_string()
}

fn formula_label(value: u8) -> String {
    match value {
        0 => "F1 Modern",
        1 => "F1 Classic",
        2 => "F2",
        3 => "F1 Generic",
        4 => "Beta",
        5 => "Supercars",
        6 => "Esports",
        7 => "F2 2021",
        8 => "F1 World",
        9 => "F1 Elimination",
        _ => return value.to_string(),
    }
    .to_string()
}

fn gearbox_assist_label(value: u8) -> String {
    match value {
        0 => "Unknown",
        1 => "Manual",
        2 => "Manual With Suggested Gear",
        3 => "Auto",
        _ => return value.to_string(),
    }
    .to_string()
}

fn track_id_label(value: i8) -> String {
    match value {
        0 => "Melbourne",
        1 => "Paul Ricard",
        2 => "Shanghai",
        3 => "Sakhir",
        4 => "Catalunya",
        5 => "Monaco",
        6 => "Montreal",
        7 => "Silverstone",
        8 => "Hockenheim",
        9 => "Hungaroring",
        10 => "Spa",
        11 => "Monza",
        12 => "Singapore",
        13 => "Suzuka",
        14 => "Abu Dhabi",
        15 => "Texas",
        16 => "Brazil",
        17 => "Austria",
        18 => "Sochi",
        19 => "Mexico",
        20 => "Baku",
        21 => "Sakhir Short",
        22 => "Silverstone Short",
        23 => "Texas Short",
        24 => "Suzuka Short",
        25 => "Hanoi",
        26 => "Zandvoort",
        27 => "Imola",
        28 => "Portimao",
        29 => "Jeddah",
        30 => "Miami",
        31 => "Las Vegas",
        32 => "Losail",
        39 => "Silverstone_Reverse",
        40 => "Austria_Reverse",
        41 => "Zandvoort_Reverse",
        _ => return value.to_string(),
    }
    .to_string()
}

fn game_mode_label(value: u8) -> String {
    match value {
        0 => "Event Mode",
        3 => "Grand Prix",
        4 => "Grand Prix 23",
        5 => "Time Trial",
        6 => "Splitscreen",
        7 => "Online Custom",
        8 => "Online League",
        11 => "Career Invitational",
        12 => "Championship Invitational",
        13 => "Championship",
        14 => "Online Championship",
        15 => "Online Weekly Event",
        17 => "Story Mode",
        19 => "Career 22",
        20 => "Career 22 Online",
        21 => "Career 23",
        22 => "Career 23 Online",
        23 => "Driver Career 24",
        24 => "Career 24 Online",
        25 => "My Team Career 24",
        26 => "Curated Career 24",
        27 => "My Team Career 25",
        28 => "Driver Career 25",
        29 => "Career 25 Online",
        30 => "Challenge Career",
        75 => "Apex Story",
        127 => "Benchmark",
        _ => return value.to_string(),
    }
    .to_string()
}

fn rule_set_label(value: u8) -> String {
    match value {
        0 => "Practice & Qualifying",
        1 => "Race",
        2 => "Time Trial",
        4 => "Time Attack",
        6 => "Checkpoint Challenge",
        8 => "Autocross",
        9 => "Drift",
        10 => "Average Speed Zone",
        11 => "Rival Duel",
        _ => return value.to_string(),
    }
    .to_string()
}

fn session_length_label(value: u8) -> String {
    match value {
        0 => "None",
        2 => "Very Short",
        3 => "Short",
        4 => "Medium",
        5 => "Medium Long",
        6 => "Long",
        7 => "Full",
        _ => return value.to_string(),
    }
    .to_string()
}

fn recovery_mode_label(value: u8) -> String {
    match value {
        0 => "NONE",
        1 => "FLASHBACKS",
        2 => "AUTO_RECOVERY",
        _ => return value.to_string(),
    }
    .to_string()
}

fn flashback_limit_label(value: u8) -> String {
    match value {
        0 => "LOW",
        1 => "MEDIUM",
        2 => "HIGH",
        3 => "UNLIMITED",
        _ => return value.to_string(),
    }
    .to_string()
}

fn surface_type_label(value: u8) -> String {
    match value {
        0 => "SIMPLIFIED",
        1 => "REALISTIC",
        _ => return value.to_string(),
    }
    .to_string()
}

fn low_fuel_mode_label(value: u8) -> String {
    match value {
        0 => "EASY",
        1 => "HARD",
        _ => return value.to_string(),
    }
    .to_string()
}

fn race_starts_label(value: u8) -> String {
    match value {
        0 => "MANUAL",
        1 => "ASSISTED",
        _ => return value.to_string(),
    }
    .to_string()
}

fn tyre_temperature_mode_label(value: u8) -> String {
    match value {
        0 => "SURFACE_ONLY",
        1 => "SURFACE_AND_CARCASS",
        _ => return value.to_string(),
    }
    .to_string()
}

fn car_damage_mode_label(value: u8) -> String {
    match value {
        0 => "OFF",
        1 => "REDUCED",
        2 => "STANDARD",
        3 => "SIMULATION",
        _ => return value.to_string(),
    }
    .to_string()
}

fn car_damage_rate_label(value: u8) -> String {
    match value {
        0 => "REDUCED",
        1 => "STANDARD",
        2 => "SIMULATION",
        _ => return value.to_string(),
    }
    .to_string()
}

fn collisions_mode_label(value: u8) -> String {
    match value {
        0 => "OFF",
        1 => "PLAYER_TO_PLAYER_OFF",
        2 => "ON",
        _ => return value.to_string(),
    }
    .to_string()
}

fn corner_cutting_label(value: u8) -> String {
    match value {
        0 => "REGULAR",
        1 => "STRICT",
        _ => return value.to_string(),
    }
    .to_string()
}

fn pit_stop_experience_label(value: u8) -> String {
    match value {
        0 => "AUTOMATIC",
        1 => "BROADCAST",
        2 => "IMMERSIVE",
        _ => return value.to_string(),
    }
    .to_string()
}

fn safety_car_setting_label(value: u8) -> String {
    match value {
        0 => "OFF",
        1 => "REDUCED",
        2 => "STANDARD",
        3 => "INCREASED",
        _ => return value.to_string(),
    }
    .to_string()
}

fn safety_car_experience_label(value: u8) -> String {
    match value {
        0 => "BROADCAST",
        1 => "IMMERSIVE",
        _ => return value.to_string(),
    }
    .to_string()
}

fn red_flags_setting_label(value: u8) -> String {
    match value {
        0 => "OFF",
        1 => "REDUCED",
        2 => "STANDARD",
        3 => "INCREASED",
        _ => return value.to_string(),
    }
    .to_string()
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum SessionDataError {
    InvalidPacketLength(InvalidPacketLengthError),
    InvalidCount(PacketCountValidationError),
}

impl fmt::Display for SessionDataError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::InvalidPacketLength(error) => write!(f, "{error}"),
            Self::InvalidCount(error) => write!(f, "{error}"),
        }
    }
}

impl std::error::Error for SessionDataError {}

impl From<InvalidPacketLengthError> for SessionDataError {
    fn from(value: InvalidPacketLengthError) -> Self {
        Self::InvalidPacketLength(value)
    }
}

impl From<PacketCountValidationError> for SessionDataError {
    fn from(value: PacketCountValidationError) -> Self {
        Self::InvalidCount(value)
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct MarshalZone {
    pub zone_start: f32,
    pub zone_flag_raw: i8,
}

impl MarshalZone {
    pub const PACKET_LEN: usize = 5;

    pub fn parse(data: &[u8]) -> Result<Self, InvalidPacketLengthError> {
        if data.len() != Self::PACKET_LEN {
            return Err(InvalidPacketLengthError::new(format!(
                "Received packet length {} expected {}",
                data.len(),
                Self::PACKET_LEN
            )));
        }

        Ok(Self {
            zone_start: f32::from_le_bytes(data[0..4].try_into().expect("fixed slice length")),
            zone_flag_raw: i8::from_le_bytes([data[4]]),
        })
    }

    pub fn to_bytes(&self) -> [u8; Self::PACKET_LEN] {
        let mut bytes = [0u8; Self::PACKET_LEN];
        bytes[0..4].copy_from_slice(&self.zone_start.to_le_bytes());
        bytes[4] = self.zone_flag_raw as u8;
        bytes
    }
}

impl Serialize for MarshalZone {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let mut map = serializer.serialize_map(Some(2))?;
        map.serialize_entry("zone-start", &self.zone_start)?;
        map.serialize_entry("zone-flag", &marshal_zone_flag_label(self.zone_flag_raw))?;
        map.end()
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct WeatherForecastSample {
    pub packet_format: u16,
    pub session_type_raw: u8,
    pub time_offset: u8,
    pub weather_raw: u8,
    pub track_temperature: i8,
    pub track_temperature_change_raw: i8,
    pub air_temperature: i8,
    pub air_temperature_change_raw: i8,
    pub rain_percentage: u8,
}

impl WeatherForecastSample {
    pub const PACKET_LEN: usize = 8;

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
            session_type_raw: data[0],
            time_offset: data[1],
            weather_raw: data[2],
            track_temperature: i8::from_le_bytes([data[3]]),
            track_temperature_change_raw: i8::from_le_bytes([data[4]]),
            air_temperature: i8::from_le_bytes([data[5]]),
            air_temperature_change_raw: i8::from_le_bytes([data[6]]),
            rain_percentage: data[7],
        })
    }

    pub fn to_bytes(&self) -> [u8; Self::PACKET_LEN] {
        [
            self.session_type_raw,
            self.time_offset,
            self.weather_raw,
            self.track_temperature as u8,
            self.track_temperature_change_raw as u8,
            self.air_temperature as u8,
            self.air_temperature_change_raw as u8,
            self.rain_percentage,
        ]
    }
}

impl Serialize for WeatherForecastSample {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let mut map = serializer.serialize_map(Some(8))?;
        map.serialize_entry(
            "session-type",
            &session_type_label(self.packet_format, self.session_type_raw),
        )?;
        map.serialize_entry("time-offset", &self.time_offset)?;
        map.serialize_entry("weather", &weather_label(self.weather_raw))?;
        map.serialize_entry("track-temperature", &self.track_temperature)?;
        map.serialize_entry(
            "track-temperature-change",
            &temperature_change_label(self.track_temperature_change_raw),
        )?;
        map.serialize_entry("air-temperature", &self.air_temperature)?;
        map.serialize_entry(
            "air-temperature-change",
            &temperature_change_label(self.air_temperature_change_raw),
        )?;
        map.serialize_entry("rain-percentage", &self.rain_percentage)?;
        map.end()
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct PacketSessionData {
    pub header: PacketHeader,
    pub weather_raw: u8,
    pub track_temperature: i8,
    pub air_temperature: i8,
    pub total_laps: i8,
    pub track_length: u16,
    pub session_type_raw: u8,
    pub track_id_raw: i8,
    pub formula_raw: u8,
    pub session_time_left: u16,
    pub session_duration: u16,
    pub pit_speed_limit: u8,
    pub game_paused: u8,
    pub is_spectating: bool,
    pub spectator_car_index: u8,
    pub sli_pro_native_support: u8,
    pub num_marshal_zones: u8,
    pub marshal_zones: Vec<MarshalZone>,
    pub safety_car_status_raw: u8,
    pub network_game: u8,
    pub num_weather_forecast_samples: u8,
    pub weather_forecast_samples: Vec<WeatherForecastSample>,
    pub forecast_accuracy: u8,
    pub ai_difficulty: u8,
    pub season_link_identifier: u32,
    pub weekend_link_identifier: u32,
    pub session_link_identifier: u32,
    pub pit_stop_window_ideal_lap: u8,
    pub pit_stop_window_latest_lap: u8,
    pub pit_stop_rejoin_position: u8,
    pub steering_assist: u8,
    pub braking_assist: u8,
    pub gearbox_assist_raw: u8,
    pub pit_assist: u8,
    pub pit_release_assist: u8,
    pub ers_assist: u8,
    pub drs_assist: u8,
    pub dynamic_racing_line: u8,
    pub dynamic_racing_line_type: u8,
    pub game_mode_raw: u8,
    pub rule_set_raw: u8,
    pub time_of_day: u32,
    pub session_length_raw: u8,
    pub speed_units_lead_player: u8,
    pub temperature_units_lead_player: u8,
    pub speed_units_secondary_player: u8,
    pub temperature_units_secondary_player: u8,
    pub num_safety_car_periods: u8,
    pub num_virtual_safety_car_periods: u8,
    pub num_red_flag_periods: u8,
    pub equal_car_performance: u8,
    pub recovery_mode_raw: u8,
    pub flashback_limit_raw: u8,
    pub surface_type_raw: u8,
    pub low_fuel_mode_raw: u8,
    pub race_starts_raw: u8,
    pub tyre_temperature_mode_raw: u8,
    pub pit_lane_tyre_sim: u8,
    pub car_damage_raw: u8,
    pub car_damage_rate_raw: u8,
    pub collisions_raw: u8,
    pub collisions_off_for_first_lap_only: u8,
    pub mp_unsafe_pit_release: u8,
    pub mp_off_for_griefing: u8,
    pub corner_cutting_stringency_raw: u8,
    pub parc_ferme_rules: u8,
    pub pit_stop_experience_raw: u8,
    pub safety_car_setting_raw: u8,
    pub safety_car_experience_raw: u8,
    pub formation_lap: u8,
    pub formation_lap_experience_raw: u8,
    pub red_flags_setting_raw: u8,
    pub affects_license_level_solo: u8,
    pub affects_license_level_mp: u8,
    pub num_sessions_in_weekend: u8,
    pub weekend_structure: Vec<u8>,
    pub sector2_lap_distance_start: f32,
    pub sector3_lap_distance_start: f32,
    pub raw_section5_2025: Option<[u8; 45]>,
}

impl PacketSessionData {
    pub const MAX_MARSHAL_ZONES: usize = 21;
    pub const MAX_WEATHER_FORECAST_SAMPLES_23: usize = 56;
    pub const MAX_WEATHER_FORECAST_SAMPLES_24: usize = 64;
    pub const SECTION_0_LEN: usize = 19;
    pub const SECTION_2_LEN: usize = 3;
    pub const SECTION_4_LEN: usize = 40;
    pub const SECTION_5_LEN: usize = 45;

    pub fn payload_len_for_format(packet_format: u16) -> usize {
        let weather_count = if packet_format == 2023 {
            Self::MAX_WEATHER_FORECAST_SAMPLES_23
        } else {
            Self::MAX_WEATHER_FORECAST_SAMPLES_24
        };
        Self::SECTION_0_LEN
            + (Self::MAX_MARSHAL_ZONES * MarshalZone::PACKET_LEN)
            + Self::SECTION_2_LEN
            + (weather_count * WeatherForecastSample::PACKET_LEN)
            + Self::SECTION_4_LEN
            + if packet_format >= 2024 {
                Self::SECTION_5_LEN
            } else {
                0
            }
    }

    pub fn parse(header: PacketHeader, data: &[u8]) -> Result<Self, SessionDataError> {
        let expected_len = Self::payload_len_for_format(header.packet_format);
        if data.len() != expected_len {
            return Err(InvalidPacketLengthError::new(format!(
                "Received packet length {} is not equal to expected {}",
                data.len(),
                expected_len
            ))
            .into());
        }

        let max_weather_forecast_samples = if header.packet_format == 2023 {
            Self::MAX_WEATHER_FORECAST_SAMPLES_23
        } else {
            Self::MAX_WEATHER_FORECAST_SAMPLES_24
        };

        let section_0 = &data[..Self::SECTION_0_LEN];
        let mut offset = Self::SECTION_0_LEN;

        let weather_raw = section_0[0];
        let track_temperature = i8::from_le_bytes([section_0[1]]);
        let air_temperature = i8::from_le_bytes([section_0[2]]);
        let total_laps = i8::from_le_bytes([section_0[3]]);
        let track_length = u16::from_le_bytes(section_0[4..6].try_into().expect("fixed slice"));
        let session_type_raw = section_0[6];
        let track_id_raw = i8::from_le_bytes([section_0[7]]);
        let formula_raw = section_0[8];
        let session_time_left =
            u16::from_le_bytes(section_0[9..11].try_into().expect("fixed slice"));
        let session_duration =
            u16::from_le_bytes(section_0[11..13].try_into().expect("fixed slice"));
        let pit_speed_limit = section_0[13];
        let game_paused = section_0[14];
        let is_spectating = section_0[15] != 0;
        let spectator_car_index = section_0[16];
        let sli_pro_native_support = section_0[17];
        let num_marshal_zones = section_0[18];

        if usize::from(num_marshal_zones) > Self::MAX_MARSHAL_ZONES {
            return Err(PacketCountValidationError::new(format!(
                "Too many MarshalZone items: {} > {}",
                num_marshal_zones,
                Self::MAX_MARSHAL_ZONES
            ))
            .into());
        }

        let marshal_raw =
            &data[offset..offset + (Self::MAX_MARSHAL_ZONES * MarshalZone::PACKET_LEN)];
        offset += Self::MAX_MARSHAL_ZONES * MarshalZone::PACKET_LEN;
        let marshal_zones = marshal_raw
            .chunks_exact(MarshalZone::PACKET_LEN)
            .take(usize::from(num_marshal_zones))
            .map(MarshalZone::parse)
            .collect::<Result<Vec<_>, _>>()?;

        let section_2 = &data[offset..offset + Self::SECTION_2_LEN];
        offset += Self::SECTION_2_LEN;
        let safety_car_status_raw = section_2[0];
        let network_game = section_2[1];
        let num_weather_forecast_samples = section_2[2];

        if usize::from(num_weather_forecast_samples) > max_weather_forecast_samples {
            return Err(PacketCountValidationError::new(format!(
                "Too many WeatherForecastSample items: {} > {}",
                num_weather_forecast_samples, max_weather_forecast_samples
            ))
            .into());
        }

        let weather_raw_block = &data
            [offset..offset + (max_weather_forecast_samples * WeatherForecastSample::PACKET_LEN)];
        offset += max_weather_forecast_samples * WeatherForecastSample::PACKET_LEN;
        let weather_forecast_samples = weather_raw_block
            .chunks_exact(WeatherForecastSample::PACKET_LEN)
            .take(usize::from(num_weather_forecast_samples))
            .map(|chunk| WeatherForecastSample::parse(chunk, header.packet_format))
            .collect::<Result<Vec<_>, _>>()?;

        let section_4 = &data[offset..offset + Self::SECTION_4_LEN];
        offset += Self::SECTION_4_LEN;

        let forecast_accuracy = section_4[0];
        let ai_difficulty = section_4[1];
        let season_link_identifier =
            u32::from_le_bytes(section_4[2..6].try_into().expect("fixed slice"));
        let weekend_link_identifier =
            u32::from_le_bytes(section_4[6..10].try_into().expect("fixed slice"));
        let session_link_identifier =
            u32::from_le_bytes(section_4[10..14].try_into().expect("fixed slice"));
        let pit_stop_window_ideal_lap = section_4[14];
        let pit_stop_window_latest_lap = section_4[15];
        let pit_stop_rejoin_position = section_4[16];
        let steering_assist = section_4[17];
        let braking_assist = section_4[18];
        let gearbox_assist_raw = section_4[19];
        let pit_assist = section_4[20];
        let pit_release_assist = section_4[21];
        let ers_assist = section_4[22];
        let drs_assist = section_4[23];
        let dynamic_racing_line = section_4[24];
        let dynamic_racing_line_type = section_4[25];
        let game_mode_raw = section_4[26];
        let rule_set_raw = section_4[27];
        let time_of_day = u32::from_le_bytes(section_4[28..32].try_into().expect("fixed slice"));
        let session_length_raw = section_4[32];
        let speed_units_lead_player = section_4[33];
        let temperature_units_lead_player = section_4[34];
        let speed_units_secondary_player = section_4[35];
        let temperature_units_secondary_player = section_4[36];
        let num_safety_car_periods = section_4[37];
        let num_virtual_safety_car_periods = section_4[38];
        let num_red_flag_periods = section_4[39];

        let (
            equal_car_performance,
            recovery_mode_raw,
            flashback_limit_raw,
            surface_type_raw,
            low_fuel_mode_raw,
            race_starts_raw,
            tyre_temperature_mode_raw,
            pit_lane_tyre_sim,
            car_damage_raw,
            car_damage_rate_raw,
            collisions_raw,
            collisions_off_for_first_lap_only,
            mp_unsafe_pit_release,
            mp_off_for_griefing,
            corner_cutting_stringency_raw,
            parc_ferme_rules,
            pit_stop_experience_raw,
            safety_car_setting_raw,
            safety_car_experience_raw,
            formation_lap,
            formation_lap_experience_raw,
            red_flags_setting_raw,
            affects_license_level_solo,
            affects_license_level_mp,
            num_sessions_in_weekend,
            weekend_structure,
            sector2_lap_distance_start,
            sector3_lap_distance_start,
            raw_section5_2025,
        ) = if header.packet_format == 2024 {
            let section_5 = &data[offset..offset + Self::SECTION_5_LEN];
            let num_sessions_in_weekend = section_5[24];
            let weekend_all = section_5[25..37].to_vec();
            let weekend_structure = weekend_all
                .into_iter()
                .take(usize::from(num_sessions_in_weekend))
                .collect::<Vec<_>>();
            (
                section_5[0],
                section_5[1],
                section_5[2],
                section_5[3],
                section_5[4],
                section_5[5],
                section_5[6],
                section_5[7],
                section_5[8],
                section_5[9],
                section_5[10],
                section_5[11],
                section_5[12],
                section_5[13],
                section_5[14],
                section_5[15],
                section_5[16],
                section_5[17],
                section_5[18],
                section_5[19],
                section_5[20],
                section_5[21],
                section_5[22],
                section_5[23],
                num_sessions_in_weekend,
                weekend_structure,
                f32::from_le_bytes(section_5[37..41].try_into().expect("fixed slice")),
                f32::from_le_bytes(section_5[41..45].try_into().expect("fixed slice")),
                None,
            )
        } else if header.packet_format >= 2025 {
            let section_5 = &data[offset..offset + Self::SECTION_5_LEN];
            let mut raw = [0u8; Self::SECTION_5_LEN];
            raw.copy_from_slice(section_5);
            (
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                vec![0; 12],
                0.0,
                0.0,
                Some(raw),
            )
        } else {
            (
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                vec![0; 12],
                0.0,
                0.0,
                None,
            )
        };

        Ok(Self {
            header,
            weather_raw,
            track_temperature,
            air_temperature,
            total_laps,
            track_length,
            session_type_raw,
            track_id_raw,
            formula_raw,
            session_time_left,
            session_duration,
            pit_speed_limit,
            game_paused,
            is_spectating,
            spectator_car_index,
            sli_pro_native_support,
            num_marshal_zones,
            marshal_zones,
            safety_car_status_raw,
            network_game,
            num_weather_forecast_samples,
            weather_forecast_samples,
            forecast_accuracy,
            ai_difficulty,
            season_link_identifier,
            weekend_link_identifier,
            session_link_identifier,
            pit_stop_window_ideal_lap,
            pit_stop_window_latest_lap,
            pit_stop_rejoin_position,
            steering_assist,
            braking_assist,
            gearbox_assist_raw,
            pit_assist,
            pit_release_assist,
            ers_assist,
            drs_assist,
            dynamic_racing_line,
            dynamic_racing_line_type,
            game_mode_raw,
            rule_set_raw,
            time_of_day,
            session_length_raw,
            speed_units_lead_player,
            temperature_units_lead_player,
            speed_units_secondary_player,
            temperature_units_secondary_player,
            num_safety_car_periods,
            num_virtual_safety_car_periods,
            num_red_flag_periods,
            equal_car_performance,
            recovery_mode_raw,
            flashback_limit_raw,
            surface_type_raw,
            low_fuel_mode_raw,
            race_starts_raw,
            tyre_temperature_mode_raw,
            pit_lane_tyre_sim,
            car_damage_raw,
            car_damage_rate_raw,
            collisions_raw,
            collisions_off_for_first_lap_only,
            mp_unsafe_pit_release,
            mp_off_for_griefing,
            corner_cutting_stringency_raw,
            parc_ferme_rules,
            pit_stop_experience_raw,
            safety_car_setting_raw,
            safety_car_experience_raw,
            formation_lap,
            formation_lap_experience_raw,
            red_flags_setting_raw,
            affects_license_level_solo,
            affects_license_level_mp,
            num_sessions_in_weekend,
            weekend_structure,
            sector2_lap_distance_start,
            sector3_lap_distance_start,
            raw_section5_2025,
        })
    }

    pub fn to_bytes(&self) -> Vec<u8> {
        let max_weather_forecast_samples = if self.header.packet_format == 2023 {
            Self::MAX_WEATHER_FORECAST_SAMPLES_23
        } else {
            Self::MAX_WEATHER_FORECAST_SAMPLES_24
        };
        let mut bytes = Vec::with_capacity(
            PacketHeader::PACKET_LEN + Self::payload_len_for_format(self.header.packet_format),
        );
        bytes.extend_from_slice(&self.header.to_bytes());

        bytes.push(self.weather_raw);
        bytes.push(self.track_temperature as u8);
        bytes.push(self.air_temperature as u8);
        bytes.push(self.total_laps as u8);
        bytes.extend_from_slice(&self.track_length.to_le_bytes());
        bytes.push(self.session_type_raw);
        bytes.push(self.track_id_raw as u8);
        bytes.push(self.formula_raw);
        bytes.extend_from_slice(&self.session_time_left.to_le_bytes());
        bytes.extend_from_slice(&self.session_duration.to_le_bytes());
        bytes.push(self.pit_speed_limit);
        bytes.push(self.game_paused);
        bytes.push(u8::from(self.is_spectating));
        bytes.push(self.spectator_car_index);
        bytes.push(self.sli_pro_native_support);
        bytes.push(self.num_marshal_zones);

        for zone in self.marshal_zones.iter().take(Self::MAX_MARSHAL_ZONES) {
            bytes.extend_from_slice(&zone.to_bytes());
        }
        let remaining_zones = Self::MAX_MARSHAL_ZONES.saturating_sub(self.marshal_zones.len());
        if remaining_zones > 0 {
            bytes.resize(bytes.len() + (remaining_zones * MarshalZone::PACKET_LEN), 0);
        }

        bytes.push(self.safety_car_status_raw);
        bytes.push(self.network_game);
        bytes.push(self.num_weather_forecast_samples);

        for sample in self
            .weather_forecast_samples
            .iter()
            .take(max_weather_forecast_samples)
        {
            bytes.extend_from_slice(&sample.to_bytes());
        }
        let remaining_samples =
            max_weather_forecast_samples.saturating_sub(self.weather_forecast_samples.len());
        if remaining_samples > 0 {
            bytes.resize(
                bytes.len() + (remaining_samples * WeatherForecastSample::PACKET_LEN),
                0,
            );
        }

        bytes.push(self.forecast_accuracy);
        bytes.push(self.ai_difficulty);
        bytes.extend_from_slice(&self.season_link_identifier.to_le_bytes());
        bytes.extend_from_slice(&self.weekend_link_identifier.to_le_bytes());
        bytes.extend_from_slice(&self.session_link_identifier.to_le_bytes());
        bytes.push(self.pit_stop_window_ideal_lap);
        bytes.push(self.pit_stop_window_latest_lap);
        bytes.push(self.pit_stop_rejoin_position);
        bytes.push(self.steering_assist);
        bytes.push(self.braking_assist);
        bytes.push(self.gearbox_assist_raw);
        bytes.push(self.pit_assist);
        bytes.push(self.pit_release_assist);
        bytes.push(self.ers_assist);
        bytes.push(self.drs_assist);
        bytes.push(self.dynamic_racing_line);
        bytes.push(self.dynamic_racing_line_type);
        bytes.push(self.game_mode_raw);
        bytes.push(self.rule_set_raw);
        bytes.extend_from_slice(&self.time_of_day.to_le_bytes());
        bytes.push(self.session_length_raw);
        bytes.push(self.speed_units_lead_player);
        bytes.push(self.temperature_units_lead_player);
        bytes.push(self.speed_units_secondary_player);
        bytes.push(self.temperature_units_secondary_player);
        bytes.push(self.num_safety_car_periods);
        bytes.push(self.num_virtual_safety_car_periods);
        bytes.push(self.num_red_flag_periods);

        if self.header.packet_format == 2024 {
            bytes.push(self.equal_car_performance);
            bytes.push(self.recovery_mode_raw);
            bytes.push(self.flashback_limit_raw);
            bytes.push(self.surface_type_raw);
            bytes.push(self.low_fuel_mode_raw);
            bytes.push(self.race_starts_raw);
            bytes.push(self.tyre_temperature_mode_raw);
            bytes.push(self.pit_lane_tyre_sim);
            bytes.push(self.car_damage_raw);
            bytes.push(self.car_damage_rate_raw);
            bytes.push(self.collisions_raw);
            bytes.push(self.collisions_off_for_first_lap_only);
            bytes.push(self.mp_unsafe_pit_release);
            bytes.push(self.mp_off_for_griefing);
            bytes.push(self.corner_cutting_stringency_raw);
            bytes.push(self.parc_ferme_rules);
            bytes.push(self.pit_stop_experience_raw);
            bytes.push(self.safety_car_setting_raw);
            bytes.push(self.safety_car_experience_raw);
            bytes.push(self.formation_lap);
            bytes.push(self.formation_lap_experience_raw);
            bytes.push(self.red_flags_setting_raw);
            bytes.push(self.affects_license_level_solo);
            bytes.push(self.affects_license_level_mp);
            bytes.push(self.num_sessions_in_weekend);

            let mut weekend = [0u8; 12];
            for (index, value) in self.weekend_structure.iter().take(12).enumerate() {
                weekend[index] = *value;
            }
            bytes.extend_from_slice(&weekend);
            bytes.extend_from_slice(&self.sector2_lap_distance_start.to_le_bytes());
            bytes.extend_from_slice(&self.sector3_lap_distance_start.to_le_bytes());
        } else if self.header.packet_format >= 2025 {
            if let Some(raw) = self.raw_section5_2025 {
                bytes.extend_from_slice(&raw);
            } else {
                bytes.resize(bytes.len() + Self::SECTION_5_LEN, 0);
            }
        }

        bytes
    }
}

impl Serialize for PacketSessionData {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let weekend_structure = self
            .weekend_structure
            .iter()
            .map(|value| value.to_string())
            .collect::<Vec<_>>();

        let mut map = serializer.serialize_map(Some(64))?;
        map.serialize_entry("weather", &weather_label(self.weather_raw))?;
        map.serialize_entry("track-temperature", &self.track_temperature)?;
        map.serialize_entry("air-temperature", &self.air_temperature)?;
        map.serialize_entry("total-laps", &self.total_laps)?;
        map.serialize_entry("track-length", &self.track_length)?;
        map.serialize_entry(
            "session-type",
            &session_type_label(self.header.packet_format, self.session_type_raw),
        )?;
        map.serialize_entry("track-id", &track_id_label(self.track_id_raw))?;
        map.serialize_entry("formula", &formula_label(self.formula_raw))?;
        map.serialize_entry("session-time-left", &self.session_time_left)?;
        map.serialize_entry("session-duration", &self.session_duration)?;
        map.serialize_entry("pit-speed-limit", &self.pit_speed_limit)?;
        map.serialize_entry("game-paused", &self.game_paused)?;
        map.serialize_entry("is-spectating", &self.is_spectating)?;
        map.serialize_entry("spectator-car-index", &self.spectator_car_index)?;
        map.serialize_entry("sli-pro-native-support", &self.sli_pro_native_support)?;
        map.serialize_entry("num-marshal-zones", &self.num_marshal_zones)?;
        map.serialize_entry("marshal-zones", &self.marshal_zones)?;
        map.serialize_entry(
            "safety-car-status",
            &safety_car_type_label(self.safety_car_status_raw),
        )?;
        map.serialize_entry("network-game", &self.network_game)?;
        map.serialize_entry(
            "num-weather-forecast-samples",
            &self.num_weather_forecast_samples,
        )?;
        map.serialize_entry("weather-forecast-samples", &self.weather_forecast_samples)?;
        map.serialize_entry("forecast-accuracy", &self.forecast_accuracy)?;
        map.serialize_entry("ai-difficulty", &self.ai_difficulty)?;
        map.serialize_entry("season-link-identifier", &self.season_link_identifier)?;
        map.serialize_entry("weekend-link-identifier", &self.weekend_link_identifier)?;
        map.serialize_entry("session-link-identifier", &self.session_link_identifier)?;
        map.serialize_entry("pit-stop-window-ideal-lap", &self.pit_stop_window_ideal_lap)?;
        map.serialize_entry(
            "pit-stop-window-latest-lap",
            &self.pit_stop_window_latest_lap,
        )?;
        map.serialize_entry("pit-stop-rejoin-position", &self.pit_stop_rejoin_position)?;
        map.serialize_entry("steering-assist", &self.steering_assist)?;
        map.serialize_entry("braking-assist", &self.braking_assist)?;
        map.serialize_entry(
            "gearbox-assist",
            &gearbox_assist_label(self.gearbox_assist_raw),
        )?;
        map.serialize_entry("pit-assist", &self.pit_assist)?;
        map.serialize_entry("pit-release-assist", &self.pit_release_assist)?;
        map.serialize_entry("ers-assist", &self.ers_assist)?;
        map.serialize_entry("drs-assist", &self.drs_assist)?;
        map.serialize_entry("dynamic-racing-line", &self.dynamic_racing_line)?;
        map.serialize_entry("dynamic-racing-line-type", &self.dynamic_racing_line_type)?;
        map.serialize_entry("game-mode", &game_mode_label(self.game_mode_raw))?;
        map.serialize_entry("rule-set", &rule_set_label(self.rule_set_raw))?;
        map.serialize_entry("time-of-day", &self.time_of_day)?;
        map.serialize_entry(
            "session-length",
            &session_length_label(self.session_length_raw),
        )?;
        map.serialize_entry("speed-units-lead-player", &self.speed_units_lead_player)?;
        map.serialize_entry(
            "temp-units-lead-player",
            &self.temperature_units_lead_player,
        )?;
        map.serialize_entry(
            "speed-units-secondary-player",
            &self.speed_units_secondary_player,
        )?;
        map.serialize_entry(
            "temp-units-secondary-player",
            &self.temperature_units_secondary_player,
        )?;
        map.serialize_entry("num-safety-car-periods", &self.num_safety_car_periods)?;
        map.serialize_entry(
            "num-virtual-safety-car-periods",
            &self.num_virtual_safety_car_periods,
        )?;
        map.serialize_entry("num-red-flag-periods", &self.num_red_flag_periods)?;
        map.serialize_entry(
            "equal-car-performance",
            &self.equal_car_performance.to_string(),
        )?;
        map.serialize_entry(
            "recovery-mode",
            &recovery_mode_label(self.recovery_mode_raw),
        )?;
        map.serialize_entry(
            "flashback-limit",
            &flashback_limit_label(self.flashback_limit_raw),
        )?;
        map.serialize_entry("surface-type", &surface_type_label(self.surface_type_raw))?;
        map.serialize_entry(
            "low-fuel-mode",
            &low_fuel_mode_label(self.low_fuel_mode_raw),
        )?;
        map.serialize_entry("race-starts", &race_starts_label(self.race_starts_raw))?;
        map.serialize_entry(
            "tyre-temperature-mode",
            &tyre_temperature_mode_label(self.tyre_temperature_mode_raw),
        )?;
        map.serialize_entry("pit-lane-tyre-sim", &self.pit_lane_tyre_sim.to_string())?;
        map.serialize_entry("car-damage", &car_damage_mode_label(self.car_damage_raw))?;
        map.serialize_entry(
            "car-damage-rate",
            &car_damage_rate_label(self.car_damage_rate_raw),
        )?;
        map.serialize_entry("collisions", &collisions_mode_label(self.collisions_raw))?;
        map.serialize_entry(
            "collisions-off-for-first-lap-only",
            &self.collisions_off_for_first_lap_only,
        )?;
        map.serialize_entry("mp-unsafe-pit-release", &self.mp_unsafe_pit_release)?;
        map.serialize_entry("mp-off-for-griefing", &self.mp_off_for_griefing)?;
        map.serialize_entry(
            "corner-cutting-stringency",
            &corner_cutting_label(self.corner_cutting_stringency_raw),
        )?;
        map.serialize_entry("parc-ferme-rules", &self.parc_ferme_rules)?;
        map.serialize_entry(
            "pit-stop-experience",
            &pit_stop_experience_label(self.pit_stop_experience_raw),
        )?;
        map.serialize_entry(
            "safety-car-setting",
            &safety_car_setting_label(self.safety_car_setting_raw),
        )?;
        map.serialize_entry(
            "safety-car-experience",
            &safety_car_experience_label(self.safety_car_experience_raw),
        )?;
        map.serialize_entry("formation-lap", &self.formation_lap)?;
        map.serialize_entry(
            "formation-lap-experience",
            &safety_car_experience_label(self.formation_lap_experience_raw),
        )?;
        map.serialize_entry(
            "red-flags-setting",
            &red_flags_setting_label(self.red_flags_setting_raw),
        )?;
        map.serialize_entry(
            "affects-license-level-solo",
            &self.affects_license_level_solo,
        )?;
        map.serialize_entry("affects-license-level-mp", &self.affects_license_level_mp)?;
        map.serialize_entry(
            "num-sessions-in-weekend",
            &self.num_sessions_in_weekend.to_string(),
        )?;
        map.serialize_entry("weekend-structure", &weekend_structure)?;
        map.serialize_entry(
            "sector-2-lap-distance-start",
            &self.sector2_lap_distance_start.to_string(),
        )?;
        map.serialize_entry(
            "sector-3-lap-distance-start",
            &self.sector3_lap_distance_start.to_string(),
        )?;
        map.end()
    }
}
