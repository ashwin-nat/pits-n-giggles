use crate::PacketHeader;
use crate::errors::InvalidPacketLengthError;
use serde::Serialize;
use serde::ser::{SerializeMap, Serializer};
use std::fmt;

#[derive(Clone, Debug, PartialEq)]
pub struct PacketLapPositionsData {
    pub header: PacketHeader,
    pub num_laps: u8,
    pub lap_start: u8,
    pub lap_positions: Vec<Vec<u8>>,
}

impl PacketLapPositionsData {
    pub const MAX_CARS: usize = 22;
    pub const MAX_LAPS: usize = 50;
    pub const TOTAL_BYTES: usize = Self::MAX_CARS * Self::MAX_LAPS;
    pub const PAYLOAD_LEN: usize = 2 + Self::TOTAL_BYTES;

    pub fn from_values(
        header: PacketHeader,
        num_laps: u8,
        lap_start: u8,
        lap_positions: Vec<Vec<u8>>,
    ) -> Self {
        let num_laps = Self::normalized_num_laps(num_laps);
        Self {
            header,
            num_laps,
            lap_start,
            lap_positions: lap_positions
                .into_iter()
                .take(num_laps as usize)
                .map(|row| row.into_iter().take(Self::MAX_CARS).collect())
                .collect(),
        }
    }

    pub fn parse(header: PacketHeader, packet: &[u8]) -> Result<Self, InvalidPacketLengthError> {
        if packet.len() != Self::PAYLOAD_LEN {
            return Err(InvalidPacketLengthError::new(format!(
                "Received packet length {} is not equal to expected {}",
                packet.len(),
                Self::PAYLOAD_LEN
            )));
        }

        let num_laps = packet[0];
        if usize::from(num_laps) > Self::MAX_LAPS {
            return Err(InvalidPacketLengthError::new(format!(
                "Received num laps {} exceeds max {}",
                num_laps,
                Self::MAX_LAPS
            )));
        }
        let lap_start = packet[1];
        let flat_array = &packet[2..];
        let lap_positions = (0..usize::from(num_laps))
            .map(|lap_index| {
                let start = lap_index * Self::MAX_CARS;
                flat_array[start..start + Self::MAX_CARS].to_vec()
            })
            .collect::<Vec<_>>();

        Ok(Self {
            header,
            num_laps,
            lap_start,
            lap_positions,
        })
    }

    pub fn to_bytes(&self) -> Vec<u8> {
        let num_laps = Self::normalized_num_laps(self.num_laps);
        let mut bytes = Vec::with_capacity(PacketHeader::PACKET_LEN + Self::PAYLOAD_LEN);
        bytes.extend_from_slice(&self.header.to_bytes());
        bytes.push(num_laps);
        bytes.push(self.lap_start);

        let mut flat = vec![0u8; Self::TOTAL_BYTES];
        for (lap_index, row) in self
            .lap_positions
            .iter()
            .take(usize::from(num_laps))
            .enumerate()
        {
            let start = lap_index * Self::MAX_CARS;
            for (car_index, value) in row.iter().take(Self::MAX_CARS).enumerate() {
                flat[start + car_index] = *value;
            }
        }
        bytes.extend_from_slice(&flat);
        bytes
    }

    fn normalized_num_laps(num_laps: u8) -> u8 {
        num_laps.min(Self::MAX_LAPS as u8)
    }
}

impl fmt::Display for PacketLapPositionsData {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "PacketLapPositionsData(Num Laps: {}, Lap Start: {})",
            self.num_laps, self.lap_start
        )
    }
}

impl Serialize for PacketLapPositionsData {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let mut map = serializer.serialize_map(Some(3))?;
        map.serialize_entry("num-laps", &self.num_laps)?;
        map.serialize_entry("lap-start", &self.lap_start)?;
        map.serialize_entry("lap-positions", &self.lap_positions)?;
        map.end()
    }
}
