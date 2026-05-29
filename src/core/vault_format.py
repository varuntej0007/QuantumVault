"""
.qvault binary file format.

Layout (all lengths are 4-byte big-endian uint32):
┌─────────────────────────────────────────────────┐
│ MAGIC       │ 8 bytes   │ b"QVAULT01"           │
│ VERSION     │ 2 bytes   │ 0x0001                │
│ KEM_ALG_LEN │ 4 bytes   │ length of KEM name    │
│ KEM_ALG     │ variable  │ e.g. "Kyber768"       │
│ SIG_ALG_LEN │ 4 bytes   │ length of SIG name    │
│ SIG_ALG     │ variable  │ e.g. "Dilithium3"     │
│ NONCE       │ 12 bytes  │ AES GCM nonce         │
│ CAPSULE_LEN │ 4 bytes   │ length of Kyber capsule│
│ CAPSULE     │ variable  │ Kyber ciphertext      │
│ SIG_LEN     │ 4 bytes   │ length of Dilithium σ │
│ SIGNATURE   │ variable  │ Dilithium signature   │
│ CT_LEN      │ 4 bytes   │ length of AES ciphertext│
│ CIPHERTEXT  │ variable  │ AES-256-GCM ciphertext │
└─────────────────────────────────────────────────┘
"""
import struct

MAGIC = b"QVAULT01"
VERSION = 1


def pack_vault(nonce: bytes, capsule: bytes, signature: bytes,
               ciphertext: bytes,
               kem_alg: str = "Kyber768",
               sig_alg: str = "Dilithium3") -> bytes:
    kem_b = kem_alg.encode()
    sig_b = sig_alg.encode()
    parts = [
        MAGIC,
        struct.pack(">H", VERSION),
        struct.pack(">I", len(kem_b)), kem_b,
        struct.pack(">I", len(sig_b)), sig_b,
        nonce,
        struct.pack(">I", len(capsule)), capsule,
        struct.pack(">I", len(signature)), signature,
        struct.pack(">I", len(ciphertext)), ciphertext,
    ]
    return b"".join(parts)


def unpack_vault(data: bytes) -> dict:
    assert data[:8] == MAGIC, "Not a valid .qvault file"
    pos = 8
    version = struct.unpack(">H", data[pos:pos+2])[0]; pos += 2
    kem_len = struct.unpack(">I", data[pos:pos+4])[0]; pos += 4
    kem_alg = data[pos:pos+kem_len].decode(); pos += kem_len
    sig_len = struct.unpack(">I", data[pos:pos+4])[0]; pos += 4
    sig_alg = data[pos:pos+sig_len].decode(); pos += sig_len
    nonce = data[pos:pos+12]; pos += 12
    cap_len = struct.unpack(">I", data[pos:pos+4])[0]; pos += 4
    capsule = data[pos:pos+cap_len]; pos += cap_len
    sign_len = struct.unpack(">I", data[pos:pos+4])[0]; pos += 4
    signature = data[pos:pos+sign_len]; pos += sign_len
    ct_len = struct.unpack(">I", data[pos:pos+4])[0]; pos += 4
    ciphertext = data[pos:pos+ct_len]
    return {
        "version": version, "kem_alg": kem_alg, "sig_alg": sig_alg,
        "nonce": nonce, "capsule": capsule,
        "signature": signature, "ciphertext": ciphertext,
    }
