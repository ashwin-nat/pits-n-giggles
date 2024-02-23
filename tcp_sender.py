import socket

def run_tcp_client(server_ip: str, server_port: int):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, server_port))

    try:
        for i in range(5):  # Sending 5 messages for demonstration
            message = f"Hello, Server! Message {i + 1}".encode('utf-8')
            client_socket.send(message)
            print(f"Sent message: {message.decode('utf-8')}")

    except KeyboardInterrupt:
        print("Client terminated by user.")
    finally:
        client_socket.close()

if __name__ == "__main__":
    server_ip = "127.0.0.1"
    server_port = 20777

    run_tcp_client(server_ip, server_port)
