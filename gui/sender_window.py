import os
import mimetypes
import random
import threading
import time
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
        self.window.geometry("520x660")
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)

        self.socket = None
        self.file_path = None
        self.shared_key = None
        self.raw_bits_var = tk.StringVar(value="256")
        self.channel_noise_var = tk.BooleanVar(value=False)
        self.channel_noise_rate_var = tk.StringVar(value="0.02")
        self.transfer_error_test_var = tk.BooleanVar(value=True)

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

        self.key_rate_label = ttk.Label(
            self.window,
            text="Secure Key Rate: N/A"
        )
        self.key_rate_label.pack(pady=4)

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

        key_bits_row = ttk.Frame(self.window)
        key_bits_row.pack(pady=4)
        ttk.Label(
            key_bits_row,
            text="Raw BB84 bits:"
        ).pack(side="left", padx=(0, 6))
        ttk.Entry(
            key_bits_row,
            width=8,
            textvariable=self.raw_bits_var
        ).pack(side="left")

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

        self.channel_noise_checkbox = ttk.Checkbutton(
            self.window,
            text="Enable Channel Noise (bit flips in BB84 transmission)",
            variable=self.channel_noise_var
        )
        self.channel_noise_checkbox.pack(pady=4)

        noise_row = ttk.Frame(self.window)
        noise_row.pack(pady=2)
        ttk.Label(
            noise_row,
            text="Noise probability (0 to 1):"
        ).pack(side="left", padx=(0, 6))
        ttk.Entry(
            noise_row,
            width=8,
            textvariable=self.channel_noise_rate_var
        ).pack(side="left")

        self.transfer_error_checkbox = ttk.Checkbutton(
            self.window,
            text="Enable Exact Transfer Error Test (sends plaintext reference)",
            variable=self.transfer_error_test_var
        )
        self.transfer_error_checkbox.pack(pady=6)

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

        self.data_type_label = ttk.Label(
            self.window,
            text="Data Type: N/A"
        )
        self.data_type_label.pack(pady=4)

        self.transfer_rate_label = ttk.Label(
            self.window,
            text="Send Rate: N/A"
        )
        self.transfer_rate_label.pack(pady=4)

        self.transfer_error_label = ttk.Label(
            self.window,
            text="Transfer Error: N/A"
        )
        self.transfer_error_label.pack(pady=4)

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

        raw_bits = self._parse_raw_bit_count()
        if raw_bits is None:
            return

        noise_probability = self._parse_noise_probability()
        if noise_probability is None:
            return

        try:
            start_time = time.perf_counter()
            self.abort_label.config(text="")
            self.qber_label.config(text="QBER: running...", foreground="#1f2937")
            self.key_rate_label.config(text="Secure Key Rate: running...")
            self.key_label.config(text="Generating...")

            send_message(self.socket, "START_BB84")
            print("START_BB84 sent")

            alice_bits, alice_bases = alice_generate(length=raw_bits)
            transmitted_bits = list(alice_bits)

            if self.test_eve_var.get():
                transmitted_bits = self._apply_test_eve(alice_bits, alice_bases)
                print("[QuDrop] Test Eve mode enabled: disturbance injected into transmitted bits.")

            if noise_probability > 0.0:
                transmitted_bits, flip_count = self._apply_channel_noise(transmitted_bits, noise_probability)
                print(
                    f"[QuDrop] Channel noise enabled: p={noise_probability:.4f}, "
                    f"flipped={flip_count}/{len(transmitted_bits)} bits."
                )

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
                self.key_rate_label.config(text="Secure Key Rate: N/A")
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
                self.key_rate_label.config(text="Secure Key Rate: N/A")
                messagebox.showerror("BB84 Aborted", abort_text)
                print(abort_text)
                return

            final_key_bytes = privacy_amplify(alice_remaining)
            if not final_key_bytes:
                self.shared_key = None
                self.key_label.config(text="ABORTED: privacy amplification failed")
                self.abort_label.config(text="Abort reason: insufficient key material")
                self.qber_label.config(text="QBER: N/A", foreground="#b91c1c")
                self.key_rate_label.config(text="Secure Key Rate: N/A")
                return

            self.shared_key = final_key_bytes
            key_bits = len(final_key_bytes) * 8
            elapsed = max(time.perf_counter() - start_time, 1e-9)
            key_rate_bps = key_bits / elapsed
            self.key_label.config(text=f"Key Ready ({key_bits} bits) | QBER: {qber * 100:.2f}%")
            self.key_rate_label.config(
                text=f"Secure Key Rate: {key_rate_bps:.2f} bit/s (live)"
            )
            self.abort_label.config(text="")
            print(f"Shared key ready: {len(final_key_bytes)} bytes")

        except Exception as e:
            print("Error during key generation:", e)
            self.key_label.config(text="Key generation failed")
            self.abort_label.config(text=f"Abort reason: {e}")
            self.qber_label.config(text="QBER: error", foreground="#b91c1c")
            self.key_rate_label.config(text="Secure Key Rate: error")

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

    def _apply_channel_noise(self, bits, flip_probability):

        noisy_bits = []
        flips = 0
        for bit in bits:
            if random.random() < flip_probability:
                noisy_bits.append(1 - bit)
                flips += 1
            else:
                noisy_bits.append(bit)

        return noisy_bits, flips

    def _parse_raw_bit_count(self):

        try:
            value = int(self.raw_bits_var.get().strip())
        except (TypeError, ValueError):
            messagebox.showwarning("Invalid Raw Bits", "Raw BB84 bits must be an integer (e.g., 256).")
            return None

        if value < 32 or value > 4096:
            messagebox.showwarning("Invalid Raw Bits", "Use a value between 32 and 4096.")
            return None

        return value

    def _parse_noise_probability(self):

        if not self.channel_noise_var.get():
            return 0.0

        try:
            value = float(self.channel_noise_rate_var.get().strip())
        except (TypeError, ValueError):
            messagebox.showwarning("Invalid Noise", "Noise probability must be a number between 0 and 1.")
            return None

        if value < 0.0 or value > 1.0:
            messagebox.showwarning("Invalid Noise", "Noise probability must be between 0 and 1.")
            return None

        return value

    def select_file(self):

        file_path = filedialog.askopenfilename()

        if file_path:
            self.file_path = file_path
            self.file_label.config(text=file_path)
            self.data_type_label.config(text=f"Data Type: {self._detect_data_type(file_path)}")
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
        self.transfer_rate_label.config(text="Send Rate: sending...")
        self.transfer_error_label.config(text="Transfer Error: waiting...")
        worker.start()

    def send_file_thread(self):

        try:
            filename = os.path.basename(self.file_path)
            file_type = self._detect_data_type(filename)

            send_message(self.socket, "FILE_TRANSFER")
            send_message(self.socket, filename)

            with open(self.file_path, "rb") as file_obj:
                file_data = file_obj.read()

            encrypted_data = xor_encrypt(file_data, self.shared_key)
            include_reference = self.transfer_error_test_var.get()
            send_list(self.socket, {
                "include_reference": include_reference
            })
            send_start = time.perf_counter()
            send_file_bytes(self.socket, encrypted_data)
            if include_reference:
                send_file_bytes(self.socket, file_data)
            send_elapsed = max(time.perf_counter() - send_start, 1e-9)
            self.window.after(
                0,
                self._update_send_rate_label,
                file_type,
                len(file_data),
                send_elapsed
            )
            result_payload = receive_list(self.socket)
            self.window.after(0, self._update_transfer_error_label, result_payload)

            print("File sent successfully")

        except Exception as e:
            print("Error during file send:", e)
            self.window.after(0, self._set_send_rate_error)
            self.window.after(0, self._set_transfer_error_error)

    def _update_send_rate_label(self, file_type, file_size, elapsed):

        kib_per_sec = (file_size / elapsed) / 1024
        self.data_type_label.config(text=f"Data Type: {file_type}")
        self.transfer_rate_label.config(
            text=f"Send Rate: {kib_per_sec:.2f} KiB/s ({file_size} bytes in {elapsed:.3f}s, live)"
        )

    def _detect_data_type(self, file_name):

        mime_type, _ = mimetypes.guess_type(file_name)
        if not mime_type:
            return "unknown"
        return mime_type.split("/", maxsplit=1)[0]

    def _set_send_rate_error(self):

        self.transfer_rate_label.config(text="Send Rate: error")

    def _update_transfer_error_label(self, result_payload):

        mode = result_payload.get("mode", "unknown")
        if mode == "exact":
            ber = float(result_payload.get("bit_error_rate_pct", 0.0))
            byte_error = float(result_payload.get("byte_error_rate_pct", 0.0))
            bit_errors = int(result_payload.get("bit_errors", 0))
            total_bits = int(result_payload.get("total_bits", 0))
            self.transfer_error_label.config(
                text=(
                    f"Transfer Error: BER={ber:.6f}% | Byte Error={byte_error:.6f}% "
                    f"({bit_errors}/{total_bits} bits)"
                )
            )
            return

        message = result_payload.get("message", "not available")
        self.transfer_error_label.config(text=f"Transfer Error: {message}")

    def _set_transfer_error_error(self):

        self.transfer_error_label.config(text="Transfer Error: error")

    def close_window(self):

        print("Sender closing")

        try:
            if self.socket:
                self.socket.close()
        except Exception:
            pass

        self.window.destroy()
