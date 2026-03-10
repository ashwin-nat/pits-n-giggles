use serde::{Deserialize, Serialize};
use std::fmt;

fn title_case_variant(name: &str) -> String {
    name.split('_')
        .map(|segment| {
            let mut chars = segment.chars();
            match chars.next() {
                Some(first) if first.is_ascii_alphabetic() => {
                    let mut result = String::with_capacity(segment.len());
                    result.push(first.to_ascii_uppercase());
                    result.extend(chars.map(|c| c.to_ascii_lowercase()));
                    result
                }
                Some(first) => {
                    let mut result = String::with_capacity(segment.len());
                    result.push(first);
                    result.extend(chars);
                    result
                }
                None => String::new(),
            }
        })
        .collect::<Vec<_>>()
        .join(" ")
}

macro_rules! impl_display_and_try_from {
    ($name:ident { $($variant:ident = $value:expr),+ $(,)? }) => {
        impl TryFrom<u8> for $name {
            type Error = u8;

            fn try_from(value: u8) -> Result<Self, Self::Error> {
                match value {
                    $($value => Ok(Self::$variant),)+
                    _ => Err(value),
                }
            }
        }

        impl fmt::Display for $name {
            fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
                let name = match self {
                    $(Self::$variant => stringify!($variant),)+
                };
                write!(f, "{}", title_case_variant(name))
            }
        }
    };
}

#[repr(u8)]
#[allow(non_camel_case_types)]
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum SessionType23 {
    UNKNOWN = 0,
    PRACTICE_1 = 1,
    PRACTICE_2 = 2,
    PRACTICE_3 = 3,
    SHORT_PRACTICE = 4,
    QUALIFYING_1 = 5,
    QUALIFYING_2 = 6,
    QUALIFYING_3 = 7,
    SHORT_QUALIFYING = 8,
    ONE_SHOT_QUALIFYING = 9,
    RACE = 10,
    RACE_2 = 11,
    RACE_3 = 12,
    TIME_TRIAL = 13,
}

impl SessionType23 {
    pub fn is_fp_type_session(self) -> bool {
        matches!(
            self,
            Self::PRACTICE_1 | Self::PRACTICE_2 | Self::PRACTICE_3 | Self::SHORT_PRACTICE
        )
    }

    pub fn is_quali_type_session(self) -> bool {
        matches!(
            self,
            Self::QUALIFYING_1
                | Self::QUALIFYING_2
                | Self::QUALIFYING_3
                | Self::SHORT_QUALIFYING
                | Self::ONE_SHOT_QUALIFYING
        )
    }

    pub fn is_race_type_session(self) -> bool {
        matches!(self, Self::RACE | Self::RACE_2 | Self::RACE_3)
    }

    pub fn is_time_trial_type_session(self) -> bool {
        matches!(self, Self::TIME_TRIAL)
    }
}

impl_display_and_try_from!(SessionType23 {
    UNKNOWN = 0,
    PRACTICE_1 = 1,
    PRACTICE_2 = 2,
    PRACTICE_3 = 3,
    SHORT_PRACTICE = 4,
    QUALIFYING_1 = 5,
    QUALIFYING_2 = 6,
    QUALIFYING_3 = 7,
    SHORT_QUALIFYING = 8,
    ONE_SHOT_QUALIFYING = 9,
    RACE = 10,
    RACE_2 = 11,
    RACE_3 = 12,
    TIME_TRIAL = 13,
});

#[repr(u8)]
#[allow(non_camel_case_types)]
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum SessionType24 {
    UNKNOWN = 0,
    PRACTICE_1 = 1,
    PRACTICE_2 = 2,
    PRACTICE_3 = 3,
    SHORT_PRACTICE = 4,
    QUALIFYING_1 = 5,
    QUALIFYING_2 = 6,
    QUALIFYING_3 = 7,
    SHORT_QUALIFYING = 8,
    ONE_SHOT_QUALIFYING = 9,
    SPRINT_SHOOTOUT_1 = 10,
    SPRINT_SHOOTOUT_2 = 11,
    SPRINT_SHOOTOUT_3 = 12,
    SHORT_SPRINT_SHOOTOUT = 13,
    ONE_SHOT_SPRINT_SHOOTOUT = 14,
    RACE = 15,
    RACE_2 = 16,
    RACE_3 = 17,
    TIME_TRIAL = 18,
}

