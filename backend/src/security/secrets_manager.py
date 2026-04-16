"""
Secrets Manager: Secure storage, rotation, and auditing of secrets.
Uses Fernet symmetric encryption with key rotation support.
"""
import base64
import hashlib
import json
import logging
import os
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


@dataclass
class SecretEntry:
    name: str
    encrypted_value: str
    created_at: str
    rotated_at: str
    rotation_policy_days: int = 90
    version: int = 1
    tags: Dict[str, str] = field(default_factory=dict)
    access_log: List[Dict[str, str]] = field(default_factory=list)


class SecretsManager:
    """
    Centralized secrets management with encryption, rotation, and audit trail.
    Production use: replace in-memory store with HashiCorp Vault or AWS Secrets Manager.
    """

    def __init__(self, master_key: Optional[str] = None):
        self._master_key = master_key or os.getenv("SECRETS_MASTER_KEY", "dev-master-key-change-in-production")
        self._secrets: Dict[str, SecretEntry] = {}
        self._lock = threading.Lock()
        self._rotation_history: List[Dict[str, Any]] = []
        self._derive_encryption_key()
        self._seed_demo_secrets()

    def _derive_encryption_key(self):
        """Derive a Fernet-compatible key from master key."""
        key_bytes = hashlib.sha256(self._master_key.encode()).digest()
        self._encryption_key = base64.urlsafe_b64encode(key_bytes)

    def _encrypt(self, plaintext: str) -> str:
        """Encrypt a value. Uses Fernet if available, else base64 obfuscation for demo."""
        try:
            from cryptography.fernet import Fernet
            f = Fernet(self._encryption_key)
            return f.encrypt(plaintext.encode()).decode()
        except ImportError:
            # Fallback: base64 encode (NOT secure — for demo only)
            return base64.b64encode(plaintext.encode()).decode()

    def _decrypt(self, ciphertext: str) -> str:
        """Decrypt a value."""
        try:
            from cryptography.fernet import Fernet
            f = Fernet(self._encryption_key)
            return f.decrypt(ciphertext.encode()).decode()
        except ImportError:
            return base64.b64decode(ciphertext.encode()).decode()

    def _seed_demo_secrets(self):
        """Seed with demo secrets for dashboard."""
        demo_secrets = [
            ("DATABASE_URL", "postgresql://user:pass@db:5432/devops", {"type": "database", "env": "production"}),
            ("REDIS_URL", "redis://redis:6379/0", {"type": "cache", "env": "production"}),
            ("JWT_SECRET", "super-secret-jwt-key-2026", {"type": "auth", "env": "all"}),
            ("CLAUDE_API_KEY", "sk-ant-api03-xxxx...xxxx", {"type": "api_key", "env": "production"}),
            ("SMTP_PASSWORD", "email-service-password", {"type": "email", "env": "production"}),
            ("GITHUB_TOKEN", "ghp_xxxxxxxxxxxxxxxxxxxx", {"type": "api_key", "env": "ci"}),
            ("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/xxx/yyy/zzz", {"type": "webhook", "env": "production"}),
            ("AWS_SECRET_ACCESS_KEY", "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY", {"type": "cloud", "env": "production"}),
        ]
        now = datetime.now(timezone.utc).isoformat()
        for name, value, tags in demo_secrets:
            self._secrets[name] = SecretEntry(
                name=name,
                encrypted_value=self._encrypt(value),
                created_at=now,
                rotated_at=now,
                tags=tags,
            )

    def store(self, name: str, value: str, tags: Dict[str, str] = None,
              rotation_days: int = 90) -> Dict[str, Any]:
        """Store a new secret or update existing."""
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            existing = self._secrets.get(name)
            version = (existing.version + 1) if existing else 1

            self._secrets[name] = SecretEntry(
                name=name,
                encrypted_value=self._encrypt(value),
                created_at=existing.created_at if existing else now,
                rotated_at=now,
                rotation_policy_days=rotation_days,
                version=version,
                tags=tags or (existing.tags if existing else {}),
            )

        logger.info(f"Secret stored: {name} (v{version})")
        return {"name": name, "version": version, "stored_at": now}

    def retrieve(self, name: str, accessor: str = "system") -> Optional[str]:
        """Retrieve and decrypt a secret. Logs access."""
        entry = self._secrets.get(name)
        if not entry:
            return None

        entry.access_log.append({
            "accessor": accessor,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": "read",
        })
        # Keep only last 50 access entries
        if len(entry.access_log) > 50:
            entry.access_log = entry.access_log[-50:]

        return self._decrypt(entry.encrypted_value)

    def rotate(self, name: str, new_value: str) -> Dict[str, Any]:
        """Rotate a secret to a new value."""
        entry = self._secrets.get(name)
        if not entry:
            raise KeyError(f"Secret '{name}' not found")

        now = datetime.now(timezone.utc).isoformat()
        old_version = entry.version
        entry.encrypted_value = self._encrypt(new_value)
        entry.version += 1
        entry.rotated_at = now

        self._rotation_history.append({
            "secret": name,
            "old_version": old_version,
            "new_version": entry.version,
            "rotated_at": now,
        })

        logger.info(f"Secret rotated: {name} v{old_version} -> v{entry.version}")
        return {"name": name, "old_version": old_version, "new_version": entry.version, "rotated_at": now}

    def delete(self, name: str) -> bool:
        """Delete a secret."""
        with self._lock:
            if name in self._secrets:
                del self._secrets[name]
                logger.info(f"Secret deleted: {name}")
                return True
        return False

    def check_rotation_needed(self) -> List[Dict[str, Any]]:
        """Check which secrets need rotation."""
        now = datetime.now(timezone.utc)
        needs_rotation = []

        for entry in self._secrets.values():
            rotated = datetime.fromisoformat(entry.rotated_at)
            days_since = (now - rotated).days
            if days_since >= entry.rotation_policy_days:
                needs_rotation.append({
                    "name": entry.name,
                    "days_since_rotation": days_since,
                    "policy_days": entry.rotation_policy_days,
                    "status": "overdue",
                })
            elif days_since >= entry.rotation_policy_days - 14:
                needs_rotation.append({
                    "name": entry.name,
                    "days_since_rotation": days_since,
                    "policy_days": entry.rotation_policy_days,
                    "status": "upcoming",
                })

        return needs_rotation

    def audit(self) -> Dict[str, Any]:
        """Full audit of secrets inventory."""
        now = datetime.now(timezone.utc)
        inventory = []
        issues = []

        for entry in self._secrets.values():
            rotated = datetime.fromisoformat(entry.rotated_at)
            days_since = (now - rotated).days

            item = {
                "name": entry.name,
                "version": entry.version,
                "created_at": entry.created_at,
                "rotated_at": entry.rotated_at,
                "days_since_rotation": days_since,
                "rotation_policy_days": entry.rotation_policy_days,
                "tags": entry.tags,
                "access_count": len(entry.access_log),
                "status": "healthy",
            }

            if days_since >= entry.rotation_policy_days:
                item["status"] = "rotation_overdue"
                issues.append({"secret": entry.name, "issue": "rotation_overdue", "severity": "high"})
            elif days_since >= entry.rotation_policy_days - 14:
                item["status"] = "rotation_soon"
                issues.append({"secret": entry.name, "issue": "rotation_upcoming", "severity": "medium"})

            inventory.append(item)

        return {
            "total_secrets": len(self._secrets),
            "inventory": inventory,
            "issues": issues,
            "rotation_history": self._rotation_history[-20:],
            "policies": {
                "default_rotation_days": 90,
                "encryption": "Fernet (AES-128-CBC)",
                "key_derivation": "SHA-256",
                "access_logging": True,
            },
        }

    @property
    def stats(self) -> Dict[str, Any]:
        return {
            "total_secrets": len(self._secrets),
            "needs_rotation": len(self.check_rotation_needed()),
            "total_rotations": len(self._rotation_history),
        }
