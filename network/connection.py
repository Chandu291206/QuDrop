import socket
import json
import struct

PORT = 5000
FRAME_HEADER_SIZE = 4


def _recv_exact(sock, size):

    chunks = bytearray()

    while len(chunks) < size:
        packet = sock.recv(size - len(chunks))
        if not packet:
            raise ConnectionError("Socket connection closed unexpectedly.")
        chunks.extend(packet)

    return bytes(chunks)


def _send_frame(sock, payload):

    header = struct.pack("!I", len(payload))
    sock.sendall(header + payload)


def _receive_frame(sock):

    header = _recv_exact(sock, FRAME_HEADER_SIZE)
    payload_size = struct.unpack("!I", header)[0]
    return _recv_exact(sock, payload_size) if payload_size > 0 else b""


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

    _send_frame(sock, message.encode("utf-8"))


def receive_message(sock):

    data = _receive_frame(sock)

    return data.decode("utf-8")

def send_list(sock, data):

    message = json.dumps(data).encode("utf-8")

    _send_frame(sock, message)


def receive_list(sock):

    data = _receive_frame(sock)

    return json.loads(data.decode("utf-8"))


def send_qber_sample(sock, sample_indices, alice_sample_bits):

    send_list(sock, {
        "sample_indices": sample_indices,
        "alice_sample_bits": alice_sample_bits
    })


def receive_qber_sample(sock):

    payload = receive_list(sock)
    return payload["sample_indices"], payload["alice_sample_bits"]

def send_file(sock, data):

    _send_frame(sock, data)


def receive_file(sock):

    return _receive_frame(sock)
