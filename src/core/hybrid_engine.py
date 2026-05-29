"""
Hybrid encryption engine.
Orchestrates: AES-256-GCM + Kyber-768 KEM + Dilithium-3 signatures.
This is the heart of QuantumVault.
"""
import os
from loguru import logger

from src.crypto.aes_gcm import aes_encrypt, aes_decrypt
from src.crypto.kyber_kem import kyber_encapsulate, kyber_decapsulate
from src.crypto.dilithium_sig import dilithium_sign, dilithium_verify
from src.core.vault_format import pack_vault, unpack_vault


def encrypt_file(input_path: str, output_path: str,
                 kyber_pubkey: bytes, dilithium_seckey: bytes) -> None:
    """
    Full hybrid encrypt pipeline:
    1. Read plaintext
    2. Generate AES-256 key via Kyber encapsulation
    3. AES-GCM encrypt the file
    4. Sign the entire package with Dilithium
    5. Write .qvault file
    """
    logger.info(f"Encrypting: {input_path}")

    # Step 1: Read plaintext
    with open(input_path, "rb") as f:
        plaintext = f.read()

    # Step 2: Kyber encapsulates the AES key
    # capsule = what we store; aes_key = symmetric key for this file
    capsule, aes_key = kyber_encapsulate(kyber_pubkey)
    logger.debug(f"Kyber capsule: {len(capsule)} bytes, AES key: {len(aes_key)} bytes")

    # Step 3: AES-256-GCM encrypt the file
    nonce, ciphertext = aes_encrypt(aes_key, plaintext)
    logger.debug(f"AES-GCM ciphertext: {len(ciphertext)} bytes")

    # Step 4: Sign (capsule + nonce + ciphertext) to cover the whole package
    # This ensures an attacker cannot swap the capsule or tamper with ciphertext
    message_to_sign = capsule + nonce + ciphertext
    signature = dilithium_sign(dilithium_seckey, message_to_sign)
    logger.debug(f"Dilithium signature: {len(signature)} bytes")

    # Step 5: Pack and write .qvault file
    vault_bytes = pack_vault(nonce, capsule, signature, ciphertext)
    with open(output_path, "wb") as f:
        f.write(vault_bytes)

    # Zero out sensitive key material from memory
    aes_key = b"\x00" * len(aes_key)
    logger.success(f"Written: {output_path} ({len(vault_bytes)} bytes)")


def decrypt_file(input_path: str, output_path: str,
                 kyber_seckey: bytes, dilithium_pubkey: bytes) -> None:
    """
    Full hybrid decrypt pipeline:
    1. Read and unpack .qvault file
    2. Verify Dilithium signature (ALWAYS first — fail fast)
    3. Decapsulate Kyber capsule to get AES key
    4. AES-GCM decrypt the file
    5. Write plaintext output
    """
    logger.info(f"Decrypting: {input_path}")

    # Step 1: Read and unpack
    with open(input_path, "rb") as f:
        vault_data = f.read()
    vault = unpack_vault(vault_data)

    # Step 2: Verify signature FIRST — reject tampered files immediately
    message_to_verify = vault["capsule"] + vault["nonce"] + vault["ciphertext"]
    if not dilithium_verify(dilithium_pubkey, message_to_verify, vault["signature"]):
        logger.error("SIGNATURE VERIFICATION FAILED — file may be tampered!")
        raise ValueError("Dilithium signature verification failed. Aborting decryption.")
    logger.info("Signature verified OK")

    # Step 3: Kyber decapsulate to recover AES key
    aes_key = kyber_decapsulate(kyber_seckey, vault["capsule"])

    # Step 4: AES-GCM decrypt
    plaintext = aes_decrypt(aes_key, vault["nonce"], vault["ciphertext"])

    # Step 5: Write output
    with open(output_path, "wb") as f:
        f.write(plaintext)

    aes_key = b"\x00" * len(aes_key)
    logger.success(f"Decrypted: {output_path}")
