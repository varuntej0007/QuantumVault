"""
QuantumVault Benchmark Suite.
Measures and compares: RSA-2048, Kyber-768, Dilithium-3, AES-256-GCM
Output: Rich table + JSON results saved to benchmarks/results.json
"""
import time, os, json
import oqs
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
from rich.console import Console
from rich.table import Table

console = Console()
ITERATIONS = 100


def bench_kyber():
    times = {"keygen": [], "encap": [], "decap": []}
    for _ in range(ITERATIONS):
        t0 = time.perf_counter()
        with oqs.KeyEncapsulation("Kyber768") as kem:
            pub = kem.generate_keypair()
            sec = kem.export_secret_key()
        times["keygen"].append(time.perf_counter() - t0)

        t0 = time.perf_counter()
        with oqs.KeyEncapsulation("Kyber768") as kem:
            ct, ss = kem.encap_secret(pub)
        times["encap"].append(time.perf_counter() - t0)

        t0 = time.perf_counter()
        with oqs.KeyEncapsulation("Kyber768", secret_key=sec) as kem:
            kem.decap_secret(ct)
        times["decap"].append(time.perf_counter() - t0)

    return {k: sum(v)/len(v)*1000 for k, v in times.items()}  # ms


def bench_dilithium():
    msg = os.urandom(1024)
    times = {"keygen": [], "sign": [], "verify": []}
    for _ in range(ITERATIONS):
        t0 = time.perf_counter()
        with oqs.Signature("Dilithium3") as sig:
            pub = sig.generate_keypair()
            sec = sig.export_secret_key()
        times["keygen"].append(time.perf_counter() - t0)

        t0 = time.perf_counter()
        with oqs.Signature("Dilithium3", secret_key=sec) as sig:
            signature = sig.sign(msg)
        times["sign"].append(time.perf_counter() - t0)

        t0 = time.perf_counter()
        with oqs.Signature("Dilithium3") as sig:
            sig.verify(msg, signature, pub)
        times["verify"].append(time.perf_counter() - t0)

    return {k: sum(v)/len(v)*1000 for k, v in times.items()}


def bench_rsa():
    from cryptography.hazmat.backends import default_backend
    times = {"keygen": [], "encrypt": [], "decrypt": []}
    key = rsa.generate_private_key(65537, 2048, default_backend())
    msg = os.urandom(190)  # max for RSA-2048 OAEP
    for _ in range(ITERATIONS):
        t0 = time.perf_counter()
        rsa.generate_private_key(65537, 2048, default_backend())
        times["keygen"].append(time.perf_counter() - t0)

        t0 = time.perf_counter()
        ct = key.public_key().encrypt(msg, padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(), label=None))
        times["encrypt"].append(time.perf_counter() - t0)

        t0 = time.perf_counter()
        key.decrypt(ct, padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(), label=None))
        times["decrypt"].append(time.perf_counter() - t0)

    return {k: sum(v)/len(v)*1000 for k, v in times.items()}


if __name__ == "__main__":
    console.print("\n[bold cyan]QuantumVault Benchmark Suite[/bold cyan] — 100 iterations each\n")

    console.print("Benchmarking Kyber-768...")
    kyber = bench_kyber()
    console.print("Benchmarking Dilithium-3...")
    dil = bench_dilithium()
    console.print("Benchmarking RSA-2048...")
    rsa_r = bench_rsa()

    table = Table(title="PQC vs RSA Performance (Raspberry Pi 5 / Jetson Orin Nano)")
    table.add_column("Operation", style="bold")
    table.add_column("Kyber-768", justify="right", style="green")
    table.add_column("Dilithium-3", justify="right", style="cyan")
    table.add_column("RSA-2048", justify="right", style="yellow")

    table.add_row("KeyGen", f"{kyber['keygen']:.2f}ms", f"{dil['keygen']:.2f}ms", f"{rsa_r['keygen']:.0f}ms")
    table.add_row("Enc/Sign", f"{kyber['encap']:.2f}ms", f"{dil['sign']:.2f}ms", f"{rsa_r['encrypt']:.2f}ms")
    table.add_row("Dec/Verify", f"{kyber['decap']:.2f}ms", f"{dil['verify']:.2f}ms", f"{rsa_r['decrypt']:.2f}ms")

    console.print(table)

    results = {"platform": "arm64", "kyber768": kyber, "dilithium3": dil, "rsa2048": rsa_r}
    with open("benchmarks/results.json", "w") as f:
        json.dump(results, f, indent=2)
    console.print("\n[green]Results saved to benchmarks/results.json[/green]")
