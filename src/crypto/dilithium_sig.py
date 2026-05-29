"""
CRYSTALS-Dilithium-3 Digital Signature.
NIST standardised as ML-DSA (FIPS 204).
Security level: ~128-bit quantum security.
Signature size: ~3293 bytes.
"""
import oqs


SIG_ALG = "Dilithium3"


def dilithium_keygen() -> tuple[bytes, bytes]:
    """
    Generate a Dilithium-3 signing keypair.
    Returns (public_key, secret_key).
    """
    with oqs.Signature(SIG_ALG) as signer:
        public_key = signer.generate_keypair()
        secret_key = signer.export_secret_key()
    return public_key, secret_key


def dilithium_sign(secret_key: bytes, message: bytes) -> bytes:
    """
    Sign a message (use the full package bytes as message).
    Returns signature (~3293 bytes).
    """
    with oqs.Signature(SIG_ALG, secret_key=secret_key) as signer:
        signature = signer.sign(message)
    return signature


def dilithium_verify(public_key: bytes, message: bytes, signature: bytes) -> bool:
    """
    Verify a Dilithium-3 signature.
    Returns True if valid, False if tampered or forged.
    NEVER skip verification before decryption.
    """
    with oqs.Signature(SIG_ALG) as verifier:
        return verifier.verify(message, signature, public_key)
