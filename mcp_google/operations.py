import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

PendingOperations = Dict[str, Dict[str, Any]]

pending_operations: PendingOperations = {}


def create_backup(
    data: Any, backup_type: str, identifier: str, backup_dir: str, logger
) -> str:
    """Create a backup file and return its path."""
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backup_{backup_type}_{identifier}_{timestamp}.json"
    filepath = os.path.join(backup_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logger.info("Backup created: %s", filepath)
    return filepath


def cleanup_expired_operations(
    store: Optional[PendingOperations] = None, ttl_minutes: int = 10
) -> None:
    """Remove operations older than TTL minutes."""
    if store is None:
        store = pending_operations
    now = datetime.now()
    expired = []
    for op_id, op in store.items():
        created = datetime.fromisoformat(op["created_at"])
        if now - created > timedelta(minutes=ttl_minutes):
            expired.append(op_id)

    for op_id in expired:
        del store[op_id]


def new_operation_id() -> str:
    return str(uuid.uuid4())[:8]
