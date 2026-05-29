# QuantumVault — Technical Architecture

## Overview

QuantumVault implements a hybrid post-quantum encryption pipeline on ARM edge hardware.
"Hybrid" means PQC handles key exchange while AES-256-GCM handles bulk data encryption —
combining quantum resistance with classical performance.

## Cryptographic Pipeline
ENCRYPTION
──────────
Input file (plaintext P)
│
├─ 1. Kyber-768 KEM
│      Generate ephemeral AES-256 key K via encapsulation
│      Output: Capsule C (1088 bytes) + shared secret K (32 bytes)
│
├─ 2. AES-256-GCM
│      Encrypt P with K and random 96-bit nonce N
│      Output: Ciphertext CT (|P| + 16 bytes GCM tag)
│
├─ 3. Dilithium-3 Signature
│      Sign(C ∥ N ∥ CT) with sender's private key
│      Output: Signature σ (3293 bytes)
│
└─ 4. .qvault file
Magic(8) | Version(2) | AlgIDs | Nonce(12) |
Capsule(1088) | Signature(3293) | CiphertextDECRYPTION
──────────
1. Verify σ over (C ∥ N ∥ CT)  ← ALWAYS FIRST. Reject if invalid.
2. Kyber-768 decapsulate C → recover K
3. AES-256-GCM decrypt CT with K, N → plaintext P

## Module Map

| Module | Responsibility |
|---|---|
| `src/crypto/kyber_kem.py` | Kyber-768 keygen, encapsulate, decapsulate |
| `src/crypto/dilithium_sig.py` | Dilithium-3 keygen, sign, verify |
| `src/crypto/aes_gcm.py` | AES-256-GCM encrypt/decrypt |
| `src/core/hybrid_engine.py` | Orchestrates full pipeline |
| `src/core/vault_format.py` | Binary .qvault pack/unpack |
| `src/core/key_manager.py` | Key generation, encrypted storage, loading |
| `src/core/migration.py` | RSA-to-PQC archive migration |
| `src/core/crypto_agility.py` | CBOM simulator, migration cost analysis |
| `src/cli/commands.py` | Click CLI: keygen, encrypt, decrypt, migrate, cbom |
| `benchmarks/` | 1000-iteration statistical benchmark suite |
| `tests/` | Failure mode and correctness tests |

## Security Design Decisions

**Why verify signature before decryption?**
Prevents chosen-ciphertext attacks. An attacker who can submit arbitrary
ciphertexts and observe decryption behaviour can potentially recover keys.
Signature-first ensures only authenticated ciphertexts are ever decrypted.

**Why AES-256-GCM and not ChaCha20-Poly1305?**
AES-NI hardware acceleration is available on most deployment targets.
GCM provides authenticated encryption with 128-bit authentication tags.
Both are acceptable; AES-256-GCM was chosen for FIPS 140-3 alignment.

**Why Kyber-768 and not Kyber-512 or Kyber-1024?**
Kyber-768 targets NIST security level 3 (~AES-192 equivalent).
Kyber-512 (level 1) is faster but lower security margin.
Kyber-1024 (level 5) is slower with marginal security gain for this use case.

## Key Sizes (bytes)

| Component | Size |
|---|---|
| Kyber-768 public key | 1184 bytes |
| Kyber-768 secret key | 2400 bytes |
| Kyber-768 capsule | 1088 bytes |
| Dilithium-3 public key | 1952 bytes |
| Dilithium-3 secret key | 4000 bytes |
| Dilithium-3 signature | 3293 bytes |
| AES-256 key | 32 bytes |
| GCM nonce | 12 bytes |
| GCM auth tag | 16 bytes |

## .qvault File FormatOffset   Size      Field
──────── ───────── ───────────────────────────────
0        8 bytes   Magic: "QVAULT01"
8        2 bytes   Version: 0x0001
10       4+N       KEM algorithm name (length-prefixed)
14+N     4+M       Signature algorithm name (length-prefixed)
...      12 bytes  AES-GCM nonce
...      4+1088    Kyber capsule (length-prefixed)
...      4+3293    Dilithium signature (length-prefixed)
...      4+|CT|    AES ciphertext + GCM tag (length-prefixed)
