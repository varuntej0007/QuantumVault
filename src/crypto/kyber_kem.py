"""
CRYSTALS-Kyber-768 Key Encapsulation Mechanism.
NIST standardised as ML-KEM (FIPS 203).
Security level: ~128-bit quantum security.
"""
import oqs


KEM_ALG = "Kyber768"


def kyber_keygen() -> tuple[bytes, bytes]:
    """
    Generate a Kyber-768 keypair.
    Returns (public_key, secret_key).
    public_key:  ~1184 bytes — share this freely
    secret_key:  ~2400 bytes — NEVER share, store encrypted
    """
    with oqs.KeyEncapsulation(KEM_ALG) as kem:
        public_key = kem.generate_keypair()
        secret_key = kem.export_secret_key()
    return public_key, secret_key


def kyber_encapsulate(public_key: bytes) -> tuple[bytes, bytes]:
    """
    Encapsulate: generate a shared secret and a ciphertext capsule.
    Returns (ciphertext_capsule, shared_secret).
    - ciphertext_capsule: ~1088 bytes — send this to the receiver
    - shared_secret: 32 bytes — use this as the AES-256 key
    """
    with oqs.KeyEncapsulation(KEM_ALG) as kem:
        ciphertext, shared_secret = kem.encap_secret(public_key)
    return ciphertext, shared_secret


def kyber_decapsulate(secret_key: bytes, ciphertext: bytes) -> bytes:
    """
    Decapsulate: recover the shared secret using your private key.
    Returns shared_secret (32 bytes) — this is your AES-256 key.
    """
    with oqs.KeyEncapsulation(KEM_ALG, secret_key=secret_key) as kem:
        shared_secret = kem.decap_secret(ciphertext)
    return shared_secret
