"""
Encryption Utilities
"""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os


def generate_key(salt: bytes = None) -> bytes:
    """
    Generate a Fernet key from a password.
    """
    if salt is None:
        salt = os.urandom(16)
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(b"verxlite-secret"))
    return key


def encrypt_data(data: str, key: str) -> str:
    """
    Encrypt data using Fernet symmetric encryption.
    """
    fernet = Fernet(key.encode())
    encrypted = fernet.encrypt(data.encode())
    return encrypted.decode()


def decrypt_data(encrypted_data: str, key: str) -> str:
    """
    Decrypt data using Fernet symmetric encryption.
    """
    fernet = Fernet(key.encode())
    decrypted = fernet.decrypt(encrypted_data.encode())
    return decrypted.decode()