impl SessionType24 {
    pub fn is_fp_type_session(self) -> bool {
        matches!(
            self,
            Self::PRACTICE_1 | Self::PRACTICE_2 | Self::PRACTICE_3 | Self::SHORT_PRACTICE
        )
    }

    pub fn is_quali_type_session(self) -> bool {
        matches!(
            self,
            Self::QUALIFYING_1
                | Self::QUALIFYING_2
                | Self::QUALIFYING_3
                | Self::SHORT_QUALIFYING
                | Self::ONE_SHOT_QUALIFYING
                | Self::SPRINT_SHOOTOUT_1
                | Self::SPRINT_SHOOTOUT_2
                | Self::SPRINT_SHOOTOUT_3
                | Self::SHORT_SPRINT_SHOOTOUT
                | Self::ONE_SHOT_SPRINT_SHOOTOUT
        )
    }

    pub fn is_race_type_session(self) -> bool {
        matches!(self, Self::RACE | Self::RACE_2 | Self::RACE_3)
    }

    pub fn is_time_trial_type_session(self) -> bool {
        matches!(self, Self::TIME_TRIAL)
    }
}

impl_display_and_try_from!(SessionType24 {
    UNKNOWN = 0,
    PRACTICE_1 = 1,
    PRACTICE_2 = 2,
    PRACTICE_3 = 3,
    SHORT_PRACTICE = 4,
    QUALIFYING_1 = 5,
    QUALIFYING_2 = 6,
    QUALIFYING_3 = 7,
    SHORT_QUALIFYING = 8,
    ONE_SHOT_QUALIFYING = 9,
    SPRINT_SHOOTOUT_1 = 10,
    SPRINT_SHOOTOUT_2 = 11,
    SPRINT_SHOOTOUT_3 = 12,
    SHORT_SPRINT_SHOOTOUT = 13,
    ONE_SHOT_SPRINT_SHOOTOUT = 14,
    RACE = 15,
    RACE_2 = 16,
    RACE_3 = 17,
    TIME_TRIAL = 18,
});

#[repr(u8)]
#[allow(non_camel_case_types)]
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum ResultStatus {
    INVALID = 0,
    INACTIVE = 1,
    ACTIVE = 2,
    FINISHED = 3,
    DID_NOT_FINISH = 4,
    DISQUALIFIED = 5,
    NOT_CLASSIFIED = 6,
    RETIRED = 7,
}

impl ResultStatus {
    pub fn from_raw(value: u8) -> Self {
        Self::try_from(value).unwrap_or(Self::INVALID)
    }
}

impl fmt::Display for ResultStatus {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let name = match self {
            Self::INVALID => "INVALID",
            Self::INACTIVE => "INACTIVE",
            Self::ACTIVE => "ACTIVE",
            Self::FINISHED => "FINISHED",
            Self::DID_NOT_FINISH => "DID_NOT_FINISH",
            Self::DISQUALIFIED => "DISQUALIFIED",
            Self::NOT_CLASSIFIED => "NOT_CLASSIFIED",
            Self::RETIRED => "RETIRED",
        };
        f.write_str(name)
    }
}

impl TryFrom<u8> for ResultStatus {
    type Error = u8;

    fn try_from(value: u8) -> Result<Self, Self::Error> {
        match value {
            0 => Ok(Self::INVALID),
            1 => Ok(Self::INACTIVE),
            2 => Ok(Self::ACTIVE),
            3 => Ok(Self::FINISHED),
            4 => Ok(Self::DID_NOT_FINISH),
            5 => Ok(Self::DISQUALIFIED),
            6 => Ok(Self::NOT_CLASSIFIED),
            7 => Ok(Self::RETIRED),
            _ => Err(value),
        }
    }
}

#[repr(u8)]
#[allow(non_camel_case_types)]
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum ResultReason {
    INVALID = 0,
    RETIRED = 1,
    FINISHED = 2,
    TERMINAL_DAMAGE = 3,
    INACTIVE = 4,
    NOT_ENOUGH_LAPS_COMPLETED = 5,
    BLACK_FLAGGED = 6,
    RED_FLAGGED = 7,
    MECHANICAL_FAILURE = 8,
    SESSION_SKIPPED = 9,
    SESSION_SIMULATED = 10,
}

