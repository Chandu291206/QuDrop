import random

def alice_generate_b92(length):
    """
    Alice generates random bits and encodes them using B92 protocol.
    0 -> |0> (Z basis)
    1 -> |+> (X basis)
    """
    bits = [random.randint(0, 1) for _ in range(length)]
    bases = ["Z" if b == 0 else "X" for b in bits]
    return bits, bases

def bob_measure_b92(alice_bits, alice_bases):
    """
    Bob measures the incoming qubits in a random basis (Z or X).
    In B92, if Bob measures 1, he gets a conclusive result about Alice's bit.
    - If Alice sends |0> (Z) and Bob measures Z -> 0 (100%)
    - If Alice sends |0> (Z) and Bob measures X -> 0 or 1 (50%)
    - If Alice sends |+> (X) and Bob measures Z -> 0 or 1 (50%)
    - If Alice sends |+> (X) and Bob measures X -> 0 (100%) (assuming standard mapping H|+> = |0>)
    
    Conclusive result is when Bob measures 1.
    """
    length = min(len(alice_bits), len(alice_bases))
    bob_bases = [random.choice(["Z", "X"]) for _ in range(length)]
    bob_results = []
    
    for i in range(length):
        if alice_bases[i] == bob_bases[i]:
            # Same basis: deterministic 0 (in our standard mapping)
            bob_results.append(0)
        else:
            # Different basis: 50% chance of 0 or 1
            bob_results.append(random.randint(0, 1))
            
    # keep_mask represents positions where Bob got a conclusive result (measured 1)
    keep_mask = [res == 1 for res in bob_results]
    return bob_bases, bob_results, keep_mask

def sift_key_b92(alice_bits, keep_mask):
    """
    Sift the key based on Bob's conclusive measurement mask.
    Bob only keeps bits where his measurement was 1.
    For these positions, he knows Alice's bit:
    - If his basis was Z and he got 1, Alice must have sent |+> (bit 1)
    - If his basis was X and he got 1, Alice must have sent |0> (bit 0)
    We extract the corresponding Alice bits using the mask.
    """
    length = min(len(alice_bits), len(keep_mask))
    key = []
    for i in range(length):
        if keep_mask[i]:
            key.append(alice_bits[i])
    return key
