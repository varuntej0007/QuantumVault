import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json, glob
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

os.makedirs("benchmarks/plots", exist_ok=True)

# Load benchmark data
files = sorted(glob.glob("benchmarks/results/bench_*.json"))
assert files, "No benchmark results found. Run full_bench.py first."
with open(files[-1]) as f:
    data = json.load(f)
print(f"Loaded: {files[-1]}")

plt.style.use("dark_background")
COLORS = ["#00d4ff", "#7c3aed", "#f59e0b"]
labels = ["Kyber-768\n(PQC)", "Dilithium-3\n(PQC)", "RSA-2048\n(Classical)"]

# --- Plot 1: KeyGen Latency ---
fig, ax = plt.subplots(figsize=(10, 6))
values = [data["kyber768"]["keygen_mean_ms"], data["dilithium3"]["keygen_mean_ms"], data["rsa2048"]["keygen_mean_ms"]]
errors = [data["kyber768"]["keygen_stdev_ms"], data["dilithium3"]["keygen_stdev_ms"], data["rsa2048"]["keygen_stdev_ms"]]
bars = ax.bar(labels, values, color=COLORS, width=0.5, edgecolor="white", linewidth=0.5,
              yerr=errors, capsize=5, error_kw={"color": "white"})
for bar, val in zip(bars, values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() * 1.15,
            f"{val:.3f}ms", ha="center", va="bottom", color="white", fontsize=11, fontweight="bold")
ax.set_ylabel("Time (ms) — log scale", fontsize=12)
ax.set_title(f"Key Generation Latency — Raspberry Pi 5  (n={data['iterations']})", fontsize=14, fontweight="bold")
ax.set_yscale("log")
ax.grid(axis="y", alpha=0.3)
speedup = data["rsa2048"]["keygen_mean_ms"] / data["kyber768"]["keygen_mean_ms"]
ax.text(0.98, 0.97, f"Kyber-768 is {speedup:.0f}x faster than RSA-2048",
        transform=ax.transAxes, ha="right", va="top", color="#00d4ff", fontsize=11,
        bbox=dict(boxstyle="round", facecolor="#111133", alpha=0.85))
plt.tight_layout()
plt.savefig("benchmarks/plots/keygen_latency.png", dpi=150, bbox_inches="tight")
print("Saved: benchmarks/plots/keygen_latency.png")
plt.close()

# --- Plot 2: Full 3-operation comparison ---
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
fig.suptitle(f"PQC vs RSA — Full Benchmark  |  Raspberry Pi 5  |  n={data['iterations']}", fontsize=13, fontweight="bold")
short_labels = ["Kyber-768", "Dilithium-3", "RSA-2048"]
ops = [
    ("Key Generation",
     [data["kyber768"]["keygen_mean_ms"], data["dilithium3"]["keygen_mean_ms"], data["rsa2048"]["keygen_mean_ms"]],
     [data["kyber768"]["keygen_stdev_ms"], data["dilithium3"]["keygen_stdev_ms"], data["rsa2048"]["keygen_stdev_ms"]]),
    ("Encrypt / Encap / Sign",
     [data["kyber768"]["encap_mean_ms"], data["dilithium3"]["sign_mean_ms"], data["rsa2048"]["encrypt_mean_ms"]],
     [data["kyber768"]["encap_stdev_ms"], data["dilithium3"]["sign_stdev_ms"], data["rsa2048"]["encrypt_stdev_ms"]]),
    ("Decrypt / Decap / Verify",
     [data["kyber768"]["decap_mean_ms"], data["dilithium3"]["verify_mean_ms"], data["rsa2048"]["decrypt_mean_ms"]],
     [data["kyber768"]["decap_stdev_ms"], data["dilithium3"]["verify_stdev_ms"], data["rsa2048"]["decrypt_stdev_ms"]]),
]
for ax, (title, vals, errs) in zip(axes, ops):
    bars = ax.bar(short_labels, vals, color=COLORS, edgecolor="white", linewidth=0.5,
                  yerr=errs, capsize=4, error_kw={"color": "white"})
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(vals)*0.02,
                f"{val:.3f}", ha="center", va="bottom", color="white", fontsize=9)
    ax.set_title(title, fontsize=10)
    ax.set_ylabel("ms")
    ax.grid(axis="y", alpha=0.3)
    ax.tick_params(axis='x', labelsize=8)
