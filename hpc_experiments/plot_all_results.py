"""
Generate publication-quality plots from all 3 HPC experiments.
Saves to hpc_experiments/plots/
"""
import json, glob, os, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

os.makedirs("hpc_experiments/plots", exist_ok=True)
plt.style.use("dark_background")

COLORS = {
    "mlkem":  "#00d4ff",
    "mldsa":  "#7c3aed",
    "rsa":    "#f59e0b",
    "jetson": "#00ff88",
    "hpc":    "#ff6b6b",
}

# Load data
exp1 = json.load(open(glob.glob("hpc_experiments/results/exp1_*.json")[0]))
exp2 = json.load(open(glob.glob("hpc_experiments/results/exp2_*.json")[0]))
exp3 = json.load(open(glob.glob("hpc_experiments/results/exp3_*.json")[0]))

# ═══════════════════════════════════════════════════════════
# PLOT 1: Concurrent Throughput — the headline result
# ═══════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 2, figsize=(16, 7))
fig.suptitle(
    "QuantumVault-X: Concurrent PQC Throughput on PARAM Rudra HPC\n"
    "IUAC National Supercomputing Facility — 48-core Node",
    fontsize=14, fontweight="bold", y=1.02
)

# Left: throughput vs workers
workers_mlkem = [r["workers"] for r in exp1["mlkem768_concurrent"]]
tps_mlkem     = [r["throughput_ops_per_sec"] for r in exp1["mlkem768_concurrent"]]
tps_mldsa     = [r["throughput_ops_per_sec"] for r in exp1["mldsa65_concurrent"]]
tps_rsa       = [r["throughput_ops_per_sec"] for r in exp1["rsa2048_concurrent"]]

ax = axes[0]
ax.plot(workers_mlkem, tps_mlkem, color=COLORS["mlkem"], marker="o",
        linewidth=2.5, markersize=8, label="ML-KEM-768 (FIPS 203)")
ax.plot(workers_mlkem, tps_mldsa, color=COLORS["mldsa"], marker="s",
        linewidth=2.5, markersize=8, label="ML-DSA-65 (FIPS 204)")
ax.plot(workers_mlkem, tps_rsa,   color=COLORS["rsa"],   marker="^",
        linewidth=2.5, markersize=8, label="RSA-2048 (Classical)")

# UPI reference line
ax.axhline(y=5000, color="white", linestyle="--", alpha=0.6, linewidth=1.5)
ax.text(1, 5300, "UPI Peak Load Reference (~5,000 TPS)",
        color="white", fontsize=9, alpha=0.8)

ax.set_xlabel("Concurrent Workers (Threads)", fontsize=12)
ax.set_ylabel("Throughput (Operations/second)", fontsize=12)
ax.set_title("Throughput vs Concurrency Level", fontsize=12)
ax.legend(fontsize=10)
ax.grid(alpha=0.3)
ax.set_xticks(workers_mlkem)

# Annotate peak values
peak_mlkem = max(tps_mlkem)
peak_mldsa = max(tps_mldsa)
ax.annotate(f"Peak: {peak_mlkem:,.0f}/s",
            xy=(workers_mlkem[tps_mlkem.index(peak_mlkem)], peak_mlkem),
            xytext=(15, peak_mlkem + 500),
            color=COLORS["mlkem"], fontsize=9, fontweight="bold")
ax.annotate(f"Peak: {peak_mldsa:,.0f}/s",
            xy=(workers_mlkem[tps_mldsa.index(peak_mldsa)], peak_mldsa),
            xytext=(15, peak_mldsa - 1500),
            color=COLORS["mldsa"], fontsize=9, fontweight="bold")

# Right: p99 tail latency vs workers
ax2 = axes[1]
p99_mlkem = [r["p99_ms"] for r in exp1["mlkem768_concurrent"]]
p99_mldsa = [r["p99_ms"] for r in exp1["mldsa65_concurrent"]]
p99_rsa   = [r["p99_ms"] for r in exp1["rsa2048_concurrent"]]

ax2.plot(workers_mlkem, p99_mlkem, color=COLORS["mlkem"], marker="o",
         linewidth=2.5, markersize=8, label="ML-KEM-768")
ax2.plot(workers_mlkem, p99_mldsa, color=COLORS["mldsa"], marker="s",
         linewidth=2.5, markersize=8, label="ML-DSA-65")
ax2.plot(workers_mlkem, p99_rsa,   color=COLORS["rsa"],   marker="^",
         linewidth=2.5, markersize=8, label="RSA-2048")

# Banking SLA reference (100ms is typical)
ax2.axhline(y=100, color="red", linestyle="--", alpha=0.6, linewidth=1.5)
ax2.text(1, 105, "Typical banking SLA threshold (100ms)",
         color="red", fontsize=9, alpha=0.8)

