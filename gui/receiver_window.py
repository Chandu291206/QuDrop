import os
import mimetypes
import threading
import time
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
        self.window.geometry("520x500")
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)

        self.socket = None
        self.shared_key = None

        backend = "Qiskit" if QISKIT_AVAILABLE else "Classical fallback"
        print(f"[QuDrop] Backend: {backend}")

        self.create_widgets()

    def create_widgets(self):

        title = ttk.Label(
            self.window,
            text="Receiver",
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

        self.data_type_label = ttk.Label(
            self.window,
            text="Data Type: N/A"
        )
        self.data_type_label.pack(pady=4)

        self.receive_rate_label = ttk.Label(
            self.window,
            text="Receive Rate: N/A"
        )
        self.receive_rate_label.pack(pady=4)

        self.transfer_error_label = ttk.Label(
            self.window,
            text="Transfer Error: N/A"
        )
        self.transfer_error_label.pack(pady=4)

    def start_receiver(self):

        self.status_label.config(text="Waiting for sender...")
        self.key_rate_label.config(text="Secure Key Rate: running...")
        self.receive_rate_label.config(text="Receive Rate: N/A")
        self.transfer_error_label.config(text="Transfer Error: N/A")

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
        key_start = time.perf_counter()

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
            self.key_rate_label.config(text="Secure Key Rate: N/A")
            print(abort_text)
            return

        final_key_bytes = privacy_amplify(bob_remaining)
        if not final_key_bytes:
            self.status_label.config(text="BB84 Aborted")
            self.key_label.config(text="Key Aborted")
            self.abort_label.config(text="Abort reason: insufficient key material")
            self.qber_label.config(text="QBER: N/A", foreground="#b91c1c")
            self.key_rate_label.config(text="Secure Key Rate: N/A")
            return

        self.shared_key = final_key_bytes
        self.abort_label.config(text="")
        key_bits = len(final_key_bytes) * 8
        key_elapsed = max(time.perf_counter() - key_start, 1e-9)
        key_rate_bps = key_bits / key_elapsed
        self.key_label.config(text=f"Key Ready ({key_bits} bits) | QBER: {qber * 100:.2f}%")
        self.key_rate_label.config(text=f"Secure Key Rate: {key_rate_bps:.2f} bit/s (live)")
        self.status_label.config(text="BB84 Key Ready")

        message = receive_message(self.socket)

        if message != "FILE_TRANSFER":
            self.status_label.config(text="No file transfer request")
            return

        filename = receive_message(self.socket)
        transfer_meta = receive_list(self.socket)
        include_reference = bool(transfer_meta.get("include_reference", False))
        file_type = self._detect_data_type(filename)
        receive_start = time.perf_counter()
        encrypted_data = receive_file(self.socket)
        reference_data = receive_file(self.socket) if include_reference else None
        receive_elapsed = max(time.perf_counter() - receive_start, 1e-9)
        decrypted_data = xor_decrypt(encrypted_data, self.shared_key)

        os.makedirs("received_files", exist_ok=True)
        file_path = os.path.join("received_files", filename)
        with open(file_path, "wb") as file_obj:
            file_obj.write(decrypted_data)

        print("File received:", filename)
        self.file_label.config(text=f"Received: {filename}")
        self._update_receive_rate_label(file_type, len(encrypted_data), receive_elapsed)
        result_payload = self._build_transfer_error_payload(reference_data, decrypted_data)
        send_list(self.socket, result_payload)
        self._update_transfer_error_label(result_payload)
        self.status_label.config(text="File received and decrypted")

    def _update_receive_rate_label(self, file_type, file_size, elapsed):

        kib_per_sec = (file_size / elapsed) / 1024
        self.data_type_label.config(text=f"Data Type: {file_type}")
        self.receive_rate_label.config(
            text=f"Receive Rate: {kib_per_sec:.2f} KiB/s ({file_size} bytes in {elapsed:.3f}s, live)"
        )

    def _detect_data_type(self, file_name):

        mime_type, _ = mimetypes.guess_type(file_name)
        if not mime_type:
            return "unknown"
        return mime_type.split("/", maxsplit=1)[0]

    def _build_transfer_error_payload(self, reference_data, decrypted_data):

        if reference_data is None:
            return {
                "mode": "disabled",
                "message": "test disabled"
            }

        bit_errors, total_bits, byte_errors, total_bytes = self._compute_transfer_error_rates(
            reference_data,
            decrypted_data
        )
        bit_error_rate_pct = (bit_errors / total_bits * 100.0) if total_bits else 0.0
        byte_error_rate_pct = (byte_errors / total_bytes * 100.0) if total_bytes else 0.0
        return {
            "mode": "exact",
            "bit_errors": bit_errors,
            "total_bits": total_bits,
            "byte_errors": byte_errors,
            "total_bytes": total_bytes,
            "bit_error_rate_pct": bit_error_rate_pct,
            "byte_error_rate_pct": byte_error_rate_pct
        }

    def _compute_transfer_error_rates(self, reference_data, decrypted_data):

        common_len = min(len(reference_data), len(decrypted_data))
        byte_errors = 0
        bit_errors = 0

        for i in range(common_len):
            ref_byte = reference_data[i]
            dec_byte = decrypted_data[i]
            if ref_byte != dec_byte:
                byte_errors += 1
                bit_errors += (ref_byte ^ dec_byte).bit_count()

        length_delta = abs(len(reference_data) - len(decrypted_data))
        byte_errors += length_delta
        bit_errors += length_delta * 8

        total_bytes = max(len(reference_data), len(decrypted_data))
        total_bits = total_bytes * 8
        return bit_errors, total_bits, byte_errors, total_bytes

    def _update_transfer_error_label(self, result_payload):

        if result_payload.get("mode") != "exact":
            message = result_payload.get("message", "not available")
            self.transfer_error_label.config(text=f"Transfer Error: {message}")
            return

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

    def close_window(self):

        print("Receiver closing")

        try:
            if self.socket:
                self.socket.close()
        except Exception:
            pass

        self.window.destroy()
