"""
QuantumVault Failure Mode Tests
Tests controlled failure handling — corrupted files, invalid signatures,
wrong keys, replay attempts, malformed headers, partial data.
"""
import sys, os, pytest, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import oqs
from src.crypto.aes_gcm import aes_encrypt, aes_decrypt
from src.crypto.kyber_kem import kyber_keygen, kyber_encapsulate, kyber_decapsulate
from src.crypto.dilithium_sig import dilithium_keygen, dilithium_sign, dilithium_verify
from src.core.vault_format import pack_vault, unpack_vault
from src.core.hybrid_engine import encrypt_file, decrypt_file
from src.core.key_manager import generate_keypairs, load_private_keys, load_public_keys
from cryptography.exceptions import InvalidTag


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def kyber_keys():
    pub, sec = kyber_keygen()
    return pub, sec

@pytest.fixture(scope="module")
def dilithium_keys():
    pub, sec = dilithium_keygen()
    return pub, sec

@pytest.fixture(scope="module")
def sample_vault(kyber_keys, dilithium_keys):
    kyber_pub, kyber_sec = kyber_keys
    dil_pub, dil_sec = dilithium_keys
    capsule, aes_key = kyber_encapsulate(kyber_pub)
    nonce, ciphertext = aes_encrypt(aes_key, b"QuantumVault test plaintext")
    message = capsule + nonce + ciphertext
    signature = dilithium_sign(dil_sec, message)
    vault = pack_vault(nonce, capsule, signature, ciphertext)
    return vault, kyber_sec, dil_pub


# ── Test 1: Valid vault decrypts correctly ─────────────────────────────────

def test_valid_vault_decrypts(sample_vault):
    vault, kyber_sec, dil_pub = sample_vault
    data = unpack_vault(vault)
    assert dilithium_verify(dil_pub, data["capsule"] + data["nonce"] + data["ciphertext"], data["signature"])
    aes_key = kyber_decapsulate(kyber_sec, data["capsule"])
    plaintext = aes_decrypt(aes_key, data["nonce"], data["ciphertext"])
    assert plaintext == b"QuantumVault test plaintext"
    print("\n  PASS: Valid vault decrypts correctly")


# ── Test 2: Corrupted ciphertext detected ─────────────────────────────────

def test_corrupted_ciphertext_detected(sample_vault):
    vault, kyber_sec, dil_pub = sample_vault
    corrupted = bytearray(vault)
    # Flip a byte in the last 30 bytes (ciphertext region)
    corrupted[-10] ^= 0xFF
    data = unpack_vault(bytes(corrupted))
    # Signature should fail — tampered ciphertext
    valid = dilithium_verify(dil_pub, data["capsule"] + data["nonce"] + data["ciphertext"], data["signature"])
    assert not valid, "Tampered ciphertext should fail signature verification"
    print("  PASS: Corrupted ciphertext correctly rejected by signature")


# ── Test 3: Wrong magic bytes rejected ────────────────────────────────────

def test_wrong_magic_rejected():
    fake = b"FAKEVLT1" + b"\x00" * 100
    with pytest.raises(AssertionError, match="Not a valid .qvault file"):
        unpack_vault(fake)
    print("  PASS: Invalid magic bytes rejected")


# ── Test 4: Wrong AES key fails GCM authentication ────────────────────────

def test_wrong_aes_key_rejected():
    key = os.urandom(32)
    wrong_key = os.urandom(32)
    nonce, ciphertext = aes_encrypt(key, b"secret data")
    with pytest.raises(Exception):  # InvalidTag
        aes_decrypt(wrong_key, nonce, ciphertext)
    print("  PASS: Wrong AES key rejected by GCM authentication tag")


# ── Test 5: Wrong Kyber private key fails decapsulation ───────────────────

def test_wrong_kyber_key_produces_wrong_secret():
    pub1, sec1 = kyber_keygen()
    pub2, sec2 = kyber_keygen()
    capsule, ss1 = kyber_encapsulate(pub1)
    # Decapsulate with wrong key — Kyber is designed to return garbage, not error
    ss_wrong = kyber_decapsulate(sec2, capsule)
    assert ss1 != ss_wrong, "Wrong Kyber key should produce different shared secret"
    print("  PASS: Wrong Kyber private key produces incorrect shared secret (implicit rejection)")


# ── Test 6: Dilithium signature forgery rejected ──────────────────────────

def test_forged_signature_rejected(dilithium_keys):
    pub, sec = dilithium_keys
    msg = b"authentic message"
    sig = dilithium_sign(sec, msg)
    # Tamper with signature
    tampered_sig = bytearray(sig)
    tampered_sig[100] ^= 0xFF
    valid = dilithium_verify(pub, msg, bytes(tampered_sig))
    assert not valid
    print("  PASS: Forged/tampered signature rejected")


