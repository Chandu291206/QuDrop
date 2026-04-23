import tkinter as tk
from tkinter import ttk, messagebox

from bb84.bb84_core import QBER_THRESHOLD, QISKIT_AVAILABLE, run_bb84_simulation


class SimulationWindow:

    def __init__(self, parent=None):

        self.window = tk.Toplevel(parent)
        self.window.title("BB84 Simulation")
        self.window.geometry("980x520")
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)

        self.simulation_data = None
        self.step_index = 0
        self.after_job = None
        self.is_animating = False

        self.bits_var = tk.StringVar(value="20")
        self.eve_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="Ready.")

        backend = "Qiskit" if QISKIT_AVAILABLE else "Classical fallback"
        print(f"[QuDrop] Backend: {backend}")

        self.create_widgets()

    def create_widgets(self):

        controls_frame = ttk.LabelFrame(self.window, text="Controls", padding=10)
        controls_frame.pack(fill="x", padx=10, pady=10)

        bits_label = ttk.Label(controls_frame, text="Number of Bits:")
        bits_label.grid(row=0, column=0, sticky="w")

        self.bits_entry = ttk.Entry(controls_frame, textvariable=self.bits_var, width=10)
        self.bits_entry.grid(row=0, column=1, padx=(8, 16), sticky="w")

        eve_checkbox = ttk.Checkbutton(
            controls_frame,
            text="Enable Eve (Eavesdropping)",
            variable=self.eve_var
        )
        eve_checkbox.grid(row=0, column=2, padx=(0, 16), sticky="w")

        self.generate_button = ttk.Button(
            controls_frame,
            text="Generate",
            command=self.generate_full_view
        )
        self.generate_button.grid(row=0, column=3, padx=4)

        self.step_button = ttk.Button(
            controls_frame,
            text="Step-by-Step",
            command=self.run_step_by_step
        )
        self.step_button.grid(row=0, column=4, padx=4)

        self.reset_button = ttk.Button(
            controls_frame,
            text="Reset",
            command=self.reset
        )
        self.reset_button.grid(row=0, column=5, padx=4)

        controls_frame.columnconfigure(6, weight=1)

        display_frame = ttk.LabelFrame(self.window, text="Display", padding=10)
        display_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.display_text = tk.Text(
            display_frame,
            font=("Consolas", 12),
            wrap="none",
            height=14
        )

        x_scroll = ttk.Scrollbar(display_frame, orient="horizontal", command=self.display_text.xview)
        y_scroll = ttk.Scrollbar(display_frame, orient="vertical", command=self.display_text.yview)
        self.display_text.configure(xscrollcommand=x_scroll.set, yscrollcommand=y_scroll.set)

        self.display_text.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

        display_frame.rowconfigure(0, weight=1)
        display_frame.columnconfigure(0, weight=1)

        self.display_text.tag_configure("match", foreground="#15803d")
        self.display_text.tag_configure("mismatch", foreground="#b91c1c")
        self.display_text.tag_configure("label", foreground="#1f2937")

        self.status_label = ttk.Label(self.window, textvariable=self.status_var)
        self.status_label.pack(fill="x", padx=12, pady=(0, 10))

        self.clear_display()

    def _parse_n_bits(self):

        try:
            n_bits = int(self.bits_var.get().strip())
            if n_bits < 1:
                raise ValueError
            return n_bits
        except ValueError:
            messagebox.showerror("Invalid Input", "Number of Bits must be a positive integer.")
            return None

    def _build_simulation(self):

        n_bits = self._parse_n_bits()
        if n_bits is None:
            return False

        self.simulation_data = run_bb84_simulation(
            n_bits=n_bits,
            eve=self.eve_var.get()
        )
        return True

    def generate_full_view(self):

        self._cancel_animation()

        if not self._build_simulation():
            return

        self.step_index = 5
        self.render_step()
        self._set_final_status()

    def run_step_by_step(self):

        self._cancel_animation()

        if not self._build_simulation():
            return

        self.is_animating = True
        self.step_index = 1
        self.generate_button.config(state="disabled")
        self.step_button.config(state="disabled")
        self.render_step()
        self._set_step_status()
        self.after_job = self.window.after(1000, self._advance_step)

    def _advance_step(self):

        if not self.is_animating:
            return

        self.step_index += 1

        if self.step_index > 5:
            self._cancel_animation()
            self._set_final_status()
            return

        self.render_step()
        self._set_step_status()
        self.after_job = self.window.after(1000, self._advance_step)

    def _cancel_animation(self):

        if self.after_job is not None:
            self.window.after_cancel(self.after_job)
            self.after_job = None

        self.is_animating = False
        self.generate_button.config(state="normal")
        self.step_button.config(state="normal")

    def clear_display(self):

        self.display_text.config(state="normal")
        self.display_text.delete("1.0", "end")
        self.display_text.insert("end", "Alice Bits:   \n")
        self.display_text.insert("end", "Alice Bases:  \n\n")
        self.display_text.insert("end", "Bob Bases:    \n")
        self.display_text.insert("end", "Bob Results:  \n\n")
        self.display_text.insert("end", "Matches:      \n")
        self.display_text.insert("end", "Final Key:    \n")
        self.display_text.insert("end", "QBER:         \n")
        self.display_text.config(state="disabled")

    def render_step(self):

        if not self.simulation_data:
            self.clear_display()
            return

        data = self.simulation_data
        n_bits = len(data["alice_bits"])

        alice_bits = " ".join(str(bit) for bit in data["alice_bits"]) if self.step_index >= 1 else ""
        alice_bases = " ".join(data["alice_bases"]) if self.step_index >= 1 else ""
        bob_bases = " ".join(data["bob_bases"]) if self.step_index >= 2 else " ".join("?" for _ in range(n_bits))
        bob_results = " ".join(str(bit) for bit in data["bob_results"]) if self.step_index >= 3 else " ".join("?" for _ in range(n_bits))
        final_key = " ".join(str(bit) for bit in data["final_key"]) if self.step_index >= 5 else ""
        qber_text = f"{data['qber']:.2f}" if self.step_index >= 5 else ""

        self.display_text.config(state="normal")
        self.display_text.delete("1.0", "end")

        self._insert_plain_row("Alice Bits:", alice_bits)
        self._insert_plain_row("Alice Bases:", alice_bases)
        self.display_text.insert("end", "\n")
        self._insert_plain_row("Bob Bases:", bob_bases)
        self._insert_plain_row("Bob Results:", bob_results)
        self.display_text.insert("end", "\n")
        self._insert_matches_row(data["matches"], reveal=self.step_index >= 4)
        self._insert_plain_row("Final Key:", final_key)
        self._insert_plain_row("QBER:", qber_text)

        self.display_text.config(state="disabled")

    def _insert_plain_row(self, label, value):

        padded_label = f"{label:<12} "
        self.display_text.insert("end", padded_label, "label")
        self.display_text.insert("end", f"{value}\n")

    def _insert_matches_row(self, matches, reveal):

        padded_label = f"{'Matches:':<12} "
        self.display_text.insert("end", padded_label, "label")

        if not reveal:
            placeholders = " ".join("?" for _ in matches)
            self.display_text.insert("end", f"{placeholders}\n")
            return

        for i, matched in enumerate(matches):
            symbol = "\u2705" if matched else "\u274c"
            tag = "match" if matched else "mismatch"
            spacer = " " if i < len(matches) - 1 else ""
            self.display_text.insert("end", symbol + spacer, tag)

        self.display_text.insert("end", "\n")

    def _set_step_status(self):

        messages = {
            1: "Step 1/5: Alice generated random bits and bases.",
            2: "Step 2/5: Bob's random bases are revealed.",
            3: "Step 3/5: Bob's measured bits are revealed.",
            4: "Step 4/5: Basis comparison shows matches and mismatches.",
            5: "Step 5/5: Final sifted key and QBER are shown."
        }
        self.status_var.set(messages.get(self.step_index, "Running simulation..."))
        self.status_label.config(foreground="#1f2937")

    def _set_final_status(self):

        if not self.simulation_data:
            self.status_var.set("Ready.")
            self.status_label.config(foreground="#1f2937")
            return

        qber = self.simulation_data["qber"]
        if qber > QBER_THRESHOLD:
            self.status_var.set("Eavesdropping Detected!")
            self.status_label.config(foreground="#b91c1c")
        else:
            self.status_var.set("Simulation complete.")
            self.status_label.config(foreground="#1f2937")

    def reset(self):

        self._cancel_animation()
        self.simulation_data = None
        self.step_index = 0
        self.bits_var.set("20")
        self.eve_var.set(False)
        self.status_var.set("Ready.")
        self.status_label.config(foreground="#1f2937")
        self.clear_display()

    def close_window(self):

        self._cancel_animation()
        self.window.destroy()
