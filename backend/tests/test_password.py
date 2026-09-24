import pytest
from app.core.security.password import verify_password, get_password_hash


class TestPassword:
    def test_hash_and_verify(self):
        password = "mypassword123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_wrong_password(self):
        hashed = get_password_hash("correct")
        assert verify_password("wrong", hashed) is False

    def test_empty_password(self):
        assert verify_password("", "hash") is False
        assert verify_password("password", "") is False

    def test_max_length_enforced(self):
        with pytest.raises(ValueError):
            get_password_hash("x" * 100)

    def test_different_hashes(self):
        h1 = get_password_hash("password")
        h2 = get_password_hash("password")
        assert h1 != h2

    def test_verify_malformed_hash(self):
        assert verify_password("password", "not-a-valid-hash") is False
