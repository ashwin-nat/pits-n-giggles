from socket_receiver import TCPListener

def run_tcp_server(port: int, bind_ip: str):
    tcp_listener = TCPListener(port, bind_ip)

    try:
        while True:
            message = tcp_listener.getNextMessage()
            print(f"Received message: {message.decode('utf-8')}")

    except KeyboardInterrupt:
        print("Server terminated by user.")
    finally:
        # Ensure the socket is closed when the server is done
        if tcp_listener.m_connection:
            tcp_listener.closeConnection()

if __name__ == "__main__":
    server_port = 8080
    server_ip = "127.0.0.1"

    run_tcp_server(server_port, server_ip)