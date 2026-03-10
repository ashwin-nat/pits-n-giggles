use std::io;
use std::io::ErrorKind;
use std::net::SocketAddr;

use tokio::io::AsyncReadExt;
use tokio::net::{TcpListener, TcpStream, UdpSocket};

pub const DEFAULT_TELEMETRY_PORT: u16 = 20_777;
pub const DEFAULT_BUFFER_SIZE: usize = 16_384;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct TelemetryMessage {
    pub payload: Vec<u8>,
    pub peer_addr: SocketAddr,
}

#[derive(Debug)]
pub struct UdpReceiver {
    socket: UdpSocket,
    buffer_size: usize,
}

impl UdpReceiver {
    pub async fn bind(bind_addr: impl tokio::net::ToSocketAddrs) -> io::Result<Self> {
        Self::bind_with_buffer(bind_addr, DEFAULT_BUFFER_SIZE).await
    }

    pub async fn bind_with_buffer(
        bind_addr: impl tokio::net::ToSocketAddrs,
        buffer_size: usize,
    ) -> io::Result<Self> {
        let socket = UdpSocket::bind(bind_addr).await?;
        Ok(Self {
            socket,
            buffer_size,
        })
    }

    pub fn local_addr(&self) -> io::Result<SocketAddr> {
        self.socket.local_addr()
    }

    pub async fn recv(&self) -> io::Result<TelemetryMessage> {
        let mut buffer = vec![0u8; self.buffer_size];
        let (bytes_read, peer_addr) = self.socket.recv_from(&mut buffer).await?;
        buffer.truncate(bytes_read);

        Ok(TelemetryMessage {
            payload: buffer,
            peer_addr,
        })
    }
}

#[derive(Debug)]
pub struct TcpReceiver {
    listener: TcpListener,
    connection: Option<TcpStream>,
}

impl TcpReceiver {
    pub async fn bind(bind_addr: impl tokio::net::ToSocketAddrs) -> io::Result<Self> {
        let listener = TcpListener::bind(bind_addr).await?;
        Ok(Self {
            listener,
            connection: None,
        })
    }

    pub fn local_addr(&self) -> io::Result<SocketAddr> {
        self.listener.local_addr()
    }

    pub async fn recv(&mut self) -> io::Result<TelemetryMessage> {
        loop {
            if self.connection.is_none() {
                let (stream, _) = self.listener.accept().await?;
                self.connection = Some(stream);
            }

            let stream = self
                .connection
                .as_mut()
                .expect("connection just initialized");
            let peer_addr = stream.peer_addr()?;

            let mut length_bytes = [0u8; 4];
            if let Err(error) = stream.read_exact(&mut length_bytes).await {
                if is_connection_reset(&error) {
                    self.connection = None;
                    continue;
                }
                return Err(error);
            }

            let payload_len = u32::from_be_bytes(length_bytes) as usize;
            let mut payload = vec![0u8; payload_len];
            if let Err(error) = stream.read_exact(&mut payload).await {
                if is_connection_reset(&error) {
                    self.connection = None;
                    continue;
                }
                return Err(error);
            }

            return Ok(TelemetryMessage { payload, peer_addr });
        }
    }
}

#[derive(Debug)]
pub enum TelemetryReceiver {
    Udp(UdpReceiver),
    Tcp(TcpReceiver),
}

impl TelemetryReceiver {
    pub async fn bind_udp(bind_addr: impl tokio::net::ToSocketAddrs) -> io::Result<Self> {
        Ok(Self::Udp(UdpReceiver::bind(bind_addr).await?))
    }

    pub async fn bind_udp_with_buffer(
        bind_addr: impl tokio::net::ToSocketAddrs,
        buffer_size: usize,
    ) -> io::Result<Self> {
        Ok(Self::Udp(
            UdpReceiver::bind_with_buffer(bind_addr, buffer_size).await?,
        ))
    }

    pub async fn bind_tcp(bind_addr: impl tokio::net::ToSocketAddrs) -> io::Result<Self> {
        Ok(Self::Tcp(TcpReceiver::bind(bind_addr).await?))
    }

    pub fn local_addr(&self) -> io::Result<SocketAddr> {
        match self {
            Self::Udp(receiver) => receiver.local_addr(),
            Self::Tcp(receiver) => receiver.local_addr(),
        }
    }

    pub async fn recv(&mut self) -> io::Result<TelemetryMessage> {
        match self {
            Self::Udp(receiver) => receiver.recv().await,
            Self::Tcp(receiver) => receiver.recv().await,
        }
    }
}

fn is_connection_reset(error: &io::Error) -> bool {
    matches!(
        error.kind(),
        ErrorKind::UnexpectedEof
            | ErrorKind::ConnectionAborted
            | ErrorKind::ConnectionReset
            | ErrorKind::BrokenPipe
    )
}
