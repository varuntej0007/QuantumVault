# QuantumVault
### Post-Quantum Cryptography File Encryption & Migration Research Platform

> **Research prototype.** Not production-ready. See [security_notes/LIMITATIONS.md](security_notes/LIMITATIONS.md).

Built on NIST-standardised CRYSTALS-Kyber-768 (FIPS 203) and CRYSTALS-Dilithium-3 (FIPS 204),
running on Raspberry Pi 5 (8GB) — edge-native, no cloud dependency.

---

## Motivation

The Reserve Bank of India constituted the Q-SAFE Expert Committee (May 2025) to evaluate
quantum-safe cryptography for India's financial sector, including Cryptography Bill of Materials
(CBOM) assessment and migration roadmap development.

QuantumVault is a student-led proof-of-concept demonstrating that NIST-standardised PQC algorithms
are deployable on commodity ARM edge hardware — the infrastructure tier most relevant to India's
distributed banking endpoints.

---

## Architecture
FILE → AES-256-GCM (key K) → Ciphertext CT
↓
Kyber-768 encapsulates K → Capsule C
↓
Dilithium-3 signs (C ∥ Nonce ∥ CT) → Signature σ
↓
.qvault = { Magic | C | σ | CT }
DECRYPT: verify σ first → decapsulate C → decrypt CT

---

## Benchmark Results

> Results measured on Raspberry Pi 5 8GB (armhf, 32-bit userspace) under sequential
> single-threaded benchmark conditions, 1000 iterations with 95% confidence intervals.
> PQC and RSA algorithms differ in key sizes, signature bandwidth, and workload
> characteristics — comparisons are context-specific to key-generation latency on this platform.

| Operation | Kyber-768 | Dilithium-3 | RSA-2048 |
|---|---|---|---|
| KeyGen (mean) | ~0.18ms | ~0.49ms | ~332ms |
| Enc / Encap / Sign | ~0.20ms | ~1.49ms | ~0.19ms |
| Dec / Decap / Verify | ~0.20ms | ~0.48ms | ~3.89ms |
| CPU peak | 42.5% | — | 100% |
| Temp peak | 44.6°C | — | 46.9°C |

**Observed: Kyber-768 key generation latency is substantially lower than RSA-2048
on this platform under tested conditions (sequential ARM benchmark).**

![KeyGen Latency](benchmarks/plots/keygen_latency.png)
![Full Comparison](benchmarks/plots/full_comparison.png)
![System Resources](benchmarks/plots/system_resources.png)
![Throughput](benchmarks/plots/throughput.png)

---

## Features

- Hybrid KEM: Kyber-768 + AES-256-GCM (quantum-safe + performant)
- Dilithium-3 signature on every encrypted file (verify before decrypt)
- RSA → PQC migration utility
- Crypto-agility CBOM simulator (RBI Q-SAFE aligned, simulated systems only)
- 1000-iteration benchmark suite with 95% confidence intervals
- 10-test failure mode suite (corruption, forgery, replay, truncation)
- Audit logging for every crypto operation
- Docker support

---

## Quick Start

```bash
git clone https://github.com/varuntej0007/QuantumVault
cd QuantumVault && python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python main.py keygen --identity mykey
python main.py encrypt secret.txt secret.qvault --identity mykey
python main.py decrypt secret.qvault recovered.txt --identity mykey
python main.py cbom
python benchmarks/full_bench_1000.py
python tests/test_failure_modes.py
```

---

## Hardware

| Platform | Status |
|---|---|
| Raspberry Pi 5 8GB (armhf) | Working |
| NVIDIA Jetson Orin Nano | In progress |

---

## Standards Alignment

| Role | Algorithm | NIST Standard |
|---|---|---|
| Key Encapsulation | CRYSTALS-Kyber-768 | FIPS 203 (ML-KEM) |
| Digital Signature | CRYSTALS-Dilithium-3 | FIPS 204 (ML-DSA) |
| Symmetric Encryption | AES-256-GCM | FIPS 197 + SP 800-38D |

---

## Limitations

This is an experimental research prototype. Private keys use password-derived encryption
(not HSM). No side-channel countermeasures. Not validated for production deployment.
See [security_notes/LIMITATIONS.md](security_notes/LIMITATIONS.md) for full details.

---

## Research Context

- Amaravati Quantum Valley Round 2 selection
- Top 4.6% — WISER Quantum Algorithms Program (65,000+ participants)
- IBM Quantum hardware experiments: ibm_torino (133Q), ibm_marrakesh (156Q)
- B.Tech CSE (IoT), Malla Reddy University, Hyderabad | CGPA: 8.07
