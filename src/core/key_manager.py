"""
Key Manager: generate, store, load, rotate Kyber and Dilithium keypairs.
Keys stored in config/key_store/ as encrypted files.
Production: replace file storage with HSM (e.g., AWS CloudHSM, YubiHSM).
"""
import os
import json
from pathlib import Path
from cryptography.fernet import Fernet
from src.crypto.kyber_kem import kyber_keygen
from src.crypto.dilithium_sig import dilithium_keygen
from loguru import logger


KEY_STORE = Path("config/key_store")


def generate_master_password_key(password: str) -> bytes:
    """Derive a Fernet key from a password (use for dev; use HSM in prod)."""
    import base64, hashlib
    raw = hashlib.sha256(password.encode()).digest()
    return base64.urlsafe_b64encode(raw)


def generate_keypairs(identity: str, password: str) -> dict:
    """
    Generate a full keypair set for an identity (user/service).
    Saves encrypted keys to key_store.
    Returns public keys (safe to distribute).
    """
    KEY_STORE.mkdir(parents=True, exist_ok=True)
    fkey = generate_master_password_key(password)
    f = Fernet(fkey)

    kyber_pub, kyber_sec = kyber_keygen()
    dil_pub, dil_sec = dilithium_keygen()

    # Store encrypted private keys
    (KEY_STORE / f"{identity}_kyber_sec.enc").write_bytes(f.encrypt(kyber_sec))
    (KEY_STORE / f"{identity}_dil_sec.enc").write_bytes(f.encrypt(dil_sec))

    # Store plaintext public keys (safe)
    (KEY_STORE / f"{identity}_kyber_pub.key").write_bytes(kyber_pub)
    (KEY_STORE / f"{identity}_dil_pub.key").write_bytes(dil_pub)

    logger.success(f"Keys generated for identity: {identity}")
    return {"kyber_pub": kyber_pub, "dil_pub": dil_pub}


def load_private_keys(identity: str, password: str) -> dict:
    """Load and decrypt private keys for an identity."""
    fkey = generate_master_password_key(password)
    f = Fernet(fkey)
    kyber_sec = f.decrypt((KEY_STORE / f"{identity}_kyber_sec.enc").read_bytes())
    dil_sec = f.decrypt((KEY_STORE / f"{identity}_dil_sec.enc").read_bytes())
    return {"kyber_sec": kyber_sec, "dil_sec": dil_sec}


def load_public_keys(identity: str) -> dict:
    """Load public keys for an identity (no password needed)."""
    kyber_pub = (KEY_STORE / f"{identity}_kyber_pub.key").read_bytes()
    dil_pub = (KEY_STORE / f"{identity}_dil_pub.key").read_bytes()
    return {"kyber_pub": kyber_pub, "dil_pub": dil_pub}
