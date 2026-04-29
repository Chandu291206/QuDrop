import random

def generate_e91_key(length):
    """
    E91 Protocol (Entanglement based).
    Simulates a source distributing entangled EPR pairs to Alice and Bob.
    Both choose random measurement bases.
    """
    alice_bases = [random.choice(["Z", "X"]) for _ in range(length)]
    bob_bases = [random.choice(["Z", "X"]) for _ in range(length)]
    
    alice_bits = []
    bob_bits = []
    
    for i in range(length):
        a_basis = alice_bases[i]
        b_basis = bob_bases[i]
        
        # Simulating Phi+ Bell state correlation
        if a_basis == b_basis:
            # 100% correlated if measured in the same basis
            bit = random.randint(0, 1)
            alice_bits.append(bit)
            bob_bits.append(bit)
        else:
            # Uncorrelated if measured in different bases
            alice_bits.append(random.randint(0, 1))
            bob_bits.append(random.randint(0, 1))
            
    return alice_bits, bob_bits, alice_bases, bob_bases

def sift_key_e91(alice_bits, bob_bits, alice_bases, bob_bases):
    """
    Sifts the E91 key by keeping only positions where Alice and Bob 
    chose the same measurement basis.
    """
    length = min(len(alice_bits), len(bob_bits), len(alice_bases), len(bob_bases))
    
    alice_sifted = []
    bob_sifted = []
    
    for i in range(length):
        if alice_bases[i] == bob_bases[i]:
            alice_sifted.append(alice_bits[i])
            bob_sifted.append(bob_bits[i])
            
    return alice_sifted, bob_sifted