ax2.set_xlabel("Concurrent Workers (Threads)", fontsize=12)
ax2.set_ylabel("p99 Latency (ms)", fontsize=12)
ax2.set_title("Tail Latency (p99) vs Concurrency Level", fontsize=12)
ax2.legend(fontsize=10)
ax2.grid(alpha=0.3)
ax2.set_xticks(workers_mlkem)

plt.tight_layout()
plt.savefig("hpc_experiments/plots/exp1_concurrent_throughput.png",
            dpi=150, bbox_inches="tight")
print("Saved: exp1_concurrent_throughput.png")
plt.close()

# ═══════════════════════════════════════════════════════════
# PLOT 2: Scaling Efficiency Curve
# ═══════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 2, figsize=(16, 6))
fig.suptitle(
    "ML-KEM-768 Parallel Scaling Analysis — PARAM Rudra HPC\n"
    "1 to 48 Cores | Sequential vs Concurrent Speedup",
    fontsize=13, fontweight="bold"
)

cores = [d["cores"] for d in exp2["scaling_data"]]
tps_s = [d["throughput_ops_per_sec"] for d in exp2["scaling_data"]]
eff_s = [d["parallel_efficiency_pct"] for d in exp2["scaling_data"]]
spd_s = [d["speedup"] for d in exp2["scaling_data"]]

# Left: throughput scaling
ax = axes[0]
ax.plot(cores, tps_s, color=COLORS["mlkem"], linewidth=2, label="Actual throughput")
# Ideal linear scaling
ideal = [tps_s[0] * c for c in cores]
ax.plot(cores, ideal, color="white", linewidth=1.5, linestyle="--",
        alpha=0.5, label="Ideal linear scaling")
ax.fill_between(cores, tps_s, ideal, alpha=0.1, color=COLORS["rsa"],
                label="Scaling gap (GIL overhead)")
ax.set_xlabel("Number of CPU Cores", fontsize=12)
ax.set_ylabel("Throughput (ops/sec)", fontsize=12)
ax.set_title("Throughput Scaling: 1→48 Cores", fontsize=12)
ax.legend(fontsize=10)
ax.grid(alpha=0.3)

# Right: parallel efficiency
ax2 = axes[1]
ax2.plot(cores, eff_s, color=COLORS["mldsa"], linewidth=2.5, marker=".")
ax2.axhline(y=80, color="white", linestyle="--", alpha=0.5)
ax2.text(2, 82, "80% efficiency threshold", color="white", fontsize=9, alpha=0.7)
ax2.fill_between(cores, eff_s, 0, alpha=0.15, color=COLORS["mldsa"])
ax2.set_xlabel("Number of CPU Cores", fontsize=12)
ax2.set_ylabel("Parallel Efficiency (%)", fontsize=12)
ax2.set_title("Parallel Efficiency vs Core Count\n(Note: Python GIL limits scaling — C impl. would be near-linear)", fontsize=11)
ax2.grid(alpha=0.3)
ax2.set_ylim(0, 110)

plt.tight_layout()
plt.savefig("hpc_experiments/plots/exp2_scaling_curve.png",
            dpi=150, bbox_inches="tight")
print("Saved: exp2_scaling_curve.png")
plt.close()

# ═══════════════════════════════════════════════════════════
# PLOT 3: AES Throughput — HPC vs Jetson vs Pi (3-way)
# ═══════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(13, 7))
fig.suptitle(
    "AES-256-GCM Encryption Throughput Across Hardware Tiers\n"
    "QuantumVault-X: Edge → HPC Infrastructure Characterization",
    fontsize=13, fontweight="bold"
)

labels = [r["size_label"] for r in exp3["cpu_results"]]
hpc_tp = [r["throughput_mbs"] for r in exp3["cpu_results"]]

# Reference data from prior experiments
jetson_ref = {
    "1 KB": 5.0, "10 KB": 341.4, "100 KB": 976.1,
    "1 MB": 1160.5, "10 MB": 1330.4
}
pi5_ref = {
    "1 KB": 6.4, "10 KB": 438.7, "100 KB": 982.8,
    "1 MB": 718.4, "10 MB": 829.4
}

x = np.arange(len(labels))
w = 0.28

# Only show sizes with all 3 platforms for comparison
common = [l for l in labels if l in jetson_ref]
x_c = np.arange(len(common))
hpc_c    = [next(r["throughput_mbs"] for r in exp3["cpu_results"] if r["size_label"]==l) for l in common]
jetson_c = [jetson_ref[l] for l in common]
pi5_c    = [pi5_ref[l] for l in common]

b1 = ax.bar(x_c - w, pi5_c,    w, label="Raspberry Pi 5 (baseline)",     color="#4a6fa5", edgecolor="white", linewidth=0.5)
b2 = ax.bar(x_c,     jetson_c, w, label="NVIDIA Jetson Orin Nano 8GB",   color=COLORS["jetson"], edgecolor="white", linewidth=0.5)
b3 = ax.bar(x_c + w, hpc_c,    w, label="PARAM Rudra HPC (this work)",   color=COLORS["hpc"], edgecolor="white", linewidth=0.5)

