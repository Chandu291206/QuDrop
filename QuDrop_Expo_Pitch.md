# 🎤 QuDrop — 5-Minute Project Expo Pitch
**3 Presenters | ~5 Minutes Total**

---

## 🟦 Presenter 1 — The Problem & The Idea *(~1 min 30 sec)*

> *[Stand in front of the demo screen. Make eye contact with the audience.]*

"Good morning / afternoon, everyone.

Imagine you need to send a sensitive file — medical records, financial data, a confidential report — over the internet. You probably assume it's encrypted. And it is. But here's the catch: **the security of that encryption depends entirely on math problems that today's computers find hard to solve.**

The moment quantum computers become powerful enough, that protection collapses. Algorithms like RSA and AES, which we've trusted for decades, could be broken in minutes.

That's the problem we set out to address.

**Quantum Key Distribution — or QKD — offers a fundamentally different approach.** Instead of relying on computational hardness, it uses the laws of quantum physics themselves to generate encryption keys. If anyone tries to intercept the key, the laws of quantum mechanics ensure they *leave a trace* — and both parties can detect it immediately.

Our project, **QuDrop**, brings this concept to life. It is a full-stack, quantum-secure file transfer application that simulates QKD from the ground up — and actually transfers encrypted files between two peers over a real TCP connection."

---

## 🟩 Presenter 2 — How It Works *(~2 minutes)*

> *[Step forward. Point to the app running on screen.]*

"Let me walk you through how QuDrop works.

At the heart of the system is a **multi-protocol QKD engine**. We've implemented four major quantum key distribution protocols: **BB84, B92, E91, and the Six-State Protocol** — each with a different mechanism for encoding quantum information onto photon polarizations.

Here's the flow in simple terms:

1. **Alice** — the sender — fires simulated photons encoded with a random bit string, using randomly chosen quantum bases.
2. **Bob** — the receiver — measures those photons using his own randomly chosen bases.
3. After transmission, they publicly compare *which bases* they used — not the actual bits — and keep only the measurements where their bases matched. This is called **key sifting**.
4. The resulting shared secret is then passed through **privacy amplification** — a hashing step — to eliminate any information a potential eavesdropper may have gained.
5. That final key is used to encrypt the file using an **XOR cipher**, expanded securely via SHA-256.

On the technical side, QuDrop is built as a **modern web application** — a React frontend powered by Vite, communicating in real time with a Python FastAPI backend over WebSockets. The actual file transfer happens over **live TCP sockets**, directly mirroring how Alice and Bob would communicate in a real QKD scenario.

> *[Switch to the Simulation or Error Rate Analysis page on screen.]*

We also built a comprehensive **error-rate analysis module**. This lets us study the **Quantum Bit Error Rate — QBER** — under different noise conditions, across different protocols, key lengths, and file types including text, binary, CSV, and JSON. This is crucial for understanding when and why a quantum channel might be considered compromised."

---

## 🟥 Presenter 3 — Results, Impact & Demo *(~1 min 30 sec)*

> *[Move to the demo station or gesture to results.]*

"Let's talk about what we found — and what this means.

Our error-rate studies showed that in a **noise-free simulation**, all four protocols produce matching keys with zero bit errors — meaning perfect secure file transfer. When we introduce even a **25% eavesdropping disturbance**, the QBER spikes dramatically — well beyond the 11% threshold that flags the channel as compromised in BB84. The system can *detect* the intrusion before a single byte of actual data is exchanged.

This validates the core promise of QKD: **security that is physically guaranteed, not computationally assumed.**

> *[Optional: Live demo — show the sender sending a file, receiver getting it decrypted.]*

Here's QuDrop in action. We select a protocol, generate a quantum key, choose a file — and transfer it securely. The receiver gets the decrypted file on the other side.

**To summarize:**
- ✅ Four fully implemented QKD protocols
- ✅ Real encrypted P2P file transfer over TCP
- ✅ Modern web UI with real-time updates
- ✅ Quantitative error and noise analysis

QuDrop is not just a theoretical exercise. It's a working proof-of-concept that shows **quantum-safe communication is implementable today** — and positions us to understand and build the security infrastructure of tomorrow.

Thank you. We're happy to take any questions."

---

## ⏱️ Timing Guide

| Presenter | Topic | Duration |
|-----------|-------|----------|
| Presenter 1 | Problem, motivation, QKD intro | ~1:30 |
| Presenter 2 | Technical architecture & protocols | ~2:00 |
| Presenter 3 | Results, demo, conclusion | ~1:30 |
| **Total** | | **~5:00** |

---

## 💡 Tips for Delivery

- **Don't read off the screen.** Memorize the key transitions and speak naturally.
- **Point to the demo** when mentioning protocols, error rates, or the file transfer — make it visual.
- **Rehearse handoffs.** The transition between presenters should feel smooth, not abrupt. A brief nod or "I'll pass it to [name]" works well.
- **Dress consistently** — all three should match the expo dress code.
- **Prepare for one question each:** "How is this different from existing encryption?", "Can this run on real quantum hardware?", "What are the limitations?"
