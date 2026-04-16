"""Secrets management API endpoints."""
import sys
import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict
from utils.auth import get_current_user

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "security"))

router = APIRouter(prefix="/secrets", tags=["secrets"])

# Singleton secrets manager
_manager = None


def _get_manager():
    global _manager
    if _manager is None:
        from secrets_manager import SecretsManager
        _manager = SecretsManager()
    return _manager


class SecretStore(BaseModel):
    name: str
    value: str
    tags: Optional[Dict[str, str]] = None
    rotation_days: int = 90


class SecretRotate(BaseModel):
    new_value: str


@router.get("/audit")
def audit_secrets(current_user=Depends(get_current_user)):
    """Full secrets audit — inventory, issues, rotation history."""
    return _get_manager().audit()


@router.get("/rotation-check")
def check_rotations(current_user=Depends(get_current_user)):
    """Check which secrets need rotation."""
    return {"needs_rotation": _get_manager().check_rotation_needed()}


@router.post("/store")
def store_secret(data: SecretStore, current_user=Depends(get_current_user)):
    """Store or update a secret."""
    result = _get_manager().store(data.name, data.value, data.tags, data.rotation_days)
    return result


@router.post("/{name}/rotate")
def rotate_secret(name: str, data: SecretRotate, current_user=Depends(get_current_user)):
    """Rotate a secret to a new value."""
    try:
        return _get_manager().rotate(name, data.new_value)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Secret '{name}' not found")


@router.delete("/{name}")
def delete_secret(name: str, current_user=Depends(get_current_user)):
    """Delete a secret."""
    if _get_manager().delete(name):
        return {"deleted": name}
    raise HTTPException(status_code=404, detail=f"Secret '{name}' not found")
