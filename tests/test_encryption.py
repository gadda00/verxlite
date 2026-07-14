"""
Tests for encryption utilities.
"""

import pytest
from verxlite_api.utils.encryption import encrypt_data, decrypt_data, generate_key


class TestEncryption:
    def test_round_trip(self):
        plaintext = "super-secret-token"
        encrypted = encrypt_data(plaintext)
        assert encrypted != plaintext
        assert decrypt_data(encrypted) == plaintext

    def test_round_trip_unicode(self):
        plaintext = "ünïcödé-tokén-✓"
        encrypted = encrypt_data(plaintext)
        assert decrypt_data(encrypted) == plaintext

    def test_round_trip_empty(self):
        # encrypt_data(None) returns None (skips).
        assert encrypt_data(None) is None
        # Empty string is falsy but not None — should still encrypt.
        assert decrypt_data(encrypt_data("")) == ""

    def test_each_encryption_is_random(self):
        """Fernet includes a random IV, so two encryptions of the same text differ."""
        plaintext = "abc"
        a = encrypt_data(plaintext)
        b = encrypt_data(plaintext)
        assert a != b
        assert decrypt_data(a) == decrypt_data(b) == plaintext

    def test_generate_key_returns_valid_fernet(self):
        from cryptography.fernet import Fernet
        key = generate_key()
        # Should not raise.
        Fernet(key.encode())

    def test_decrypt_invalid_token_returns_input(self):
        # decrypt_data returns the input unchanged for falsy inputs.
        assert decrypt_data("") == ""
        assert decrypt_data(None) is None

    def test_decrypt_garbage_raises(self):
        with pytest.raises(Exception):
            decrypt_data("not-a-valid-fernet-token")