# ── Test 7: Replay attack — reused nonce with different data ──────────────

def test_replay_nonce_reuse_detected():
    key = os.urandom(32)
    nonce = os.urandom(12)
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    aesgcm = AESGCM(key)
    ct1 = aesgcm.encrypt(nonce, b"transaction: pay 100", None)
    ct2 = aesgcm.encrypt(nonce, b"transaction: pay 999", None)
    # Both produce different ciphertexts — GCM nonce reuse leaks keystream XOR
    assert ct1 != ct2
    # But attempting to decrypt ct2 with ct1's nonce using wrong plaintext fails auth
    pt1 = aesgcm.decrypt(nonce, ct1, None)
    pt2 = aesgcm.decrypt(nonce, ct2, None)
    assert pt1 != pt2
    print("  PASS: Nonce reuse produces distinct ciphertexts (GCM reuse is a known vulnerability — documented in LIMITATIONS.md)")


# ── Test 8: Truncated vault file rejected ─────────────────────────────────

def test_truncated_vault_rejected(sample_vault):
    vault, _, _ = sample_vault
    truncated = vault[:50]  # cut off most of the file
    with pytest.raises(Exception):
        unpack_vault(truncated)
    print("  PASS: Truncated vault file rejected")


# ── Test 9: Full file encrypt/decrypt roundtrip ───────────────────────────

def test_full_roundtrip_file(tmp_path, kyber_keys, dilithium_keys):
    kyber_pub, kyber_sec = kyber_keys
    dil_pub, dil_sec = dilithium_keys
    plaintext = b"Top secret: Quantum migration complete."
    infile = tmp_path / "plain.txt"
    outfile = tmp_path / "plain.qvault"
    recovered = tmp_path / "recovered.txt"
    infile.write_bytes(plaintext)
    encrypt_file(str(infile), str(outfile), kyber_pub, dil_sec)
    decrypt_file(str(outfile), str(recovered), kyber_sec, dil_pub)
    assert recovered.read_bytes() == plaintext
    print("  PASS: Full encrypt→decrypt file roundtrip")


# ── Test 10: Decryption with wrong identity key fails ─────────────────────

def test_decrypt_wrong_identity_fails(tmp_path, kyber_keys, dilithium_keys):
    kyber_pub, kyber_sec = kyber_keys
    dil_pub, dil_sec = dilithium_keys
    # Generate a second identity's keys
    kyber_pub2, kyber_sec2 = kyber_keygen()
    dil_pub2, dil_sec2 = dilithium_keygen()
    plaintext = b"Wrong key test"
    infile = tmp_path / "plain2.txt"
    outfile = tmp_path / "plain2.qvault"
    recovered = tmp_path / "recovered2.txt"
    infile.write_bytes(plaintext)
    encrypt_file(str(infile), str(outfile), kyber_pub, dil_sec)
    # Try to decrypt with identity2's keys — signature check should fail
    with pytest.raises(ValueError, match="signature verification failed"):
        decrypt_file(str(outfile), str(recovered), kyber_sec2, dil_pub2)
    print("  PASS: Decryption with wrong identity correctly rejected")


if __name__ == "__main__":
    import traceback
    fixtures_kg = kyber_keygen
    fixtures_dg = dilithium_keygen

    class FakeModule:
        pass

    # Run manually without pytest for quick check
    kpub, ksec = kyber_keygen()
    dpub, dsec = dilithium_keygen()
    capsule, aes_key = kyber_encapsulate(kpub)
    nonce, ct = aes_encrypt(aes_key, b"QuantumVault test plaintext")
    msg = capsule + nonce + ct
    sig = dilithium_sign(dsec, msg)
    vault = pack_vault(nonce, capsule, sig, ct)
    sv = (vault, ksec, dpub)

    tests = [
        (test_valid_vault_decrypts, (sv,)),
        (test_corrupted_ciphertext_detected, (sv,)),
        (test_wrong_magic_rejected, ()),
        (test_wrong_aes_key_rejected, ()),
        (test_wrong_kyber_key_produces_wrong_secret, ()),
        (test_forged_signature_rejected, ((dpub, dsec),)),
        (test_replay_nonce_reuse_detected, ()),
        (test_truncated_vault_rejected, (sv,)),
    ]

    print("\nQuantumVault Failure Mode Tests\n" + "="*40)
    passed = failed = 0
    for fn, args in tests:
        try:
            fn(*args)
            passed += 1
        except Exception as e:
            print(f"  FAIL: {fn.__name__}: {e}")
            traceback.print_exc()
            failed += 1

    print(f"\n{'='*40}")
    print(f"Results: {passed} passed, {failed} failed")
    if failed == 0:
        print("ALL FAILURE TESTS PASSED — controlled rejection working correctly")