impl ResultReason {
    pub fn from_raw(value: u8) -> Self {
        Self::try_from(value).unwrap_or(Self::INVALID)
    }
}

impl fmt::Display for ResultReason {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let name = match self {
            Self::INVALID => "invalid",
            Self::RETIRED => "retired",
            Self::FINISHED => "finished",
            Self::TERMINAL_DAMAGE => "terminal_damage",
            Self::INACTIVE => "inactive",
            Self::NOT_ENOUGH_LAPS_COMPLETED => "not_enough_laps_completed",
            Self::BLACK_FLAGGED => "black_flagged",
            Self::RED_FLAGGED => "red_flagged",
            Self::MECHANICAL_FAILURE => "mechanical_failure",
            Self::SESSION_SKIPPED => "session_skipped",
            Self::SESSION_SIMULATED => "session_simulated",
        };
        f.write_str(name)
    }
}

impl TryFrom<u8> for ResultReason {
    type Error = u8;

    fn try_from(value: u8) -> Result<Self, Self::Error> {
        match value {
            0 => Ok(Self::INVALID),
            1 => Ok(Self::RETIRED),
            2 => Ok(Self::FINISHED),
            3 => Ok(Self::TERMINAL_DAMAGE),
            4 => Ok(Self::INACTIVE),
            5 => Ok(Self::NOT_ENOUGH_LAPS_COMPLETED),
            6 => Ok(Self::BLACK_FLAGGED),
            7 => Ok(Self::RED_FLAGGED),
            8 => Ok(Self::MECHANICAL_FAILURE),
            9 => Ok(Self::SESSION_SKIPPED),
            10 => Ok(Self::SESSION_SIMULATED),
            _ => Err(value),
        }
    }
}

#[repr(u8)]
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum ActualTyreCompound {
    C6 = 22,
    C5 = 16,
    C4 = 17,
    C3 = 18,
    C2 = 19,
    C1 = 20,
    C0 = 21,
    Inter = 7,
    Wet = 8,
    Dry = 9,
    WetClassic = 10,
    SuperSoft = 11,
    Soft = 12,
    Medium = 13,
    Hard = 14,
    WetF2 = 15,
    Unknown = 255,
}

impl ActualTyreCompound {
    pub fn from_raw(value: u8) -> Self {
        Self::try_from(value).unwrap_or(Self::Unknown)
    }
}

impl TryFrom<u8> for ActualTyreCompound {
    type Error = u8;

    fn try_from(value: u8) -> Result<Self, Self::Error> {
        match value {
            22 => Ok(Self::C6),
            16 => Ok(Self::C5),
            17 => Ok(Self::C4),
            18 => Ok(Self::C3),
            19 => Ok(Self::C2),
            20 => Ok(Self::C1),
            21 => Ok(Self::C0),
            7 => Ok(Self::Inter),
            8 => Ok(Self::Wet),
            9 => Ok(Self::Dry),
            10 => Ok(Self::WetClassic),
            11 => Ok(Self::SuperSoft),
            12 => Ok(Self::Soft),
            13 => Ok(Self::Medium),
            14 => Ok(Self::Hard),
            15 => Ok(Self::WetF2),
            255 => Ok(Self::Unknown),
            _ => Err(value),
        }
    }
}

impl fmt::Display for ActualTyreCompound {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(match self {
            Self::C6 => "C6",
            Self::C5 => "C5",
            Self::C4 => "C4",
            Self::C3 => "C3",
            Self::C2 => "C2",
            Self::C1 => "C1",
            Self::C0 => "C0",
            Self::Inter => "Inters",
            Self::Wet => "Wet",
            Self::Dry => "Dry",
            Self::WetClassic => "Wet (Classic)",
            Self::SuperSoft => "Super Soft",
            Self::Soft => "Soft",
            Self::Medium => "Medium",
            Self::Hard => "Hard",
            Self::WetF2 => "Wet (F2)",
            Self::Unknown => "Unknown",
        })
    }
}

#[repr(u8)]
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum VisualTyreCompound {
    Soft = 16,
    Medium = 17,
    Hard = 18,
    Inter = 7,
    Wet = 8,
    SuperSoft = 19,
    SoftF2 = 20,
    MediumF2 = 21,
    HardF2 = 22,
    WetF2 = 15,
    Unknown = 255,
}

impl VisualTyreCompound {
    pub fn from_raw(value: u8) -> Self {
        Self::try_from(value).unwrap_or(Self::Unknown)
    }
}