plt.tight_layout()
plt.savefig("benchmarks/plots/full_comparison.png", dpi=150, bbox_inches="tight")
print("Saved: benchmarks/plots/full_comparison.png")
plt.close()

# --- Plot 3: System resources ---
if "system" in data and data["system"]:
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    fig.suptitle("System Resource Usage During Benchmark — Raspberry Pi 5", fontsize=13)
    metrics = [
        ("CPU Usage (%)",    data["system"]["cpu_mean_pct"],  data["system"]["cpu_max_pct"],  "#00d4ff"),
        ("Temperature (°C)", data["system"]["temp_mean_c"],   data["system"]["temp_max_c"],   "#f59e0b"),
        ("RAM Usage (MB)",   data["system"]["ram_mean_mb"],   data["system"]["ram_peak_mb"],  "#7c3aed"),
    ]
    for ax, (label, mean, peak, color) in zip(axes, metrics):
        # Fix: pass alpha per-bar as separate calls, not as a list
        ax.bar(["Mean"], [mean], color=color, alpha=0.65, edgecolor="white", linewidth=0.5)
        ax.bar(["Peak"], [peak], color=color, alpha=1.0,  edgecolor="white", linewidth=0.5)
        ax.set_title(label, fontsize=11)
        ax.set_ylabel(label)
        ax.grid(axis="y", alpha=0.3)
        for xpos, val in enumerate([mean, peak]):
            ax.text(xpos, val * 1.02, f"{val:.1f}", ha="center", va="bottom", color="white", fontsize=10)
    plt.tight_layout()
    plt.savefig("benchmarks/plots/system_resources.png", dpi=150, bbox_inches="tight")
    print("Saved: benchmarks/plots/system_resources.png")
    plt.close()

# --- Plot 4: Throughput scaling ---
tfiles = sorted(glob.glob("benchmarks/results/throughput_*.json"))
if tfiles:
    with open(tfiles[-1]) as f:
        tdata = json.load(f)
    sizes      = [r["size_label"]    for r in tdata]
    enc_ms     = [r["enc_mean_ms"]   for r in tdata]
    throughput = [r["throughput_mbs"] for r in tdata]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle("AES-256-GCM Throughput — Raspberry Pi 5 (Kyber-768 key exchange)", fontsize=13)

    ax1.plot(range(len(sizes)), enc_ms, color="#00d4ff", marker="o", linewidth=2, markersize=7)
    ax1.fill_between(range(len(sizes)), enc_ms, alpha=0.15, color="#00d4ff")
    ax1.set_xticks(range(len(sizes)))
    ax1.set_xticklabels(sizes)
    ax1.set_ylabel("Encryption Time (ms)")
    ax1.set_title("Latency by File Size")
    ax1.grid(alpha=0.3)

    ax2.bar(range(len(sizes)), throughput, color="#7c3aed", edgecolor="white", linewidth=0.5)
    ax2.set_xticks(range(len(sizes)))
    ax2.set_xticklabels(sizes)
    for i, val in enumerate(throughput):
        ax2.text(i, val + max(throughput)*0.01, f"{val:.0f}", ha="center", color="white", fontsize=9)
    ax2.set_ylabel("Throughput (MB/s)")
    ax2.set_title("Encryption Throughput by File Size")
    ax2.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    plt.savefig("benchmarks/plots/throughput.png", dpi=150, bbox_inches="tight")
    print("Saved: benchmarks/plots/throughput.png")
    plt.close()
else:
    print("No throughput data found — skipping throughput plot")

print("\nDone. All plots saved to benchmarks/plots/")
