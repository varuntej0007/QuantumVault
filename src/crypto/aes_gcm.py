"""
AES-256-GCM authenticated encryption module.
Uses 96-bit random nonce per encryption (NIST SP 800-38D compliant).
Never reuse a nonce — catastrophic if you do.
"""
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def aes_encrypt(key: bytes, plaintext: bytes) -> tuple[bytes, bytes]:
    """
    Encrypt plaintext with AES-256-GCM.
    Returns (nonce, ciphertext_with_tag).
    The 16-byte GCM auth tag is appended to ciphertext automatically.
    """
    assert len(key) == 32, "AES key must be 32 bytes (256-bit)"
    nonce = os.urandom(12)   # 96-bit nonce — NIST recommended
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)  # None = no AAD
    return nonce, ciphertext


def aes_decrypt(key: bytes, nonce: bytes, ciphertext: bytes) -> bytes:
    """
    Decrypt AES-256-GCM ciphertext.
    Raises InvalidTag if authentication fails — NEVER ignore this exception.
    """
    assert len(key) == 32
    assert len(nonce) == 12
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None)
