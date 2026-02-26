import socket
import json

PORT = 5000


# Receiver Side
def start_server():

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_socket.bind(("", PORT))

    server_socket.listen(1)

    print("Waiting for sender...")

    conn, addr = server_socket.accept()

    print("Connected from:", addr)

    return conn


# Sender Side
def connect_to_server(ip):

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    client_socket.connect((ip, PORT))

    print("Connected to receiver")

    return client_socket

def send_message(sock, message):

    sock.sendall(message.encode())


def receive_message(sock):

    data = sock.recv(1024)

    return data.decode()

def send_list(sock, data):

    message = json.dumps(data)

    sock.sendall(message.encode())


def receive_list(sock):

    data = sock.recv(8192)

    return json.loads(data.decode())

def send_file(sock, data):

    size = len(data)

    sock.sendall(str(size).encode())

    sock.recv(1024)

    sock.sendall(data)


def receive_file(sock):

    size = int(sock.recv(1024).decode())

    sock.sendall(b"OK")

    data = bytearray()

    while len(data) < size:

        remaining = size - len(data)

        packet = sock.recv(min(4096, remaining))

        if not packet:
            break

        data.extend(packet)

    return bytes(data)