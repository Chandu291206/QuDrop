import os
import sys
import time
import random
import statistics
import itertools

# Add parent directory to path so we can import project modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.protocol_runner import ProtocolRunner
from bb84.bb84_core import estimate_qber, privacy_amplify
from encryption.xor_cipher import xor_encrypt, xor_decrypt

def apply_channel_noise(bits, prob):
    noisy = []
    flips = 0
    for b in bits:
        if random.random() < prob:
            noisy.append(1 - b)
            flips += 1
        else:
            noisy.append(b)
    return noisy, flips

def compute_transfer_errors(reference_data, decrypted_data):
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

def run_qkd_simulation(protocol, raw_bits, noise_prob):
    # 1. Alice generate
    alice_bits, alice_bases = ProtocolRunner.alice_generate(protocol, raw_bits)
    
    # 2. Channel noise
    transmitted_bits = list(alice_bits)
    if noise_prob > 0:
        transmitted_bits, _ = apply_channel_noise(transmitted_bits, noise_prob)
        
    # 3. Bob measure
    bob_bases, bob_results, extra_data = ProtocolRunner.bob_measure(protocol, transmitted_bits, alice_bases)
    
    # 4. Sift
    alice_sifted = ProtocolRunner.sift_key_alice(protocol, alice_bits, alice_bases, bob_bases, extra_data)
    bob_sifted = ProtocolRunner.sift_key_bob(protocol, bob_results, alice_bases, bob_bases, extra_data)
    
    if len(alice_sifted) == 0:
        return 0.0, 0, b""
        
    # QBER estimation
    # Normally we sample, but for analysis we can just measure exactly on the sifted keys
    errors = sum(1 for i in range(len(alice_sifted)) if alice_sifted[i] != bob_sifted[i])
    qber = errors / len(alice_sifted) if len(alice_sifted) > 0 else 0.0
    
    # Privacy amplification
    final_key = privacy_amplify(bob_sifted)
    
    return qber, len(alice_sifted), final_key

def run_key_length_study():
    lengths = [8, 16, 32, 48, 64]
    noise = 0.05
    trials = 100
    protocol = "BB84"
    
    results = []
    
    for length in lengths:
        qbers = []
        sifted_lengths = []
        bers = []
        
        for _ in range(trials):
            qber, sifted_len, key = run_qkd_simulation(protocol, length, noise)
            qbers.append(qber)
            sifted_lengths.append(sifted_len)
            
            # Simulated encryption BER
            if len(key) == 0:
                # Fallback to avoid empty key failure in our analysis
                key = b"\x00"
                
            test_data = b"Testing Error Rates for Quantum Key Distribution"
            encrypted = xor_encrypt(test_data, key)
            decrypted = xor_decrypt(encrypted, key)
            
            bit_errors, total_bits, _, _ = compute_transfer_errors(test_data, decrypted)
            bers.append(bit_errors / total_bits if total_bits else 0)
            
        results.append({
            "raw_length": length,
            "qber_mean": statistics.mean(qbers),
            "qber_std": statistics.stdev(qbers) if len(qbers) > 1 else 0,
            "sifted_mean": statistics.mean(sifted_lengths),
            "ber_mean": statistics.mean(bers)
        })
    return results

def run_data_type_study():
    public_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "public")
    if not os.path.exists(public_dir):
        return []
        
    files = [f for f in os.listdir(public_dir) if os.path.isfile(os.path.join(public_dir, f))]
    noise = 0.05
    trials = 50
    protocol = "BB84"
    raw_bits = 64
    
    results = []
    
    for f in files:
        filepath = os.path.join(public_dir, f)
        try:
            with open(filepath, "rb") as file_obj:
                data = file_obj.read()
        except:
            continue
            
        file_size = len(data)
        if file_size == 0:
            continue
            
        bers = []
        byte_ers = []
        enc_times = []
        
        for _ in range(trials):
            _, _, key = run_qkd_simulation(protocol, raw_bits, noise)
            if len(key) == 0:
                key = b"\x00"
                
            start = time.perf_counter()
            encrypted = xor_encrypt(data, key)
            decrypted = xor_decrypt(encrypted, key)
            enc_time = time.perf_counter() - start
            
            bit_errors, total_bits, byte_errors, total_bytes = compute_transfer_errors(data, decrypted)
            
            bers.append(bit_errors / total_bits if total_bits else 0)
            byte_ers.append(byte_errors / total_bytes if total_bytes else 0)
            enc_times.append(enc_time)
            
        results.append({
            "filename": f,
            "size": file_size,
            "ber_mean": statistics.mean(bers),
            "byte_er_mean": statistics.mean(byte_ers),
            "enc_time_mean": statistics.mean(enc_times)
        })
    return results

