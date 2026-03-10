use std::collections::HashSet;

use f1_types::{F1Packet, F1PacketType};

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum FrameGateDropReason {
    OutOfOrderPacket,
    DuplicatePacketType,
}

#[derive(Clone, Debug)]
pub struct SessionFrameGate {
    enabled: bool,
    last_session_uid: Option<u64>,
    last_frame: Option<u32>,
    seen_packet_types: HashSet<F1PacketType>,
    last_drop_reason: Option<FrameGateDropReason>,
}

impl SessionFrameGate {
    pub fn new(enabled: bool) -> Self {
        Self {
            enabled,
            last_session_uid: None,
            last_frame: None,
            seen_packet_types: HashSet::new(),
            last_drop_reason: None,
        }
    }

    pub fn should_accept(&mut self, packet: &F1Packet) -> bool {
        self.last_drop_reason = None;
        if !self.enabled {
            return true;
        }

        let header = packet.header();
        let session_uid = header.session_uid;
        let frame = header.overall_frame_identifier;
        let packet_type = packet.packet_type();

        if self.last_session_uid.is_none() {
            self.last_session_uid = Some(session_uid);
            self.last_frame = Some(frame);
            self.seen_packet_types = if frame == 0 {
                HashSet::new()
            } else {
                HashSet::from([packet_type])
            };
            return true;
        }

        if Some(session_uid) != self.last_session_uid {
            self.last_session_uid = Some(session_uid);
            self.last_frame = Some(frame);
            self.seen_packet_types = if frame == 0 {
                HashSet::new()
            } else {
                HashSet::from([packet_type])
            };
            return true;
        }

        if frame == 0 {
            self.last_frame = Some(0);
            self.seen_packet_types.clear();
            return true;
        }

        if let Some(last_frame) = self.last_frame {
            if frame < last_frame {
                self.last_drop_reason = Some(FrameGateDropReason::OutOfOrderPacket);
                return false;
            }

            if frame > last_frame {
                self.last_frame = Some(frame);
                self.seen_packet_types = HashSet::from([packet_type]);
                return true;
            }
        } else {
            self.last_frame = Some(frame);
            self.seen_packet_types = HashSet::from([packet_type]);
            return true;
        }

        if self.seen_packet_types.contains(&packet_type) {
            self.last_drop_reason = Some(FrameGateDropReason::DuplicatePacketType);
            return false;
        }

        self.seen_packet_types.insert(packet_type);
        true
    }

    pub fn should_drop(&mut self, packet: &F1Packet) -> bool {
        !self.should_accept(packet)
    }

    pub fn last_drop_reason(&self) -> Option<FrameGateDropReason> {
        self.last_drop_reason
    }
}

impl Default for SessionFrameGate {
    fn default() -> Self {
        Self::new(true)
    }
}
