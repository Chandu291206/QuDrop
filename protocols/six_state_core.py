import random

def alice_generate_six_state(length):
    """
    Six-State Protocol Key Generation.
    Alice generates random bits and encodes them in one of 3 bases (Z, X, Y).
    """
    bits = [random.randint(0, 1) for _ in range(length)]
    bases = [random.choice(["Z", "X", "Y"]) for _ in range(length)]
    return bits, bases

def bob_measure_six_state(alice_bits, alice_bases):
    """
    Bob measures the incoming qubits in a random basis (Z, X, Y).
    """
    length = min(len(alice_bits), len(alice_bases))
    bob_bases = [random.choice(["Z", "X", "Y"]) for _ in range(length)]
    bob_results = []
    
    for i in range(length):
        if alice_bases[i] == bob_bases[i]:
            # Same basis -> deterministic correct bit
            bob_results.append(alice_bits[i])
        else:
            # Different basis -> 50% chance of random bit
            bob_results.append(random.randint(0, 1))
            
    return bob_bases, bob_results

def sift_key_six_state(alice_bits, alice_bases, bob_bases):
    """
    Sifts the key by keeping only positions where Alice and Bob 
    chose the same basis. Efficiency is ~1/3.
    """
    length = min(len(alice_bits), len(alice_bases), len(bob_bases))
    key = []
    
    for i in range(length):
        if alice_bases[i] == bob_bases[i]:
            key.append(alice_bits[i])
            
    return key
