"""Encryption service for sensitive data at rest.

Uses Fernet symmetric encryption for fields like API keys, webhook URLs, OAuth tokens.
"""
import os
import base64
from cryptography.fernet import Fernet

# Generate key: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")


class EncryptionService:
    """Encrypt/decrypt sensitive fields stored in the database."""

    def __init__(self):
        if ENCRYPTION_KEY:
            self._fernet = Fernet(ENCRYPTION_KEY.encode())
            self.available = True
        else:
            self._fernet = None
            self.available = False

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a string value. Returns base64 ciphertext."""
        if not self.available or not plaintext:
            return plaintext
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a ciphertext string back to plaintext."""
        if not self.available or not ciphertext:
            return ciphertext
        try:
            return self._fernet.decrypt(ciphertext.encode()).decode()
        except Exception:
            return ciphertext  # Return as-is if not encrypted

    def rotate_key(self, old_key: str, new_key: str, ciphertext: str) -> str:
        """Re-encrypt data with a new key."""
        old_fernet = Fernet(old_key.encode())
        new_fernet = Fernet(new_key.encode())
        plaintext = old_fernet.decrypt(ciphertext.encode())
        return new_fernet.encrypt(plaintext).decode()


# Global instance
encryption = EncryptionService()
