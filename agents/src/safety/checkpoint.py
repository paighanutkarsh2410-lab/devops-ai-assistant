"""
Checkpoint Manager: Creates and restores service state snapshots for rollback.
"""
import json
import os
import uuid
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

CHECKPOINT_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'checkpoints')


class CheckpointManager:
    """Manages service state checkpoints for safe rollback."""

    def __init__(self, storage_dir: str = None):
        self.storage_dir = storage_dir or CHECKPOINT_DIR
        os.makedirs(self.storage_dir, exist_ok=True)

    def create_checkpoint(self, service: str, context: dict) -> str:
        """
        Create a checkpoint of current service state.
        Returns checkpoint_id.
        """
        checkpoint_id = f"chk_{service}_{uuid.uuid4().hex[:8]}"
        checkpoint = {
            "id": checkpoint_id,
            "service": service,
            "created_at": datetime.utcnow().isoformat(),
            "state": {
                "metrics": context.get("metrics", {}),
                "config": context.get("config", {}),
                "container_state": context.get("container_state", {}),
                "replicas": context.get("replicas", 1),
                "version": context.get("version", ""),
                "env_vars": context.get("env_vars", {}),
            },
            "restored": False,
        }

        filepath = os.path.join(self.storage_dir, f"{checkpoint_id}.json")
        with open(filepath, 'w') as f:
            json.dump(checkpoint, f, indent=2)

        logger.info(f"[Checkpoint] Created {checkpoint_id} for {service}")
        return checkpoint_id

    def restore_checkpoint(self, checkpoint_id: str) -> dict:
        """
        Restore a checkpoint. Returns the saved state.
        The caller is responsible for applying the state to the service.
        """
        filepath = os.path.join(self.storage_dir, f"{checkpoint_id}.json")
        if not os.path.exists(filepath):
            logger.error(f"[Checkpoint] Not found: {checkpoint_id}")
            return {}

        with open(filepath) as f:
            checkpoint = json.load(f)

        checkpoint["restored"] = True
        checkpoint["restored_at"] = datetime.utcnow().isoformat()
        with open(filepath, 'w') as f:
            json.dump(checkpoint, f, indent=2)

        logger.info(f"[Checkpoint] Restored {checkpoint_id} for {checkpoint['service']}")
        return checkpoint.get("state", {})

    def get_checkpoint(self, checkpoint_id: str) -> dict:
        """Get checkpoint data without restoring."""
        filepath = os.path.join(self.storage_dir, f"{checkpoint_id}.json")
        if not os.path.exists(filepath):
            return {}
        with open(filepath) as f:
            return json.load(f)

    def list_checkpoints(self, service: str = None) -> list:
        """List all checkpoints, optionally filtered by service."""
        checkpoints = []
        for fname in os.listdir(self.storage_dir):
            if fname.endswith('.json'):
                filepath = os.path.join(self.storage_dir, fname)
                try:
                    with open(filepath) as f:
                        data = json.load(f)
                    if service is None or data.get("service") == service:
                        checkpoints.append(data)
                except Exception:
                    continue
        return sorted(checkpoints, key=lambda c: c.get("created_at", ""), reverse=True)

    def cleanup_old(self, max_age_hours: int = 24):
        """Remove checkpoints older than max_age_hours."""
        cutoff = datetime.utcnow()
        removed = 0
        for fname in os.listdir(self.storage_dir):
            if fname.endswith('.json'):
                filepath = os.path.join(self.storage_dir, fname)
                try:
                    with open(filepath) as f:
                        data = json.load(f)
                    created = datetime.fromisoformat(data.get("created_at", ""))
                    age_hours = (cutoff - created).total_seconds() / 3600
                    if age_hours > max_age_hours:
                        os.remove(filepath)
                        removed += 1
                except Exception:
                    continue
        if removed:
            logger.info(f"[Checkpoint] Cleaned up {removed} old checkpoints")
