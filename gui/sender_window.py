from concurrent.futures import thread
import tkinter as tk
from tkinter import ttk, filedialog
from network.connection import connect_to_server
from network.connection import send_message
from bb84.bb84_core import alice_generate, sift_key
from network.connection import send_list, receive_list
from encryption.xor_cipher import xor_encrypt
from network.connection import send_file
import threading
class SenderWindow:

    def __init__(self):

        self.window = tk.Toplevel()
        self.window.title("BB84 Sender")
        self.window.geometry("500x400")
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)

        self.create_widgets()

    def create_widgets(self):

        title = ttk.Label(
            self.window,
            text="Sender (Alice)",
            font=("Arial", 16)
        )
        title.pack(pady=10)

        # Receiver IP

        ip_label = ttk.Label(
            self.window,
            text="Receiver IP:"
        )
        ip_label.pack()

        self.ip_entry = ttk.Entry(
            self.window,
            width=30
        )
        self.ip_entry.pack(pady=5)

        # Connection Button

        connect_button = ttk.Button(
            self.window,
            text="Connect",
            command=self.connect
        )
        connect_button.pack(pady=10)

        status_title = ttk.Label(
            self.window,
            text="Connection Status:",
            font=("Arial", 12)
        )
        status_title.pack(pady=5)

        self.connection_label = ttk.Label(
            self.window,
            text="Not Connected"
        )
        self.connection_label.pack(pady=5)


        # Key Generation

        key_button = ttk.Button(
            self.window,
            text="Generate BB84 Key",
            command=self.generate_key
        )
        key_button.pack(pady=10)

        # File Selection

        file_button = ttk.Button(
            self.window,
            text="Select File",
            command=self.select_file
        )
        file_button.pack(pady=10)

        self.file_label = ttk.Label(
            self.window,
            text="No file selected"
        )
        self.file_label.pack(pady=5)

        # Send Button

        send_button = ttk.Button(
            self.window,
            text="Send File",
            command=self.send_file
        )
        send_button.pack(pady=20)

        encryption_title = ttk.Label(
            self.window,
            text="Encryption:",
            font=("Arial", 12)
        )
        encryption_title.pack(pady=5)

        self.encryption_label = ttk.Label(
            self.window,
            text="XOR"
        )
        self.encryption_label.pack(pady=5)

    def connect(self):

        ip = self.ip_entry.get()

        try:
            self.socket = connect_to_server(ip)

            print("Connected successfully")

            self.connection_label.config(
            text="Connected"
            )

        except Exception as e:

            print("Connection failed:", e)

    def generate_key(self):

        try:

            send_message(self.socket, "START_BB84")

            print("START_BB84 sent")

            alice_bits, alice_bases = alice_generate()

            # Send Alice Data
            send_list(self.socket, {
                "bits": alice_bits,
                "bases": alice_bases
            })

            print("Alice bases sent")

            # Receive Bob Bases
            bob_bases = receive_list(self.socket)

            print("Bob bases received")

            key = sift_key(alice_bits, alice_bases, bob_bases)

            self.shared_key = key

            self.key_label.config(
                text=f"Key Ready ({len(key)} bits)"
            )

        except Exception as e:

            print("Error:", e)

        key_title = ttk.Label(
            self.window,
                text="BB84 Key Status:",
                font=("Arial", 12)
        )
        key_title.pack(pady=5)

        self.key_label = ttk.Label(
                self.window,
                text="Not Generated"
        )
        self.key_label.pack(pady=5)

    def select_file(self):

        file_path = filedialog.askopenfilename()

        if file_path:

            self.file_path = file_path

            self.file_label.config(text=file_path)

            print("Selected file:", file_path)

    def send_file(self):

        thread = threading.Thread(
            target=self.send_file_thread,
            daemon=True
        )

        thread.start()

    def send_file_thread(self):

        try:

            import os

            filename = os.path.basename(self.file_path)

            send_message(self.socket, "FILE_TRANSFER")

            send_message(self.socket, filename)

            with open(self.file_path, "rb") as f:
                file_data = f.read()

            encrypted_data = xor_encrypt(
                file_data,
                self.shared_key
            )

            send_file(self.socket, encrypted_data)

            print("File sent successfully")

        except Exception as e:

            print("Error:", e)
    def close_window(self):

        print("Sender closing")
    
        try:
            if hasattr(self, "socket"):
                self.socket.close()
        except:
            pass
        
        self.window.destroy()