impl TryFrom<u8> for VisualTyreCompound {
    type Error = u8;

    fn try_from(value: u8) -> Result<Self, Self::Error> {
        match value {
            16 => Ok(Self::Soft),
            17 => Ok(Self::Medium),
            18 => Ok(Self::Hard),
            7 => Ok(Self::Inter),
            8 => Ok(Self::Wet),
            19 => Ok(Self::SuperSoft),
            20 => Ok(Self::SoftF2),
            21 => Ok(Self::MediumF2),
            22 => Ok(Self::HardF2),
            15 => Ok(Self::WetF2),
            255 => Ok(Self::Unknown),
            _ => Err(value),
        }
    }
}

impl fmt::Display for VisualTyreCompound {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(match self {
            Self::Soft => "Soft",
            Self::Medium => "Medium",
            Self::Hard => "Hard",
            Self::Inter => "Inters",
            Self::Wet => "Wet",
            Self::SuperSoft => "Super Soft",
            Self::SoftF2 => "Soft",
            Self::MediumF2 => "Medium",
            Self::HardF2 => "Hard",
            Self::WetF2 => "Wet",
            Self::Unknown => "Unknown",
        })
    }
}

#[repr(u8)]
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum TractionControlAssistMode {
    Off = 0,
    Medium = 1,
    Full = 2,
}

impl TryFrom<u8> for TractionControlAssistMode {
    type Error = u8;

    fn try_from(value: u8) -> Result<Self, Self::Error> {
        match value {
            0 => Ok(Self::Off),
            1 => Ok(Self::Medium),
            2 => Ok(Self::Full),
            _ => Err(value),
        }
    }
}

impl fmt::Display for TractionControlAssistMode {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(match self {
            Self::Off => "OFF",
            Self::Medium => "MEDIUM",
            Self::Full => "FULL",
        })
    }
}

#[repr(u8)]
#[allow(non_camel_case_types)]
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum TeamID24 {
    MERCEDES = 0,
    FERRARI = 1,
    RED_BULL_RACING = 2,
    WILLIAMS = 3,
    ASTON_MARTIN = 4,
    ALPINE = 5,
    RB = 6,
    HAAS = 7,
    MCLAREN = 8,
    SAUBER = 9,
    F1_GENERIC = 41,
    F1_CUSTOM_TEAM = 104,
    ART_GP_23 = 143,
    CAMPOS_23 = 144,
    CARLIN_23 = 145,
    PHM_23 = 146,
    DAMS_23 = 147,
    HITECH_23 = 148,
    MP_MOTORSPORT_23 = 149,
    PREMA_23 = 150,
    TRIDENT_23 = 151,
    VAN_AMERSFOORT_RACING_23 = 152,
    VIRTUOSI_23 = 153,
    MY_TEAM = 255,
}

impl TeamID24 {
    pub fn from_raw(value: u8) -> Option<Self> {
        Self::try_from(value).ok()
    }
}

impl TryFrom<u8> for TeamID24 {
    type Error = u8;

    fn try_from(value: u8) -> Result<Self, Self::Error> {
        match value {
            0 => Ok(Self::MERCEDES),
            1 => Ok(Self::FERRARI),
            2 => Ok(Self::RED_BULL_RACING),
            3 => Ok(Self::WILLIAMS),
            4 => Ok(Self::ASTON_MARTIN),
            5 => Ok(Self::ALPINE),
            6 => Ok(Self::RB),
            7 => Ok(Self::HAAS),
            8 => Ok(Self::MCLAREN),
            9 => Ok(Self::SAUBER),
            41 => Ok(Self::F1_GENERIC),
            104 => Ok(Self::F1_CUSTOM_TEAM),
            143 => Ok(Self::ART_GP_23),
            144 => Ok(Self::CAMPOS_23),
            145 => Ok(Self::CARLIN_23),
            146 => Ok(Self::PHM_23),
            147 => Ok(Self::DAMS_23),
            148 => Ok(Self::HITECH_23),
            149 => Ok(Self::MP_MOTORSPORT_23),
            150 => Ok(Self::PREMA_23),
            151 => Ok(Self::TRIDENT_23),
            152 => Ok(Self::VAN_AMERSFOORT_RACING_23),
            153 => Ok(Self::VIRTUOSI_23),
            255 => Ok(Self::MY_TEAM),
            _ => Err(value),
        }
    }
}

