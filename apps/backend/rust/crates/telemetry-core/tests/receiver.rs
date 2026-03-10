use std::time::Duration;

use telemetry_core::{TcpReceiver, UdpReceiver};
use tokio::io::AsyncWriteExt;
use tokio::net::{TcpStream, UdpSocket};

#[tokio::test]
async fn udp_receiver_reads_loopback_datagram() {
    let receiver = UdpReceiver::bind("127.0.0.1:0")
        .await
        .expect("bind receiver");
    let sender = UdpSocket::bind("127.0.0.1:0").await.expect("bind sender");
    let receiver_addr = receiver.local_addr().expect("receiver addr");
    let sender_addr = sender.local_addr().expect("sender addr");

    sender
        .send_to(b"hello telemetry", receiver_addr)
        .await
        .expect("send datagram");

    let message = tokio::time::timeout(Duration::from_secs(1), receiver.recv())
        .await
        .expect("recv timeout")
        .expect("recv");

    assert_eq!(message.payload, b"hello telemetry");
    assert_eq!(message.peer_addr, sender_addr);
}

#[tokio::test]
async fn tcp_receiver_reads_length_prefixed_payload() {
    let mut receiver = TcpReceiver::bind("127.0.0.1:0")
        .await
        .expect("bind receiver");
    let receiver_addr = receiver.local_addr().expect("receiver addr");

    let client = tokio::spawn(async move {
        let mut stream = TcpStream::connect(receiver_addr).await.expect("connect");
        let payload = b"time trial packet";
        stream
            .write_all(&(payload.len() as u32).to_be_bytes())
            .await
            .expect("write length");
        stream.write_all(payload).await.expect("write payload");
        stream.flush().await.expect("flush");
        stream.local_addr().expect("local addr")
    });

    let message = tokio::time::timeout(Duration::from_secs(1), receiver.recv())
        .await
        .expect("recv timeout")
        .expect("recv");
    let client_addr = client.await.expect("client join");

    assert_eq!(message.payload, b"time trial packet");
    assert_eq!(message.peer_addr, client_addr);
}
