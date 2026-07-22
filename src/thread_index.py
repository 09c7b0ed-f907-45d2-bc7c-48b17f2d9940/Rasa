"""Thread index helpers for Rasa custom thread routes.

Pure, storage-agnostic functions only. Persistence lives in
thread_index_store.py (a plain Redis key-value store, one JSON value per
user) -- these functions just transform already-loaded payload dicts.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_thread_list_from_payload(payload: Any) -> dict[int, dict[str, Any]]:
    """Build active thread records from a JSON payload persisted in the index store."""
    if not payload:
        return {}

    try:
        data = json.loads(payload) if isinstance(payload, str) else payload
    except (json.JSONDecodeError, TypeError):
        return {}

    if not isinstance(data, dict):
        return {}

    threads: dict[int, dict[str, Any]] = {}
    for raw_id, raw_thread in data.items():
        try:
            thread_id = int(raw_id)
        except (TypeError, ValueError):
            continue

        if not isinstance(raw_thread, dict):
            continue

        action = raw_thread.get("action", "create")
        if action == "delete":
            continue

        created_at = raw_thread.get("created_at")
        updated_at = raw_thread.get("timestamp")
        threads[thread_id] = {
            "id": thread_id,
            "name": str(raw_thread.get("name", "")),
            "created_at": created_at if isinstance(created_at, str) else utcnow_iso(),
            "updated_at": updated_at if isinstance(updated_at, str) else utcnow_iso(),
            "deleted": False,
        }

    return threads


def build_thread_list_response(threads: dict[int, dict[str, Any]]) -> dict[str, Any]:
    """Serialize thread records into API response format."""
    ordered_threads = sorted(
        threads.values(),
        key=lambda thread: thread.get("updated_at", ""),
        reverse=True,
    )

    return {
        "threads": ordered_threads,
        "count": len(ordered_threads),
        "timestamp": utcnow_iso(),
    }


def next_thread_id_from_payload(payload: dict[str, Any]) -> int:
    """Return the next monotonic thread id from persisted index payload."""
    max_thread_id = 0
    for raw_id in payload.keys():
        try:
            parsed = int(raw_id)
        except (TypeError, ValueError):
            continue
        if parsed > max_thread_id:
            max_thread_id = parsed
    return max_thread_id + 1


def apply_index_action(payload: dict[str, Any], thread_id: int, action: str, name: str = "") -> dict[str, Any]:
    """Apply create/rename/delete action to an in-memory index payload."""
    next_payload = dict(payload)
    key = str(thread_id)
    current = next_payload.get(key)
    current_data = current if isinstance(current, dict) else {}

    now = utcnow_iso()
    if action == "create":
        next_payload[key] = {
            "id": thread_id,
            "name": str(name),
            "action": "create",
            "created_at": current_data.get("created_at", now),
            "timestamp": now,
        }
    elif action == "rename":
        created_at = current_data.get("created_at", now)
        next_payload[key] = {
            "id": thread_id,
            "name": str(name),
            "action": "rename",
            "created_at": created_at,
            "timestamp": now,
        }
    elif action == "delete":
        created_at = current_data.get("created_at", now)
        next_payload[key] = {
            "id": thread_id,
            "name": str(current_data.get("name", "")),
            "action": "delete",
            "created_at": created_at,
            "timestamp": now,
        }
    else:
        raise ValueError(f"Unsupported action: {action}")

    return next_payload