impl fmt::Display for TeamID24 {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let label = match self {
            Self::MERCEDES => "Mercedes",
            Self::FERRARI => "Ferrari",
            Self::RED_BULL_RACING => "Red Bull Racing",
            Self::WILLIAMS => "Williams",
            Self::ASTON_MARTIN => "Aston Martin",
            Self::ALPINE => "Alpine",
            Self::RB => "VCARB",
            Self::HAAS => "Haas",
            Self::MCLAREN => "McLaren",
            Self::SAUBER => "Sauber",
            Self::F1_GENERIC => "Generic",
            Self::F1_CUSTOM_TEAM => "Custom",
            Self::MY_TEAM => "MY_TEAM",
            value => {
                return f.write_str(&title_case_variant(match value {
                    Self::ART_GP_23 => "ART_GP_23",
                    Self::CAMPOS_23 => "CAMPOS_23",
                    Self::CARLIN_23 => "CARLIN_23",
                    Self::PHM_23 => "PHM_23",
                    Self::DAMS_23 => "DAMS_23",
                    Self::HITECH_23 => "HITECH_23",
                    Self::MP_MOTORSPORT_23 => "MP_MOTORSPORT_23",
                    Self::PREMA_23 => "PREMA_23",
                    Self::TRIDENT_23 => "TRIDENT_23",
                    Self::VAN_AMERSFOORT_RACING_23 => "VAN_AMERSFOORT_RACING_23",
                    Self::VIRTUOSI_23 => "VIRTUOSI_23",
                    _ => unreachable!(),
                }));
            }
        };
        f.write_str(label)
    }
}

#[repr(u8)]
#[allow(non_camel_case_types)]
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum TeamID25 {
    MERCEDES = 0,
    FERRARI = 1,
    RED_BULL_RACING = 2,
    WILLIAMS = 3,
    ASTON_MARTIN = 4,
    ALPINE = 5,
    RB = 6,
    HAAS = 7,
    MCLAREN = 8,
    SAUBER = 9,
    F1_GENERIC = 41,
    F1_CUSTOM_TEAM = 104,
    KONNERSPORT = 129,
    APXGP_24 = 142,
    APXGP_25 = 154,
    KONNERSPORT_24 = 155,
    ART_GP_24 = 158,
    CAMPOS_24 = 159,
    RODIN_MOTORSPORT_24 = 160,
    AIX_RACING_24 = 161,
    DAMS_24 = 162,
    HITECH_24 = 163,
    MP_MOTORSPORT_24 = 164,
    PREMA_24 = 165,
    TRIDENT_24 = 166,
    VAN_AMERSFOORT_RACING_24 = 167,
    INVICTA_24 = 168,
    MERCEDES_24 = 185,
    FERRARI_24 = 186,
    RED_BULL_RACING_24 = 187,
    WILLIAMS_24 = 188,
    ASTON_MARTIN_24 = 189,
    ALPINE_24 = 190,
    RB_24 = 191,
    HAAS_24 = 192,
    MCLAREN_24 = 193,
    SAUBER_24 = 194,
    MY_TEAM = 255,
}

impl TeamID25 {
    pub fn from_raw(value: u8) -> Option<Self> {
        Self::try_from(value).ok()
    }
}

impl TryFrom<u8> for TeamID25 {
    type Error = u8;

