import hashlib
import random

try:
    from qiskit import QuantumCircuit
    from qiskit_aer import AerSimulator
    from qiskit.compiler import transpile
    QISKIT_AVAILABLE = True
except Exception:
    QuantumCircuit = None
    AerSimulator = None
    transpile = None
    QISKIT_AVAILABLE = False

KEY_LENGTH = 32
QBER_THRESHOLD = 0.11  # 11% is the BB84 theoretical security bound


# Alice generates bits and bases
def alice_generate(length=KEY_LENGTH):

    bits = [random.randint(0, 1) for _ in range(length)]
    bases = [random.choice(["Z", "X"]) for _ in range(length)]

    return bits, bases


# Quantum Measurement (Bob)
def bob_measure(alice_bits, alice_bases):

    length = min(len(alice_bits), len(alice_bases))
    bob_bases = [random.choice(["Z", "X"]) for _ in range(length)]

    if QISKIT_AVAILABLE:

        try:
            simulator = AerSimulator()
            circuits = []

            for i in range(length):

                qc = QuantumCircuit(1, 1)

                # Alice encoding
                if alice_bits[i] == 1:
                    qc.x(0)

                if alice_bases[i] == "X":
                    qc.h(0)

                # Bob measurement basis
                if bob_bases[i] == "X":
                    qc.h(0)

                qc.measure(0, 0)
                circuits.append(qc)
                
            compiled = transpile(circuits, simulator)
            job = simulator.run(compiled, shots=1)
            result = job.result()
            
            results = []
            for i in range(length):
                counts = result.get_counts(i)
                bit = int(list(counts.keys())[0])
                results.append(bit)

            return bob_bases, results

        except Exception:
            pass

    # Fallback simulator without Qiskit:
    # same basis -> Bob gets Alice's bit, different basis -> random bit.
    results = []
    for i in range(length):
        if alice_bases[i] == bob_bases[i]:
            results.append(alice_bits[i])
        else:
            results.append(random.randint(0, 1))

    return bob_bases, results


# Key Sifting
def sift_key(alice_bits, alice_bases, bob_bases):

    length = min(len(alice_bits), len(alice_bases), len(bob_bases))
    key = []

    for i in range(length):

        if alice_bases[i] == bob_bases[i]:

            key.append(alice_bits[i])

    return key


def run_bb84_simulation(n_bits=20, eve=False):

    try:
        n_bits = int(n_bits)
    except (TypeError, ValueError):
        n_bits = 20

    if n_bits < 1:
        n_bits = 1

    alice_bits = [random.randint(0, 1) for _ in range(n_bits)]
    alice_bases = [random.choice(["+", "x"]) for _ in range(n_bits)]
    bob_bases = [random.choice(["+", "x"]) for _ in range(n_bits)]

    bob_results = []

    if eve:
        eve_bases = [random.choice(["+", "x"]) for _ in range(n_bits)]

        for i in range(n_bits):
            if eve_bases[i] == alice_bases[i]:
                eve_bit = alice_bits[i]
            else:
                eve_bit = random.randint(0, 1)

            if bob_bases[i] == eve_bases[i]:
                bob_results.append(eve_bit)
            else:
                bob_results.append(random.randint(0, 1))

    else:
        for i in range(n_bits):
            if alice_bases[i] == bob_bases[i]:
                bob_results.append(alice_bits[i])
            else:
                bob_results.append(random.randint(0, 1))

    matches = [alice_bases[i] == bob_bases[i] for i in range(n_bits)]
    final_key = [bob_results[i] for i in range(n_bits) if matches[i]]
    alice_sifted = [alice_bits[i] for i in range(n_bits) if matches[i]]

    if final_key:
        errors = sum(1 for i in range(len(final_key)) if final_key[i] != alice_sifted[i])
        qber = errors / len(final_key)
    else:
        qber = 0.0

    return {
        "alice_bits": alice_bits,
        "alice_bases": alice_bases,
        "bob_bases": bob_bases,
        "bob_results": bob_results,
        "matches": matches,
        "final_key": final_key,
        "qber": qber
    }


def estimate_qber(alice_sifted, bob_sifted, sample_fraction=0.25):
    """Estimate QBER from a random sample and discard sampled positions.

    Returns:
        (qber, sample_indices, alice_remaining, bob_remaining)
    """
    n = min(len(alice_sifted), len(bob_sifted))
    if n == 0:
        return 0.0, [], [], []

    k = max(1, int(n * sample_fraction))
    k = min(k, n)
    sample_indices = sorted(random.sample(range(n), k))

    sample_set = set(sample_indices)
    errors = sum(1 for i in sample_indices if alice_sifted[i] != bob_sifted[i])
    qber = errors / k

    alice_remaining = [alice_sifted[i] for i in range(n) if i not in sample_set]
    bob_remaining = [bob_sifted[i] for i in range(n) if i not in sample_set]

    return qber, sample_indices, alice_remaining, bob_remaining


def privacy_amplify(key_bits, target_length=None):
    """Compress sifted key bits into final key bytes via SHA-256.

    target_length is in bytes. If omitted, defaults to len(key_bits) // 2.
    """
    if not key_bits:
        return b""

    # Pack bits into bytes (MSB first), pad to full bytes.
    pad = (-len(key_bits)) % 8
    bits = list(key_bits) + [0] * pad
    raw = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for b in bits[i:i + 8]:
            byte = (byte << 1) | b
        raw.append(byte)

    if target_length is None:
        target_length = max(1, len(key_bits) // 2)

    target_length = max(1, int(target_length))
    seed = bytes(raw)
    digest = hashlib.sha256(seed).digest()

    if target_length <= len(digest):
        return digest[:target_length]

    # Expand deterministically for callers asking more than one digest.
    output = bytearray()
    counter = 0
    while len(output) < target_length:
        block = hashlib.sha256(seed + counter.to_bytes(4, "big")).digest()
        output.extend(block)
        counter += 1

    return bytes(output[:target_length])

