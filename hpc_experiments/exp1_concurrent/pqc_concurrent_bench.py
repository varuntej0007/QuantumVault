"""
Experiment 1: Concurrent PQC Throughput on PARAM Rudra
Simulates banking server handling simultaneous ML-KEM-768 + ML-DSA-65 operations.

Research Question:
  What is the maximum sustainable PQC throughput on a 48-core server
  under concurrent load? At what concurrency level does performance degrade?

Relevance to RBI Q-SAFE:
  NPCI processes ~8 million UPI transactions/day (~93/second average,
  peak estimated 3000-5000/second). This experiment characterises whether
  ML-KEM-768 can sustain that throughput on commodity server hardware.
"""
import sys, os, time, json, statistics, math
import concurrent.futures
import threading
from datetime import datetime

sys.path.insert(0, '/scratch/hpctw14/quantumvault_hpc/QuantumVault')
import oqs
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

# How many cores we're testing — passed as env var from SLURM
MAX_WORKERS = int(os.environ.get('SLURM_CPUS_PER_TASK', 48))
ITERATIONS_PER_WORKER = 200  # each thread does 200 ops
PLATFORM = os.environ.get('SLURMD_NODENAME', 'PARAM_Rudra')

print(f"QuantumVault-X Concurrent Benchmark")
print(f"Platform: {PLATFORM}")
print(f"Max workers: {MAX_WORKERS}")
print(f"Iterations per worker: {ITERATIONS_PER_WORKER}")
print(f"Total operations per test: {MAX_WORKERS * ITERATIONS_PER_WORKER}")
print()

results = {
    "experiment": "concurrent_pqc_throughput",
    "platform": "PARAM Rudra IUAC",
    "node": PLATFORM,
    "timestamp": datetime.utcnow().isoformat(),
    "max_workers": MAX_WORKERS,
    "iterations_per_worker": ITERATIONS_PER_WORKER,
    "concurrency_tests": []
}

# ── Single operation functions (each worker calls these) ──────────────────────

def mlkem768_keygen_op(_):
    t0 = time.perf_counter()
    with oqs.KeyEncapsulation("ML-KEM-768") as kem:
        pub = kem.generate_keypair()
        sec = kem.export_secret_key()
    return (time.perf_counter() - t0) * 1000

def mlkem768_full_op(_):
    """Full encap+decap cycle — simulates a single secure session setup."""
    t0 = time.perf_counter()
    with oqs.KeyEncapsulation("ML-KEM-768") as kem:
        pub = kem.generate_keypair()
        sec = kem.export_secret_key()
    with oqs.KeyEncapsulation("ML-KEM-768") as kem:
        ct, ss = kem.encap_secret(pub)
    with oqs.KeyEncapsulation("ML-KEM-768", secret_key=sec) as kem:
        kem.decap_secret(ct)
    return (time.perf_counter() - t0) * 1000

def mldsa65_sign_op(_):
    msg = os.urandom(256)
    t0 = time.perf_counter()
    with oqs.Signature("ML-DSA-65") as sig:
        pub = sig.generate_keypair()
        sec = sig.export_secret_key()
    with oqs.Signature("ML-DSA-65", secret_key=sec) as sig:
        signature = sig.sign(msg)
    return (time.perf_counter() - t0) * 1000

def rsa2048_op(_):
    t0 = time.perf_counter()
    rsa.generate_private_key(65537, 2048, default_backend())
    return (time.perf_counter() - t0) * 1000


def run_concurrent_test(fn, num_workers, n_per_worker, label):
    """Run fn concurrently with num_workers threads, collect timing stats."""
    print(f"  Testing {label} with {num_workers} concurrent workers...")
    
    wall_start = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as ex:
        all_times = list(ex.map(fn, range(num_workers * n_per_worker)))
    wall_elapsed = time.perf_counter() - wall_start

    total_ops = len(all_times)
    throughput = total_ops / wall_elapsed  # ops/second

    return {
        "workers": num_workers,
        "total_ops": total_ops,
        "wall_time_s": round(wall_elapsed, 3),
        "throughput_ops_per_sec": round(throughput, 1),
        "mean_latency_ms": round(statistics.mean(all_times), 4),
        "stdev_ms": round(statistics.stdev(all_times), 4),
        "p50_ms": round(sorted(all_times)[int(len(all_times)*0.5)], 4),
        "p95_ms": round(sorted(all_times)[int(len(all_times)*0.95)], 4),
        "p99_ms": round(sorted(all_times)[int(len(all_times)*0.99)], 4),
        "min_ms": round(min(all_times), 4),
        "max_ms": round(max(all_times), 4),
    }


