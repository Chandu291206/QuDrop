import random
from protocols import PROTOCOLS
from bb84.bb84_core import estimate_qber, privacy_amplify

class ProtocolRunner:
    @staticmethod
    def alice_generate(protocol, length):
        if protocol not in PROTOCOLS:
            raise ValueError(f"Unknown protocol: {protocol}")
        
        if protocol == "E91":
            # For E91 simulation over network, Alice generates the correlated bits
            # as if she's the entanglement source.
            alice_bits, bob_bits, alice_bases, bob_bases = PROTOCOLS[protocol]["generate_key"](length)
            return alice_bits, alice_bases
        else:
            return PROTOCOLS[protocol]["alice_generate"](length)
            
    @staticmethod
    def bob_measure(protocol, alice_bits, alice_bases):
        if protocol == "E91":
            length = min(len(alice_bits), len(alice_bases))
            bob_bases = [random.choice(["Z", "X"]) for _ in range(length)]
            bob_results = []
            for i in range(length):
                if alice_bases[i] == bob_bases[i]:
                    bob_results.append(alice_bits[i])
                else:
                    bob_results.append(random.randint(0, 1))
            return bob_bases, bob_results, None
            
        elif protocol == "B92":
            bob_bases, bob_results, keep_mask = PROTOCOLS[protocol]["bob_measure"](alice_bits, alice_bases)
            return bob_bases, bob_results, keep_mask
            
        else: # BB84 and Six-State
            bob_bases, bob_results = PROTOCOLS[protocol]["bob_measure"](alice_bits, alice_bases)
            return bob_bases, bob_results, None
            
    @staticmethod
    def sift_key_alice(protocol, alice_bits, alice_bases, bob_bases, extra_data=None):
        if protocol == "B92":
            keep_mask = extra_data
            return PROTOCOLS[protocol]["sift_key"](alice_bits, keep_mask)
        elif protocol == "Six-State":
            return PROTOCOLS[protocol]["sift_key"](alice_bits, alice_bases, bob_bases)
        elif protocol == "E91":
            alice_sifted, _ = PROTOCOLS[protocol]["sift_key"](alice_bits, alice_bits, alice_bases, bob_bases)
            return alice_sifted
        else: # BB84
            return PROTOCOLS[protocol]["sift_key"](alice_bits, alice_bases, bob_bases)

    @staticmethod
    def sift_key_bob(protocol, bob_results, alice_bases, bob_bases, extra_data=None):
        if protocol == "B92":
            keep_mask = extra_data
            # In B92, Bob knows Alice's exact bits for the kept positions.
            # But the 'bob_results' here is exactly that knowledge (0 or 1).
            # Wait, in B92, Bob measures 1. The bit Alice sent is inferred.
            # Let's re-calculate Bob's sifted key based on his bases and results.
            sifted = []
            for i in range(len(keep_mask)):
                if keep_mask[i]:
                    # Bob knows Alice's bit
                    if bob_bases[i] == "Z":
                        sifted.append(1) # Alice must have sent |+> (1)
                    else:
                        sifted.append(0) # Alice must have sent |0> (0)
            return sifted
        elif protocol == "Six-State":
            return PROTOCOLS[protocol]["sift_key"](bob_results, alice_bases, bob_bases)
        elif protocol == "E91":
            _, bob_sifted = PROTOCOLS[protocol]["sift_key"](bob_results, bob_results, alice_bases, bob_bases)
            return bob_sifted
        else: # BB84
            return PROTOCOLS[protocol]["sift_key"](bob_results, alice_bases, bob_bases)
