import tkinter as tk
from tkinter import ttk, messagebox

from gui.sender_window import SenderWindow
from gui.receiver_window import ReceiverWindow
from gui.simulation_window import SimulationWindow


class MainWindow:

    def __init__(self):

        self.root = tk.Tk()
        self.root.title("BB84 Secure File Transfer")
        self.root.geometry("400x300")

        self.mode = tk.StringVar()

        self.create_widgets()

    def create_widgets(self):

        title = ttk.Label(
            self.root,
            text="BB84 Secure File Transfer",
            font=("Arial", 16)
        )
        title.pack(pady=20)

        label = ttk.Label(
            self.root,
            text="Select Mode:",
            font=("Arial", 12)
        )
        label.pack(pady=10)

        sender_radio = ttk.Radiobutton(
            self.root,
            text="Sender",
            variable=self.mode,
            value="sender"
        )
        sender_radio.pack(pady=5)

        receiver_radio = ttk.Radiobutton(
            self.root,
            text="Receiver",
            variable=self.mode,
            value="receiver"
        )
        receiver_radio.pack(pady=5)

        start_button = ttk.Button(
            self.root,
            text="Start",
            command=self.start_mode
        )
        start_button.pack(pady=20)

        simulation_button = ttk.Button(
            self.root,
            text="Simulation Mode",
            command=self.open_simulation
        )
        simulation_button.pack(pady=5)

    def start_mode(self):

        selected = self.mode.get()

        if selected == "":
            messagebox.showwarning(
                "Warning",
                "Please select a mode"
            )
            return

        if selected == "sender":
            SenderWindow()

        elif selected == "receiver":
            ReceiverWindow()

    def open_simulation(self):

        SimulationWindow(self.root)

    def run(self):

        self.root.mainloop()
