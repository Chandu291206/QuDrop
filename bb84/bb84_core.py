import random
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit.compiler import transpile

KEY_LENGTH = 32


# Alice generates bits and bases
def alice_generate():

    bits = [random.randint(0, 1) for _ in range(KEY_LENGTH)]

    bases = [random.choice(['Z', 'X']) for _ in range(KEY_LENGTH)]

    return bits, bases


# Quantum Measurement (Bob)
def bob_measure(alice_bits, alice_bases):

    simulator = AerSimulator()

    bob_bases = [random.choice(['Z', 'X']) for _ in range(KEY_LENGTH)]

    results = []

    for i in range(KEY_LENGTH):

        qc = QuantumCircuit(1, 1)

        # Alice Encoding

        if alice_bits[i] == 1:
            qc.x(0)

        if alice_bases[i] == 'X':
            qc.h(0)

        # Bob Measurement Basis

        if bob_bases[i] == 'X':
            qc.h(0)

        qc.measure(0, 0)

        compiled = transpile(qc, simulator)

        job = simulator.run(compiled, shots=1)

        result = job.result()

        counts = result.get_counts()

        bit = int(list(counts.keys())[0])

        results.append(bit)

    return bob_bases, results


# Key Sifting
def sift_key(alice_bits, alice_bases, bob_bases):

    key = []

    for i in range(KEY_LENGTH):

        if alice_bases[i] == bob_bases[i]:

            key.append(alice_bits[i])

    return key