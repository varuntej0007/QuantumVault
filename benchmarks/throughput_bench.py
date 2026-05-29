import sys, os, time, json, statistics
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import oqs
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from datetime import datetime

def aes_encrypt(key, plaintext):
    nonce = os.urandom(12)
    return nonce, AESGCM(key).encrypt(nonce, plaintext, None)

def aes_decrypt(key, nonce, ciphertext):
    return AESGCM(key).decrypt(nonce, ciphertext, None)

FILE_SIZES = [
    ("1 KB",    1_000),
    ("10 KB",   10_000),
    ("100 KB",  100_000),
    ("1 MB",    1_000_000),
    ("10 MB",   10_000_000),
]
ITERATIONS = 10

print(f"\nQuantumVault Throughput Benchmark (n={ITERATIONS} per size)\n")
print(f"{'Size':<10} {'Enc ms':>10} {'Dec ms':>10} {'Throughput':>15}")
print("-" * 50)

with oqs.KeyEncapsulation("Kyber768") as kem:
    pub = kem.generate_keypair()
    sec = kem.export_secret_key()

results = []
for size_label, size_bytes in FILE_SIZES:
    plaintext = os.urandom(size_bytes)
    enc_times, dec_times = [], []

    for _ in range(ITERATIONS):
        with oqs.KeyEncapsulation("Kyber768") as kem:
            capsule, aes_key = kem.encap_secret(pub)

        t0 = time.perf_counter()
        nonce, ciphertext = aes_encrypt(aes_key, plaintext)
        enc_times.append(time.perf_counter() - t0)

        t0 = time.perf_counter()
        aes_decrypt(aes_key, nonce, ciphertext)
        dec_times.append(time.perf_counter() - t0)

    enc_ms = statistics.mean(enc_times) * 1000
    dec_ms = statistics.mean(dec_times) * 1000
    throughput = (size_bytes / 1e6) / statistics.mean(enc_times)

    print(f"{size_label:<10} {enc_ms:>10.2f} {dec_ms:>10.2f} {throughput:>12.1f} MB/s")
    results.append({
        "size_label": size_label,
        "size_bytes": size_bytes,
        "enc_mean_ms": enc_ms,
        "dec_mean_ms": dec_ms,
        "throughput_mbs": throughput
    })

os.makedirs("benchmarks/results", exist_ok=True)
outfile = f"benchmarks/results/throughput_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
with open(outfile, "w") as f:
    json.dump(results, f, indent=2)
print(f"\nSaved to {outfile}")
