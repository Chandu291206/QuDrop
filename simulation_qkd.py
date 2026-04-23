from pathlib import Path
import itertools

from bb84.bb84_core import alice_generate, bob_measure, privacy_amplify, sift_key


def xor_bytes(data: bytes, key: bytes) -> bytes:
    if not key:
        raise ValueError("Key must not be empty.")
    return bytes(d ^ k for d, k in zip(data, itertools.cycle(key)))


def simulate_qkd_file_transfer(input_path="test.txt"):
    # 1. Alice generates random bits and bases.
    alice_bits, alice_bases = alice_generate()
    print("Alice bits:   ", alice_bits)
    print("Alice bases:  ", alice_bases)

    # 2. Bob measures.
    bob_bases, bob_results = bob_measure(alice_bits, alice_bases)
    print("Bob bases:    ", bob_bases)
    print("Bob results:  ", bob_results)

    # 3. Sift key (keep positions with same basis).
    shared_key_bits = sift_key(alice_bits, alice_bases, bob_bases)
    print("Shared key bits (after sifting):", shared_key_bits)
    print("Key length (bits):", len(shared_key_bits))

    # 4. Privacy amplification to produce final key bytes.
    key_bytes = privacy_amplify(shared_key_bits)
    print(f"Final key length: {len(key_bytes)} bytes")

    # 5. Load file to send.
    data = Path(input_path).read_bytes()
    print(f"Plaintext file size: {len(data)} bytes")

    # 6. Encrypt (sender side).
    ciphertext = xor_bytes(data, key_bytes)
    Path("ciphertext.bin").write_bytes(ciphertext)
    print("Ciphertext written to ciphertext.bin")

    # 7. Decrypt (receiver side, using same final key).
    decrypted = xor_bytes(ciphertext, key_bytes)
    Path("decrypted.txt").write_bytes(decrypted)
    print("Decrypted file written to decrypted.txt")

    # Quick integrity check.
    print("Decryption success:", decrypted == data)


if __name__ == "__main__":
    simulate_qkd_file_transfer()
