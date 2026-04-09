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
            results = []

            for i in range(length):

                qc = QuantumCircuit(1, 1)

                # Alice Encoding
                if alice_bits[i] == 1:
                    qc.x(0)

                if alice_bases[i] == "X":
                    qc.h(0)

                # Bob Measurement Basis
                if bob_bases[i] == "X":
                    qc.h(0)

                qc.measure(0, 0)
                compiled = transpile(qc, simulator)
                job = simulator.run(compiled, shots=1)
                result = job.result()
                counts = result.get_counts()
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
