# Qudrop - Quantum Secure File Transfer

## Abstract
Qudrop is an advanced, end-to-end Python application designed to demonstrate and simulate Quantum Key Distribution (QKD) for secure peer-to-peer file transfer. By implementing and evaluating multiple prominent QKD protocols—including **BB84, B92, E91, and Six-State**—the project provides a comprehensive sandbox for understanding quantum cryptography. The system derives highly secure, privacy-amplified shared keys from simulated quantum channels, which are then used to symmetrically encrypt various data types via a fast XOR cipher before transmission over classical TCP sockets. 

Beyond core file transfer, Qudrop features a robust error-rate analysis module to study the impact of quantum channel noise (bit-flip disturbances) on the Quantum Bit Error Rate (QBER) and the resulting classical file Bit Error Rate (BER). The application provides both a modernized React-based web interface driven by a FastAPI backend, as well as a legacy desktop GUI for direct local testing.

## Features
- **Multi-Protocol QKD Engine**: Full simulation of BB84, B92, E91, and Six-State protocols, including key generation, quantum measurement, and key sifting.
- **Modern Web Application**: A sleek, responsive React (Vite) frontend communicating with a high-performance Python FastAPI backend.
- **Comprehensive Error Analysis**: Automated scripts to analyze the effects of channel noise across different protocols, key lengths, and data types (text, binary, CSV, JSON).
- **P2P Secure Transfer**: Live, local TCP socket communication mirroring real-world Alice/Bob transfer dynamics.
- **File Agnostic Encryption**: Quantum keys are deterministically expanded via SHA-256 for XOR-based encryption of any file format.

## Project Structure

- `frontend/`: Modern React/Vite-based user interface.
- `server/`: FastAPI backend to bridge the web interface with core Python QKD logic.
- `gui/`: Legacy Tkinter desktop GUI (Sender/Receiver).
- `protocols/` & `bb84/`: Implementations of the supported QKD protocols.
- `analysis/`: Error-rate studies, automated testing scripts, and generated markdown/text reports.
- `network/`: TCP socket communication utilities for P2P networking.
- `encryption/`: Cryptographic utilities including XOR file encryption/decryption.
- `main.py` / `main_gui.py`: Entry points for the legacy GUI application.
- `simulation_qkd.py` / `test_error_rates.py`: Local testing and simulation scripts.

## Requirements

- **Python 3.10+**
- **Node.js 18+** (Required for running the modern React frontend)

## Setup (Recommended: Virtual Environment)

Create and activate a Python virtual environment:

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

Install dependencies:
```bash
pip install -r requirements.txt
```

Optional: If you want to use the Qiskit-backed measurement path instead of the built-in fallback simulator:
```bash
pip install qiskit qiskit-aer
```

## How to Run

### 1. Modern Web Application (Recommended)
You can run the modernized FastAPI and React stack.

**Start the FastAPI Backend:**
Open a terminal and start the server:
```bash
cd server
uvicorn main:app --reload --port 8000
```

**Start the React Frontend:**
Open a second terminal, navigate to the frontend directory, install dependencies, and start the Vite development server:
```bash
cd frontend
npm install
npm run dev
```

### 2. Legacy GUI Application
If you prefer the original Tkinter interface, you can run Alice (Sender) and Bob (Receiver) locally.

**Start Receiver (Bob)**
1. Run `python main.py`
2. Select **Receiver (Bob)** and click Start.
3. Click **Start Receiver**.

**Start Sender (Alice)**
1. Open a second terminal and run `python main.py`
2. Select **Sender (Alice)** and click Start.
3. Enter Receiver IP (use `127.0.0.1` for localhost).
4. Click **Connect**, then **Generate Key** (Select your preferred protocol).
5. Select a file and click **Send File**.

Received files are saved in the `received_files/` directory.

## Analysis & Simulation

To run the error rate analysis study (evaluating QBER and classical file BER under noise):
```bash
python analysis/error_rate_study.py
```
This will run trials across all supported protocols and generate reports (`error_rate_report.txt` and `error_rate_table.md`) in the `analysis` folder.

To run a basic script-based file transfer simulation:
```bash
python simulation_qkd.py
```

## Notes
- The default TCP port for the legacy app is `5000` (configured in `network/connection.py`).
- If Qiskit fails to import, the project automatically falls back to a pure-Python measurement model.
- Because the simulation doesn't currently execute the Information Reconciliation (Error Correction) phase, injecting noise will result in mismatched post-amplification keys and high final Bit Error Rates. This is expected and highlighted in the analysis reports.
