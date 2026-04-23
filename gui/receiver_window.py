import os
import threading
import tkinter as tk
from tkinter import ttk

from bb84.bb84_core import (
    QBER_THRESHOLD,
    QISKIT_AVAILABLE,
    bob_measure,
    privacy_amplify,
    sift_key,
)
from encryption.xor_cipher import xor_decrypt
from network.connection import (
    receive_file,
    receive_message,
    receive_list,
    receive_qber_sample,
    send_list,
    start_server,
)


class ReceiverWindow:

    def __init__(self):

        self.window = tk.Toplevel()
        self.window.title("BB84 Receiver")
        self.window.geometry("520x420")
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)

        self.socket = None
        self.shared_key = None

        backend = "Qiskit" if QISKIT_AVAILABLE else "Classical fallback"
        print(f"[QuDrop] Backend: {backend}")

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

        self.connection_label = ttk.Label(
            self.window,
            text="Waiting..."
        )
        self.connection_label.pack(pady=5)

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

        self.qber_label = ttk.Label(
            self.window,
            text="QBER: N/A"
        )
        self.qber_label.pack(pady=4)

        self.abort_label = ttk.Label(
            self.window,
            text="",
            foreground="#b91c1c"
        )
        self.abort_label.pack(pady=4)

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

        self.status_label.config(text="Waiting for sender...")

        worker = threading.Thread(
            target=self.wait_for_sender,
            daemon=True
        )
        worker.start()

    def _compute_qber(self, bob_sifted, sample_indices, alice_sample_bits):

        if not sample_indices:
            return 0.0, list(bob_sifted)

        valid_pairs = []
        for idx, alice_bit in zip(sample_indices, alice_sample_bits):
            if 0 <= idx < len(bob_sifted):
                valid_pairs.append((idx, alice_bit))

        if not valid_pairs:
            return 1.0, []

        errors = sum(1 for idx, alice_bit in valid_pairs if bob_sifted[idx] != alice_bit)
        qber = errors / len(valid_pairs)

        sample_set = {idx for idx, _ in valid_pairs}
        bob_remaining = [bit for i, bit in enumerate(bob_sifted) if i not in sample_set]

        return qber, bob_remaining

    def wait_for_sender(self):

        self.socket = start_server()

        self.status_label.config(text="Sender Connected")
        self.connection_label.config(text="Connected")

        message = receive_message(self.socket)
        print("Received:", message)

        if message != "START_BB84":
            self.status_label.config(text="Unexpected protocol message")
            return

        self.status_label.config(text="BB84 Session Started")

        alice_data = receive_list(self.socket)
        alice_bits = alice_data["bits"]
        alice_bases = alice_data["bases"]
        print("Alice bits and bases received")

        bob_bases, bob_results = bob_measure(alice_bits, alice_bases)
        send_list(self.socket, bob_bases)
        print("Bob bases sent")

        # Bob's sifted key must be built from Bob's measured bits.
        bob_sifted = sift_key(bob_results, alice_bases, bob_bases)

        sample_indices, alice_sample_bits = receive_qber_sample(self.socket)
        qber, bob_remaining = self._compute_qber(bob_sifted, sample_indices, alice_sample_bits)

        send_list(self.socket, {"qber": qber})

        qber_color = "#15803d" if qber <= QBER_THRESHOLD else "#b91c1c"
        self.qber_label.config(text=f"QBER: {qber * 100:.2f}%", foreground=qber_color)

        if qber > QBER_THRESHOLD:
            abort_text = f"ABORT: Eavesdropping detected (QBER={qber * 100:.2f}%)"
            self.status_label.config(text="BB84 Aborted")
            self.key_label.config(text="Key Aborted")
            self.abort_label.config(text=abort_text)
            print(abort_text)
            return

        final_key_bytes = privacy_amplify(bob_remaining)
        if not final_key_bytes:
            self.status_label.config(text="BB84 Aborted")
            self.key_label.config(text="Key Aborted")
            self.abort_label.config(text="Abort reason: insufficient key material")
            self.qber_label.config(text="QBER: N/A", foreground="#b91c1c")
            return

        self.shared_key = final_key_bytes
        self.abort_label.config(text="")
        self.key_label.config(text=f"Key Ready ({len(final_key_bytes) * 8} bits) | QBER: {qber * 100:.2f}%")
        self.status_label.config(text="BB84 Key Ready")

        message = receive_message(self.socket)

        if message != "FILE_TRANSFER":
            self.status_label.config(text="No file transfer request")
            return

        filename = receive_message(self.socket)
        encrypted_data = receive_file(self.socket)
        decrypted_data = xor_decrypt(encrypted_data, self.shared_key)

        os.makedirs("received_files", exist_ok=True)
        file_path = os.path.join("received_files", filename)
        with open(file_path, "wb") as file_obj:
            file_obj.write(decrypted_data)

        print("File received:", filename)
        self.file_label.config(text=f"Received: {filename}")
        self.status_label.config(text="File received and decrypted")

    def close_window(self):

        print("Receiver closing")

        try:
            if self.socket:
                self.socket.close()
        except Exception:
            pass

        self.window.destroy()
