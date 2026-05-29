import sys, os, time, json, statistics
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import oqs
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from datetime import datetime
from benchmarks.system_monitor import SystemMonitor

ITERATIONS = 500
print(f"QuantumVault Benchmark Suite — {ITERATIONS} iterations each")
print("This will take ~5 minutes on Pi 5. Do not interrupt.\n")

results = {
    "platform": "Raspberry Pi 5 8GB",
    "arch": "armhf on aarch64 kernel",
    "timestamp": datetime.utcnow().isoformat(),
    "iterations": ITERATIONS,
    "kyber768": {},
    "dilithium3": {},
    "rsa2048": {},
    "system": {}
}

monitor = SystemMonitor(interval=0.2)
monitor.start()

# --- Kyber-768 ---
print("Benchmarking Kyber-768...")
keygen_times, encap_times, decap_times = [], [], []
pub_key_len = capsule_len = ss_len = 0

for _ in range(ITERATIONS):
    t0 = time.perf_counter()
    with oqs.KeyEncapsulation("Kyber768") as kem:
        pub = kem.generate_keypair()
        sec = kem.export_secret_key()
    keygen_times.append((time.perf_counter() - t0) * 1000)

    t0 = time.perf_counter()
    with oqs.KeyEncapsulation("Kyber768") as kem:
        ct, ss = kem.encap_secret(pub)
    encap_times.append((time.perf_counter() - t0) * 1000)

    t0 = time.perf_counter()
    with oqs.KeyEncapsulation("Kyber768", secret_key=sec) as kem:
        kem.decap_secret(ct)
    decap_times.append((time.perf_counter() - t0) * 1000)

    pub_key_len = len(pub)
    capsule_len = len(ct)
    ss_len = len(ss)

results["kyber768"] = {
    "keygen_mean_ms":  statistics.mean(keygen_times),
    "keygen_stdev_ms": statistics.stdev(keygen_times),
    "encap_mean_ms":   statistics.mean(encap_times),
    "encap_stdev_ms":  statistics.stdev(encap_times),
    "decap_mean_ms":   statistics.mean(decap_times),
    "decap_stdev_ms":  statistics.stdev(decap_times),
    "pub_key_bytes":   pub_key_len,
    "capsule_bytes":   capsule_len,
    "shared_secret_bytes": ss_len
}
print(f"  KeyGen: {results['kyber768']['keygen_mean_ms']:.3f}ms ± {results['kyber768']['keygen_stdev_ms']:.3f}ms")

# --- Dilithium-3 ---
print("Benchmarking Dilithium-3...")
msg = os.urandom(1024)
keygen_t, sign_t, verify_t = [], [], []
sig_len = pub_d_len = 0

for _ in range(ITERATIONS):
    t0 = time.perf_counter()
    with oqs.Signature("Dilithium3") as sig:
        pub_d = sig.generate_keypair()
        sec_d = sig.export_secret_key()
    keygen_t.append((time.perf_counter() - t0) * 1000)

    t0 = time.perf_counter()
    with oqs.Signature("Dilithium3", secret_key=sec_d) as sig:
        signature = sig.sign(msg)
    sign_t.append((time.perf_counter() - t0) * 1000)

    t0 = time.perf_counter()
    with oqs.Signature("Dilithium3") as sig:
        sig.verify(msg, signature, pub_d)
    verify_t.append((time.perf_counter() - t0) * 1000)

    sig_len = len(signature)
    pub_d_len = len(pub_d)

results["dilithium3"] = {
    "keygen_mean_ms":  statistics.mean(keygen_t),
    "keygen_stdev_ms": statistics.stdev(keygen_t),
    "sign_mean_ms":    statistics.mean(sign_t),
    "sign_stdev_ms":   statistics.stdev(sign_t),
    "verify_mean_ms":  statistics.mean(verify_t),
    "verify_stdev_ms": statistics.stdev(verify_t),
    "signature_bytes": sig_len,
    "pub_key_bytes":   pub_d_len
}
print(f"  Sign:   {results['dilithium3']['sign_mean_ms']:.3f}ms ± {results['dilithium3']['sign_stdev_ms']:.3f}ms")

# --- RSA-2048 ---
print("Benchmarking RSA-2048 (slowest — please wait)...")
key = rsa.generate_private_key(65537, 2048, default_backend())
msg_rsa = os.urandom(190)
kg_t, enc_t, dec_t = [], [], []

for _ in range(ITERATIONS):
    t0 = time.perf_counter()
    rsa.generate_private_key(65537, 2048, default_backend())
    kg_t.append((time.perf_counter() - t0) * 1000)

    t0 = time.perf_counter()
    ct_r = key.public_key().encrypt(msg_rsa, padding.OAEP(
        mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
    enc_t.append((time.perf_counter() - t0) * 1000)

    t0 = time.perf_counter()
    key.decrypt(ct_r, padding.OAEP(
        mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
    dec_t.append((time.perf_counter() - t0) * 1000)

results["rsa2048"] = {
    "keygen_mean_ms":  statistics.mean(kg_t),
    "keygen_stdev_ms": statistics.stdev(kg_t),
    "encrypt_mean_ms": statistics.mean(enc_t),
    "encrypt_stdev_ms":statistics.stdev(enc_t),
    "decrypt_mean_ms": statistics.mean(dec_t),
    "decrypt_stdev_ms":statistics.stdev(dec_t)
}
print(f"  KeyGen: {results['rsa2048']['keygen_mean_ms']:.1f}ms ± {results['rsa2048']['keygen_stdev_ms']:.1f}ms")

# --- Stop monitor ---
monitor.stop()
results["system"] = monitor.summary()

# --- Save ---
os.makedirs("benchmarks/results", exist_ok=True)
outfile = f"benchmarks/results/bench_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
with open(outfile, "w") as f:
    json.dump(results, f, indent=2)

print(f"\nResults saved to {outfile}")
print(f"\n{'Operation':<20} {'Kyber-768':>12} {'Dilithium-3':>14} {'RSA-2048':>12}")
print("-" * 62)
print(f"{'KeyGen':<20} {results['kyber768']['keygen_mean_ms']:>11.3f}ms {results['dilithium3']['keygen_mean_ms']:>13.3f}ms {results['rsa2048']['keygen_mean_ms']:>10.1f}ms")
print(f"{'Enc/Encap/Sign':<20} {results['kyber768']['encap_mean_ms']:>11.3f}ms {results['dilithium3']['sign_mean_ms']:>13.3f}ms {results['rsa2048']['encrypt_mean_ms']:>10.3f}ms")
print(f"{'Dec/Decap/Verify':<20} {results['kyber768']['decap_mean_ms']:>11.3f}ms {results['dilithium3']['verify_mean_ms']:>13.3f}ms {results['rsa2048']['decrypt_mean_ms']:>10.3f}ms")

speedup = results['rsa2048']['keygen_mean_ms'] / results['kyber768']['keygen_mean_ms']
print(f"\nSpeedup (KeyGen): Kyber-768 is {speedup:.0f}x faster than RSA-2048")
print(f"CPU peak: {results['system'].get('cpu_max_pct', 0):.1f}%  Temp peak: {results['system'].get('temp_max_c', 0):.1f}°C")
