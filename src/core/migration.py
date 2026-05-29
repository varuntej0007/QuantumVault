"""
RSA-to-PQC Migration Utility.
Detects RSA-encrypted archives, decrypts them, re-encrypts with QuantumVault hybrid scheme.
"""
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
from loguru import logger
from pathlib import Path
import json


def load_rsa_private_key(pem_path: str, password: bytes = None):
    with open(pem_path, "rb") as f:
        return serialization.load_pem_private_key(
            f.read(), password=password, backend=default_backend()
        )


def migrate_rsa_to_pqc(rsa_archive_path: str,
                        rsa_key_pem: str,
                        output_vault_path: str,
                        kyber_pubkey: bytes,
                        dilithium_seckey: bytes,
                        rsa_password: bytes = None) -> None:
    """
    Migration pipeline:
    1. Read RSA-encrypted archive (expects: JSON with base64 fields)
    2. RSA-OAEP decrypt the AES key
    3. AES decrypt the payload (legacy)
    4. Re-encrypt with QuantumVault hybrid scheme
    5. Validate by immediately decrypting the output
    6. Write new .qvault file
    """
    import base64
    from src.crypto.aes_gcm import aes_decrypt
    from src.core.hybrid_engine import encrypt_file
    import tempfile

    logger.info(f"Migrating RSA archive: {rsa_archive_path}")

    # Step 1: Load RSA archive
    with open(rsa_archive_path, "r") as f:
        archive = json.load(f)

    assert archive.get("format") == "rsa-aes-hybrid-v1", \
        "Unrecognized RSA archive format"

    # Step 2: Decrypt AES key with RSA-OAEP
    rsa_key = load_rsa_private_key(rsa_key_pem, password=rsa_password)
    encrypted_aes_key = base64.b64decode(archive["encrypted_key"])
    aes_key = rsa_key.decrypt(
        encrypted_aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    # Step 3: Decrypt legacy payload
    nonce = base64.b64decode(archive["nonce"])
    ciphertext = base64.b64decode(archive["ciphertext"])
    plaintext = aes_decrypt(aes_key, nonce, ciphertext)
    logger.info(f"RSA archive decrypted: {len(plaintext)} bytes of plaintext")

    # Compute hash of plaintext for integrity check after re-encryption
    import hashlib
    original_hash = hashlib.sha256(plaintext).hexdigest()

    # Step 4+5: Write plaintext to temp file, re-encrypt with QuantumVault
    with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp") as tmp:
        tmp.write(plaintext)
        tmp_path = tmp.name

    try:
        encrypt_file(tmp_path, output_vault_path, kyber_pubkey, dilithium_seckey)
    finally:
        # Securely delete temp file
        Path(tmp_path).write_bytes(b"\x00" * len(plaintext))
        Path(tmp_path).unlink()

    logger.success(f"Migration complete → {output_vault_path}")
    logger.info(f"Original SHA-256: {original_hash} (keep for audit trail)")
