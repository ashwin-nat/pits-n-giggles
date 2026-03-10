use std::collections::HashSet;
use std::io;

use f1_types::{F1Packet, F1PacketParseError, F1PacketType, PacketHeader};

use crate::frame_gate::{FrameGateDropReason, SessionFrameGate};
use crate::receiver::TelemetryReceiver;

pub const MIN_SUPPORTED_PACKET_FORMAT: u16 = 2023;

#[derive(Clone, Debug)]
pub struct TelemetryManagerConfig {
    pub interested_packets: Option<HashSet<F1PacketType>>,
    pub frame_gate_enabled: bool,
    pub min_supported_packet_format: u16,
}

impl Default for TelemetryManagerConfig {
    fn default() -> Self {
        Self {
            interested_packets: None,
            frame_gate_enabled: false,
            min_supported_packet_format: MIN_SUPPORTED_PACKET_FORMAT,
        }
    }
}

#[derive(Clone, Debug, PartialEq)]
pub enum PacketDropReason {
    IncompletePacket { actual: usize, minimum: usize },
    UnsupportedPacketFormat(u16),
    UnsupportedPacketType(u8),
    UninterestedPacket(F1PacketType),
    ParseError(F1PacketParseError),
    FrameGate(FrameGateDropReason),
}

#[derive(Clone, Debug, PartialEq)]
pub enum PacketProcessingOutcome {
    Accepted(F1Packet),
    Dropped(PacketDropReason),
}

pub struct TelemetryManager {
    receiver: TelemetryReceiver,
    interested_packets: Option<HashSet<F1PacketType>>,
    frame_gate: SessionFrameGate,
    min_supported_packet_format: u16,
}

impl TelemetryManager {
    pub fn new(receiver: TelemetryReceiver, config: TelemetryManagerConfig) -> Self {
        Self {
            receiver,
            interested_packets: config.interested_packets,
            frame_gate: SessionFrameGate::new(config.frame_gate_enabled),
            min_supported_packet_format: config.min_supported_packet_format,
        }
    }

    pub fn receiver(&self) -> &TelemetryReceiver {
        &self.receiver
    }

    pub fn receiver_mut(&mut self) -> &mut TelemetryReceiver {
        &mut self.receiver
    }

    pub fn process_raw_packet(&mut self, raw_packet: &[u8]) -> PacketProcessingOutcome {
        if raw_packet.len() < PacketHeader::PACKET_LEN {
            return PacketProcessingOutcome::Dropped(PacketDropReason::IncompletePacket {
                actual: raw_packet.len(),
                minimum: PacketHeader::PACKET_LEN,
            });
        }

        let header = PacketHeader::parse(&raw_packet[..PacketHeader::PACKET_LEN])
            .expect("packet header slice length checked above");
        let Some(packet_type) = header.packet_id else {
            return PacketProcessingOutcome::Dropped(PacketDropReason::UnsupportedPacketType(
                header.packet_id_raw,
            ));
        };

        if header.packet_format < self.min_supported_packet_format {
            return PacketProcessingOutcome::Dropped(PacketDropReason::UnsupportedPacketFormat(
                header.packet_format,
            ));
        }

        if let Some(interested_packets) = &self.interested_packets {
            if !interested_packets.contains(&packet_type) {
                return PacketProcessingOutcome::Dropped(PacketDropReason::UninterestedPacket(
                    packet_type,
                ));
            }
        }

        let packet = match F1Packet::parse(raw_packet) {
            Ok(packet) => packet,
            Err(error) => {
                return PacketProcessingOutcome::Dropped(PacketDropReason::ParseError(error));
            }
        };

        if self.frame_gate.should_drop(&packet) {
            return PacketProcessingOutcome::Dropped(PacketDropReason::FrameGate(
                self.frame_gate
                    .last_drop_reason()
                    .expect("frame gate drop must set reason"),
            ));
        }

        PacketProcessingOutcome::Accepted(packet)
    }

    pub async fn next(&mut self) -> io::Result<PacketProcessingOutcome> {
        let message = self.receiver.recv().await?;
        Ok(self.process_raw_packet(&message.payload))
    }

    pub async fn next_accepted_packet(&mut self) -> io::Result<F1Packet> {
        loop {
            match self.next().await? {
                PacketProcessingOutcome::Accepted(packet) => return Ok(packet),
                PacketProcessingOutcome::Dropped(_) => {}
            }
        }
    }

    pub async fn run<F>(&mut self, mut on_packet: F) -> io::Result<()>
    where
        F: FnMut(F1Packet),
    {
        loop {
            on_packet(self.next_accepted_packet().await?);
        }
    }
}
