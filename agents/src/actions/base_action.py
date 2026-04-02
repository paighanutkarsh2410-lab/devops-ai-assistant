"""
Base class for all remediation actions.
"""
from abc import ABC, abstractmethod
from typing import Tuple


class RemediationAction(ABC):
    """Abstract base class for remediation actions."""

    name: str = "base_action"
    description: str = "Base remediation action"
    risk_level: str = "MEDIUM"  # LOW, MEDIUM, HIGH
    estimated_duration_seconds: int = 30

    @abstractmethod
    def validate(self, context: dict) -> Tuple[bool, str]:
        """Validate that the action can be performed. Returns (valid, message)."""
        pass

    @abstractmethod
    def execute(self, context: dict) -> dict:
        """Execute the action. Returns {"success": bool, "message": str, ...}."""
        pass

    @abstractmethod
    def rollback(self, context: dict) -> dict:
        """Rollback the action. Returns {"success": bool, "message": str}."""
        pass

    def verify(self, context: dict) -> dict:
        """Verify the action was successful. Returns {"success": bool, "score": int}."""
        return {"success": True, "score": 50, "message": "No verification implemented"}

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "risk_level": self.risk_level,
            "estimated_duration_seconds": self.estimated_duration_seconds,
        }
