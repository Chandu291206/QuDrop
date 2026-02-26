import tkinter as tk
from tkinter import ttk
from network.connection import start_server
import threading
from network.connection import receive_message
from bb84.bb84_core import bob_measure, sift_key
from network.connection import send_list, receive_list
from encryption.xor_cipher import xor_decrypt
from network.connection import receive_file

class ReceiverWindow:

    def __init__(self):

        self.window = tk.Toplevel()
        self.window.title("BB84 Receiver")
        self.window.geometry("500x300")
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)

        self.create_widgets()

    def create_widgets(self):

        title = ttk.Label(
            self.window,
            text="Receiver (Bob)",
            font=("Arial", 16)
        )
        title.pack(pady=10)

        connection_title = ttk.Label(
            self.window,
            text="Connection Status:",
            font=("Arial", 12)
        )
        connection_title.pack(pady=5)

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

        self.connection_label = ttk.Label(
            self.window,
            text="Waiting..."
        )
        self.connection_label.pack(pady=5)

        self.status_label = ttk.Label(
            self.window,
            text="Waiting to start receiver..."
        )
        self.status_label.pack(pady=10)

        start_button = ttk.Button(
            self.window,
            text="Start Receiver",
            command=self.start_receiver
        )
        start_button.pack(pady=20)

        self.file_label = ttk.Label(
            self.window,
            text="No file received yet"
        )
        self.file_label.pack(pady=10)

    def start_receiver(self):

        self.status_label.config(
            text="Waiting for sender..."
        )

        thread = threading.Thread(
            target=self.wait_for_sender,
            daemon=True
        )

        thread.start()


    def wait_for_sender(self):

        self.socket = start_server()

        self.status_label.config(
            text="Sender Connected"
        )

        self.connection_label.config(
            text="Connected"
        )

        message = receive_message(self.socket)

        print("Received:", message)

        if message == "START_BB84":

            self.status_label.config(
                text="BB84 Session Started"
            )

            # Receive Alice Data
            alice_data = receive_list(self.socket)

            alice_bits = alice_data["bits"]
            alice_bases = alice_data["bases"]

            print("Alice bases received")

            bob_bases, bob_results = bob_measure(
                alice_bits,
                alice_bases
            )

            # Send Bob Bases
            send_list(self.socket, bob_bases)

            print("Bob bases sent")

            key = sift_key(
                alice_bits,
                alice_bases,
                bob_bases
            )

            self.shared_key = key

            print("Shared Key:", key)

            self.status_label.config(
                text="BB84 Key Ready"
            )

            self.key_label.config(
                text=f"Key Ready ({len(key)} bits)"
            )
            message = receive_message(self.socket)

            if message == "FILE_TRANSFER":
                
                import os
                # Receive filename
                filename = receive_message(self.socket)
                encrypted_data = receive_file(self.socket)
                decrypted_data = xor_decrypt(
                    encrypted_data,
                    self.shared_key
                )
                os.makedirs("received_files", exist_ok=True)
                file_path = os.path.join(
                    "received_files",
                    filename
                )
                with open(file_path, "wb") as f:
                    f.write(decrypted_data)
                print("File received:", filename)
                self.file_label.config(
                    text=f"Received: {filename}"
                )

    def close_window(self):
    
        print("Receiver closing")
    
        try:
            if hasattr(self, "socket"):
                self.socket.close()
        except:
            pass
        
        self.window.destroy()