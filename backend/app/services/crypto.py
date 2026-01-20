import base64
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import settings


def _get_key_bytes() -> bytes:
    key_b64 = settings.encryption_key.strip()
    try:
        # Accept missing base64 padding when env vars strip '='.
        padding = (-len(key_b64)) % 4
        key = base64.urlsafe_b64decode(key_b64 + ("=" * padding))
    except Exception as exc:
        raise ValueError("ENCRYPTION_KEY must be urlsafe base64") from exc
    if len(key) != 32:
        raise ValueError("ENCRYPTION_KEY must decode to 32 bytes (AES-256)")
    return key


def encrypt_text(plaintext: str) -> str:
    key = _get_key_bytes()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    payload = nonce + ciphertext
    return base64.urlsafe_b64encode(payload).decode("ascii")


def decrypt_text(ciphertext_b64: str) -> str:
    key = _get_key_bytes()
    raw = base64.urlsafe_b64decode(ciphertext_b64)
    nonce = raw[:12]
    ciphertext = raw[12:]
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode("utf-8")


def generate_key() -> str:
    return base64.urlsafe_b64encode(os.urandom(32)).decode("ascii")
