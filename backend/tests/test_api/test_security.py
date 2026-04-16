"""Test security validators and encryption."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import pytest
from security.validators import validate_password, sanitize_input, validate_service_name
from security.encryption import EncryptionService
from fastapi import HTTPException


def test_password_too_short():
    with pytest.raises(HTTPException) as exc:
        validate_password("Ab1!")
    assert "8 characters" in str(exc.value.detail)


def test_password_no_uppercase():
    with pytest.raises(HTTPException):
        validate_password("abcdefg1!")


def test_password_no_lowercase():
    with pytest.raises(HTTPException):
        validate_password("ABCDEFG1!")


def test_password_no_digit():
    with pytest.raises(HTTPException):
        validate_password("Abcdefgh!")


def test_password_no_special():
    with pytest.raises(HTTPException):
        validate_password("Abcdefg1")


def test_password_valid():
    result = validate_password("SecurePass1!")
    assert result == "SecurePass1!"


def test_sanitize_html():
    result = sanitize_input("<script>alert('xss')</script>")
    assert "<script>" not in result
    assert "&lt;script&gt;" in result


def test_sanitize_null_bytes():
    result = sanitize_input("hello\x00world")
    assert "\x00" not in result


def test_sanitize_max_length():
    result = sanitize_input("a" * 20000, max_length=100)
    assert len(result) == 100


def test_validate_service_name_valid():
    assert validate_service_name("api-server") == "api-server"
    assert validate_service_name("web_app_v2") == "web_app_v2"


def test_validate_service_name_invalid():
    with pytest.raises(HTTPException):
        validate_service_name("invalid service name!")


def test_encryption_roundtrip():
    """Test encrypt/decrypt with a generated key."""
    from cryptography.fernet import Fernet
    key = Fernet.generate_key().decode()
    os.environ["ENCRYPTION_KEY"] = key
    svc = EncryptionService()
    svc._fernet = Fernet(key.encode())
    svc.available = True

    encrypted = svc.encrypt("my-secret-api-key")
    assert encrypted != "my-secret-api-key"
    decrypted = svc.decrypt(encrypted)
    assert decrypted == "my-secret-api-key"
    del os.environ["ENCRYPTION_KEY"]
