import os
import random
import sys

# Ensure the parent directory is in path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from encryption.xor_cipher import xor_encrypt, xor_decrypt

def compute_transfer_error_rates(reference_data, decrypted_data):
    common_len = min(len(reference_data), len(decrypted_data))
    byte_errors = 0
    bit_errors = 0
    for i in range(common_len):
        ref_byte = reference_data[i]
        dec_byte = decrypted_data[i]
        if ref_byte != dec_byte:
            byte_errors += 1
            bit_errors += (ref_byte ^ dec_byte).bit_count()
    length_delta = abs(len(reference_data) - len(decrypted_data))
    byte_errors += length_delta
    bit_errors += length_delta * 8
    total_bytes = max(len(reference_data), len(decrypted_data))
    total_bits = total_bytes * 8
    return bit_errors, total_bits, byte_errors, total_bytes

def test_key_lengths():
    print("--- Testing different key lengths ---")
    lengths = [8, 16, 32, 48, 64]
    test_data = b"Hello Quantum World! " * 50  # 1050 bytes
    
    for length in lengths:
        key_bytes = max(1, length // 8)
        key = os.urandom(key_bytes)
        
        encrypted = xor_encrypt(test_data, key)
        decrypted = xor_decrypt(encrypted, key)
        
        bit_errors, total_bits, byte_errors, total_bytes = compute_transfer_error_rates(test_data, decrypted)
        ber = (bit_errors / total_bits * 100) if total_bits else 0
        byte_err = (byte_errors / total_bytes * 100) if total_bytes else 0
        
        print(f"Key Length {length:>2} bits ({key_bytes:>2} bytes): BER = {ber:.4f}% | Byte Error = {byte_err:.4f}%")

def create_dummy_files():
    public_dir = "public"
    os.makedirs(public_dir, exist_ok=True)
    
    # 1. Text file
    with open(os.path.join(public_dir, "test_text.txt"), "w", encoding="utf-8") as f:
        f.write("This is a simple text file.\n" * 50)
        
    # 2. Binary file
    with open(os.path.join(public_dir, "test_bin.dat"), "wb") as f:
        f.write(os.urandom(2048))
        
    # 3. CSV file
    with open(os.path.join(public_dir, "test_data.csv"), "w", encoding="utf-8") as f:
        f.write("id,name,value\n")
        for i in range(50):
            f.write(f"{i},Name_{i},{random.randint(1, 1000)}\n")
            
    # 4. JSON file
    with open(os.path.join(public_dir, "test_data.json"), "w", encoding="utf-8") as f:
        f.write('{"data": [')
        f.write(", ".join(str(i) for i in range(100)))
        f.write(']}')

def test_data_types():
    print("\n--- Testing different data types in public folder ---")
    public_dir = "public"
    key = os.urandom(16) # 128-bit key
    
    for filename in os.listdir(public_dir):
        filepath = os.path.join(public_dir, filename)
        if not os.path.isfile(filepath):
            continue
            
        with open(filepath, "rb") as f:
            data = f.read()
            
        encrypted = xor_encrypt(data, key)
        decrypted = xor_decrypt(encrypted, key)
        
        bit_errors, total_bits, byte_errors, total_bytes = compute_transfer_error_rates(data, decrypted)
        ber = (bit_errors / total_bits * 100) if total_bits else 0
        byte_err = (byte_errors / total_bytes * 100) if total_bytes else 0
        
        print(f"File: {filename:<15} ({len(data):>4} bytes) -> BER = {ber:.4f}% | Byte Error = {byte_err:.4f}%")

if __name__ == "__main__":
    test_key_lengths()
    create_dummy_files()
    test_data_types()