    fn try_from(value: u8) -> Result<Self, Self::Error> {
        match value {
            0 => Ok(Self::MERCEDES),
            1 => Ok(Self::FERRARI),
            2 => Ok(Self::RED_BULL_RACING),
            3 => Ok(Self::WILLIAMS),
            4 => Ok(Self::ASTON_MARTIN),
            5 => Ok(Self::ALPINE),
            6 => Ok(Self::RB),
            7 => Ok(Self::HAAS),
            8 => Ok(Self::MCLAREN),
            9 => Ok(Self::SAUBER),
            41 => Ok(Self::F1_GENERIC),
            104 => Ok(Self::F1_CUSTOM_TEAM),
            129 => Ok(Self::KONNERSPORT),
            142 => Ok(Self::APXGP_24),
            154 => Ok(Self::APXGP_25),
            155 => Ok(Self::KONNERSPORT_24),
            158 => Ok(Self::ART_GP_24),
            159 => Ok(Self::CAMPOS_24),
            160 => Ok(Self::RODIN_MOTORSPORT_24),
            161 => Ok(Self::AIX_RACING_24),
            162 => Ok(Self::DAMS_24),
            163 => Ok(Self::HITECH_24),
            164 => Ok(Self::MP_MOTORSPORT_24),
            165 => Ok(Self::PREMA_24),
            166 => Ok(Self::TRIDENT_24),
            167 => Ok(Self::VAN_AMERSFOORT_RACING_24),
            168 => Ok(Self::INVICTA_24),
            185 => Ok(Self::MERCEDES_24),
            186 => Ok(Self::FERRARI_24),
            187 => Ok(Self::RED_BULL_RACING_24),
            188 => Ok(Self::WILLIAMS_24),
            189 => Ok(Self::ASTON_MARTIN_24),
            190 => Ok(Self::ALPINE_24),
            191 => Ok(Self::RB_24),
            192 => Ok(Self::HAAS_24),
            193 => Ok(Self::MCLAREN_24),
            194 => Ok(Self::SAUBER_24),
            255 => Ok(Self::MY_TEAM),
            _ => Err(value),
        }
    }
}

impl fmt::Display for TeamID25 {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        if matches!(self, Self::MY_TEAM) {
            return f.write_str("MY_TEAM");
        }
        if matches!(self, Self::RB) {
            return f.write_str("RB");
        }

        let raw = match self {
            Self::MERCEDES => "MERCEDES",
            Self::FERRARI => "FERRARI",
            Self::RED_BULL_RACING => "RED_BULL_RACING",
            Self::WILLIAMS => "WILLIAMS",
            Self::ASTON_MARTIN => "ASTON_MARTIN",
            Self::ALPINE => "ALPINE",
            Self::HAAS => "HAAS",
            Self::MCLAREN => "MCLAREN",
            Self::SAUBER => "SAUBER",
            Self::F1_GENERIC => "F1_GENERIC",
            Self::F1_CUSTOM_TEAM => "F1_CUSTOM_TEAM",
            Self::KONNERSPORT => "KONNERSPORT",
            Self::APXGP_24 => "APXGP_24",
            Self::APXGP_25 => "APXGP_25",
            Self::KONNERSPORT_24 => "KONNERSPORT_24",
            Self::ART_GP_24 => "ART_GP_24",
            Self::CAMPOS_24 => "CAMPOS_24",
            Self::RODIN_MOTORSPORT_24 => "RODIN_MOTORSPORT_24",
            Self::AIX_RACING_24 => "AIX_RACING_24",
            Self::DAMS_24 => "DAMS_24",
            Self::HITECH_24 => "HITECH_24",
            Self::MP_MOTORSPORT_24 => "MP_MOTORSPORT_24",
            Self::PREMA_24 => "PREMA_24",
            Self::TRIDENT_24 => "TRIDENT_24",
            Self::VAN_AMERSFOORT_RACING_24 => "VAN_AMERSFOORT_RACING_24",
            Self::INVICTA_24 => "INVICTA_24",
            Self::MERCEDES_24 => "MERCEDES_24",
            Self::FERRARI_24 => "FERRARI_24",
            Self::RED_BULL_RACING_24 => "RED_BULL_RACING_24",
            Self::WILLIAMS_24 => "WILLIAMS_24",
            Self::ASTON_MARTIN_24 => "ASTON_MARTIN_24",
            Self::ALPINE_24 => "ALPINE_24",
            Self::RB_24 => "RB_24",
            Self::HAAS_24 => "HAAS_24",
            Self::MCLAREN_24 => "MCLAREN_24",
            Self::SAUBER_24 => "SAUBER_24",
            Self::RB | Self::MY_TEAM => unreachable!(),
        };

        let label = raw
            .replace('_', " ")
            .to_ascii_lowercase()
            .split(' ')
            .map(|segment| {
                let mut chars = segment.chars();
                match chars.next() {
                    Some(first) => {
                        let mut s = String::new();
                        s.push(first.to_ascii_uppercase());
                        s.extend(chars);
                        s
                    }
                    None => String::new(),
                }
            })
            .collect::<Vec<_>>()
            .join(" ")
            .replace("Gp", "GP")
            .replace("24", "'24")
            .replace("25", "'25");

        f.write_str(&label)
    }
}
