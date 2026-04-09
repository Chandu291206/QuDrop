
from bb84.bb84_core import alice_generate, bob_measure, sift_key
from pathlib import Path
import itertools

def bits_to_bytes(bits):
    # pad to multiple of 8
    pad = (-len(bits)) % 8
    bits = bits + [0] * pad
    by = []
    for i in range(0, len(bits), 8):
        byte = 0
        for b in bits[i:i+8]:
            byte = (byte << 1) | b
        by.append(byte)
    return bytes(by)

def derive_key_bytes(shared_bits, length):
    key_stream = bytes()
    while len(key_stream) < length:
        key_stream += bits_to_bytes(shared_bits)
    return key_stream[:length]

def xor_bytes(data: bytes, key: bytes) -> bytes:
    return bytes(d ^ k for d, k in zip(data, key))

def simulate_qkd_file_transfer(input_path="test.txt"):
    # 1. Alice generates random bits & bases
    alice_bits, alice_bases = alice_generate()
    print("Alice bits:   ", alice_bits)
    print("Alice bases:  ", alice_bases)

    # 2. Bob measures
    bob_bases, bob_results = bob_measure(alice_bits, alice_bases)
    print("Bob bases:    ", bob_bases)
    print("Bob results:  ", bob_results)

    # 3. Sift key (keep positions with same basis)
    shared_key_bits = sift_key(alice_bits, alice_bases, bob_bases)
    print("Shared key bits (after sifting):", shared_key_bits)
    print("Key length (bits):", len(shared_key_bits))

    # 4. Load file to “send”
    data = Path(input_path).read_bytes()
    print(f"Plaintext file size: {len(data)} bytes")

    # 5. Derive key bytes stream from shared bits
    key_bytes = derive_key_bytes(shared_key_bits, len(data))

    # 6. Encrypt (sender side)
    ciphertext = xor_bytes(data, key_bytes)
    Path("ciphertext.bin").write_bytes(ciphertext)
    print("Ciphertext written to ciphertext.bin")

    # 7. Decrypt (receiver side, using same shared key)
    decrypted = xor_bytes(ciphertext, key_bytes)
    Path("decrypted.txt").write_bytes(decrypted)
    print("Decrypted file written to decrypted.txt")

    # Quick integrity check
    print("Decryption success:", decrypted == data)

if __name__ == "__main__":
    simulate_qkd_file_transfer()
