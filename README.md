# QuantumVault
### Post-Quantum Cryptography File Encryption & Migration Research Platform

> **Research prototype.** Not production-ready. See [security_notes/LIMITATIONS.md](security_notes/LIMITATIONS.md).

Built on NIST-standardized CRYSTALS-Kyber-768 (FIPS 203) and CRYSTALS-Dilithium-3 (FIPS 204), running on Raspberry Pi 5 (8GB) — edge-native, no cloud dependency.

---

## Motivation

The Reserve Bank of India constituted the Q-SAFE Expert Committee (May 2025) to evaluate quantum-safe cryptography for India's financial sector, including Cryptography Bill of Materials (CBOM) assessment and migration roadmap development.

QuantumVault is a student-led proof-of-concept demonstrating that NIST-standardized PQC algorithms are deployable on commodity ARM edge hardware — the infrastructure tier most relevant to distributed banking endpoints and edge systems.

---

## Architecture

```text
FILE -> AES-256-GCM (key K) -> Ciphertext CT
        |
        v
Kyber-768 encapsulates K -> Capsule C
        |
        v
Dilithium-3 signs (C | Nonce | CT) -> Signature
        |
        v
.qvault = { Magic | Capsule | Signature | Ciphertext }

DECRYPT:
Verify Signature -> Decapsulate Capsule -> Recover AES Key -> Decrypt Ciphertext
Benchmark Results

Results measured on Raspberry Pi 5 8GB (armhf, 32-bit userspace) under sequential single-threaded benchmark conditions, 1000 iterations with 95% confidence intervals.

PQC and RSA algorithms differ in key sizes, bandwidth overhead, and workload characteristics. Comparisons are platform-specific and context-dependent.

Operation	Kyber-768	Dilithium-3	RSA-2048
KeyGen (mean)	~0.18ms	~0.49ms	~332ms
Enc / Encap / Sign	~0.20ms	~1.49ms	~0.19ms
Dec / Decap / Verify	~0.20ms	~0.48ms	~3.89ms
CPU peak	42.5%	—	100%
Temp peak	44.6°C	—	46.9°C
Observation

Observed substantially lower key-generation latency for Kyber-768 compared to RSA-2048 on Raspberry Pi 5 ARM hardware under tested benchmark conditions.

Throughput Benchmarks
File Size	Encrypt Time	Decrypt Time	Throughput
1 KB	0.16ms	0.01ms	6.3 MB/s
10 KB	0.02ms	0.02ms	438.7 MB/s
100 KB	0.10ms	0.11ms	953.8 MB/s
1 MB	1.30ms	1.31ms	768.2 MB/s
10 MB	11.64ms	11.82ms	859.2 MB/s
Features
Kyber-768 key encapsulation
Dilithium-3 digital signatures
AES-256-GCM authenticated encryption
Hybrid PQC encryption pipeline
Custom .qvault secure container format
RSA-to-PQC migration simulation
CBOM-oriented infrastructure analysis
ARM edge benchmarking suite
Statistical benchmark framework
JSON benchmark export
Automated plot generation
CBOM Simulation

QuantumVault includes an experimental Cryptography Bill of Materials (CBOM) simulator aligned with RBI Q-SAFE migration themes.

Example simulated infrastructure:

ATM Network Nodes
Core Banking TLS
Mobile Banking Authentication
Inter-bank Settlement Systems
Audit Log Integrity
Document Signing Pipelines
Repository Structure
/core
/benchmarks
/results
/plots
/tests
/docs
/security_notes
Security Notes

QuantumVault is an experimental research platform.

Current implementation does NOT yet address:

side-channel resistance
hardware fault attacks
secure enclave integration
enterprise key management
formal cryptographic audits
production-scale deployment hardening

See:

security_notes/LIMITATIONS.md
security_notes/THREAT_MODEL.md
Future Work
NVIDIA Jetson Orin Nano benchmarking
GPU-assisted cryptographic acceleration
Secure edge transaction simulation
Hybrid RSA + PQC migration workflows
Thermal and power characterization
Concurrent workload benchmarking
Extended failure-mode analysis
Reproducibility

Benchmarks include:

500-iteration and 1000-iteration runs
JSON result archival
matplotlib plot generation
confidence interval calculation
ARM platform-specific measurement logging
Disclaimer

QuantumVault is a research and educational project intended for experimental benchmarking and infrastructure migration analysis only.

It is NOT production-ready banking software and should not be deployed in real financial environments without formal security review and cryptographic audit.
