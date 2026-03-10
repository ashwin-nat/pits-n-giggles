use std::fmt;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct InvalidPacketLengthError {
    message: String,
}

impl InvalidPacketLengthError {
    pub fn new(message: impl Into<String>) -> Self {
        Self {
            message: format!("Invalid packet length. {}", message.into()),
        }
    }
}

impl fmt::Display for InvalidPacketLengthError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&self.message)
    }
}

impl std::error::Error for InvalidPacketLengthError {}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PacketParsingError {
    message: String,
}

impl PacketParsingError {
    pub fn new(message: impl Into<String>) -> Self {
        Self {
            message: format!("Malformed packet. {}", message.into()),
        }
    }
}

impl fmt::Display for PacketParsingError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&self.message)
    }
}

impl std::error::Error for PacketParsingError {}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PacketCountValidationError {
    message: String,
}

impl PacketCountValidationError {
    pub fn new(message: impl Into<String>) -> Self {
        Self {
            message: format!("Packet count validation error. {}", message.into()),
        }
    }
}

impl fmt::Display for PacketCountValidationError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&self.message)
    }
}

impl std::error::Error for PacketCountValidationError {}