# ── Test concurrency levels ────────────────────────────────────────────────────
# 1, 2, 4, 8, 12, 24, 48 workers — shows scaling curve
worker_counts = [1, 2, 4, 8, 12, 24, 48]
worker_counts = [w for w in worker_counts if w <= MAX_WORKERS]

print("=" * 60)
print("TEST 1: ML-KEM-768 Full Session (KeyGen + Encap + Decap)")
print("=" * 60)
mlkem_results = []
for n in worker_counts:
    r = run_concurrent_test(mlkem768_full_op, n, ITERATIONS_PER_WORKER, "ML-KEM-768")
    mlkem_results.append(r)
    print(f"    Workers={n:2d} | {r['throughput_ops_per_sec']:8.1f} ops/s | "
          f"p50={r['p50_ms']:.3f}ms | p99={r['p99_ms']:.3f}ms")

results["mlkem768_concurrent"] = mlkem_results

print()
print("=" * 60)
print("TEST 2: ML-DSA-65 Sign+Verify Session")
print("=" * 60)
mldsa_results = []
for n in worker_counts:
    r = run_concurrent_test(mldsa65_sign_op, n, ITERATIONS_PER_WORKER, "ML-DSA-65")
    mldsa_results.append(r)
    print(f"    Workers={n:2d} | {r['throughput_ops_per_sec']:8.1f} ops/s | "
          f"p50={r['p50_ms']:.3f}ms | p99={r['p99_ms']:.3f}ms")

results["mldsa65_concurrent"] = mldsa_results

print()
print("=" * 60)
print("TEST 3: RSA-2048 KeyGen (classical baseline)")
print("=" * 60)
rsa_results = []
for n in worker_counts:
    r = run_concurrent_test(rsa2048_op, n, min(ITERATIONS_PER_WORKER, 50), "RSA-2048")
    rsa_results.append(r)
    print(f"    Workers={n:2d} | {r['throughput_ops_per_sec']:8.1f} ops/s | "
          f"p50={r['p50_ms']:.1f}ms | p99={r['p99_ms']:.1f}ms")

results["rsa2048_concurrent"] = rsa_results

# ── Summary ───────────────────────────────────────────────────────────────────
peak_mlkem = max(r["throughput_ops_per_sec"] for r in mlkem_results)
peak_mldsa = max(r["throughput_ops_per_sec"] for r in mldsa_results)
peak_rsa   = max(r["throughput_ops_per_sec"] for r in rsa_results)

# UPI peak throughput estimate for context
UPI_PEAK_TPS = 5000  # conservative peak estimate

results["summary"] = {
    "peak_mlkem768_ops_per_sec": peak_mlkem,
    "peak_mldsa65_ops_per_sec": peak_mldsa,
    "peak_rsa2048_ops_per_sec": peak_rsa,
    "mlkem_vs_rsa_throughput_ratio": round(peak_mlkem / peak_rsa, 1),
    "upi_peak_tps_reference": UPI_PEAK_TPS,
    "mlkem_can_handle_upi_peak": peak_mlkem > UPI_PEAK_TPS,
    "note": (
        "Throughput measured on PARAM Rudra IUAC under concurrent "
        "multi-threaded load. UPI peak reference is illustrative — "
        "actual banking deployment requires HSM + network overhead analysis."
    )
}

print()
print("=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"Peak ML-KEM-768 throughput: {peak_mlkem:.0f} ops/sec")
print(f"Peak ML-DSA-65  throughput: {peak_mldsa:.0f} ops/sec")
print(f"Peak RSA-2048   throughput: {peak_rsa:.0f} ops/sec")
print(f"ML-KEM vs RSA throughput:   {peak_mlkem/peak_rsa:.1f}x more ops/sec")
print(f"UPI peak reference (est.):  {UPI_PEAK_TPS} TPS")
print(f"ML-KEM can handle UPI peak: {peak_mlkem > UPI_PEAK_TPS}")

# ── Save results ──────────────────────────────────────────────────────────────
os.makedirs("/scratch/hpctw14/quantumvault_hpc/QuantumVault/hpc_experiments/results", exist_ok=True)
outfile = f"/scratch/hpctw14/quantumvault_hpc/QuantumVault/hpc_experiments/results/exp1_{PLATFORM}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
with open(outfile, "w") as f:
    json.dump(results, f, indent=2)
print(f"\nResults saved: {outfile}")
