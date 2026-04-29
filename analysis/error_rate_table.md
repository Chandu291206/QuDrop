# QKD Error Rate Analysis

## 1. Key-Length Study (Protocol: BB84, Noise: 5%, Trials: 100)

| Raw Bits | Sifted Bits (Mean) | QBER (Mean) | QBER (Std) | Encryption BER |
|---|---|---|---|---|
| 8 | 3.98 | 5.06% | 12.08% | 0.0000% |
| 16 | 7.90 | 5.90% | 8.95% | 0.0000% |
| 32 | 16.02 | 5.66% | 5.58% | 0.0000% |
| 48 | 23.81 | 4.68% | 4.41% | 0.0000% |
| 64 | 31.57 | 5.48% | 3.93% | 0.0000% |

## 2. Data-Type Study (Protocol: BB84, Raw Bits: 64, Noise: 5%, Trials: 50)

| Filename | File Size (Bytes) | Bit Error Rate | Byte Error Rate | Avg Enc/Dec Time (s) |
|---|---|---|---|---|
| test.txt | 19 | 0.000000% | 0.000000% | 0.00001 |
| test_bin.dat | 2048 | 0.000000% | 0.000000% | 0.00041 |
| test_data.csv | 789 | 0.000000% | 0.000000% | 0.00017 |
| test_data.json | 400 | 0.000000% | 0.000000% | 0.00016 |
| test_text.txt | 1450 | 0.000000% | 0.000000% | 0.00058 |
