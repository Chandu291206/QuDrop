# Qudrop - BB84 Secure File Transfer

Qudrop is a Python project that demonstrates BB84 quantum key distribution (QKD) for secure file transfer.

It includes:
- A GUI app to run as Sender (Alice) or Receiver (Bob)
- A local simulation script that encrypts/decrypts a file using a BB84-derived key

## Project Structure

- `main.py`: Starts the GUI app
- `gui/`: Sender/Receiver windows and main mode selector
- `bb84/bb84_core.py`: BB84 key generation, measurement, and key sifting logic
- `network/connection.py`: TCP socket communication utilities
- `encryption/xor_cipher.py`: XOR-based file encryption/decryption
- `simulation_qkd.py`: End-to-end local BB84 file transfer simulation

## Requirements

- Python 3.10+ (Python 3.9 is not required)
- Tkinter (usually included with standard Python on Windows)

This project runs without mandatory third-party packages.

## Setup (Recommended: Virtual Environment)

Create and activate a virtual environment before running the project.

### Windows (PowerShell)

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Install optional dependencies from `requirements.txt`:

```bash
pip install -r requirements.txt
```

Optional: if you want to use the Qiskit-backed measurement path instead of the built-in fallback simulator:

```bash
pip install qiskit qiskit-aer
```

Deactivate the environment when done:

```bash
deactivate
```

## How to Run (GUI Mode)

### 1. Start Receiver (Bob)

```bash
python main.py
```

- Select `Receiver (Bob)`
- Click `Start`
- In the receiver window, click `Start Receiver`

### 2. Start Sender (Alice)

Open a second terminal (or second machine) and run:

```bash
python main.py
```

- Select `Sender (Alice)`
- Click `Start`
- Enter Receiver IP (use `127.0.0.1` if both are on the same machine)
- Click `Connect`
- Click `Generate BB84 Key`
- Click `Select File` and choose a file
- Click `Send File`

Received files are saved in:

```text
received_files/
```

## How to Run Simulation

### GUI Simulation Mode

```bash
python main.py
```

- Click `Simulation Mode`
- Set Number of Bits and optionally enable Eve (eavesdropping)
- Click `Generate` for full results or `Step-by-Step` for animated stages

### Local Script Simulation

To run the script-based simulation with default input file (`test.txt`):

```bash
python simulation_qkd.py
```

This generates:
- `ciphertext.bin`
- `decrypted.txt`

## Notes

- Default TCP port is `5000` (configured in `network/connection.py`).
- If sender cannot connect, make sure firewall rules allow the port.
- If Qiskit fails to import (DLL/runtime issues), the project automatically falls back to a pure-Python BB84 measurement model.