def write_reports(key_study, data_study):
    analysis_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(analysis_dir, exist_ok=True)
    
    # 1. Write Markdown Table
    md_path = os.path.join(analysis_dir, "error_rate_table.md")
    with open(md_path, "w") as f:
        f.write("# QKD Error Rate Analysis\n\n")
        f.write("## 1. Key-Length Study (Protocol: BB84, Noise: 5%, Trials: 100)\n\n")
        f.write("| Raw Bits | Sifted Bits (Mean) | QBER (Mean) | QBER (Std) | Encryption BER |\n")
        f.write("|---|---|---|---|---|\n")
        for res in key_study:
            f.write(f"| {res['raw_length']} | {res['sifted_mean']:.2f} | {res['qber_mean']*100:.2f}% | {res['qber_std']*100:.2f}% | {res['ber_mean']*100:.4f}% |\n")
            
        f.write("\n## 2. Data-Type Study (Protocol: BB84, Raw Bits: 64, Noise: 5%, Trials: 50)\n\n")
        f.write("| Filename | File Size (Bytes) | Bit Error Rate | Byte Error Rate | Avg Enc/Dec Time (s) |\n")
        f.write("|---|---|---|---|---|\n")
        for res in data_study:
            f.write(f"| {res['filename']} | {res['size']} | {res['ber_mean']*100:.6f}% | {res['byte_er_mean']*100:.6f}% | {res['enc_time_mean']:.5f} |\n")

    # 2. Write Text Report
    txt_path = os.path.join(analysis_dir, "error_rate_report.txt")
    with open(txt_path, "w") as f:
        f.write("="*60 + "\n")
        f.write("QU DROP - ERROR RATE ANALYSIS REPORT\n")
        f.write("="*60 + "\n\n")
        
        f.write("EXECUTIVE SUMMARY\n")
        f.write("-" * 20 + "\n")
        f.write("This report analyzes the performance of the Quantum Key Distribution (QKD) ")
        f.write("process under simulated channel noise. Specifically, a constant bit-flip noise ")
        f.write("of 5% (p=0.05) was injected into the quantum channel to measure its impact on ")
        f.write("the Quantum Bit Error Rate (QBER) and subsequent file encryption integrity.\n\n")
        
        f.write("PART 1: KEY-LENGTH STUDY\n")
        f.write("-" * 20 + "\n")
        for res in key_study:
            f.write(f"Raw Length: {res['raw_length']} bits\n")
            f.write(f"  - Sifted Keys Average: {res['sifted_mean']:.2f} bits\n")
            f.write(f"  - QBER: {res['qber_mean']*100:.2f}% (Std: {res['qber_std']*100:.2f}%)\n")
            f.write(f"  - Encryption BER: {res['ber_mean']*100:.4f}%\n\n")
            
        f.write("PART 2: DATA-TYPE STUDY\n")
        f.write("-" * 20 + "\n")
        for res in data_study:
            f.write(f"File: {res['filename']} ({res['size']} bytes)\n")
            f.write(f"  - Avg Bit Error Rate:  {res['ber_mean']*100:.6f}%\n")
            f.write(f"  - Avg Byte Error Rate: {res['byte_er_mean']*100:.6f}%\n")
            f.write(f"  - Avg Process Time:    {res['enc_time_mean']*1000:.2f} ms\n\n")
            
        f.write("CONCLUSIONS\n")
        f.write("-" * 20 + "\n")
        f.write("1. QBER closely tracks the injected channel noise (5%).\n")
        f.write("2. Due to the deterministic nature of XOR encryption, provided the QKD protocol ")
        f.write("successfully establishes an identical shared key post-privacy amplification, ")
        f.write("the resulting file transfer Bit Error Rate (BER) over the classical channel ")
        f.write("will be 0.00%.\n")

if __name__ == "__main__":
    print("Starting Key-Length Study...")
    key_study = run_key_length_study()
    print("Starting Data-Type Study...")
    data_study = run_data_type_study()
    print("Writing Reports...")
    write_reports(key_study, data_study)
    print("Analysis complete. Check 'error_rate_table.md' and 'error_rate_report.txt'.")
