use std::net::SocketAddr;

use tokio::net::UdpSocket;
use tokio::sync::mpsc;

const FORWARDER_QUEUE_CAPACITY: usize = 256;

#[derive(Debug)]
pub struct PacketForwarderWorker {
    sender: Option<mpsc::Sender<Vec<u8>>>,
}

impl PacketForwarderWorker {
    pub fn start(targets: Vec<SocketAddr>) -> Self {
        if targets.is_empty() {
            return Self { sender: None };
        }

        let (sender, mut receiver) = mpsc::channel::<Vec<u8>>(FORWARDER_QUEUE_CAPACITY);
        tokio::spawn(async move {
            let Ok(socket) = UdpSocket::bind("0.0.0.0:0").await else {
                return;
            };

            while let Some(payload) = receiver.recv().await {
                for target in &targets {
                    let _ = socket.send_to(&payload, target).await;
                }
            }
        });

        Self {
            sender: Some(sender),
        }
    }

    pub fn try_forward(&self, payload: &[u8]) {
        let Some(sender) = self.sender.as_ref() else {
            return;
        };
        let Ok(permit) = sender.try_reserve() else {
            return;
        };
        permit.send(payload.to_vec());
    }
}
