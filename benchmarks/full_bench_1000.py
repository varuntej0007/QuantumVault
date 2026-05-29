import sys, os, time, json, statistics, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import oqs
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from datetime import datetime
from benchmarks.system_monitor import SystemMonitor

ITERATIONS = 1000

def confidence_interval_95(data):
    n = len(data)
    mean = statistics.mean(data)
    stdev = statistics.stdev(data)
    # t-value for 95% CI, large n ~ 1.96
    margin = 1.96 * (stdev / math.sqrt(n))
    return mean - margin, mean + margin

def stats(data):
    mean = statistics.mean(data)
    stdev = statistics.stdev(data)
    lo, hi = confidence_interval_95(data)
    return {
        "mean_ms": round(mean, 4),
        "stdev_ms": round(stdev, 4),
        "min_ms": round(min(data), 4),
        "max_ms": round(max(data), 4),
        "ci95_lo_ms": round(lo, 4),
        "ci95_hi_ms": round(hi, 4),
        "n": len(data)
    }

print(f"QuantumVault Statistical Benchmark — {ITERATIONS} iterations")
print("Note: All claims are specific to Raspberry Pi 5 armhf under tested conditions.\n")

results = {
    "metadata": {
        "platform": "Raspberry Pi 5 8GB",
        "arch": "armhf (32-bit userspace on aarch64 kernel)",
        "os": "Raspberry Pi OS Bookworm",
        "liboqs_version": "0.10.1",
        "timestamp": datetime.utcnow().isoformat(),
        "iterations": ITERATIONS,
        "disclaimer": (
            "Results represent key-generation and operation latency under "
            "sequential single-threaded benchmark conditions on this specific "
            "hardware. PQC algorithms differ from RSA in key sizes, signature "
            "bandwidth, and workload characteristics — direct comparisons are "
            "context-dependent."
        )
    },
    "kyber768": {}, "dilithium3": {}, "rsa2048": {}, "system": {}
}

monitor = SystemMonitor(interval=0.2)
monitor.start()

# Kyber-768
print("Benchmarking Kyber-768 (1000 iterations)...")
kg, enc, dec = [], [], []
for i in range(ITERATIONS):
    if i % 200 == 0: print(f"  {i}/{ITERATIONS}")
    t0 = time.perf_counter()
    with oqs.KeyEncapsulation("Kyber768") as kem:
        pub = kem.generate_keypair(); sec = kem.export_secret_key()
    kg.append((time.perf_counter()-t0)*1000)
    t0 = time.perf_counter()
    with oqs.KeyEncapsulation("Kyber768") as kem:
        ct, ss = kem.encap_secret(pub)
    enc.append((time.perf_counter()-t0)*1000)
    t0 = time.perf_counter()
    with oqs.KeyEncapsulation("Kyber768", secret_key=sec) as kem:
        kem.decap_secret(ct)
    dec.append((time.perf_counter()-t0)*1000)

results["kyber768"] = {
    "keygen": stats(kg), "encap": stats(enc), "decap": stats(dec),
    "key_sizes": {"pub_bytes": len(pub), "capsule_bytes": len(ct), "shared_secret_bytes": len(ss)}
}
print(f"  KeyGen mean: {results['kyber768']['keygen']['mean_ms']}ms  95%CI [{results['kyber768']['keygen']['ci95_lo_ms']}, {results['kyber768']['keygen']['ci95_hi_ms']}]")

# Dilithium-3
print("Benchmarking Dilithium-3 (1000 iterations)...")
msg = os.urandom(1024)
kg2, sign, verify = [], [], []
for i in range(ITERATIONS):
    if i % 200 == 0: print(f"  {i}/{ITERATIONS}")
    t0 = time.perf_counter()
    with oqs.Signature("Dilithium3") as s:
        pub_d = s.generate_keypair(); sec_d = s.export_secret_key()
    kg2.append((time.perf_counter()-t0)*1000)
    t0 = time.perf_counter()
    with oqs.Signature("Dilithium3", secret_key=sec_d) as s:
        signature = s.sign(msg)
    sign.append((time.perf_counter()-t0)*1000)
    t0 = time.perf_counter()
    with oqs.Signature("Dilithium3") as s:
        s.verify(msg, signature, pub_d)
    verify.append((time.perf_counter()-t0)*1000)

results["dilithium3"] = {
    "keygen": stats(kg2), "sign": stats(sign), "verify": stats(verify),
    "key_sizes": {"pub_bytes": len(pub_d), "signature_bytes": len(signature)}
}
print(f"  Sign mean: {results['dilithium3']['sign']['mean_ms']}ms  95%CI [{results['dilithium3']['sign']['ci95_lo_ms']}, {results['dilithium3']['sign']['ci95_hi_ms']}]")

# RSA-2048
print("Benchmarking RSA-2048 (1000 iterations, this takes ~6 min)...")
key = rsa.generate_private_key(65537, 2048, default_backend())
msg_rsa = os.urandom(190)
kg3, enc3, dec3 = [], [], []
for i in range(ITERATIONS):
    if i % 200 == 0: print(f"  {i}/{ITERATIONS}")
    t0 = time.perf_counter()
    rsa.generate_private_key(65537, 2048, default_backend())
    kg3.append((time.perf_counter()-t0)*1000)
    t0 = time.perf_counter()
    ct_r = key.public_key().encrypt(msg_rsa, padding.OAEP(
        mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
    enc3.append((time.perf_counter()-t0)*1000)
    t0 = time.perf_counter()
    key.decrypt(ct_r, padding.OAEP(
        mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
    dec3.append((time.perf_counter()-t0)*1000)

results["rsa2048"] = {
    "keygen": stats(kg3), "encrypt": stats(enc3), "decrypt": stats(dec3)
}
print(f"  KeyGen mean: {results['rsa2048']['keygen']['mean_ms']}ms  95%CI [{results['rsa2048']['keygen']['ci95_lo_ms']}, {results['rsa2048']['keygen']['ci95_hi_ms']}]")

monitor.stop()
results["system"] = monitor.summary()

os.makedirs("benchmarks/results", exist_ok=True)
outfile = f"benchmarks/results/bench1000_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
with open(outfile, "w") as f:
    json.dump(results, f, indent=2)

print(f"\nSaved: {outfile}")
print(f"\n{'Operation':<22} {'Mean':>10} {'95% CI Lo':>12} {'95% CI Hi':>12}")
print("-" * 60)
print(f"{'Kyber768 KeyGen':<22} {results['kyber768']['keygen']['mean_ms']:>9.3f}ms {results['kyber768']['keygen']['ci95_lo_ms']:>11.3f}ms {results['kyber768']['keygen']['ci95_hi_ms']:>11.3f}ms")
print(f"{'Dilithium3 Sign':<22} {results['dilithium3']['sign']['mean_ms']:>9.3f}ms {results['dilithium3']['sign']['ci95_lo_ms']:>11.3f}ms {results['dilithium3']['sign']['ci95_hi_ms']:>11.3f}ms")
print(f"{'RSA-2048 KeyGen':<22} {results['rsa2048']['keygen']['mean_ms']:>9.1f}ms {results['rsa2048']['keygen']['ci95_lo_ms']:>11.1f}ms {results['rsa2048']['keygen']['ci95_hi_ms']:>11.1f}ms")
print(f"\nNote: Kyber-768 key generation observed {results['rsa2048']['keygen']['mean_ms']/results['kyber768']['keygen']['mean_ms']:.0f}x lower latency")
print("than RSA-2048 on this platform under sequential benchmark conditions.")