ax.set_xticks(x_c)
ax.set_xticklabels(common, fontsize=11)
ax.set_ylabel("AES-256-GCM Throughput (MB/s)", fontsize=12)
ax.set_title("Three-Tier Hardware Comparison: Edge → HPC", fontsize=12)
ax.legend(fontsize=11)
ax.grid(axis="y", alpha=0.3)

for bar in b3:
    ax.text(bar.get_x() + bar.get_width()/2,
            bar.get_height() + 20,
            f"{bar.get_height():.0f}",
            ha="center", va="bottom", color="white", fontsize=9)

plt.tight_layout()
plt.savefig("hpc_experiments/plots/exp3_aes_throughput_comparison.png",
            dpi=150, bbox_inches="tight")
print("Saved: exp3_aes_throughput_comparison.png")
plt.close()

# ═══════════════════════════════════════════════════════════
# PLOT 4: The headline summary — for LinkedIn/paper abstract
# ═══════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 3, figsize=(18, 6))
fig.suptitle(
    "QuantumVault-X: Post-Quantum Cryptography at Banking Scale\n"
    "PARAM Rudra HPC | NVIDIA Jetson Orin Nano | NIST FIPS 203/204",
    fontsize=14, fontweight="bold"
)

# Panel 1: Peak throughput comparison bar
ax = axes[0]
algos = ["ML-KEM-768\n(PQC)", "ML-DSA-65\n(PQC)", "RSA-2048\n(Classical)"]
peaks = [
    exp1["summary"]["peak_mlkem768_ops_per_sec"],
    exp1["summary"]["peak_mldsa65_ops_per_sec"],
    exp1["summary"]["peak_rsa2048_ops_per_sec"],
]
colors = [COLORS["mlkem"], COLORS["mldsa"], COLORS["rsa"]]
bars = ax.bar(algos, peaks, color=colors, edgecolor="white", linewidth=0.5)
ax.axhline(y=5000, color="white", linestyle="--", alpha=0.6)
ax.text(0, 5200, "UPI Peak ~5K TPS", color="white", fontsize=9)
for bar, val in zip(bars, peaks):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 100,
            f"{val:,.0f}/s", ha="center", color="white",
            fontsize=10, fontweight="bold")
ax.set_ylabel("Peak ops/second (48-core HPC)")
ax.set_title("Peak Concurrent Throughput\nPARAM Rudra 48-core Node")
ax.grid(axis="y", alpha=0.3)

# Panel 2: p99 latency comparison
ax2 = axes[1]
# At peak throughput worker count
p99_vals = [
    exp1["mlkem768_concurrent"][1]["p99_ms"],  # 2 workers (peak)
    exp1["mldsa65_concurrent"][3]["p99_ms"],   # 8 workers (peak)
    exp1["rsa2048_concurrent"][-1]["p99_ms"],  # 48 workers (best)
]
bars2 = ax2.bar(algos, p99_vals, color=colors, edgecolor="white", linewidth=0.5)
ax2.axhline(y=100, color="red", linestyle="--", alpha=0.6)
ax2.text(0, 105, "Banking SLA 100ms", color="red", fontsize=9)
for bar, val in zip(bars2, p99_vals):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
             f"{val:.1f}ms", ha="center", color="white", fontsize=10, fontweight="bold")
ax2.set_ylabel("p99 Tail Latency (ms) at Peak Throughput")
ax2.set_title("Tail Latency at Peak Load\n(p99 — worst 1% of operations)")
ax2.grid(axis="y", alpha=0.3)

# Panel 3: Three-tier AES at 10MB
ax3 = axes[2]
tiers = ["Raspberry Pi 5\n(Edge)", "Jetson Orin Nano\n(Edge GPU)", "PARAM Rudra\n(HPC Server)"]
aes_10mb = [829.4, 1330.4, 3485.0]
tier_colors = ["#4a6fa5", COLORS["jetson"], COLORS["hpc"]]
bars3 = ax3.bar(tiers, aes_10mb, color=tier_colors, edgecolor="white", linewidth=0.5)
for bar, val in zip(bars3, aes_10mb):
    ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 30,
             f"{val:.0f} MB/s", ha="center", color="white",
             fontsize=10, fontweight="bold")
ax3.set_ylabel("AES-256-GCM Throughput MB/s (10MB files)")
ax3.set_title("Bulk Encryption Throughput\nAcross Hardware Tiers")
ax3.grid(axis="y", alpha=0.3)

plt.tight_layout()
plt.savefig("hpc_experiments/plots/exp_summary_headline.png",
            dpi=150, bbox_inches="tight")
print("Saved: exp_summary_headline.png")
plt.close()

print("\n=== ALL PLOTS GENERATED ===")
print("Files in hpc_experiments/plots/:")
for f in sorted(os.listdir("hpc_experiments/plots/")):
    size = os.path.getsize(f"hpc_experiments/plots/{f}") // 1024
    print(f"  {f} ({size}KB)")
