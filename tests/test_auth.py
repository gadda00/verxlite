"""
Tests for auth deps & JWT.
"""

import pytest
from verxlite_api.deps import (
    create_access_token,
    verify_access_token,
    hash_password,
    verify_password,
)


class TestJWT:
    def test_round_trip(self):
        token = create_access_token(data={"sub": "user_1", "role": "admin"})
        payload = verify_access_token(token)
        assert payload["sub"] == "user_1"
        assert payload["role"] == "admin"
        assert "exp" in payload
        assert "iat" in payload

    def test_invalid_token_raises(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            verify_access_token("not-a-real-token")
        assert exc_info.value.status_code == 401
        assert "Invalid token" in exc_info.value.detail


class TestPasswordHashing:
    def test_hash_and_verify(self):
        password = "supersecret123"
        hashed = hash_password(password)
        assert hashed != password
        assert verify_password(password, hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("correct-password")
        assert verify_password("wrong-password", hashed) is False

    def test_verify_no_hash(self):
        assert verify_password("anything", None) is False

    def test_verify_malformed_hash(self):
        assert verify_password("anything", "not-a-real-hash") is False

    def test_each_hash_is_unique(self):
        """bcrypt uses a random salt — same password produces different hashes."""
        a = hash_password("same")
        b = hash_password("same")
        assert a != b
        assert verify_password("same", a) is True
        assert verify_password("same", b) is True
