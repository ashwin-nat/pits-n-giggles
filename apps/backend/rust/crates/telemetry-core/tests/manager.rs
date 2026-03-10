use std::collections::HashSet;
use std::time::Duration;

use f1_types::{EventPacketType, F1PacketType, PacketEventData, PacketHeader};
use telemetry_core::{
    FrameGateDropReason, PacketDropReason, PacketProcessingOutcome, TelemetryManager,
    TelemetryManagerConfig, TelemetryReceiver,
};
use tokio::net::UdpSocket;

fn event_bytes(
    packet_format: u16,
    session_uid: u64,
    frame_identifier: u32,
    overall_frame_identifier: u32,
) -> Vec<u8> {
    PacketEventData::from_values(
        PacketHeader::from_values(
            packet_format,
            if packet_format >= 2025 { 25 } else { 24 },
            1,
            0,
            1,
            F1PacketType::Event,
            session_uid,
            0.0,
            frame_identifier,
            overall_frame_identifier,
            0,
            255,
        ),
        EventPacketType::SessionStarted,
        None,
    )
    .to_bytes()
}

#[tokio::test]
async fn manager_accepts_valid_packet() {
    let receiver = TelemetryReceiver::Udp(
        telemetry_core::UdpReceiver::bind_with_buffer("127.0.0.1:0", 4_096)
            .await
            .expect("bind"),
    );
    let mut manager = TelemetryManager::new(receiver, TelemetryManagerConfig::default());

    let outcome = manager.process_raw_packet(&event_bytes(2025, 7, 10, 10));
    assert!(matches!(
        outcome,
        PacketProcessingOutcome::Accepted(packet) if packet.packet_type() == F1PacketType::Event
    ));
}

#[tokio::test]
async fn manager_drops_short_packets() {
    let receiver = TelemetryReceiver::Udp(
        telemetry_core::UdpReceiver::bind_with_buffer("127.0.0.1:0", 4_096)
            .await
            .expect("bind"),
    );
    let mut manager = TelemetryManager::new(receiver, TelemetryManagerConfig::default());

    assert_eq!(
        manager.process_raw_packet(&[1, 2, 3]),
        PacketProcessingOutcome::Dropped(PacketDropReason::IncompletePacket {
            actual: 3,
            minimum: PacketHeader::PACKET_LEN,
        })
    );
}

#[tokio::test]
async fn manager_respects_interested_packet_filter() {
    let receiver = TelemetryReceiver::Udp(
        telemetry_core::UdpReceiver::bind_with_buffer("127.0.0.1:0", 4_096)
            .await
            .expect("bind"),
    );
    let mut manager = TelemetryManager::new(
        receiver,
        TelemetryManagerConfig {
            interested_packets: Some(HashSet::from([F1PacketType::Motion])),
            ..TelemetryManagerConfig::default()
        },
    );

    assert_eq!(
        manager.process_raw_packet(&event_bytes(2025, 7, 10, 10)),
        PacketProcessingOutcome::Dropped(PacketDropReason::UninterestedPacket(F1PacketType::Event))
    );
}

#[tokio::test]
async fn manager_drops_unsupported_packet_format() {
    let receiver = TelemetryReceiver::Udp(
        telemetry_core::UdpReceiver::bind_with_buffer("127.0.0.1:0", 4_096)
            .await
            .expect("bind"),
    );
    let mut manager = TelemetryManager::new(receiver, TelemetryManagerConfig::default());

    assert_eq!(
        manager.process_raw_packet(&event_bytes(2022, 7, 10, 10)),
        PacketProcessingOutcome::Dropped(PacketDropReason::UnsupportedPacketFormat(2022))
    );
}

#[tokio::test]
async fn manager_drops_duplicate_packet_type_when_frame_gate_enabled() {
    let receiver = TelemetryReceiver::Udp(
        telemetry_core::UdpReceiver::bind_with_buffer("127.0.0.1:0", 4_096)
            .await
            .expect("bind"),
    );
    let mut manager = TelemetryManager::new(
        receiver,
        TelemetryManagerConfig {
            frame_gate_enabled: true,
            ..TelemetryManagerConfig::default()
        },
    );

    assert!(matches!(
        manager.process_raw_packet(&event_bytes(2025, 7, 10, 10)),
        PacketProcessingOutcome::Accepted(_)
    ));
    assert_eq!(
        manager.process_raw_packet(&event_bytes(2025, 7, 10, 10)),
        PacketProcessingOutcome::Dropped(PacketDropReason::FrameGate(
            FrameGateDropReason::DuplicatePacketType
        ))
    );
}

#[tokio::test]
async fn manager_reads_and_dispatches_udp_packets() {
    let receiver = TelemetryReceiver::bind_udp("127.0.0.1:0")
        .await
        .expect("bind receiver");
    let receiver_addr = receiver.local_addr().expect("receiver addr");
    let mut manager = TelemetryManager::new(receiver, TelemetryManagerConfig::default());
    let sender = UdpSocket::bind("127.0.0.1:0").await.expect("bind sender");

    sender
        .send_to(&event_bytes(2025, 42, 5, 5), receiver_addr)
        .await
        .expect("send");

    let outcome = tokio::time::timeout(Duration::from_secs(1), manager.next())
        .await
        .expect("recv timeout")
        .expect("manager recv");

    assert!(matches!(
        outcome,
        PacketProcessingOutcome::Accepted(packet) if packet.packet_type() == F1PacketType::Event
    ));
}
