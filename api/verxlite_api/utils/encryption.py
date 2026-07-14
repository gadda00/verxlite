"""
Encryption Utilities

Uses Fernet symmetric encryption. The key is provided by Settings.ENCRYPTION_KEY
(or derived deterministically from JWT_SECRET in dev — see config.get_encryption_key).
"""

from cryptography.fernet import Fernet


def _get_fernet(key: str | bytes | None = None) -> Fernet:
    """
    Build a Fernet instance from a key string (or pull the configured key).
    """
    if key is None:
        # Lazy import to avoid circular dependency at module load time.
        from verxlite_api.config import settings

        key = settings.get_encryption_key()
    if isinstance(key, str):
        key = key.encode()
    return Fernet(key)


def generate_key() -> str:
    """
    Generate a new random Fernet key (call once, store the result, set as ENCRYPTION_KEY).
    """
    return Fernet.generate_key().decode()


def encrypt_data(data: str, key: str | bytes | None = None) -> str:
    """
    Encrypt a UTF-8 string and return a URL-safe string safe to store in a TEXT column.
    """
    if data is None:
        return None  # type: ignore[return-value]
    fernet = _get_fernet(key)
    encrypted = fernet.encrypt(data.encode("utf-8"))
    return encrypted.decode("ascii")


def decrypt_data(encrypted_data: str, key: str | bytes | None = None) -> str:
    """
    Decrypt a string previously produced by :func:`encrypt_data`.
    """
    if not encrypted_data:
        return encrypted_data  # type: ignore[return-value]
    fernet = _get_fernet(key)
    decrypted = fernet.decrypt(encrypted_data.encode("ascii"))
    return decrypted.decode("utf-8")
