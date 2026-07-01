"""
Experiment 2: PQC Throughput Scaling Curve
Measures how PQC throughput scales from 1 to 48 cores.
Identifies: linear scaling range, saturation point, optimal core count.

This answers: "How many cores does a bank server need to handle PQC at scale?"
"""
import sys, os, time, json, statistics
import concurrent.futures
from datetime import datetime

sys.path.insert(0, '/scratch/hpctw14/quantumvault_hpc/QuantumVault')
import oqs

PLATFORM = os.environ.get('SLURMD_NODENAME', 'PARAM_Rudra')
MAX_WORKERS = int(os.environ.get('SLURM_CPUS_PER_TASK', 48))
OPS_PER_WORKER = 500

print(f"Experiment 2: PQC Scaling Curve — {PLATFORM}")
print(f"Testing 1 to {MAX_WORKERS} cores, {OPS_PER_WORKER} ops/core\n")

def mlkem_op(_):
    with oqs.KeyEncapsulation("ML-KEM-768") as kem:
        pub = kem.generate_keypair()
        sec = kem.export_secret_key()
    with oqs.KeyEncapsulation("ML-KEM-768") as kem:
        ct, ss = kem.encap_secret(pub)
    with oqs.KeyEncapsulation("ML-KEM-768", secret_key=sec) as kem:
        kem.decap_secret(ct)
    return 1

# Test every step from 1 to 48
core_counts = list(range(1, MAX_WORKERS+1, 1))
scaling_data = []

print(f"{'Cores':>6} {'Throughput':>14} {'Efficiency':>12} {'Speedup':>10}")
print("-" * 50)

baseline_tps = None
for n in core_counts:
    wall_start = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=n) as ex:
        list(ex.map(mlkem_op, range(n * OPS_PER_WORKER)))
    wall_elapsed = time.perf_counter() - wall_start
    tps = (n * OPS_PER_WORKER) / wall_elapsed

    if baseline_tps is None:
        baseline_tps = tps
    speedup = tps / baseline_tps
    efficiency = speedup / n * 100

    scaling_data.append({
        "cores": n,
        "throughput_ops_per_sec": round(tps, 1),
        "speedup": round(speedup, 3),
        "parallel_efficiency_pct": round(efficiency, 1),
        "wall_time_s": round(wall_elapsed, 3)
    })

    print(f"{n:>6} {tps:>12.1f}/s {efficiency:>11.1f}% {speedup:>9.2f}x")

# Find optimal point (where efficiency drops below 80%)
optimal = next((d for d in scaling_data if d["parallel_efficiency_pct"] < 80), scaling_data[-1])

results = {
    "experiment": "scaling_curve",
    "platform": "PARAM Rudra IUAC",
    "node": PLATFORM,
    "timestamp": datetime.utcnow().isoformat(),
    "algorithm": "ML-KEM-768",
    "ops_per_core": OPS_PER_WORKER,
    "scaling_data": scaling_data,
    "analysis": {
        "single_core_tps": scaling_data[0]["throughput_ops_per_sec"],
        "max_tps": max(d["throughput_ops_per_sec"] for d in scaling_data),
        "optimal_core_count": optimal["cores"],
        "peak_efficiency_pct": scaling_data[0]["parallel_efficiency_pct"],
        "note": "Parallel efficiency = actual speedup / ideal linear speedup"
    }
}

outfile = f"/scratch/hpctw14/quantumvault_hpc/QuantumVault/hpc_experiments/results/exp2_scaling_{PLATFORM}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
os.makedirs(os.path.dirname(outfile), exist_ok=True)
with open(outfile, "w") as f:
    json.dump(results, f, indent=2)

print(f"\nPeak throughput: {results['analysis']['max_tps']:.0f} ops/sec at {MAX_WORKERS} cores")
print(f"Single-core baseline: {results['analysis']['single_core_tps']:.0f} ops/sec")
print(f"Results saved: {outfile}")
