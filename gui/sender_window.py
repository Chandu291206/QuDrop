import os
import random
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from bb84.bb84_core import (
    QBER_THRESHOLD,
    QISKIT_AVAILABLE,
    alice_generate,
    estimate_qber,
    privacy_amplify,
    sift_key,
)
from encryption.xor_cipher import xor_encrypt
from network.connection import (
    connect_to_server,
    receive_list,
    send_file as send_file_bytes,
    send_list,
    send_message,
    send_qber_sample,
)


class SenderWindow:

    def __init__(self):

        self.window = tk.Toplevel()
        self.window.title("BB84 Sender")
        self.window.geometry("520x560")
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)

        self.socket = None
        self.file_path = None
        self.shared_key = None

        backend = "Qiskit" if QISKIT_AVAILABLE else "Classical fallback"
        print(f"[QuDrop] Backend: {backend}")

        self.create_widgets()

    def create_widgets(self):

        title = ttk.Label(
            self.window,
            text="Sender (Alice)",
            font=("Arial", 16)
        )
        title.pack(pady=10)

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

        key_title = ttk.Label(
            self.window,
            text="BB84 Key Status:",
            font=("Arial", 12)
        )
        key_title.pack(pady=(10, 4))

        self.key_label = ttk.Label(
            self.window,
            text="Not Generated"
        )
        self.key_label.pack(pady=4)

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

        key_button = ttk.Button(
            self.window,
            text="Generate BB84 Key",
            command=self.generate_key
        )
        key_button.pack(pady=10)

        self.test_eve_var = tk.BooleanVar(value=False)
        self.test_eve_checkbox = ttk.Checkbutton(
            self.window,
            text="Enable Test Eve (inject BB84 disturbance)",
            variable=self.test_eve_var
        )
        self.test_eve_checkbox.pack(pady=4)

        self.test_eve_note = ttk.Label(
            self.window,
            text="Use for validation: expected QBER is around 25% and transfer should abort.",
            foreground="#6b7280"
        )
        self.test_eve_note.pack(pady=(0, 6))

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

        ip = self.ip_entry.get().strip()
        if not ip:
            messagebox.showwarning("Missing IP", "Enter receiver IP before connecting.")
            return

        try:
            self.socket = connect_to_server(ip)
            self.connection_label.config(text="Connected")
            print("Connected successfully")
        except Exception as e:
            print("Connection failed:", e)
            self.connection_label.config(text="Connection failed")
            messagebox.showerror("Connection Failed", str(e))

    def generate_key(self):

        if not self.socket:
            messagebox.showwarning("Not Connected", "Connect to receiver first.")
            return

        try:
            self.abort_label.config(text="")
            self.qber_label.config(text="QBER: running...", foreground="#1f2937")
            self.key_label.config(text="Generating...")

            send_message(self.socket, "START_BB84")
            print("START_BB84 sent")

            alice_bits, alice_bases = alice_generate()
            transmitted_bits = list(alice_bits)

            if self.test_eve_var.get():
                transmitted_bits = self._apply_test_eve(alice_bits, alice_bases)
                print("[QuDrop] Test Eve mode enabled: disturbance injected into transmitted bits.")

            send_list(self.socket, {
                "bits": transmitted_bits,
                "bases": alice_bases
            })
            print("Alice bits and bases sent")

            bob_bases = receive_list(self.socket)
            print("Bob bases received")

            alice_sifted = sift_key(alice_bits, alice_bases, bob_bases)
            if not alice_sifted:
                self.shared_key = None
                self.key_label.config(text="ABORTED: no sifted bits")
                self.abort_label.config(text="Abort reason: no matching bases")
                self.qber_label.config(text="QBER: N/A", foreground="#b91c1c")
                return

            _, sample_indices, alice_remaining, _ = estimate_qber(alice_sifted, alice_sifted)
            alice_sample_bits = [alice_sifted[i] for i in sample_indices]
            send_qber_sample(self.socket, sample_indices, alice_sample_bits)
            print("QBER sample revealed to receiver")

            qber_payload = receive_list(self.socket)
            qber = float(qber_payload.get("qber", 1.0))

            qber_color = "#15803d" if qber <= QBER_THRESHOLD else "#b91c1c"
            self.qber_label.config(text=f"QBER: {qber * 100:.2f}%", foreground=qber_color)

            if qber > QBER_THRESHOLD:
                self.shared_key = None
                abort_text = f"ABORT: Eavesdropping detected (QBER={qber * 100:.2f}%)"
                self.key_label.config(text="Key Aborted")
                self.abort_label.config(text=abort_text)
                messagebox.showerror("BB84 Aborted", abort_text)
                print(abort_text)
                return

            final_key_bytes = privacy_amplify(alice_remaining)
            if not final_key_bytes:
                self.shared_key = None
                self.key_label.config(text="ABORTED: privacy amplification failed")
                self.abort_label.config(text="Abort reason: insufficient key material")
                self.qber_label.config(text="QBER: N/A", foreground="#b91c1c")
                return

            self.shared_key = final_key_bytes
            key_bits = len(final_key_bytes) * 8
            self.key_label.config(text=f"Key Ready ({key_bits} bits) | QBER: {qber * 100:.2f}%")
            self.abort_label.config(text="")
            print(f"Shared key ready: {len(final_key_bytes)} bytes")

        except Exception as e:
            print("Error during key generation:", e)
            self.key_label.config(text="Key generation failed")
            self.abort_label.config(text=f"Abort reason: {e}")
            self.qber_label.config(text="QBER: error", foreground="#b91c1c")

    def _apply_test_eve(self, alice_bits, alice_bases):

        disturbed_bits = []

        for bit, basis in zip(alice_bits, alice_bases):
            eve_basis = random.choice(["Z", "X"])

            if eve_basis == basis:
                eve_bit = bit
            else:
                eve_bit = random.randint(0, 1)

            disturbed_bits.append(eve_bit)

        return disturbed_bits

    def select_file(self):

        file_path = filedialog.askopenfilename()

        if file_path:
            self.file_path = file_path
            self.file_label.config(text=file_path)
            print("Selected file:", file_path)

    def send_file(self):

        if not self.socket:
            messagebox.showwarning("Not Connected", "Connect to receiver first.")
            return

        if not self.shared_key:
            messagebox.showwarning("No Key", "Generate a BB84 key before sending a file.")
            return

        if not self.file_path:
            messagebox.showwarning("No File", "Select a file first.")
            return

        worker = threading.Thread(
            target=self.send_file_thread,
            daemon=True
        )
        worker.start()

    def send_file_thread(self):

        try:
            filename = os.path.basename(self.file_path)

            send_message(self.socket, "FILE_TRANSFER")
            send_message(self.socket, filename)

            with open(self.file_path, "rb") as file_obj:
                file_data = file_obj.read()

            encrypted_data = xor_encrypt(file_data, self.shared_key)
            send_file_bytes(self.socket, encrypted_data)

            print("File sent successfully")

        except Exception as e:
            print("Error during file send:", e)

    def close_window(self):

        print("Sender closing")

        try:
            if self.socket:
                self.socket.close()
        except Exception:
            pass

        self.window.destroy()
